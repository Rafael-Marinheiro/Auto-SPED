# Adaptadores de referência

O Auto-SPED inclui três adaptadores genéricos para acelerar integrações. Eles
não substituem a validação fiscal dos dados e não alteram o capturador Firebird
homologado.

## Diretório CSV

`CsvDirectoryProvider` procura arquivos UTF-8 separados por ponto e vírgula:

```text
company.csv          accountant.csv
participants.csv     products.csv
units.csv            invoices.csv
invoice_items.csv
```

Os cabeçalhos podem usar diretamente os campos canônicos do
[guia de conectores](CONNECTOR_GUIDE.md). Para outros nomes, passe um
`DeclarativeMapping`. Arquivos de entidades sem dados podem ser omitidos.

```python
from sped_mensal.providers import CsvDirectoryProvider

provider = CsvDirectoryProvider("exportacao/")
```

## XML canônico

`XmlFileProvider` usa uma estrutura deliberadamente simples:

```xml
<auto-sped>
  <company NOME="EMPRESA" CNPJ="00000000000000" />
  <invoices>
    <row DOC_ID="1" VENDA_ID="10" COD_MOD="55" DT_DOC="2026-08-15" />
  </invoices>
  <invoice_items>
    <row DOC_ID="1" VENDA_ID="10" COD_MOD="55" COD_ITEM="A" />
  </invoice_items>
</auto-sped>
```

Campos também podem ser elementos filhos. Por segurança, DTD e entidades são
rejeitados e o tamanho padrão é limitado a 50 MiB. Este formato é uma ponte de
integração canônica; ele não pretende interpretar qualquer XML de NF-e sem uma
tradução específica.

## PostgreSQL

Instale o extra opcional:

```bash
pip install -e ".[postgres]"
```

`PostgresProvider` recebe sete consultas parametrizadas. As consultas de
documentos recebem `(start_date, end_date)`; a de itens recebe
`(cod_mod, doc_id, venda_id, ind_oper, origem)`. Todas as capturas iniciam a
transação com `SET TRANSACTION READ ONLY`.

```python
from sped_mensal.providers import PostgresProvider, PostgresQueries

queries = PostgresQueries(
    company="SELECT ...",
    accountant="SELECT ...",
    participants="SELECT ...",
    products="SELECT ...",
    units="SELECT ...",
    invoices="SELECT ... WHERE data_emissao BETWEEN %s AND %s",
    invoice_items="SELECT ... WHERE modelo=%s AND documento_id=%s AND venda_id=%s AND operacao IS NOT DISTINCT FROM %s AND origem IS NOT DISTINCT FROM %s",
)
provider = PostgresProvider("postgresql://usuario@host/banco", queries)
```

Mantenha senhas fora do código e do repositório. Use variáveis de ambiente ou
um gerenciador de segredos e conceda ao usuário do banco somente `SELECT`.
