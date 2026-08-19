# Roteiro de apresentação da V6

## 1. Problema

Uma porcentagem baseada apenas em palavras não mostra por que currículo e vaga
combinam. Requisitos obrigatórios, sinônimos, negações e evidências incompletas
precisam ser tratados de modo verificável.

## 2. Proposta

A V6 usa oito agentes sequenciais para anonimizar o currículo, estruturar as entradas,
recuperar evidências, calcular score, revisar casos limítrofes, recomendar ações e
gerar relatório. O fluxo é Python explícito; não usa LangGraph nem ciclo iterativo de
revisão.

## 3. Demonstração

Use apenas os exemplos sintéticos do repositório.

1. Selecione o perfil `demo` e rigor `equilibrado`.
2. Carregue o exemplo ou cole currículo e vaga sintéticos.
3. Confirme o aviso de uso responsável.
4. Execute a análise.
5. Mostre o score, os obrigatórios ausentes e o resumo.
6. Abra uma evidência e compare TF-IDF, RapidFuzz, semântico e score final.
7. Mostre recomendações que não inventam experiência.
8. Abra privacidade e explique o que foi removido antes dos embeddings.
9. Abra agentes e mostre duração, confiança, warnings e backend real.
10. Exporte um relatório.

Não afirme que o perfil semântico carregou sem conferir o painel do motor.

## 4. Arquitetura

Explique que Streamlit e FastAPI chamam `ResumeAnalysisService`. Domínio, agentes e
infraestrutura são separados, e SQLite implementa uma porta opcional de histórico.
O agente revisor somente diagnostica lacunas e limiares; não muda o score nem
reexecuta retrieval.

## 5. Avaliação

Mostre os comandos, não números copiados de outra máquina:

```bash
python scripts/benchmark_retrieval.py --runs 3 --k 3
python scripts/benchmark_pipeline.py --profile demo --runs 3
```

Explique Precision, Recall, F1, Precision@K, Recall@K, MRR, NDCG@K, média, p95 e
delta de RSS. Confirme SHA-256 do dataset e `backend_status`.

## 6. Engenharia

Apresente:

- `AgentResult` e diagnóstico individual;
- logs JSON e `X-Request-ID`;
- validação robusta de PDF, DOCX e TXT;
- erros seguros, limites, API key e CORS;
- suítes unit, integration, security e evaluation;
- CI em Python 3.11, 3.12 e 3.13;
- wheel, sdist e container non-root.

## 7. Limitações

- anonimização e matching podem errar;
- layouts complexos e PDFs de imagem podem falhar;
- datasets atuais são sintéticos e pequenos;
- não há avaliação sistemática de viés concluída;
- rate limiting, métricas e SQLite são locais;
- o resultado não toma decisão de contratação.
