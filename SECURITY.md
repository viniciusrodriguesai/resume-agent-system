# Segurança e privacidade

- extensões permitidas: PDF, DOCX e TXT;
- limite padrão: 10 MB;
- assinatura de PDF e estrutura de DOCX validadas;
- dados pessoais removidos antes de embeddings e cache;
- nenhum currículo ou vaga é registrado em logs;
- histórico SQLite não guarda documentos;
- `.env`, segredos, caches e bancos locais estão no `.gitignore`;
- API key opcional por `RESUME_API_KEY`;
- XSRF do Streamlit permanece habilitado;
- dependências auditadas no CI com `pip-audit`.

Não exponha o Streamlit diretamente na internet sem autenticação, HTTPS e revisão adicional.
