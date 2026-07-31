# Roteiro de apresentação

## 1. Problema

Comparadores simples de currículos procuram apenas palavras idênticas. Isso gera falsos negativos e fornece pouca explicação.

## 2. Solução

A V4 usa agentes especializados, recuperação semântica, reranqueamento, catálogo de competências, privacidade e auditoria.

## 3. Demonstração

1. Enviar ou colar currículo e vaga.
2. Mostrar os dados pessoais removidos.
3. Mostrar a estrutura do currículo e da vaga.
4. Abrir a tabela de requisitos e evidências.
5. Explicar a pontuação por categoria.
6. Mostrar o ciclo de revisão no rastreio.
7. Baixar o relatório.
8. Abrir o histórico.

## 4. Diferencial multiagente

O revisor não apenas escreve uma conclusão. Ele pode devolver a análise ao agente de evidências, aumentar a quantidade de candidatos recuperados e executar uma segunda passagem.

## 5. Parte experimental

Comparar:

- TF-IDF + RapidFuzz;
- BGE-M3 sem reranker;
- BGE-M3 com reranker.

Medir precisão, recall, F1 e matriz de confusão.

## 6. Limitações

- O ESCO completo precisa ser importado separadamente.
- Modelos grandes exigem memória e tempo na primeira execução.
- A análise apoia pessoas; não deve substituir decisões humanas.
