from resume_v4.config import Config
from resume_v4.workflow import SistemaV4

def sistema_fallback(monkeypatch,tmp_path):
    monkeypatch.setenv('RESUME_V4_DATA_DIR',str(tmp_path))
    monkeypatch.setenv('RESUME_V4_USAR_EMBEDDINGS','0')
    monkeypatch.setenv('RESUME_V4_USAR_RERANKER','0')
    monkeypatch.setenv('RESUME_V4_USAR_PRESIDIO','0')
    return SistemaV4(Config())

def test_fluxo_completo(monkeypatch,tmp_path):
    sistema=sistema_fallback(monkeypatch,tmp_path)
    curriculo='Ana\nana@example.com\nEstudante de Ciência de Dados. Python, SQL, Pandas e machine learning. Desenvolvi modelos preditivos.'
    vaga='Estágio em Dados\nObrigatório Python, SQL, Pandas e aprendizado de máquina. Desejável Docker e AWS.'
    resultado=sistema.analisar(curriculo,vaga)
    assert 0 <= resultado['pontuacao']['score_geral'] <= 100
    assert resultado['revisao']['decisao']=='aprovado'
    assert resultado['relatorio_markdown']
    assert len(resultado['rastreio'])>=8

def test_lacunas_limitam_pontuacao(monkeypatch,tmp_path):
    sistema=sistema_fallback(monkeypatch,tmp_path)
    resultado=sistema.analisar('Atendimento e comunicação.','Obrigatório Python SQL Docker AWS e machine learning.')
    assert resultado['pontuacao']['ausentes_obrigatorios']>=1
    assert resultado['pontuacao']['score_geral']<=72
