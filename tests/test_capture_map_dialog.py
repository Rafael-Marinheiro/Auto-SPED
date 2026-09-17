from sped_mensal.services.capture_map import transformation_for


def test_capture_map_explains_tax_normalization():
    assert "Normalização fiscal" in transformation_for("COMPRA_ITENS.CST_ICM, CFOP")


def test_capture_map_marks_non_tax_data_as_direct_capture():
    assert transformation_for("EMPRESA.RAZAO") == "Captura direta"
