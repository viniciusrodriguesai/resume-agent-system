# SkillSpan: external skill-component results v1

The unchanged catalog was evaluated against **existing human annotations from an external research team**, rather than this project's synthetic matching examples. Source: Zhang, Jensen, Sonniks and Plank, [SkillSpan (NAACL 2022)](https://aclanthology.org/2022.naacl-main.366/), [official repository](https://github.com/kris927b/SkillSpan) (MIT license). No test sentences or annotations are redistributed here.

**Finding: this small, fixed catalog has very low recall on broad job-posting skills. It is not a general skill extractor.** This component benchmark does not measure resume/job compatibility accuracy or replace independent annotation of the matched/partial/missing task.

## Scope and provenance

- [Protocol](SKILLSPAN_PROTOCOL.md) initially committed in `7dd26dd00a39701fa6212addf41c291fd1a2151c` before retrieving the test split. Catalog and normalization code remained unchanged.
- Published full test split, both released sources: 3,569 sentences, 42,786 tokens, **65 source/posting clusters**. Sentence count is not the number of independent resumes or jobs.
- Upstream revision `2ccf3de5b5af7a5409b8dd814fb1315dd6e0ae1b`; file SHA-256 `8438eda34939a5877b984ea5daf9e6ff39b2d5c7e3d73cca0499d3de3784d24a`.
- Two attempts aborted on source-format issues (plain BIO and orphan I tags) without producing aggregate reports. Corrections were documented and committed before the completed pass in `1f0c3ef444892e89ecfba43ae1252f7a426d180a`; no predictions/catalog were tuned. Runtime script and protocol hashes match the published report.
- One completed full-split pass, Python 3.12.14 / NumPy 2.2.6. Existing public test labels are external to the project, but this execution is by the developer, not a blinded third-party audit.

## Metrics

The API returns canonical skill names, not token spans. A fixed **localization adapter** projects aliases of detected names to minimal matching token windows. Gold-positive tokens are the union of the original non-O skill and knowledge labels. The denominator includes uncatalogued competencies; no easy/technical-only subset was selected.

These are adapter token metrics, **not exact-span NER leaderboard scores**. Localization is sentence-level: when a name is detected, alias windows can include another occurrence with a different local context. The catalog and adapter are both part of the measured component.

| Source | Sentences | Token precision | Token recall | Token F1 | Fully covered gold spans |
| --- | --- | --- | --- | --- | --- |
| all | 3569 | 0.7742 | 0.0420 | 0.0797 | 172/2248 |
| tech | 2286 | 0.7895 | 0.0672 | 0.1239 | 137/1237 |
| house | 1283 | 0.7200 | 0.0171 | 0.0334 | 35/1011 |

Overall: 264 true-positive tokens, 77 false-positive tokens, **6,016 missed gold tokens** out of 6,280. Predictions cover only 341 tokens. Low recall persists even in tech (6.72%); the result cannot be dismissed solely as a non-technical-domain mismatch. Fully covered spans are a secondary coverage measure, not exact-span precision/F1.

500 posting-cluster bootstrap replicates, seed 20261002, percentile 95% intervals: precision [0.7173, 0.8247], recall [0.0325, 0.0534], F1 [0.0623, 0.1002]. There are only 65 clusters; intervals reflect this sample and fixed catalog, not unseen languages or future vacancies.

## Product consequence

Keep the demo lexical by default: the [previous 36-case ablation](MODEL_ABLATION.md) found identical labels with lexical, E5-small, and E5-small plus mMARCO reranking, with higher model latency. `Settings()` and `Settings.for_profile("demo")` now disable embeddings by default, and `.env.example` agrees. Explicit `RESUME_EMBEDDING_ENABLED=true` still works; choosing balanced/complete explicitly keeps their model-enabled defaults. This operational choice is based on the bounded matching ablation, **not** on SkillSpan (the optional models act downstream, not in catalog extraction).

Do not present detected catalog skills as an exhaustive competence list. The requirement extractor also processes uncatalogued text; therefore 4.20% skill-token recall is not a claim that the entire matching pipeline misses 95.80% of job requirements. The matching pipeline remains separately unvalidated on real independently labeled pairs.

No catalog expansion or learned model was fit to this now-observed test. Future extraction work should use train/dev annotations for development and retain this test as exposed regression evidence. A new protected dataset is needed for a stronger prospective generalization claim.

## Reproduce

```bash
python -m pip install -r requirements-skillspan.txt
```

Retrieve `data/json/test.json` from the pinned upstream revision (it is JSONL despite its extension). Then, from the project root:

```bash
python scripts/evaluate_skillspan.py --data /path/to/test.json --output /path/to/new-output --source-revision 2ccf3de5b5af7a5409b8dd814fb1315dd6e0ae1b
python -m pytest tests/evaluation/test_skillspan_adapter.py tests/unit/test_settings.py
```

The output directory must be new. Do not overwrite a previous test report. Key numerical/parser dependencies are pinned in `requirements-skillspan.txt`; remaining application dependency ranges are not a complete environment lock. [Machine-readable aggregate report](../evaluation/external/skillspan-v1.json) includes source, protocol, script/catalog/normalizer fingerprints and bootstrap intervals.

## Full-pipeline independent evaluation still pending

The [reviewer guide and blank template](INDEPENDENT_EVALUATION.md) require independently annotated, consented or publicly licensed real resume/job pairs with per-requirement labels, two reviewers and adjudication. SkillSpan supplies job skill spans; it has no resume evidence or matched/partial/missing labels. Neither this benchmark nor the 36 self-authored cases can establish end-to-end generalization, ranking validity, fairness or hiring suitability. No such annotations or reviewer agreement have been invented.
