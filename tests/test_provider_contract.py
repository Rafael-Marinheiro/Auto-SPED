from sped_mensal.providers import CaptureMapping, FirebirdSaoPedroProvider


def test_firebird_provider_describes_fiscal_capture():
    provider = FirebirdSaoPedroProvider("DADOS.FDB")

    mappings = provider.describe_capture()

    assert provider.provider_id == "firebird-sao-pedro"
    assert all(isinstance(mapping, CaptureMapping) for mapping in mappings)
    assert any(
        mapping.source == "COMPRA_ITENS" and "C170" in mapping.sped_targets
        for mapping in mappings
    )
