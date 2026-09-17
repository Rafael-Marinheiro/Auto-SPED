# -*- coding: cp1252 -*-
"""UtilitÃ¡rios para geraÃ§Ã£o do arquivo SPED."""

from __future__ import annotations

from dataclasses import dataclass
from inspect import signature
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Sequence

from .registers import RegisterDefinition, get_definition


@dataclass
class RegisterEntry:
    """Representa um registro individual informado pelo usuÃ¡rio."""

    code: str
    data: Dict[str, str]
    definition: RegisterDefinition

    @classmethod
    def create(cls, code: str, data: Dict[str, str]) -> "RegisterEntry":
        definition = get_definition(code)
        if definition.block == "9":
            raise ValueError(
                "Registros do bloco 9 sÃ£o gerados automaticamente e nÃ£o devem ser informados."
            )
        values = definition.ordered_values(data)
        # ordered_values jÃ¡ valida a presenÃ§a dos campos obrigatÃ³rios.
        ordered_data = dict(zip(definition.fields, values))
        return cls(code=code, data=ordered_data, definition=definition)

    def formatted_line(self) -> str:
        values = [self.data[field] for field in self.definition.fields]
        return format_line(self.code, values)


@dataclass
class SpedConfig:
    """ConfiguraÃ§Ã£o do SPED, tipicamente carregada de um arquivo JSON."""

    registers: Sequence[Dict[str, Dict[str, str]]]

    @classmethod
    def from_dict(cls, payload: Dict) -> "SpedConfig":
        if "registers" not in payload or not isinstance(payload["registers"], list):
            raise ValueError("O arquivo de configuraÃ§Ã£o deve possuir a chave 'registers'.")
        return cls(registers=payload["registers"])

    @classmethod
    def from_json(cls, path: Path) -> "SpedConfig":
        import json

        with path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)
        return cls.from_dict(payload)


