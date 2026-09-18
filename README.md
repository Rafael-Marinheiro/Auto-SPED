# Auto-SPED

[![Testes](https://github.com/Rafael-Marinheiro/Auto-SPED/actions/workflows/tests.yml/badge.svg)](https://github.com/Rafael-Marinheiro/Auto-SPED/actions/workflows/tests.yml)
[![Build Windows](https://github.com/Rafael-Marinheiro/Auto-SPED/actions/workflows/windows-build.yml/badge.svg)](https://github.com/Rafael-Marinheiro/Auto-SPED/actions/workflows/windows-build.yml)
[![Licença MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-19d3a2.svg)](LICENSE)

Gerador de **EFD ICMS/IPI** com arquitetura de capturadores reutilizáveis. O
projeto transforma dados de um ERP, banco, API ou arquivo em registros fiscais
padronizados, valida a consistência e gera o TXT para importação no PVA.

> Projeto de portfólio e colaboração técnica. O Auto-SPED não é um produto
> oficial da Receita Federal e não substitui a validação no PVA nem a revisão
> de um profissional fiscal responsável.

## Status

O capturador Firebird do ERP São Pedro está em transição segura: a emissão
mensal homologada por `main_fast.py` continua disponível para o `DADOS.FDB`.
A nova camada não a substitui até haver testes de paridade e validação no PVA.

### Emissão mensal homologada

O fluxo já utilizado no ERP agora recebe o período e o destino por parâmetros,
sem edição do código:

```bash
python main_fast.py --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --output saida_sped_out_2026-08.txt --encoding utf-8
```

A codificação do TXT pode ser escolhida como `utf-8`, `iso-8859-1` ou
`cp1252`. UTF-8 permanece como padrão para preservar o comportamento atual.

O código de receita do registro E116 é selecionado nesta ordem: opção
`--revenue-code`, configuração `COD_REC_E116`/`E116_COD_REC`/`COD_REC` da
empresa e padrão confirmado da UF. Há padrões oficiais verificados para AP,
CE, GO, PB, PE, PR, RJ, RN, SC e SP. Consulte o
[catálogo do E116](docs/E116_REVENUE_CODES.md). Nas demais UFs, informe o
código aplicável à empresa, por exemplo:

```bash
python main_fast.py --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --output saida_sped.txt --revenue-code CODIGO-DA-UF
```

A emissão é bloqueada quando não existe configuração segura; assim, um código
estadual não é aplicado silenciosamente a uma empresa incompatível.

O COD_VER do registro 0000 também é resolvido pela competência: 018 para
2024, 019 para 2025 e 020 para 2026. Uma seleção manual incompatível ou uma
competência ainda não cadastrada bloqueia a emissão. Consulte o
[versionamento fiscal](docs/FISCAL_VERSIONING.md).

Quando houver mais de uma versão do Firebird instalada, passe a DLL cliente
correta com `--fbclient`. Consulte a [configuração do Firebird](docs/FIREBIRD_SETUP.md).

### Seletor desktop do cliente Firebird

Instale a interface opcional e abra o seletor para detectar DLLs locais ou
baixar um kit ZIP oficial da versão escolhida. Os binários ficam no perfil
local do usuário, nunca no repositório.

```bash
pip install -e ".[desktop]"
auto-sped-desktop
```

## Arquitetura

```text
Fonte de dados → Capturador → Regras fiscais e validação → SPED TXT
```

O contrato `FiscalDataProvider` permite criar novos conectores sem alterar o
escritor do SPED. O primeiro exemplo é `FirebirdSaoPedroProvider`, que documenta
a captura das tabelas do ERP atual.

- [Arquitetura e mapa de captura](docs/ARCHITECTURE.md)
- [Guia e projeto-base para novos conectores](docs/CONNECTOR_GUIDE.md)
- [Adaptadores de referência: PostgreSQL, XML e CSV](docs/REFERENCE_CONNECTORS.md)
- [Suíte de certificação de conectores](docs/CONNECTOR_CERTIFICATION.md)
- [Build e instalador para Windows](docs/WINDOWS_DISTRIBUTION.md)
- [Implantação e operação](docs/DEPLOYMENT.md)
- [Segurança operacional](docs/SECURITY.md)
- [Solução de problemas](docs/TROUBLESHOOTING.md)
- [Versionamento de leiautes e regras fiscais](docs/FISCAL_VERSIONING.md)
- [Backlog priorizado](docs/BACKLOG.md)
- [Cliente Firebird e downloads oficiais](docs/FIREBIRD_SETUP.md)
- [Texto e checklist para publicação no LinkedIn](docs/LINKEDIN_POST.md)
- [Carrossel do projeto em PDF](output/pdf/Auto-SPED_LinkedIn_Carrossel.pdf)

## Desenvolvimento

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .
python -m pytest -q
python -m ruff check .
python -m mypy
```

O CI executa testes em Python 3.10, 3.11 e 3.12 e torna lint e tipos
obrigatórios no núcleo reutilizável e nos conectores. Os módulos do fluxo
legado ainda estão excluídos da checagem estrita para preservar sua paridade
enquanto a migração ocorre por etapas.

### Pré-validação

Antes de emitir, é possível conferir os dados sem alterar o banco nem gerar o
TXT. O relatório aponta a tabela/origem e o registro SPED impactado.

```bash
sped-generate --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --fbclient "C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll" --validate-only --validation-report relatorio.json
```

### Mapa de captura

O capturador de referência pode ser consultado sem abrir o banco. Isso mostra
quais tabelas/campos abastecem cada registro do SPED:

```bash
sped-capture-map --format table
sped-capture-map --format json
```

### Validação do arquivo gerado

Além da pré-validação do banco, o TXT pode ser conferido antes de abrir o PVA:

```bash
sped-validate saida_sped.txt --report relatorio-sped.json
```

### Prévia da captura

Confira os dados que serão usados no período antes da validação ou geração:

```bash
sped-summary --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --format table
```

## Segurança de dados

Nunca versione bancos `.FDB`, arquivos SPED emitidos, XMLs, credenciais, logs
ou relatórios de clientes. Use apenas bancos e exemplos anonimizados em testes
e documentação.

## Licença

Distribuído sob a [licença MIT](LICENSE). Você pode estudar, adaptar e criar
seus próprios conectores, preservando o aviso de copyright e a licença.
