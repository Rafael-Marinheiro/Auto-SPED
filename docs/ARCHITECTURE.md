# Arquitetura do Auto-SPED

```text
Banco, API, XML ou CSV
          │
          ▼
 FiscalDataProvider (capturador)
          │  dados fiscais padronizados
          ▼
 Serviços de normalização e validação
          │
          ▼
 SpedWriter ──► TXT EFD ICMS/IPI ──► PVA
          ▲
          │
 CLI e aplicação desktop
```

## Capturadores

Um capturador é responsável apenas por conhecer a fonte: conexão, consultas e
tradução para os nomes fiscais usados pelo núcleo. Ele implementa
`FiscalDataProvider` e fornece `describe_capture()`.

O método `describe_capture()` alimentará a tela **Mapa de captura**, indicando:

| Dado | Origem | Destino SPED |
| --- | --- | --- |
| Cabeçalho NF-e | `NFE_MASTER` | `C100` |
| Item NF-e | `NFE_DETALHE` | `C170`, `C190` |
| Item de compra | `COMPRA_ITENS` | `C170`, `C190` |

O capturador Firebird São Pedro é a implementação de referência. Novos ERPs
devem criar outro módulo, sem modificar o escritor nem as regras fiscais.

## Transição segura

`main_fast.py` é o caminho de emissão atualmente homologado para o `DADOS.FDB`.
Ele permanece em uso mensal. A nova camada só substituirá esse caminho após
testes automatizados compararem os arquivos por período e as saídas forem
aceitas no PVA.
