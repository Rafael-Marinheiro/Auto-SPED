import json

import pytest

from sped_mensal.services.declarative_mapping import DeclarativeMapping


def _product_config():
    return {
        "version": 1,
        "entities": {
            "product": {
                "COD_ITEM": {"source": "id", "transforms": ["strip"], "required": True},
                "DESCR_ITEM": {"source": "name", "transforms": ["strip", "upper"]},
                "COD_NCM": {"source": "ncm", "transforms": ["ncm"]},
                "UNID_INV": {"source": "unit", "transforms": ["upper"], "default": "UN"},
            }
        },
    }


def test_maps_rows_with_whitelisted_transforms_without_mutating_source():
    mapping = DeclarativeMapping.from_dict(_product_config())
    source = {"id": " 10 ", "name": " café ", "ncm": "09.01.21.00"}

    mapped = mapping.map_row("product", source)

    assert mapped == {
        "COD_ITEM": "10",
        "DESCR_ITEM": "CAFÉ",
        "COD_NCM": "09012100",
        "UNID_INV": "UN",
    }
    assert source["name"] == " café "


def test_loads_json_and_supports_short_source_rule(tmp_path):
    config = {
        "entities": {
            "unit": {
                "UNID": "code",
                "DESCR": {"source": "description", "transforms": ["strip"]},
            }
        }
    }
    path = tmp_path / "mapping.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    mapping = DeclarativeMapping.from_json(path)

    assert mapping.map_rows("unit", [{"code": "UN", "description": " Unidade "}]) == [
        {"UNID": "UN", "DESCR": "Unidade"}
    ]


def test_rejects_unknown_transform_and_missing_required_value():
    config = _product_config()
    config["entities"]["product"]["COD_ITEM"]["transforms"] = ["python_eval"]
    with pytest.raises(ValueError, match="não permitida"):
        DeclarativeMapping.from_dict(config)

    mapping = DeclarativeMapping.from_dict(_product_config())
    with pytest.raises(ValueError, match="product.COD_ITEM"):
        mapping.map_row("product", {"name": "Produto"})


def test_rejects_unknown_entity_and_schema_version():
    mapping = DeclarativeMapping.from_dict(_product_config())
    with pytest.raises(KeyError, match="invoice"):
        mapping.map_row("invoice", {})
    with pytest.raises(ValueError, match="versão"):
        DeclarativeMapping.from_dict({"version": 2, "entities": {"x": {"Y": "y"}}})
