# Instalação e deployment

A V6 é local-first. Não existe deployment público oficial declarado neste
repositório. Os caminhos suportados são execução Python direta e containers locais.
Para rede, adicione proxy, TLS, autenticação e controles operacionais externos.

## Requisitos

- Python 3.11, 3.12 ou 3.13;
- ambiente virtual recomendado;
- acesso ao índice de pacotes durante a instalação;
- Docker apenas para o caminho de containers;
- internet e espaço adicionais se modelos opcionais forem baixados.

## Instalação base

PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Bash:

```bash
python -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Copie `.env.example` para `.env` somente na máquina de execução e revise os
valores. Nunca versione `.env`.

## Dependências opcionais

```bash
python -m pip install -r requirements-ai.txt
python -m pip install -r requirements-full.txt
```

`requirements-ai.txt` adiciona a pilha Torch de embeddings e reranker.
`requirements-full.txt` acrescenta Presidio, Docling, LanceDB e Prometheus, além
da restrição transitiva de `cryptography` exigida pela auditoria. Instalar um pacote
não garante que o modelo correspondente já esteja baixado ou que o backend funcione
na plataforma.

Para pré-carregar:

```bash
python scripts/preload_models.py --profile demo
```

## Streamlit

```bash
python -m streamlit run app.py
```

O endereço padrão é `http://127.0.0.1:8501`. A configuração versionada:

- limita upload e mensagens a 10 MB;
- mantém XSRF e CORS do Streamlit;
- oculta detalhes de erro;
- desativa telemetria de uso;
- executa headless.

Para exigir OIDC, configure `RESUME_REQUIRE_LOGIN=true` e os segredos do provedor
fora do Git. Consulte [../AUTHENTICATION.md](../AUTHENTICATION.md).

## FastAPI

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Verifique:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

Em produção, defina `RESUME_ENVIRONMENT=production` e `RESUME_API_KEY`. Isso não
habilita HTTPS; termine TLS no proxy. Veja [API.md](API.md) e
[../SECURITY.md](../SECURITY.md).

## Persistência local

O histórico padrão usa `data/history.sqlite3`. Cache de resultados fica em memória,
a menos que o operador habilite cache em disco e consinta com armazenamento de texto
anonimizado.

Garanta:

- diretório gravável apenas pelo usuário da aplicação;
- backup e retenção definidos pelo operador;
- volume persistente se o histórico deve sobreviver a recriações de container;
- exclusão segura quando os dados deixam de ser necessários;
- nenhum compartilhamento do diretório em serviço público de arquivos.

## Docker

O `Dockerfile`:

- usa Python 3.11 slim fixado por digest;
- instala apenas `requirements.txt`;
- copia somente aplicação e assets de runtime;
- cria diretórios graváveis antes de trocar usuário;
- executa como `appuser`, UID 10001;
- expõe 8501;
- verifica `/_stcore/health`;
- inicia Streamlit em `0.0.0.0` dentro do container.

Validar a configuração sem iniciar containers:

```bash
docker compose config
```

Build e inicialização:

```bash
docker compose build
docker compose up
```

O Compose cria dois serviços a partir da mesma imagem:

- `app`: Streamlit em `127.0.0.1:8501`;
- `api`: Uvicorn em `127.0.0.1:8000`, com probe em `/ready`.

Ambos desabilitam embeddings no perfil demo para evitar download durante startup e
montam `./data` em `/app/data`. Os bindings em loopback impedem exposição direta
em outras interfaces do host.

Para encerrar:

```bash
docker compose down
```

Esse comando remove containers e rede, mas preserva `./data` porque o Compose usa
bind mount. Revise o conteúdo antes de qualquer exclusão manual.

## Validação do container

Uma configuração válida não prova que a imagem foi construída. Com daemon
disponível, registre separadamente:

```bash
docker version
docker info
docker compose config
docker compose build
docker compose up
```

Depois confirme usuário, probes, portas, logs, shutdown e ausência de segredos na
configuração efetiva. Não registre como validado um build que não foi executado.

O build base não inclui modelos, Docling ou Presidio. Uma imagem para o perfil
completo exige decisão explícita sobre dependências, tamanho, download, cache e
licenças; ela não é gerada automaticamente pela V6.

## Empacotamento Python

```bash
python -m build
```

O comando deve produzir sdist e wheel em `dist`. O pacote inclui `api`,
`evaluation`, `resume_ai`, datasets JSON sintéticos e o módulo `app`. Diretórios
históricos, testes, slides, bancos e caches não pertencem à distribuição.

Valide o conteúdo e instale o wheel em ambiente temporário antes de publicar. A V6
não configura upload automático para PyPI.

## CI

O workflow em `.github/workflows/ci.yml` executa:

- unitários em Python 3.11, 3.12 e 3.13;
- integração, segurança e avaliação em Python 3.11;
- Ruff, mypy, regressão de qualidade e pip-audit;
- build de sdist e wheel.

Execução local não comprova o status remoto. Consulte o commit específico no GitHub
Actions e diferencie falhas de código, plataforma e infraestrutura.

## Checklist para exposição em rede

Antes de alterar os bindings de loopback:

- HTTPS e HSTS no proxy que termina TLS;
- autenticação e autorização adequadas ao público;
- rate limiting compartilhado e limites de conexão;
- proteção ou bloqueio de `/metrics`, `/health`, `/ready` e documentação;
- secrets manager e rotação de chaves;
- limites de CPU, memória, processos e disco;
- isolamento adicional de parsing;
- política de retenção, backup e exclusão do SQLite;
- monitoramento sem PII;
- scanner da imagem e SBOM;
- revisão jurídica e de uso responsável.

Kubernetes, worker, fila, Redis, PostgreSQL obrigatório e frontend React não fazem
parte desta versão.
