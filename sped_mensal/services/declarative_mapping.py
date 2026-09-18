"""Mapeamento declarativo seguro de fontes simples para campos fiscais."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from .normalization import (
    digits_only,
    format_sped_money,
    normalize_access_key,
    normalize_cest,
    normalize_cfop,
    normalize_cst,
    normalize_municipality_code,
    normalize_ncm,
    normalize_sped_date,
    normalize_tax_rate,
    normalize_tipo_item,
)


Transform = Callable[[Any], Any]
_MISSING = object()


def _strip(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _upper(value: Any) -> str:
    return _strip(value).upper()


TRANSFORMS: Mapping[str, Transform] = {
    "strip": _strip,
    "upper": _upper,
    "digits": digits_only,
    "access_key": normalize_access_key,
    "municipality_code": normalize_municipality_code,
    "cfop": normalize_cfop,
    "cst": normalize_cst,
    "ncm": normalize_ncm,
    "cest": normalize_cest,
    "item_type": normalize_tipo_item,
    "tax_rate": normalize_tax_rate,
    "date": normalize_sped_date,
    "money": format_sped_money,
}


@dataclass(frozen=True)
class FieldRule:
    source: str
    transforms: tuple[str, ...] = ()
    default: Any = _MISSING
    required: bool = False


@dataclass(frozen=True)
class DeclarativeMapping:
    """Configuração validada de entidades e campos canônicos."""

    entities: Mapping[str, Mapping[str, FieldRule]]
    version: int = 1

    @classmethod
    def from_dict(cls, config: Mapping[str, Any]) -> "DeclarativeMapping":
        version = config.get("version", 1)
        if version != 1:
            raise ValueError(f"versão de mapeamento não suportada: {version!r}")

        raw_entities = config.get("entities")
        if not isinstance(raw_entities, Mapping) or not raw_entities:
            raise ValueError("a configuração deve conter 'entities'")

        entities: dict[str, dict[str, FieldRule]] = {}
        for entity, raw_fields in raw_entities.items():
            if not isinstance(entity, str) or not entity.strip():
                raise ValueError("o nome da entidade deve ser texto não vazio")
            if not isinstance(raw_fields, Mapping) or not raw_fields:
                raise ValueError(f"a entidade {entity!r} deve conter campos")

            fields: dict[str, FieldRule] = {}
            for target, raw_rule in raw_fields.items():
                fields[str(target)] = _parse_field_rule(entity, str(target), raw_rule)
            entities[entity] = fields
        return cls(entities=entities, version=version)

    @classmethod
    def from_json(cls, path: str | Path) -> "DeclarativeMapping":
        with Path(path).open("r", encoding="utf-8") as stream:
            config = json.load(stream)
        if not isinstance(config, Mapping):
            raise ValueError("a raiz do mapeamento JSON deve ser um objeto")
        return cls.from_dict(config)

    def map_row(self, entity: str, source_row: Mapping[str, Any]) -> dict[str, Any]:
        try:
            rules = self.entities[entity]
        except KeyError as exc:
            raise KeyError(f"entidade não configurada: {entity}") from exc

        result: dict[str, Any] = {}
        for target, rule in rules.items():
            value = source_row.get(rule.source, rule.default)
            if value is _MISSING:
                value = ""
            for transform_name in rule.transforms:
                value = TRANSFORMS[transform_name](value)
            if rule.required and _is_empty(value):
                raise ValueError(
                    f"campo obrigatório ausente: {entity}.{target} "
                    f"(origem {rule.source})"
                )
            result[target] = value
        return result

    def map_rows(
        self,
        entity: str,
        source_rows: Sequence[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        return [self.map_row(entity, row) for row in source_rows]


def _parse_field_rule(entity: str, target: str, raw_rule: Any) -> FieldRule:
    if isinstance(raw_rule, str):
        raw_rule = {"source": raw_rule}
    if not isinstance(raw_rule, Mapping):
        raise ValueError(f"regra inválida para {entity}.{target}")

    source = raw_rule.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError(f"'source' obrigatório em {entity}.{target}")

    transforms = raw_rule.get("transforms", ())
    if not isinstance(transforms, (list, tuple)) or not all(
        isinstance(name, str) for name in transforms
    ):
        raise ValueError(f"'transforms' deve ser uma lista em {entity}.{target}")
    unknown = [name for name in transforms if name not in TRANSFORMS]
    if unknown:
        raise ValueError(
            f"transformação não permitida em {entity}.{target}: {unknown[0]}"
        )

    required = raw_rule.get("required", False)
    if not isinstance(required, bool):
        raise ValueError(f"'required' deve ser booleano em {entity}.{target}")

    default = raw_rule.get("default", _MISSING)
    return FieldRule(
        source=source,
        transforms=tuple(transforms),
        default=default,
        required=required,
    )


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())
