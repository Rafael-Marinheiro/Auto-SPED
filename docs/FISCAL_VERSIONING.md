# Versionamento fiscal

O Auto-SPED mantém um catálogo explícito de conjuntos de regras da EFD
ICMS/IPI. A competência determina o valor de `COD_VER` do registro `0000`;
o sistema não reutiliza silenciosamente o último leiaute conhecido.

| Competência | COD_VER | Conjunto de regras | Referência |
| --- | --- | --- | --- |
| 2024 | 018 | `efd-icms-ipi-2024.1` | Nota Técnica 2023.001 v1.2 |
| 2025 | 019 | `efd-icms-ipi-2025.1` | Nota Técnica 2024.001 v1.0 |
| 2026 | 020 | `efd-icms-ipi-2026.1` | Nota Técnica 2025.001 v1.0 e Guia 3.2.2 |

As vigências 018, 019 e 020 constam na página oficial de
[manuais e guias](https://sped.rfb.gov.br/item/show/1573). O leiaute 020,
válido de 01/01/2026 a 31/12/2026, também está documentado na
[Nota Técnica 2025.001](https://sped.rfb.gov.br/item/show/7819).

## Comportamento seguro

- A opção automática é o padrão da CLI, da API e da interface desktop.
- Uma versão manual é aceita somente quando coincide com a competência.
- Períodos que atravessam duas vigências são recusados.
- Competências posteriores ao catálogo são bloqueadas até revisão da
  documentação oficial e inclusão de um novo conjunto de regras.
- O identificador do conjunto separa a versão do leiaute da evolução das
  regras de negócio, permitindo futuras revisões dentro do mesmo `COD_VER`.

Exemplo opcional de seleção explícita:

```bash
python main_fast.py --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --output saida.txt --layout-version 020
```

## Processo de atualização anual

1. Confirmar a Nota Técnica, o Ato COTEPE e o Guia Prático nos canais oficiais.
2. Adicionar uma nova entrada em
   `sped_mensal/services/fiscal_versioning.py`, sem ampliar a vigência de uma
   regra antiga.
3. Implementar mudanças de campos e validações vinculadas ao novo conjunto.
4. Adicionar testes de fronteira, incompatibilidade e paridade do fluxo mensal.
5. Validar um arquivo anonimizado no PVA antes de liberar a versão.

A seleção do `COD_VER` não substitui a validação tributária da empresa, da UF
ou do PVA; ela garante que o gerador não aplique uma versão fora da vigência
cadastrada.
