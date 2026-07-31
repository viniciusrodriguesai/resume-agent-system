# Arquitetura da V4

```text
INÍCIO
  ↓
Agente de Privacidade
  ↓
Agente de Currículo
  ↓
Agente de Vaga
  ↓
Recuperação híbrida de evidências
  ├── BGE-M3, quando instalado
  └── TF-IDF + RapidFuzz, como fallback
  ↓
Reranqueamento
  ├── BGE Reranker v2 M3, quando instalado
  └── pontuação de recuperação, como fallback
  ↓
Agente de Pontuação
  ↓
Agente Revisor
  ├── solicitar revisão → aumentar top-k → recuperar novamente
  └── aprovar
  ↓
Agente de Recomendações
  ↓
Agente de Relatório
  ↓
FIM
```

O LangGraph administra os nós e a rota condicional. Quando o pacote de checkpoint SQLite está disponível, o estado do grafo é salvo localmente. O histórico resumido também é armazenado em SQLite.

## Explicabilidade

Cada requisito recebe:

- prioridade;
- categoria;
- status;
- pontuação semântica;
- trecho do currículo usado como evidência;
- método de recuperação;
- método de reranqueamento.

## Modos de operação

### IA completa

- Docling;
- Presidio;
- BGE-M3;
- BGE Reranker v2 M3;
- LangGraph;
- ESCO importado.

### Fallback local

- PyPDF e python-docx;
- expressões regulares para privacidade;
- TF-IDF;
- RapidFuzz;
- catálogo ESCO de amostra.
