# Segurança e privacidade

Este documento descreve os controles realmente implementados na V6 e seus limites.
O sistema processa currículos, que devem ser tratados como dados pessoais mesmo
quando a execução é local.

## Modelo de ameaça

As principais entradas não confiáveis são arquivos enviados, textos de currículo e
vaga, cabeçalhos HTTP e configuração de ambiente. Os riscos considerados incluem
exposição de PII, MIME spoofing, path traversal, ZIP bombs, XML perigoso, abuso de
parser, payloads excessivos, injeção em logs, acesso não autorizado e persistência
local indevida.

O projeto não é um sandbox antimalware e não isola parsers em outro processo. Não
exponha a aplicação diretamente à internet nem aceite arquivos de origem desconhecida
sem controles adicionais de borda.

## Uploads e parsing

Formatos aceitos por padrão: PDF, DOCX e TXT, com limite de 10 MB por arquivo.
`resume_ai/infrastructure/security.py` valida antes do parser:

- nome simples, sem separadores, caracteres reservados, controles ou nomes de
  dispositivo do Windows;
- extensão permitida e, quando informado, MIME declarado igual ao formato esperado;
- assinatura PDF, versão reconhecida e marcador final próximo ao fim do arquivo;
- estrutura ZIP do DOCX, entradas únicas, caminhos relativos, ausência de links
  simbólicos e apenas compressões permitidas;
- DOCX não criptografado, até 2.048 entradas, até 50 MB descompactados, limites por
  entrada e razão de compressão;
- presença de `word/document.xml` e do content type principal do Word;
- ausência de `DOCTYPE` e `ENTITY` em XML e relacionamentos do DOCX;
- TXT UTF-8, sem NUL nem caracteres de controle binários.

O parser limita PDFs a 40 páginas e interrompe a extração ao atingir
`RESUME_MAX_DOCUMENT_CHARS`. Erros de bibliotecas e caminhos locais são encapsulados
em mensagens públicas genéricas. Esses controles reduzem risco, mas não substituem
antivírus, isolamento de processo ou limites de CPU/memória do sistema operacional.

## Minimização e anonimização

O currículo passa pelo agente de privacidade antes da estruturação e dos embeddings.
O modo base usa expressões regulares locais para e-mail, telefone, CPF, CNPJ, CEP,
RG, URL, endereço, nascimento, identificadores sociais, nomes rotulados e uma
provável linha de nome próxima ao cabeçalho. O modo completo pode complementar esse
processo com Microsoft Presidio.

Anonimização automática é imperfeita: dados indiretos, formatos inesperados e texto
extraído incorretamente podem permanecer. O resultado deve ser revisado antes de ser
compartilhado.

Por padrão:

- currículo bruto não é persistido;
- cache fica em memória;
- cache em disco é recusado sem
  `RESUME_STORE_ANONYMIZED_DOCUMENTS=true`;
- SQLite não salva currículo, vaga completa, título inferido ou evidências;
- o histórico atual salva ID, horário, perfil, score, nível, tempos e somente flags
  enumeradas do estado do motor;
- a retenção padrão mantém as 500 entradas mais recentes e pode ser reduzida por
  configuração.

O arquivo SQLite e seus arquivos WAL/SHM são ignorados pelo Git. Quem opera a
instalação é responsável por permissões, backup, retenção e exclusão do diretório
`data`.

## API

A FastAPI implementa:

- limite de corpo antes da desserialização, inclusive para streaming;
- limites Pydantic e limites menores configuráveis no serviço;
- allowlist de perfis;
- rate limiting em memória por endereço de cliente;
- chave `X-API-Key` opcional fora de produção e obrigatória quando
  `RESUME_ENVIRONMENT=production`;
- comparação da chave em tempo constante;
- CORS explícito, sem credenciais;
- `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` e
  `Permissions-Policy`;
- `Cache-Control: no-store` na análise;
- envelope de erro público sem detalhes de exceção;
- `X-Request-ID` validado, limitado e devolvido na resposta.

O limitador é por processo e a tabela de clientes não possui armazenamento
distribuído. `/health`, `/ready`, `/v1/profiles` e `/metrics` não exigem API key.
Coloque autenticação, TLS, limites globais e proteção contra abuso em um proxy ou
gateway para qualquer uso em rede.

Não há HSTS porque o projeto não termina TLS. Configure HSTS somente no componente
que realmente oferece HTTPS.

## Streamlit e autenticação

O Streamlit mantém proteção XSRF e CORS habilitadas, oculta detalhes de erro e limita
upload e mensagem a 10 MB. Login OIDC é opcional e só é aplicado quando
`RESUME_REQUIRE_LOGIN=true`. Consulte [AUTHENTICATION.md](AUTHENTICATION.md).

Os bindings do Docker Compose são `127.0.0.1` por padrão. Alterar para uma interface
de rede amplia deliberadamente a superfície de ataque.

## Logs, métricas e correlação

Logs estruturados aceitam apenas nomes técnicos de evento e campos operacionais
enumerados. Strings longas, e-mails, telefones, objetos arbitrários, quebras de linha
e campos desconhecidos são removidos ou redigidos. Currículo, vaga, evidências e
mensagens de exceção não são enviados ao logger.

Os identificadores de correlação aceitam no máximo 64 caracteres de um alfabeto
restrito; valores inválidos são substituídos por UUID local. Métricas incluem
contagens, latência, cache, score mais recente e memória do processo, sem conteúdo dos
documentos.

## Segredos e artefatos

Nunca versione `.env`, `.streamlit/secrets.toml`, chaves, tokens, bancos, uploads,
cache ou relatórios privados. `.gitignore` e `.dockerignore` cobrem esses padrões,
mas devem ser tratados como última defesa, não como cofre.

Use variáveis de ambiente ou o gerenciador de segredos do ambiente. Não coloque
segredos em argumentos de imagem, commits, logs, fixtures ou exemplos.

## Dependências e containers

O CI executa `pip-audit` sobre `requirements.txt`; findings não devem ser ocultados.
Dependências opcionais precisam de auditoria separada quando forem instaladas.

A imagem usa base Python fixada por digest, copia apenas artefatos de runtime e roda
como UID 10001. Isso melhora reprodutibilidade e reduz privilégios, mas não prova que
a imagem está livre de vulnerabilidades de sistema operacional. Build e execução
reais dependem de um daemon Docker disponível e são registrados separadamente na
validação da versão.

## Uso responsável

O score é evidência auxiliar. Não use o sistema para decisão automática de
contratação, inferência de atributos sensíveis ou ranking definitivo de pessoas.
Mantenha revisão humana, possibilidade de contestação e avaliação periódica de viés.

## Relato de vulnerabilidade

Não publique currículos, segredos ou detalhes exploráveis em issues abertas. Use o
canal privado de segurança do repositório quando disponível e inclua passos mínimos
de reprodução com dados sintéticos.
