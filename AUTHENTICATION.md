# Autenticação

## Streamlit

Para uso somente no computador local, mantenha:

```dotenv
RESUME_REQUIRE_LOGIN=false
```

Quando `RESUME_REQUIRE_LOGIN=true`, a aplicação exige uma sessão OIDC fornecida pelo
Streamlit. Configure o provedor em `.streamlit/secrets.toml`, arquivo ignorado pelo
Git, conforme a documentação do Streamlit. Usuários não autenticados veem o botão de
entrada e a execução é interrompida; usuários autenticados recebem opção de logout.

OIDC não substitui TLS nem autorização por função. A aplicação apenas verifica se há
sessão autenticada; não implementa papéis, grupos ou políticas por usuário.

## FastAPI

A API aceita uma chave estática no header `X-API-Key`:

```dotenv
RESUME_API_KEY=gere-uma-chave-forte-e-mantenha-fora-do-git
```

Envie essa chave no header `X-API-Key` de `POST /v1/analyze`.

Quando a chave está configurada, o endpoint exige valor idêntico. Em
`RESUME_ENVIRONMENT=production`, a ausência de `RESUME_API_KEY` deixa a análise
indisponível com HTTP 503. Saúde, readiness, perfis e métricas permanecem públicos.

A chave é uma proteção simples para instalação local ou atrás de gateway; não há
rotação, usuários, escopos ou revogação individual. Para exposição em rede, termine
HTTPS e implemente autenticação e autorização no proxy ou gateway.

Veja também [SECURITY.md](SECURITY.md) para limites de CORS, rate limiting, logs e
deployment.
