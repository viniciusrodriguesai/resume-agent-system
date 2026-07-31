# Resume Match AI V5.2

Atualização pequena e compatível com a arquitetura da V5.1.

## Alterações

- nova escala de compatibilidade: baixa, moderada, boa, alta e excelente;
- cartão principal mais compacto;
- cards com textos mais claros;
- separação entre lacunas obrigatórias e desejáveis;
- resumo automático da análise;
- aviso quando todos os requisitos obrigatórios têm evidência;
- painel de pontos fortes e lacunas principais;
- relatórios e documentação atualizados;
- versão do cache alterada para 5.2.0.

## Compatibilidade

Não adiciona dependências obrigatórias. A mesma `.venv` da V5.1 pode ser reutilizada.

## V5.2.1 — correção de compatibilidade de sessão

- remove automaticamente resultados antigos incompatíveis com o esquema atual;
- trata `ValidationError` sem derrubar a aplicação;
- atualiza a versão interna e a chave de cache para `5.2.1`.
