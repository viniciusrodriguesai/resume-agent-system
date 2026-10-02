"""Controlled internal ablation; reject a requested model that falls back to lexical."""
import argparse
import hashlib
import importlib.metadata
import json
import platform
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from resume_ai.application.analyze_resume import ResumeAnalysisService  # noqa: E402
from resume_ai.domain.models import AnalysisRequest  # noqa: E402
from resume_ai.evaluation import classification_metrics  # noqa: E402
from resume_ai.settings import Settings  # noqa: E402


def evaluate(path: Path, mode: str) -> dict:
    import resource

    import torch

    torch.manual_seed(0)
    torch.set_num_threads(2)
    data = json.loads(path.read_text())
    cases = data['cases']
    if not cases or any(c['expected'] not in {'matched', 'partial', 'missing'} for c in cases):
        raise ValueError('Every case requires an existing valid label')
    if len({c['id'] for c in cases}) != len(cases):
        raise ValueError('Duplicate case IDs')
    settings = Settings(embedding_enabled=mode!='lexical', reranker_enabled=mode=='reranked',
                        embedding_model='intfloat/multilingual-e5-small',
                        reranker_model='cross-encoder/mmarco-mMiniLMv2-L12-H384-v1',
                        embedding_device='cpu', history_enabled=False, cache_enabled=False,
                        log_level='ERROR')
    service = ResumeAnalysisService(settings)
    cold_start = time.perf_counter()
    if mode!='lexical' and service.engine._load_model() is None:
        raise RuntimeError(f'Embedding model failed: {service.engine.status}')
    if mode=='reranked' and service.engine._load_reranker() is None:
        raise RuntimeError(f'Reranker failed: {service.engine.status}')
    load_seconds = time.perf_counter()-cold_start
    revisions = {}
    if mode!='lexical':
        revisions['embedding'] = service.engine._model._first_module().auto_model.config._commit_hash
    if mode=='reranked':
        revisions['reranker'] = service.engine._reranker.model.config._commit_hash
    results = []
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024
    for case in cases:
        started = time.perf_counter()
        result = service.analyze(AnalysisRequest(resume_text=case['resume'],
                    job_text='Data internship\nREQUISITOS OBRIGATÓRIOS\n- '+case['requirement']))
        duration = time.perf_counter()-started
        if len(result.matches)!=1:
            raise ValueError('Exactly one requirement expected')
        status = service.engine.status
        if (mode!='lexical' and status['embedding_error']) or (mode=='reranked' and status['reranker_error']):
            raise RuntimeError(f'Inference fallback: {status}')
        match = result.matches[0]
        results.append({'id':case['id'], 'expected':case['expected'], 'predicted':match.status,
                        'category':case['category'], 'score':match.final_score,
                        'evidence':match.evidence, 'seconds':duration,
                        'retrieval_methods':sorted({c.retrieval_method for c in match.top_candidates})})
        rss=max(rss, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024)
    durations=sorted(c['seconds'] for c in results)
    metrics=classification_metrics([c['expected'] for c in results],[c['predicted'] for c in results])
    return {'mode':mode, 'annotation_origin':data['annotation_origin'], 'total':len(results), **metrics,
            'model_revisions':revisions, 'engine_status':service.engine.status,
            'settings':settings.model_dump(mode='json'), 'seed':0, 'torch_threads':2,
            'load_seconds_includes_download_if_uncached':load_seconds,
            'median_case_seconds':statistics.median(durations), 'p95_case_seconds':durations[int(.95*(len(durations)-1))],
            'process_high_water_rss_bytes':rss, 'python':platform.python_version(),
            'versions':{p:importlib.metadata.version(p) for p in ['torch','sentence-transformers','transformers','numpy','pandas','rapidfuzz','pydantic']},
            'dataset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'cases':results}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases',type=Path,required=True)
    parser.add_argument('--mode',choices=['lexical','embedding','reranked'],required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Preserve prior output; choose a new path')
    report=evaluate(args.cases,args.mode)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:
        json.dump(report,f,indent=2,ensure_ascii=False,allow_nan=False)
        f.write('\n')
    print(json.dumps({k:report[k] for k in ['mode','accuracy','macro_f1','median_case_seconds','engine_status']}))
