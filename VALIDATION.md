# Validação realizada neste pacote

- todos os arquivos Python passaram por `compileall`;
- testes centrais executados: **5 passed**;
- fluxo completo executado sem modelos pesados, usando fallback local;
- exemplo de teste: 15 requisitos, nota 67%, 3 dados pessoais removidos;
- relatórios Markdown, JSON e CSV foram gerados;
- API `/health` foi validada pelo teste de integração.

Os modelos ONNX, BGE-M3, Docling e Presidio não foram baixados neste ambiente. Eles permanecem opcionais e o sistema continua funcional com o modo lexical local.
