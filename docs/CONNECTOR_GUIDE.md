# Guia para criar conectores

Um conector do Auto-SPED traduz uma fonte externa para o contrato fiscal
`FiscalDataProvider`. Ele conhece tabelas, APIs ou arquivos da origem, mas não
decide regras de escrituração. Normalização, validação e geração permanecem no
núcleo para que todos os conectores produzam o mesmo comportamento fiscal.

Use como ponto de partida o
[`TemplateProvider`](../examples/connectors/template_provider.py). O exemplo é
executável, não abre conexões e permite testar o contrato com dados anônimos
antes de integrar a fonte real.

## Responsabilidades

O conector deve:

- abrir a fonte em modo somente leitura durante captura e fechar recursos;
- filtrar documentos pelo período solicitado, incluindo as duas datas;
- traduzir nomes da origem para os nomes fiscais canônicos;
- preservar identificadores de origem em `DOC_ID`, `VENDA_ID` e `ORIGEM`;
- retornar valores brutos confiáveis, sem inventar CST, CFOP ou tributação;
- explicar cada captura por meio de `describe_capture()`;
- evitar estado global, credenciais no código e alterações silenciosas na fonte.

O conector não deve montar linhas `|C100|`, `|C170|` ou outras linhas TXT.
Essa responsabilidade é do núcleo.

## Contrato mínimo

Implemente os atributos `provider_id` e `display_name` e estes métodos:

| Método | Resultado |
| --- | --- |
| `describe_capture()` | origem e destino de cada grupo de campos |
| `get_company_info()` | empresa declarante |
| `get_accountant_info()` | contabilista |
| `get_participants()` | clientes e fornecedores referenciados |
| `get_products()` | itens referenciados nos documentos |
| `get_units()` | unidades usadas pelos produtos e itens |
| `get_invoices(início, fim)` | documentos fiscais do período |
| `get_invoice_items_by_ids(...)` | itens de um documento específico |

Os resultados são dicionários ou sequências de dicionários. O contrato
completo e tipado está em `sped_mensal/providers/base.py`.

## Campos canônicos principais

O conjunto exato depende dos modelos e operações existentes na fonte. Estes
são os campos centrais que devem ser priorizados:

| Entidade | Campos principais |
| --- | --- |
| Empresa | `NOME`, `CNPJ` ou `CPF`, `IE`, `UF`, `COD_MUN` |
| Participante | `COD_PART`, `NOME`, `COD_PAIS`, `CNPJ` ou `CPF`, `IE`, `COD_MUN` |
| Produto | `COD_ITEM`, `DESCR_ITEM`, `UNID_INV`, `TIPO_ITEM`, `COD_NCM`, `CEST`, `ALIQ_ICMS` |
| Unidade | `UNID`, `DESCR` |
| Documento | `DOC_ID`, `VENDA_ID`, `ORIGEM`, `IND_OPER`, `COD_MOD`, `COD_SIT`, `SER`, `NUM_DOC`, `CHV_NFE`, `DT_DOC`, `DT_E_S`, `COD_PART`, `VL_DOC`, `VL_MERC` |
| Item | `NUM_ITEM`, `COD_ITEM`, `QTD`, `UNID`, `VL_ITEM`, `VL_DESC`, `CST_ICMS`, `CFOP`, `VL_BC_ICMS`, `ALIQ_ICMS`, `VL_ICMS` |

Datas podem chegar nos formatos aceitos pelo núcleo, mas prefira `AAAA-MM-DD`.
Valores devem manter a precisão da fonte, idealmente como `Decimal`; não use
`float` para arredondar valores fiscais. Códigos com zeros à esquerda devem ser
texto.

## Sequência de implementação

1. Copie `examples/connectors/template_provider.py` para seu pacote.
2. Troque `provider_id`, `display_name` e o mapa de captura.
3. Implemente a leitura da fonte e traduza cada linha para os campos acima.
4. Mantenha a leitura e a tradução em funções separadas.
5. Teste primeiro com um período sem movimento e depois com compras, NF-e,
   NFC-e, cancelamentos e tributações distintas.
6. Execute `python -m pytest -q` e compare o resultado no PVA aplicável.

## Critérios para contribuição

- nenhum banco, XML real, credencial ou dado identificável no commit;
- testes anônimos para filtro de período, vínculo documento/item e mapeamentos;
- mapa de captura completo e legível na interface e na CLI;
- erros de conexão com mensagem acionável, sem ocultar a exceção original;
- compatibilidade com a versão mínima de Python declarada no projeto;
- nenhuma mudança no fluxo Firebird homologado para adicionar o conector.

Antes de considerar um conector pronto para produção, valide amostras no PVA
e reconcilie totais por documento, CFOP, CST e apuração. A aceitação pelo PVA
não substitui a conferência fiscal da empresa.
