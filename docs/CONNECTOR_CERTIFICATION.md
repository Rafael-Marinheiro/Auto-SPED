# Certificação de conectores

A suíte de certificação executa verificações somente leitura sobre um
`FiscalDataProvider`. Ela ajuda a detectar incompatibilidades antes da geração,
mas não substitui testes de paridade, conferência fiscal ou validação no PVA.

## Uso em testes

Crie o conector apontando para uma base anônima e chame:

```python
from sped_mensal.services import assert_provider_certified

def test_my_connector_contract(provider):
    report = assert_provider_certified(
        provider,
        "2026-01-01",
        "2026-01-31",
        max_documents=25,
    )
    assert report.checked_documents > 0
```

Para produzir um relatório sem gerar uma exceção:

```python
import json
from sped_mensal.services import certify_provider

report = certify_provider(provider, "2026-01-01", "2026-01-31")
print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
```

## Verificações atuais

- implementação estrutural completa de `FiscalDataProvider`;
- mapa de captura existente, tipado e com origem/destino;
- tipos de retorno de empresa, contabilista e coleções;
- nome e CNPJ/CPF da empresa;
- documentos com identificador de origem, modelo e data;
- documentos restritos ao período solicitado;
- ausência de duplicidade da chave fiscal do C100;
- leitura dos itens pelo vínculo do documento;
- conversão das exceções do conector em achados rastreáveis.

O relatório separa `error` de `warning`. Um conector passa quando não há
erros. Período sem documentos gera advertência, pois o contrato pode estar
correto, mas a amostra não comprova a captura real.

## Critérios adicionais de liberação

Depois da suíte automática, compare pelo menos um período representativo com a
fonte, reconcilie totais e valide o TXT no PVA vigente. Mantenha a evidência sem
dados pessoais ou fiscais reais no repositório.
