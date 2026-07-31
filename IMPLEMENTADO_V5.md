# Escopo entregue na V5.1

## Implementado e funcional localmente

- arquitetura modular e tipada;
- frontend Streamlit aprimorado;
- API FastAPI;
- perfis de desempenho;
- embeddings ONNX opcionais;
- fallback lexical completo;
- reranker opcional;
- privacidade pt-BR e Presidio opcional;
- uploads seguros;
- parsing PDF/DOCX/TXT;
- cache seguro e histórico mínimo;
- relatórios e gráficos;
- testes, CI, auditoria, Docker e scripts Windows.

## Preparado, mas depende de instalação/configuração opcional

- BGE-M3 e BGE Reranker;
- Docling;
- Presidio completo;
- LanceDB;
- OpenTelemetry/Prometheus;
- Playwright + axe-core;
- API key e autenticação externa.

Serviços externos, OIDC real, Redis/RQ, Grafana e Kubernetes não são ativados por padrão porque o requisito é execução local no VS Code e Windows.
