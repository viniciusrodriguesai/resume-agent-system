# Segurança e privacidade

- extensões permitidas: PDF, DOCX e TXT;
- limite padrão: 10 MB;
- assinatura de PDF e estrutura de DOCX validadas;
- DOCX protegido contra arquivos criptografados, excesso de entradas e ZIP bombs;
- dados pessoais removidos antes de embeddings e cache;
- cache de resultados somente em memória por padrão;
- cache em disco exige `RESUME_STORE_ANONYMIZED_DOCUMENTS=true`;
- nenhum currículo ou vaga é registrado em logs;
- histórico SQLite não guarda documentos;
- `.env`, segredos, caches e bancos locais estão no `.gitignore`;
- API key opcional em desenvolvimento e obrigatória quando `RESUME_ENVIRONMENT=production`;
- limite de corpo, texto, perfis permitidos e requisições por minuto na API;
- XSRF do Streamlit permanece habilitado;
- dependências auditadas no CI com `pip-audit`.

Arquivos `.env`, chaves privadas, bancos, WAL/SHM, uploads e relatórios privados são excluídos do Git e do contexto de build Docker.

Não exponha Streamlit ou FastAPI diretamente na internet sem HTTPS, autenticação, proxy reverso e revisão adicional. Rate limiting em memória protege uma única instância; deployments distribuídos devem usar um limitador compartilhado no gateway.
