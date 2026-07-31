from pathlib import Path
from resume_v4.workflow import SistemaV4
base=Path(__file__).resolve().parent
curriculo=(base/'examples'/'curriculo_exemplo.txt').read_text(encoding='utf-8')
vaga=(base/'examples'/'vaga_exemplo.txt').read_text(encoding='utf-8')
resultado=SistemaV4().analisar(curriculo,vaga)
print(resultado['revisao']['texto_final'])
print(resultado['relatorio_markdown'])