class SpedWriter:
    """ResponsÃ¡vel por montar o arquivo SPED a partir dos registros fornecidos."""

    def __init__(self) -> None:
        self._entries: List[RegisterEntry] = []

    def add_register(self, code: str, data: Dict[str, str]) -> None:
        entry = RegisterEntry.create(code, data)
        self._entries.append(entry)

    def extend_from_config(self, config: SpedConfig) -> None:
        for item in config.registers:
            try:
                code = item["code"]
                data = item["data"]
            except KeyError as exc:
                raise ValueError(
                    "Cada registro deve possuir as chaves 'code' e 'data'."
                ) from exc
            if not isinstance(data, dict):
                raise ValueError("O campo 'data' deve ser um objeto com os valores do registro.")
            self.add_register(code, data)

    def validate(self) -> None:
        if not self._entries:
            raise ValueError("Ã‰ necessÃ¡rio informar ao menos o registro 0000.")
        if self._entries[0].code != "0000":
            raise ValueError("O primeiro registro do arquivo deve ser o 0000.")
        codes = [entry.code for entry in self._entries]
        if codes.count("0000") != 1:
            raise ValueError("O registro 0000 deve ser informado exatamente uma vez.")
        if "0001" not in codes:
            raise ValueError("O registro 0001 Ã© obrigatÃ³rio no bloco 0.")
        block_c_entries = [entry for entry in self._entries if entry.definition.block == "C"]
        if block_c_entries and block_c_entries[0].code != "C001":
            raise ValueError("O bloco C deve iniciar com o registro C001.")

    def to_lines(self) -> List[str]:
        self.validate()
        lines: List[str] = []
        register_counts: Dict[str, int] = {}

        def append_line(code: str, values: Iterable[str]) -> None:
            line = format_line(code, values)
            lines.append(line)
            register_counts[code] = register_counts.get(code, 0) + 1

        block_0_entries = [entry for entry in self._entries if entry.definition.block == "0"]
        if not block_0_entries:
            raise ValueError("O bloco 0 Ã© obrigatÃ³rio e nÃ£o foi informado.")
        for entry in block_0_entries:
            append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
        append_line("0990", [str(len(block_0_entries) + 1)])

        # Bloco B - mÃ­nimo (B001/B990)
        block_b_entries = [entry for entry in self._entries if entry.definition.block == "B"]
        if block_b_entries:
            for entry in block_b_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_b = len(block_b_entries) + 1
        else:
            default_b001 = RegisterEntry.create("B001", {"IND_MOV": "1"})
            append_line(default_b001.code, [default_b001.data[field] for field in default_b001.definition.fields])
            qtd_lin_b = 2  # B001 + B990
        append_line("B990", [str(qtd_lin_b)])

        block_c_entries = [entry for entry in self._entries if entry.definition.block == "C"]
        if block_c_entries:
            for entry in block_c_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_c = len(block_c_entries) + 1
        else:
            default_c001 = RegisterEntry.create("C001", {"IND_MOV": "1"})
            append_line(default_c001.code, [default_c001.data[field] for field in default_c001.definition.fields])
            qtd_lin_c = 1 + 1  # C001 + C990
        append_line("C990", [str(qtd_lin_c)])

        # Bloco D - mÃ­nimo (D001/D990)
        block_d_entries = [entry for entry in self._entries if entry.definition.block == "D"]
        if block_d_entries:
            for entry in block_d_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_d = len(block_d_entries) + 1
        else:
            default_d001 = RegisterEntry.create("D001", {"IND_MOV": "1"})
            append_line(default_d001.code, [default_d001.data[field] for field in default_d001.definition.fields])
            qtd_lin_d = 2
        append_line("D990", [str(qtd_lin_d)])

        # Bloco E - versÃ£o mÃ­nima (E001/E990)
        block_e_entries = [entry for entry in self._entries if entry.definition.block == "E"]
        if block_e_entries:
            for entry in block_e_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_e = len(block_e_entries) + 1
        else:
            default_e001 = RegisterEntry.create("E001", {"IND_MOV": "1"})
            append_line(default_e001.code, [default_e001.data[field] for field in default_e001.definition.fields])
            qtd_lin_e = 1 + 1  # E001 + E990
        append_line("E990", [str(qtd_lin_e)])

        # Bloco G - mÃ­nimo (G001/G990)
        block_g_entries = [entry for entry in self._entries if entry.definition.block == "G"]
        if block_g_entries:
            for entry in block_g_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_g = len(block_g_entries) + 1
        else:
            default_g001 = RegisterEntry.create("G001", {"IND_MOV": "1"})
            append_line(default_g001.code, [default_g001.data[field] for field in default_g001.definition.fields])
            qtd_lin_g = 2
        append_line("G990", [str(qtd_lin_g)])

        # Bloco H - mÃ­nimo (H001/H990)
        block_h_entries = [entry for entry in self._entries if entry.definition.block == "H"]
        if block_h_entries:
            for entry in block_h_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_h = len(block_h_entries) + 1
        else:
            default_h001 = RegisterEntry.create("H001", {"IND_MOV": "1"})
            append_line(default_h001.code, [default_h001.data[field] for field in default_h001.definition.fields])
            qtd_lin_h = 2
        append_line("H990", [str(qtd_lin_h)])

        # Bloco K - mÃ­nimo (K001/K990)
        block_k_entries = [entry for entry in self._entries if entry.definition.block == "K"]
        if block_k_entries:
            for entry in block_k_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_k = len(block_k_entries) + 1
        else:
            default_k001 = RegisterEntry.create("K001", {"IND_MOV": "1"})
            append_line(default_k001.code, [default_k001.data[field] for field in default_k001.definition.fields])
            qtd_lin_k = 2
        append_line("K990", [str(qtd_lin_k)])

        # Bloco 1 - mÃ­nimo (1001/1990)
        block_1_entries = [entry for entry in self._entries if entry.definition.block == "1"]
        if block_1_entries:
            for entry in block_1_entries:
                append_line(entry.code, [entry.data[field] for field in entry.definition.fields])
            qtd_lin_1 = len(block_1_entries) + 1
        else:
            default_1001 = RegisterEntry.create("1001", {"IND_MOV": "0"})
            append_line(default_1001.code, [default_1001.data[field] for field in default_1001.definition.fields])
            qtd_lin_1 = 2
        append_line("1990", [str(qtd_lin_1)])

        snapshot_counts = dict(register_counts)

        append_line("9001", ["1"])

        control_counts: Dict[str, int] = dict(snapshot_counts)
        control_counts["9001"] = control_counts.get("9001", 0) + 1
        control_counts["9990"] = 1
        control_counts["9999"] = 1

        distinct_codes = sorted(set(control_counts) | {"9900"})
        control_counts["9900"] = len(distinct_codes)

        for code in distinct_codes:
            append_line("9900", [code, str(control_counts[code])])

        qtd_lin_9 = 1 + len(distinct_codes) + 2  # 9001 + 9900 registros + 9990 + 9999
        append_line("9990", [str(qtd_lin_9)])

        total_lines = len(lines) + 1  # inclui o 9999
        append_line("9999", [str(total_lines)])

        return lines

    def to_string(self) -> str:
        lines = self.to_lines()
        # Remove any empty lines that might be present
        lines = [line for line in lines if line.strip()]
        return "\n".join(lines)

    def generate_sped_from_db(self, company_info, accountant_info, participants, products, units, invoices, extractor, start_date, end_date, log_fn: Callable[[str], None] | None = None):
        """Gera o SPED a partir dos dados extraÃ­dos do banco de dados."""
        logger = log_fn or (lambda msg: None)

        def digits_only(value: str) -> str:
            s = "" if value is None else str(value)
            return "".join(ch for ch in s if ch.isdigit())

        def normalize_person_ids(cnpj_val: str, cpf_val: str) -> tuple[str, str]:
            """Garante que CNPJ/CPF fiquem no campo correto.

            - Se CNPJ vier com 11 dígitos, trata como CPF.
            - Se CPF vier com 14 dígitos, trata como CNPJ.
            - Só aceita CNPJ com 14 e CPF com 11 dígitos; caso contrário, em branco.
            """
            cnpj = digits_only(cnpj_val)
            cpf = digits_only(cpf_val)
            if len(cnpj) == 14:
                cpf_ok = cpf if len(cpf) == 11 else ""
                return cnpj, cpf_ok
            if len(cnpj) == 11 and (len(cpf) != 11):
                return "", cnpj
            if len(cpf) == 14 and (len(cnpj) != 14):
                return cpf, ""
            if len(cpf) == 11:
                return "", cpf
            return "", ""

        def sanitize_mun(value: str) -> str:
            v = digits_only(value)
            return "" if v in {"", "0"} else v

        def fmt_date(value: str) -> str:
            from datetime import datetime
            s = "" if value is None else str(value)
            if not s:
                return ""
            for fmt in ("%Y-%m-%d", "%Y%m%d", "%d/%m/%Y", "%d%m%Y"):
                try:
                    return datetime.strptime(s, fmt).strftime("%d%m%Y")
                except ValueError:
                    continue
            return s.replace("-", "")

        def map_cod_sit(raw: str) -> str:
            s = "" if raw is None else str(raw).strip().upper()
            # JÃ¡ Ã© um cÃ³digo vÃ¡lido
            if s in {"00","01","02","03","04","05","06","07","08"}:
                return s
            # HeurÃ­sticas de mapeamento
            if s in {"C","CANC","CANCEL","CANCELADA","CANCELADO"}:
                return "02"
            if s.startswith("DENEG") or s in {"D","DEN","DENEGADA","DENEGADO"}:
                return "04"
            if s.startswith("INUTIL") or s in {"I","INUTILIZADA","INUTILIZADO"}:
                return "05"
            # SituaÃ§Ãµes normalizadas ou desconhecidas tratadas como regular
            if s in {"T","O","AUTORIZADA","AUTORIZADO","NORMAL","REGULAR","EMITIDA"}:
                return "00"
            return "00"

        # Formatação monetária com 2 casas (para campos VL_*)
        from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

        def _to_decimal_2(x) -> Decimal:
            s = "" if x is None else str(x).strip()
            if s == "":
                return Decimal("0")
            if "," in s and "." in s:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", ".")
            try:
                return Decimal(s)
            except InvalidOperation:
                return Decimal("0")

        def money2(x) -> str:
            d = x if isinstance(x, Decimal) else _to_decimal_2(x)
            return str(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

        def normalize_cst(value: str, width: int) -> str:
            s = "" if value is None else str(value)
            # Mantém apenas dígitos e ajusta ao tamanho esperado
            digits = "".join(ch for ch in s if ch.isdigit())
            if len(digits) > width:
                digits = digits[-width:]
            return digits.zfill(width) if digits else ""

        def normalize_chv(chv: str) -> str:
            # Chave NFe/NFC-e: exatamente 44 dígitos; caso contrário, em branco
            s = "" if chv is None else str(chv)
            digits = "".join(ch for ch in s if ch.isdigit())
            return digits if len(digits) == 44 else ""
        # Registro 0000 - Abertura do arquivo
        self.add_register("0000", {
            "COD_VER": "020",  # VersÃ£o do layout
            "COD_FIN": "0",    # Remessa original
            "DT_INI": fmt_date(start_date),
            "DT_FIN": fmt_date(end_date),
            "NOME": company_info.get("NOME", ""),
            **(lambda cnpj_cpf: {"CNPJ": cnpj_cpf[0], "CPF": cnpj_cpf[1]})(normalize_person_ids(company_info.get("CNPJ", ""), company_info.get("CPF", ""))),
            "UF": company_info.get("UF", ""),
            "IE": digits_only(company_info.get("IE", "")),
            "COD_MUN": sanitize_mun(company_info.get("COD_MUN", "")),
            "IM": company_info.get("IM", ""),
            "SUFRAMA": company_info.get("SUFRAMA", ""),
            "IND_PERFIL": "A",  # Perfil A
            "IND_ATIV": "1",    # Industrial ou equiparado
        })

        # Registro 0001 - Abertura do bloco 0
        has_block0_movement = bool(participants or products or units)
        self.add_register("0001", {"IND_MOV": "0" if has_block0_movement else "1"})

        # Registro 0005 - Dados complementares da entidade
        self.add_register("0005", {
            "FANTASIA": company_info.get("FANTASIA", ""),
            "CEP": digits_only(company_info.get("CEP", "")),
            "END": company_info.get("END", ""),
            "NUM": digits_only(company_info.get("NUM", "")) or company_info.get("NUM", ""),
            "COMPL": company_info.get("COMPL", ""),
            "BAIRRO": company_info.get("BAIRRO", ""),
            "FONE": digits_only(company_info.get("FONE", "")),
            "FAX": digits_only(company_info.get("FAX", "")),
            "EMAIL": company_info.get("EMAIL", ""),
        })

        # Registro 0100 - Dados do contador
        self.add_register("0100", {
            "NOME": accountant_info.get("NOME", ""),
            **(lambda cnpj_cpf: {"CPF": cnpj_cpf[1], "CNPJ": cnpj_cpf[0]})(normalize_person_ids(accountant_info.get("CNPJ", ""), accountant_info.get("CPF", ""))),
            "CRC": accountant_info.get("CRC", ""),
            "CEP": digits_only(accountant_info.get("CEP", "")),
            "END": accountant_info.get("END", ""),
            "NUM": digits_only(accountant_info.get("NUM", "")) or accountant_info.get("NUM", ""),
            "COMPL": accountant_info.get("COMPL", ""),
            "BAIRRO": accountant_info.get("BAIRRO", ""),
            "FONE": digits_only(accountant_info.get("FONE", "")),
            "FAX": digits_only(accountant_info.get("FAX", "")),
            "EMAIL": accountant_info.get("EMAIL", ""),
            "COD_MUN": sanitize_mun(accountant_info.get("COD_MUN", "")),
        })

        # Registros 0150 - Participantes
        for participant in participants:
            self.add_register("0150", {
                "COD_PART": participant.get("COD_PART", ""),
                "NOME": participant.get("NOME", ""),
                "COD_PAIS": "1058",  # Brasil (cÃ³digo IBGE)
                **(lambda cnpj_cpf: {"CNPJ": cnpj_cpf[0], "CPF": cnpj_cpf[1]})(normalize_person_ids(participant.get("CNPJ", ""), participant.get("CPF", ""))),
                "IE": digits_only(participant.get("IE", "")),
                "COD_MUN": sanitize_mun(participant.get("COD_MUN", "")),
                "SUFRAMA": "",
                "END": participant.get("END", ""),
                "NUM": digits_only(participant.get("NUM", "")) or participant.get("NUM", ""),
                "COMPL": participant.get("COMPL", ""),
                "BAIRRO": participant.get("BAIRRO", ""),
            })

        # Registros 0190 - Unidades de medida
        for unit in units:
            self.add_register("0190", {
                "UNID": unit.get("UNID", ""),
                "DESCR": unit.get("DESCR", ""),
            })

        # Registros 0200 - Produtos
        for product in products:
            self.add_register("0200", {
                "COD_ITEM": product.get("COD_ITEM", ""),
                "DESCR_ITEM": product.get("DESCR_ITEM", ""),
                "COD_BARRA": "",
                "COD_ANT_ITEM": "",
                "UNID_INV": product.get("UNID_INV", ""),
                # TIPO_ITEM deve conter apenas o código (ex.: "00")
                "TIPO_ITEM": digits_only(product.get("TIPO_ITEM", "")),
                "COD_NCM": digits_only(product.get("COD_NCM", "")),
                "EX_IPI": "",
                "COD_GEN": "",
                "COD_LST": "",
                "ALIQ_ICMS": product.get("ALIQ_ICMS", ""),
            })

        product_unit_map = {str(p.get("COD_ITEM", "")).strip(): str(p.get("UNID_INV", "")).strip() for p in products}
        # Registro C001 - Abertura do bloco C
        # IND_MOV: 0 = com movimento; 1 = sem movimento
        has_invoices = bool(invoices)
        self.add_register("C001", {"IND_MOV": "0" if has_invoices else "1"})

        # Registros C100 - Notas fiscais
        total_invoices = len(invoices)
        for idx, invoice in enumerate(invoices, start=1):
            if idx == 1 or idx % 100 == 0 or idx == total_invoices:
                logger(f"Processando nota {idx}/{total_invoices}")
            ind_oper = str(invoice.get("IND_OPER", "")).strip()
            cod_mod = str(invoice.get("COD_MOD", "")).strip()
            if idx <= 5:
                logger(f"Preparando nota {idx} (modelo {cod_mod})")
            # Normaliza COD_MOD como string
            invoice["COD_MOD"] = cod_mod
            # Define IND_EMIT conforme leiaute: 0=PrÃ³pria, 1=Terceiros
            if cod_mod == "65":
                invoice["IND_OPER"] = "1"
                invoice["IND_EMIT"] = "0"
            elif cod_mod == "55":
                invoice["IND_EMIT"] = "0" if ind_oper == "1" else "1"
            else:
                invoice["IND_EMIT"] = str(invoice.get("IND_EMIT", "")).strip() or ("0" if ind_oper == "1" else "1")
            def map_ind_pgto(raw: str, cod_mod: str) -> str:
                s = "" if raw is None else str(raw).strip().upper()
                # 0 = à vista, 1 = a prazo, 2 = outros
                if s in {"0","A VISTA","AVISTA","VISTA","DINHEIRO","PIX","DEBITO","DÉBITO","CARTAO DEBITO","CARTÃO DÉBITO"}:
                    return "0"
                if s in {"1","A PRAZO","APRAZO","PRAZO","CREDITO","CRÉDITO","CARTAO CREDITO","CARTÃO CRÉDITO","BOLETO","DUPLICATA"}:
                    return "1"
                if s == "":
                    return "0" if cod_mod == "65" else "2"
                return "2"

            c100 = {
                "IND_OPER": invoice.get("IND_OPER", ""),
                "IND_EMIT": invoice.get("IND_EMIT", ""),
                "COD_PART": invoice.get("COD_PART", ""),
                "COD_MOD": invoice.get("COD_MOD", ""),
                "COD_SIT": map_cod_sit(invoice.get("COD_SIT", "")),
                "SER": invoice.get("SER", ""),
                "NUM_DOC": invoice.get("NUM_DOC", ""),
                "CHV_NFE": normalize_chv(invoice.get("CHV_NFE", "")),
                "DT_DOC": fmt_date(invoice.get("DT_DOC", "")),
                "DT_E_S": fmt_date(invoice.get("DT_E_S", "")),
                "VL_DOC": money2(invoice.get("VL_DOC", 0)),
                "IND_PGTO": map_ind_pgto(invoice.get("FORMA_PAGAMENTO", ""), invoice.get("COD_MOD", "")),
                "VL_DESC": money2(invoice.get("VL_DESC", 0)),
                "VL_ABAT_NT": money2(0),
                "VL_MERC": money2(invoice.get("VL_MERC", 0)),
                "IND_FRT": "0",
                "VL_FRT": money2(invoice.get("VL_FRT", 0)),
                "VL_SEG": money2(invoice.get("VL_SEG", 0)),
                "VL_OUT_DA": money2(invoice.get("VL_OUT_DA", 0)),
                "VL_BC_ICMS": money2(invoice.get("VL_BC_ICMS", 0)),
                "VL_ICMS": money2(invoice.get("VL_ICMS", 0)),
                "VL_BC_ICMS_ST": money2(0),
                "VL_ICMS_ST": money2(0),
                "VL_IPI": money2(invoice.get("VL_IPI", 0)),
                "VL_PIS": money2(invoice.get("VL_PIS", 0)),
                "VL_COFINS": money2(invoice.get("VL_COFINS", 0)),
                "VL_PIS_ST": money2(0),
                "VL_COFINS_ST": money2(0),
            }
            # NFC-e (modelo 65): não informar campos proibidos pelo validador
            if cod_mod == "65":
                c100["COD_PART"] = ""
                for fld in ("VL_BC_ICMS_ST","VL_ICMS_ST","VL_IPI","VL_PIS","VL_COFINS","VL_PIS_ST","VL_COFINS_ST"):
                    c100[fld] = ""
            self.add_register("C100", c100)

            # Registros C170 - Itens da nota fiscal
            # Preferir novo método por IDs; se ausentes, resolver pelo par (SER, NUM_DOC)
            get_by_ids = getattr(extractor, "get_invoice_items_by_ids", None)
            if callable(get_by_ids):
                doc_id = invoice.get("DOC_ID", "")
                venda_id = invoice.get("VENDA_ID", "")
                if (not doc_id) and hasattr(extractor, "resolve_invoice_ids"):
                    ids = extractor.resolve_invoice_ids(invoice.get("COD_MOD", ""), invoice.get("SER", ""), invoice.get("NUM_DOC", ""))
                    doc_id = ids.get("DOC_ID", "")
                    venda_id = ids.get("VENDA_ID", "")
                if idx <= 5:
                    logger(f"Buscando itens nota {idx} (doc_id={doc_id}, venda_id={venda_id})")
                # Os conectores atuais recebem também operação e origem. Mantemos
                # os três argumentos originais para conectores já existentes.
                parameter_count = len(signature(get_by_ids).parameters)
                if parameter_count >= 5:
                    items = get_by_ids(
                        invoice.get("COD_MOD", ""),
                        doc_id,
                        venda_id,
                        invoice.get("IND_OPER", ""),
                        invoice.get("ORIGEM", ""),
                    )
                else:
                    items = get_by_ids(invoice.get("COD_MOD", ""), doc_id, venda_id)
            else:
                if idx <= 5:
                    logger(f"Buscando itens nota {idx} por NUM_DOC")
                items = extractor.get_invoice_items(invoice.get("NUM_DOC", ""))

            # Helpers for C170 normalization
            from decimal import Decimal, InvalidOperation
            def _dec2(x) -> Decimal:
                s = "" if x is None else str(x).strip()
                if s == "":
                    return Decimal("0")
                if "," in s and "." in s:
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", ".")
                try:
                    return Decimal(s)
                except InvalidOperation:
                    return Decimal("0")
            def _fmt2(x) -> str:
                # returns string with dot as decimal sep, 2 decimal places
                return f"{_dec2(x):.2f}"
            def _pad(s: str, width: int) -> str:
                t = "" if s is None else str(s).strip()
                t = "".join(ch for ch in t if ch.isalnum())
                return t.zfill(width) if t else ""

            if idx <= 5:
                logger(f"Itens carregados nota {idx}: {len(items)}")
            if cod_mod != "65":
                doc_cfop_base = None
                valid_base = {"5", "6"} if ind_oper == "1" else {"1", "2"}
                for it in items:
                    cfop_raw_it = digits_only(it.get("CFOP", ""))
                    if len(cfop_raw_it) > 4:
                        cfop_raw_it = cfop_raw_it[-4:]
                    cfop_norm_it = cfop_raw_it.zfill(4) if cfop_raw_it else ""
                    fd = cfop_norm_it[0] if cfop_norm_it else ""
                    if fd in valid_base:
                        doc_cfop_base = fd
                        break
                if doc_cfop_base is None:
                    doc_cfop_base = "5" if ind_oper == "1" else "1"
                for item_idx, item in enumerate(items, start=1):
                    cfop_raw = digits_only(item.get("CFOP", ""))
                    if len(cfop_raw) > 4:
                        cfop_raw = cfop_raw[-4:]
                    cfop_norm = cfop_raw.zfill(4) if cfop_raw else ""
                    if len(cfop_norm) == 4:
                        cfop_norm = doc_cfop_base + cfop_norm[1:]
                    else:
                        tail = cfop_norm[-3:] if cfop_norm else "102"
                        cfop_norm = doc_cfop_base + tail.zfill(3)
                    item["CFOP"] = cfop_norm
                    cfop_num = cfop_norm
                    cfop_first = cfop_num[0] if cfop_num else ""
                    raw_cst_ipi = "".join(ch for ch in str(item.get("CST_IPI", "")).strip() if ch.isdigit())
                    valid_in = {"00", "01", "02", "03", "04", "05", "49"}
                    valid_out = {"50", "51", "52", "53", "54", "99"}
                    if cfop_first in {"1", "2", "3"}:
                        raw_cst_ipi = raw_cst_ipi if raw_cst_ipi in valid_in else "49"
                    elif cfop_first in {"5", "6", "7"}:
                        raw_cst_ipi = raw_cst_ipi if raw_cst_ipi in valid_out else "99"
                    else:
                        raw_cst_ipi = raw_cst_ipi if raw_cst_ipi else "49"
                    vl_item_total = _dec2(item.get("VL_TOTAL", 0))
                    if vl_item_total == Decimal("0"):
                        qty_dec = _dec2(item.get("QTD", 0))
                        unit_price_dec = _dec2(item.get("VL_ITEM", 0))
                        if qty_dec != Decimal("0") and unit_price_dec != Decimal("0"):
                            vl_item_total = unit_price_dec * qty_dec
                        else:
                            vl_item_total = unit_price_dec
                    # guarda o valor total calculado para reutilizar no C190
                    item["_VL_ITEM_TOTAL"] = vl_item_total
                    self.add_register("C170", {
                        "NUM_ITEM": str(item_idx),
                        "COD_ITEM": item.get("COD_ITEM", ""),
                        "DESCR_COMPL": "",
                        "QTD": str(item.get("QTD", 0)),
                        "UNID": (product_unit_map.get(str(item.get("COD_ITEM", "")).strip()) or str(item.get("UNID", "")).strip()),
                        "VL_ITEM": money2(vl_item_total),
                        "VL_DESC": money2(item.get("VL_DESC", 0)),
                        "IND_MOV": "0",
                        "CST_ICMS": normalize_cst(item.get("CST_ICMS", ""), 3),
                        "CFOP": digits_only(item.get("CFOP", "")),
                        "COD_NAT": "",
                        "VL_BC_ICMS": money2(item.get("VL_BC_ICMS", 0)),
                        "ALIQ_ICMS": _fmt2(item.get("ALIQ_ICMS", 0)),
                        "VL_ICMS": money2(item.get("VL_ICMS", 0)),
                        "VL_BC_ICMS_ST": "0",
                        "ALIQ_ST": "0",
                        "VL_ICMS_ST": "0",
                        "IND_APUR": "0",
                        "CST_IPI": normalize_cst(raw_cst_ipi, 2),
                        "COD_ENQ": "",
                        "VL_BC_IPI": money2(0),
                        "ALIQ_IPI": _fmt2(0),
                        "VL_IPI": money2(item.get("VL_IPI", 0)),
                        "CST_PIS": normalize_cst(item.get("CST_PIS", ""), 2),
                        "VL_BC_PIS": money2(item.get("VL_BC_PIS", 0)),
                        "ALIQ_PIS": _fmt2(item.get("ALIQ_PIS", 0)),
                        "QUANT_BC_PIS": "",
                        "ALIQ_PIS_REAIS": "",
                        "VL_PIS": money2(item.get("VL_PIS", 0)),
                        "CST_COFINS": normalize_cst(item.get("CST_COFINS", ""), 2),
                        "VL_BC_COFINS": money2(item.get("VL_BC_COFINS", 0)),
                        "ALIQ_COFINS": _fmt2(item.get("ALIQ_COFINS", 0)),
                        "QUANT_BC_COFINS": "",
                        "ALIQ_COFINS_REAIS": "",
                        "VL_COFINS": money2(item.get("VL_COFINS", 0)),
                        "COD_CTA": "",
                        "VL_ABAT_NT": money2(0),
                    })

            # Registros C190 - Resumo por CST/CFOP/ALIQ da nota fiscal
            # Agrega valores a partir dos itens (mesmo quando não emitimos C170, ex.: NFC-e)
            from decimal import Decimal, InvalidOperation

            def _dec(x) -> Decimal:
                s = "" if x is None else str(x).strip()
                if s == "":
                    return Decimal("0")
                if "," in s and "." in s:
                    s = s.replace(".", "").replace(",", ".")
                else:
                    s = s.replace(",", ".")
                try:
                    return Decimal(s)
                except InvalidOperation:
                    return Decimal("0")

            # Cancelada? Não gerar C190
            cod_sit_norm = map_cod_sit(invoice.get("COD_SIT", ""))
            is_canceled = (cod_sit_norm == "02") or (str(invoice.get("SITUACAO", "")).strip().upper() == "C")

            aggregates: Dict[tuple, Dict[str, Decimal]] = {}
            if not is_canceled:
                for item in items:
                    cst = normalize_cst(item.get("CST_ICMS", ""), 3) or "000"
                    cfop = digits_only(item.get("CFOP", "")) or "0000"
                    aliq_val = _dec(item.get("ALIQ_ICMS", 0))
                    aliq = f"{aliq_val:.2f}"
                    key = (cst, cfop, aliq)
                    g = aggregates.setdefault(key, {
                        "VL_OPR": Decimal("0"),
                        "VL_BC_ICMS": Decimal("0"),
                        "VL_ICMS": Decimal("0"),
                        "VL_BC_ICMS_ST": Decimal("0"),
                        "VL_ICMS_ST": Decimal("0"),
                        "VL_RED_BC": Decimal("0"),
                        "VL_IPI": Decimal("0"),
                    })
                    # VL_OPR: somatório do VALOR_ITEM/total; usar VL_TOTAL quando disponível
                    g["VL_OPR"] += _dec(item.get("_VL_ITEM_TOTAL", item.get("VL_TOTAL", item.get("VL_ITEM", 0))))
                    g["VL_BC_ICMS"] += _dec(item.get("VL_BC_ICMS", 0))
                    g["VL_ICMS"] += _dec(item.get("VL_ICMS", 0))
                    g["VL_BC_ICMS_ST"] += _dec(item.get("VL_BC_ICMS_ST", 0))
                    g["VL_ICMS_ST"] += _dec(item.get("VL_ICMS_ST", 0))
                    # VL_RED_BC zerado conforme orientação
                    if cst == "020":
                        vl_tot = _dec(item.get("_VL_ITEM_TOTAL", item.get("VL_TOTAL", item.get("VL_ITEM", 0))))
                        vl_bc = _dec(item.get("VL_BC_ICMS", 0))
                        diff = vl_tot - vl_bc
                        if diff < Decimal("0"):
                            diff = Decimal("0")
                        g["VL_RED_BC"] += diff
                    else:
                        g["VL_RED_BC"] += Decimal("0")
                    g["VL_IPI"] += _dec(item.get("VL_IPI", 0))

                # Geração mínima: se não houver itens/agrupamentos, gerar C190 zerado padrão
                if not aggregates:
                    aggregates[("000", "5102", "0")] = {
                        "VL_OPR": Decimal("0"),
                        "VL_BC_ICMS": Decimal("0"),
                        "VL_ICMS": Decimal("0"),
                        "VL_BC_ICMS_ST": Decimal("0"),
                        "VL_ICMS_ST": Decimal("0"),
                        "VL_RED_BC": Decimal("0"),
                        "VL_IPI": Decimal("0"),
                    }
                # Fallback: se itens somam ICMS=0 mas a nota tem VL_ICMS>0, usa valores da nota
                try:
                    total_icms_sum = sum(v["VL_ICMS"] for v in aggregates.values())
                except Exception:
                    total_icms_sum = Decimal("0")
                inv_vl_icms = _dec(invoice.get("_ORIG_VL_ICMS", invoice.get("VL_ICMS", 0)))
                inv_bc_icms = _dec(invoice.get("_ORIG_VL_BC_ICMS", invoice.get("VL_BC_ICMS", 0)))
                inv_vl_doc = _dec(invoice.get("VL_DOC", 0))
                if total_icms_sum == 0 and inv_vl_icms > 0:
                    base_cfop = "5102" if ind_oper == "1" else "1102"
                    aliq_val = (inv_vl_icms / inv_bc_icms * 100) if inv_bc_icms > 0 else Decimal("0")
                    aggregates = {
                        ("000", base_cfop, f"{aliq_val:.2f}"): {
                            "VL_OPR": inv_vl_doc if inv_vl_doc > 0 else inv_bc_icms,
                            "VL_BC_ICMS": inv_bc_icms,
                            "VL_ICMS": inv_vl_icms,
                            "VL_BC_ICMS_ST": Decimal("0"),
                            "VL_ICMS_ST": Decimal("0"),
                            "VL_RED_BC": Decimal("0"),
                            "VL_IPI": Decimal("0"),
                        }
                    }

                for (cst, cfop, aliq), sums in aggregates.items():
                    # Regras para NFC-e (modelo 65): zerar ST/IPI/RED_BC e COD_OBS em branco
                    if cod_mod == "65":
                        sums["VL_BC_ICMS_ST"] = Decimal("0")
                        sums["VL_ICMS_ST"] = Decimal("0")
                        sums["VL_IPI"] = Decimal("0")
                        sums["VL_RED_BC"] = Decimal("0")
                    cfop_norm = cfop or ("5102" if ind_oper == "1" else "1102")
                    if (not cfop_norm.isdigit()) or len(cfop_norm) != 4:
                        cfop_norm = "5102" if ind_oper == "1" else "1102"
                    else:
                        base = "5" if ind_oper == "1" else "1"
                        if cfop_norm[0] not in {base, str(int(base) + 1)}:
                            cfop_norm = base + cfop_norm[1:]
                        common_tail = "102"
                        allowed_tails = {
                            "101","102","103","104","110","111","112","113","114","115","116","125","126","135","136",
                            "141","145","150","151","152","155","199","201","202","203","210","211","215","220","225","229",
                            "250","251","252","255","256","291","292","293","294","295","296","297","298","299","401","402",
                            "403","404","405","406","407","408","409","410","411","412","413","414","415","416","417","418",
                            "419","420","421","422","423","424","425","426","427","428","429","430","431","432","433","434",
                            "435","536","540","541","542","543","544","545","546","547","548","549","550","551","552","553",
                            "554","555","556","557","558","559"
                        }
                        if cfop_norm[1:] not in allowed_tails:
                            cfop_norm = base + common_tail
                    self.add_register("C190", {
                        "CST_ICMS": ("" if cst is None else str(cst)).zfill(3),
                        "CFOP": cfop_norm,
                        "ALIQ_ICMS": _fmt2(aliq),
                        "VL_OPR": money2(sums["VL_OPR"]),
                        "VL_BC_ICMS": money2(sums["VL_BC_ICMS"]),
                        "VL_ICMS": money2(sums["VL_ICMS"]),
                        "VL_BC_ICMS_ST": money2(sums["VL_BC_ICMS_ST"]),
                        "VL_ICMS_ST": money2(sums["VL_ICMS_ST"]),
                        "VL_RED_BC": money2(sums["VL_RED_BC"]),
                        "VL_IPI": money2(sums["VL_IPI"]),
                        "COD_OBS": "",
                    })

        # -------- Bloco E (ApuraÃ§Ã£o do ICMS) --------
        # E001 - indicador de movimento do bloco E
        # Considera movimento quando houver qualquer dÃ©bito/crÃ©dito de ICMS no perÃ­odo.
        from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

        def _to_decimal(x) -> Decimal:
            s = "" if x is None else str(x).strip()
            if s == "":
                return Decimal("0")
            # Normaliza separadores: permite formatos "1234,56" ou "1.234,56" ou "1234.56"
            if "," in s and "." in s:
                # supÃµe ponto como milhar e vÃ­rgula como decimal
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", ".")
            try:
                return Decimal(s)
            except InvalidOperation:
                return Decimal("0")

        total_debitos = Decimal("0")
        total_creditos = Decimal("0")
        for inv in invoices:
            vl_doc = _to_decimal(inv.get("VL_DOC", 0))
            vl_icms = _to_decimal(inv.get("VL_ICMS", 0))
            ind_oper_inv = str(inv.get("IND_OPER", "")).strip()
            cod_mod_inv = str(inv.get("COD_MOD", "")).strip()
            # Saneamento: ignora valores de ICMS fora de faixa razoÃ¡vel
            if vl_doc <= 0:
                continue
            if vl_icms < 0 or vl_icms > vl_doc:
                continue
            # NFC-e sempre saÃ­da (dÃ©bito)
            if cod_mod_inv == "65":
                total_debitos += vl_icms
            else:
                if ind_oper_inv == "1":
                    total_debitos += vl_icms
                else:
                    total_creditos += vl_icms

        has_e_movement = (total_debitos > 0) or (total_creditos > 0)
        self.add_register("E001", {"IND_MOV": "0" if has_e_movement else "1"})

        # E100 - PerÃ­odo de apuraÃ§Ã£o
        self.add_register("E100", {
            "DT_INI": fmt_date(start_date),
            "DT_FIN": fmt_date(end_date),
        })

        # E110 - ApuraÃ§Ã£o consolidada (mÃ­nima)
        vl_aj_debitos = Decimal("0")
        vl_tot_aj_debitos = Decimal("0")
        vl_estornos_cred = Decimal("0")
        vl_aj_creditos = Decimal("0")
        vl_tot_aj_creditos = Decimal("0")
        vl_estornos_deb = Decimal("0")
        vl_sld_credor_ant = Decimal("0")
        vl_tot_ded = Decimal("0")
        deb_esp = Decimal("0")
        vl_out_ded = Decimal("0")

        diff = total_debitos - total_creditos
        if diff >= 0:
            vl_sld_apurado = diff
            vl_icms_recolher = (diff - vl_tot_ded) if (diff - vl_tot_ded) > 0 else Decimal("0")
            vl_sld_credor_transportar = Decimal("0")
        else:
            vl_sld_apurado = Decimal("0")
            vl_icms_recolher = Decimal("0")
            vl_sld_credor_transportar = -diff

        self.add_register("E110", {
            "VL_TOT_DEBITOS": str(total_debitos.normalize()),
            "VL_AJ_DEBITOS": str(vl_aj_debitos.normalize()),
            "VL_TOT_AJ_DEBITOS": str(vl_tot_aj_debitos.normalize()),
            "VL_ESTORNOS_CRED": str(vl_estornos_cred.normalize()),
            "VL_TOT_CREDITOS": str(total_creditos.normalize()),
            "VL_AJ_CREDITOS": str(vl_aj_creditos.normalize()),
            "VL_TOT_AJ_CREDITOS": str(vl_tot_aj_creditos.normalize()),
            "VL_ESTORNOS_DEB": str(vl_estornos_deb.normalize()),
            "VL_SLD_CREDOR_ANT": str(vl_sld_credor_ant.normalize()),
            "VL_SLD_APURADO": str(Decimal(vl_sld_apurado).normalize()),
            "VL_TOT_DED": str(vl_tot_ded.normalize()),
            "VL_ICMS_RECOLHER": str(Decimal(vl_icms_recolher).normalize()),
            "DEB_ESP": str(deb_esp.normalize()),
            "VL_SLD_CREDOR_TRANSPORTAR": str(Decimal(vl_sld_credor_transportar).normalize()),
            "VL_OUT_DED": str(vl_out_ded.normalize()),
        })

    def write(self, path: Path) -> None:
        content = self.to_string()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def format_line(code: str, values: Iterable[str]) -> str:
    import re

    def sanitize(value):
        s = "" if value is None else str(value)
        if s.strip() in {"None", "none", "NULL", "null"}:
            s = ""
        s = s.replace("|", " ").replace("\r", " ").replace("\n", " ")
        # Only convert decimal separator for decimal-looking numbers (with a dot).
        # Preserve integer-like strings (e.g., CNPJ, IE, CFOP, COD_MUN) exactly.
        if re.fullmatch(r"-?\d+\.\d+", s):
            return s.replace(".", ",")
        return s

    sanitized = [sanitize(value) for value in values]
    return "|" + "|".join([code, *sanitized]) + "|"
