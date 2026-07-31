from __future__ import annotations
import argparse,csv
from pathlib import Path
from sklearn.metrics import classification_report,confusion_matrix
from resume_v4.workflow import SistemaV4

def avaliar(caminho: Path,limiar: int=62) -> None:
    sistema=SistemaV4(); y_true=[]; y_pred=[]
    with caminho.open(encoding='utf-8-sig',newline='') as arquivo:
        for linha in csv.DictReader(arquivo):
            resultado=sistema.analisar(linha['curriculo'],linha['vaga'])
            y_true.append(int(linha['rotulo']))
            y_pred.append(int(resultado['pontuacao']['score_geral']>=limiar))
    print(classification_report(y_true,y_pred,digits=3,zero_division=0))
    print('Matriz de confusão:')
    print(confusion_matrix(y_true,y_pred))

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('csv',type=Path)
    parser.add_argument('--limiar',type=int,default=62)
    args=parser.parse_args(); avaliar(args.csv,args.limiar)
