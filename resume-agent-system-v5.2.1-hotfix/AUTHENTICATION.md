# Autenticação opcional

Para uso apenas no seu computador, deixe `RESUME_REQUIRE_LOGIN=false`.

Quando a aplicação for exposta em rede, o projeto possui suporte opcional a `st.login`/OIDC. Defina `RESUME_REQUIRE_LOGIN=true` e configure o provedor no arquivo `.streamlit/secrets.toml`, que já está ignorado pelo Git.

A API também aceita uma chave local opcional em `RESUME_API_KEY`, enviada no header `X-API-Key`.
