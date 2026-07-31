from __future__ import annotations
import argparse,csv,sqlite3
from pathlib import Path
from resume_v4.config import Config

COLUNAS_ROTULO=['preferredLabel','preferred label','rotulo','label','title']
COLUNAS_ID=['conceptUri','concept uri','id','uri']
COLUNAS_ALT=['altLabels','alternative labels','aliases','alt labels']

def primeira(linha,opcoes):
    for coluna in opcoes:
        if coluna in linha and linha[coluna]: return linha[coluna]
    return ''

def importar(caminho: Path,categoria: str='esco') -> int:
    config=Config(); config.preparar(); registros=[]
    with caminho.open(encoding='utf-8-sig',newline='') as arquivo:
        leitor=csv.DictReader(arquivo)
        for indice,linha in enumerate(leitor,1):
            rotulo=primeira(linha,COLUNAS_ROTULO)
            if not rotulo: continue
            ident=primeira(linha,COLUNAS_ID) or f'esco-{indice}'
            aliases=primeira(linha,COLUNAS_ALT).replace(';','|')
            registros.append((ident,rotulo,categoria,aliases))
    with sqlite3.connect(config.banco_esco) as con:
        con.execute('CREATE TABLE IF NOT EXISTS competencias (id TEXT PRIMARY KEY, rotulo TEXT NOT NULL, categoria TEXT, aliases TEXT)')
        con.executemany('INSERT OR REPLACE INTO competencias VALUES (?,?,?,?)',registros)
    return len(registros)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description='Importa um CSV do ESCO para o catálogo local.')
    parser.add_argument('csv',type=Path)
    parser.add_argument('--categoria',default='esco')
    args=parser.parse_args()
    quantidade=importar(args.csv,args.categoria)
    print(f'{quantidade} competências importadas.')
