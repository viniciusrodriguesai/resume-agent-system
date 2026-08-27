# Resume Match AI 6.0.2

Patch de validação manual pós-release da versão 6.0.1. Esta versão corrige defeitos
de parsing, contexto e ranking observados no fluxo estável, sem introduzir features
da 6.1 nem alterar a arquitetura ou as dependências obrigatórias.

## CONFIRMED FIXES

- conceitos alternativos explicitamente negados não contam mais como experiência
  positiva; negações locais em português e inglês preservam um match OR válido
  quando outra alternativa possui evidência real;
- conhecimento básico, noções, estudo, leitura e cursos introdutórios não recebem
  automaticamente o boost de requisitos de experiência;
- cabeçalhos estruturais de vagas não são mais emitidos como requisitos, removendo
  sua contaminação de score, categorias, review, recomendações, gráficos e relatório;
- seções alternativas preservam origem `alternative` e prioridade neutra na
  representação backward-compatible atual, enquanto infraestrutura e requisitos
  técnicos mantêm prioridade obrigatória e origem própria;
- leitura de artigos ou tutoriais, estudo de conceitos e ocorrências negadas da
  mesma tecnologia não se combinam mais em experiência prática;
- CI/CD, pytest, Redis, RabbitMQ, Kubernetes, GitHub Actions, Terraform e
  CloudFormation passam a integrar o catálogo estruturado usado pela fixture,
  preservando negação e força contextual;
- evidência quantificada de volume de requisições ranqueia acima de experiência web
  genérica no fallback, com piso conservador parcial e sem equivalência universal
  entre uma quantidade fixa e alto volume;
- requisitos de experiência preferem evidência operacional a uma listagem isolada
  da tecnologia, sem invalidar listagens em requisitos de conhecimento;
- o parser de título preserva cargos explícitos em inglês, português e Unicode e
  não substitui o título por um parágrafo introdutório;
- a UI diferencia modelos carregados, habilitados com fallback e desativados, e
  apresenta motivos sanitizados quando uma dependência opcional está indisponível.

## INVESTIGATED — NO CHANGE REQUIRED

- embeddings e reranker continuam opcionais e carregados de forma preguiçosa por
  design; a instalação base usa fallback lexical determinístico quando
  `requirements-ai.txt` não está instalado;
- nenhuma dependência pesada foi promovida ao runtime obrigatório e os perfis
  `balanced` e `complete` continuam descrevendo configuração, não garantia de
  carregamento do backend;
- o suporte declarado permanece Python 3.11, 3.12 e 3.13.

## VALIDATION

- cenário sintético completo aprovado nos rigores flexível, equilibrado e
  conservador, com monotonicidade e privacidade preservadas;
- Python 3.11: 296 testes aprovados;
- cobertura de `resume_ai`: 89%;
- Ruff e mypy: aprovados;
- `pip-audit` de runtime e desenvolvimento: nenhuma vulnerabilidade conhecida;
- `pip check`, build de sdist/wheel, API smoke, Streamlit smoke e Docker Compose:
  aprovados;
- runtime Docker: não validado porque o daemon não estava disponível.
