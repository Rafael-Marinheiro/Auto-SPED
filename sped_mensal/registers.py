"""Definições de registros do SPED EFD ICMS/IPI utilizados no projeto."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence


@dataclass(frozen=True)
class RegisterDefinition:
    """Descrição de um registro do SPED."""

    code: str
    block: str
    fields: Sequence[str]
    required_fields: Sequence[str]

    def validate(self, data: Dict[str, str]) -> None:
        missing = [field for field in self.required_fields if field not in data]
        if missing:
            raise ValueError(
                f"Registro {self.code} está faltando os campos obrigatórios: {', '.join(missing)}"
            )

    def ordered_values(self, data: Dict[str, str]) -> List[str]:
        self.validate(data)
        return [str(data.get(field, "")) for field in self.fields]


_REGISTER_DEFINITIONS: Dict[str, RegisterDefinition] = {
    "0000": RegisterDefinition(
        code="0000",
        block="0",
        fields=(
            "COD_VER",
            "COD_FIN",
            "DT_INI",
            "DT_FIN",
            "NOME",
            "CNPJ",
            "CPF",
            "UF",
            "IE",
            "COD_MUN",
            "IM",
            "SUFRAMA",
            "IND_PERFIL",
            "IND_ATIV",
        ),
        required_fields=(
            "COD_VER",
            "COD_FIN",
            "DT_INI",
            "DT_FIN",
            "NOME",
            "UF",
            "IND_PERFIL",
            "IND_ATIV",
        ),
    ),
    "0001": RegisterDefinition(
        code="0001",
        block="0",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "0005": RegisterDefinition(
        code="0005",
        block="0",
        fields=(
            "FANTASIA",
            "CEP",
            "END",
            "NUM",
            "COMPL",
            "BAIRRO",
            "FONE",
            "FAX",
            "EMAIL",
        ),
        required_fields=("FANTASIA", "CEP", "END", "NUM", "BAIRRO"),
    ),
    "0100": RegisterDefinition(
        code="0100",
        block="0",
        fields=(
            "NOME",
            "CPF",
            "CRC",
            "CNPJ",
            "CEP",
            "END",
            "NUM",
            "COMPL",
            "BAIRRO",
            "FONE",
            "FAX",
            "EMAIL",
            "COD_MUN",
        ),
        required_fields=("NOME", "CPF", "CRC", "CEP", "END", "NUM", "COD_MUN"),
    ),
    "0150": RegisterDefinition(
        code="0150",
        block="0",
        fields=(
            "COD_PART",
            "NOME",
            "COD_PAIS",
            "CNPJ",
            "CPF",
            "IE",
            "COD_MUN",
            "SUFRAMA",
            "END",
            "NUM",
            "COMPL",
            "BAIRRO",
        ),
        required_fields=("COD_PART", "NOME"),
    ),
    "0190": RegisterDefinition(
        code="0190",
        block="0",
        fields=("UNID", "DESCR"),
        required_fields=("UNID", "DESCR"),
    ),
    "0200": RegisterDefinition(
        code="0200",
        block="0",
        fields=(
            "COD_ITEM",
            "DESCR_ITEM",
            "COD_BARRA",
            "COD_ANT_ITEM",
            "UNID_INV",
            "TIPO_ITEM",
            "COD_NCM",
            "EX_IPI",
            "COD_GEN",
            "COD_LST",
            "ALIQ_ICMS",
            "CEST",
        ),
        required_fields=("COD_ITEM", "DESCR_ITEM", "UNID_INV", "TIPO_ITEM"),
    ),
    "C001": RegisterDefinition(
        code="C001",
        block="C",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "C100": RegisterDefinition(
        code="C100",
        block="C",
        fields=(
            "IND_OPER",
            "IND_EMIT",
            "COD_PART",
            "COD_MOD",
            "COD_SIT",
            "SER",
            "NUM_DOC",
            "CHV_NFE",
            "DT_DOC",
            "DT_E_S",
            "VL_DOC",
            "IND_PGTO",
            "VL_DESC",
            "VL_ABAT_NT",
            "VL_MERC",
            "IND_FRT",
            "VL_FRT",
            "VL_SEG",
            "VL_OUT_DA",
            "VL_BC_ICMS",
            "VL_ICMS",
            "VL_BC_ICMS_ST",
            "VL_ICMS_ST",
            "VL_IPI",
            "VL_PIS",
            "VL_COFINS",
            "VL_PIS_ST",
            "VL_COFINS_ST",
        ),
        required_fields=(
            "IND_OPER",
            "IND_EMIT",
            "COD_MOD",
            "COD_SIT",
            "SER",
            "NUM_DOC",
            "DT_DOC",
            "VL_DOC",
        ),
    ),
    "C170": RegisterDefinition(
        code="C170",
        block="C",
        fields=(
            "NUM_ITEM",
            "COD_ITEM",
            "DESCR_COMPL",
            "QTD",
            "UNID",
            "VL_ITEM",
            "VL_DESC",
            "IND_MOV",
            "CST_ICMS",
            "CFOP",
            "COD_NAT",
            "VL_BC_ICMS",
            "ALIQ_ICMS",
            "VL_ICMS",
            "VL_BC_ICMS_ST",
            "ALIQ_ST",
            "VL_ICMS_ST",
            "IND_APUR",
            "CST_IPI",
            "COD_ENQ",
            "VL_BC_IPI",
            "ALIQ_IPI",
            "VL_IPI",
            "CST_PIS",
            "VL_BC_PIS",
            "ALIQ_PIS",
            "QUANT_BC_PIS",
            "ALIQ_PIS_REAIS",
            "VL_PIS",
            "CST_COFINS",
            "VL_BC_COFINS",
            "ALIQ_COFINS",
            "QUANT_BC_COFINS",
            "ALIQ_COFINS_REAIS",
            "VL_COFINS",
            "COD_CTA",
            "VL_ABAT_NT",
        ),
        required_fields=(
            "NUM_ITEM",
            "COD_ITEM",
            "QTD",
            "UNID",
            "VL_ITEM",
            "IND_MOV",
            "CST_ICMS",
            "CFOP",
        ),
    ),
    "C190": RegisterDefinition(
        code="C190",
        block="C",
        fields=(
            "CST_ICMS",
            "CFOP",
            "ALIQ_ICMS",
            "VL_OPR",
            "VL_BC_ICMS",
            "VL_ICMS",
            "VL_BC_ICMS_ST",
            "VL_ICMS_ST",
            "VL_RED_BC",
            "VL_IPI",
            "COD_OBS",
        ),
        required_fields=("CST_ICMS", "CFOP"),
    ),
    "0990": RegisterDefinition(
        code="0990",
        block="0",
        fields=("QTD_LIN_0",),
        required_fields=("QTD_LIN_0",),
    ),
    "C990": RegisterDefinition(
        code="C990",
        block="C",
        fields=("QTD_LIN_C",),
        required_fields=("QTD_LIN_C",),
    ),
    # Bloco B (mínimo)
    "B001": RegisterDefinition(
        code="B001",
        block="B",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "B990": RegisterDefinition(
        code="B990",
        block="B",
        fields=("QTD_LIN_B",),
        required_fields=("QTD_LIN_B",),
    ),
    # Bloco D (mínimo)
    "D001": RegisterDefinition(
        code="D001",
        block="D",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "D990": RegisterDefinition(
        code="D990",
        block="D",
        fields=("QTD_LIN_D",),
        required_fields=("QTD_LIN_D",),
    ),
    "E001": RegisterDefinition(
        code="E001",
        block="E",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "E100": RegisterDefinition(
        code="E100",
        block="E",
        fields=(
            "DT_INI",
            "DT_FIN",
        ),
        required_fields=("DT_INI", "DT_FIN"),
    ),
    "E110": RegisterDefinition(
        code="E110",
        block="E",
        fields=(
            "VL_TOT_DEBITOS",
            "VL_AJ_DEBITOS",
            "VL_TOT_AJ_DEBITOS",
            "VL_ESTORNOS_CRED",
            "VL_TOT_CREDITOS",
            "VL_AJ_CREDITOS",
            "VL_TOT_AJ_CREDITOS",
            "VL_ESTORNOS_DEB",
            "VL_SLD_CREDOR_ANT",
            "VL_SLD_APURADO",
            "VL_TOT_DED",
            "VL_ICMS_RECOLHER",
            "DEB_ESP",
            "VL_SLD_CREDOR_TRANSPORTAR",
            "VL_OUT_DED",
        ),
        required_fields=(
            "VL_TOT_DEBITOS",
            "VL_TOT_CREDITOS",
            "VL_SLD_APURADO",
            "VL_ICMS_RECOLHER",
        ),
    ),
    "E990": RegisterDefinition(
        code="E990",
        block="E",
        fields=("QTD_LIN_E",),
        required_fields=("QTD_LIN_E",),
    ),
    # Bloco G (mínimo)
    "G001": RegisterDefinition(
        code="G001",
        block="G",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "G990": RegisterDefinition(
        code="G990",
        block="G",
        fields=("QTD_LIN_G",),
        required_fields=("QTD_LIN_G",),
    ),
    # Bloco H (mínimo)
    "H001": RegisterDefinition(
        code="H001",
        block="H",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "H990": RegisterDefinition(
        code="H990",
        block="H",
        fields=("QTD_LIN_H",),
        required_fields=("QTD_LIN_H",),
    ),
    # Bloco K (mínimo)
    "K001": RegisterDefinition(
        code="K001",
        block="K",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "K990": RegisterDefinition(
        code="K990",
        block="K",
        fields=("QTD_LIN_K",),
        required_fields=("QTD_LIN_K",),
    ),
    # Bloco 1 (mínimo)
    "1001": RegisterDefinition(
        code="1001",
        block="1",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "1990": RegisterDefinition(
        code="1990",
        block="1",
        fields=("QTD_LIN_1",),
        required_fields=("QTD_LIN_1",),
    ),
    "9001": RegisterDefinition(
        code="9001",
        block="9",
        fields=("IND_MOV",),
        required_fields=("IND_MOV",),
    ),
    "9900": RegisterDefinition(
        code="9900",
        block="9",
        fields=("REG_BLC", "QTD_REG_BLC"),
        required_fields=("REG_BLC", "QTD_REG_BLC"),
    ),
    "9990": RegisterDefinition(
        code="9990",
        block="9",
        fields=("QTD_LIN_9",),
        required_fields=("QTD_LIN_9",),
    ),
    "9999": RegisterDefinition(
        code="9999",
        block="9",
        fields=("QTD_LIN",),
        required_fields=("QTD_LIN",),
    ),
}


def get_definition(code: str) -> RegisterDefinition:
    try:
        return _REGISTER_DEFINITIONS[code]
    except KeyError as exc:
        raise KeyError(f"Registro {code} não é suportado pelo gerador") from exc


def supported_registers() -> Iterable[str]:
    return _REGISTER_DEFINITIONS.keys()
