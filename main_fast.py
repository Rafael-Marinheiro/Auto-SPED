#!/usr/bin/env python3
"""Gera o SPED de 10/2025 com consultas otimizadas (sem itens para NFC-e).

Uso: python main_fast.py
"""

from pathlib import Path
import argparse
from sped_mensal.database import SpedDataExtractor
from sped_mensal.output_encoding import SUPPORTED_OUTPUT_ENCODINGS, normalize_output_encoding
from sped_mensal.services.normalization import (
    normalize_document_status,
    normalize_fiscal_item_mapping,
    normalize_product_mapping,
    parse_fiscal_date,
    parse_sped_decimal,
)
from sped_mensal.services.revenue_code import resolve_e116_revenue_code
from sped_mensal.writer import SpedWriter


def _log(message: str) -> None:
    try:
        log_path = Path("execucao.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fp:
            fp.write(message + "\n")
    except Exception:
        pass


def main(
    db_path: str = "DADOS.FDB",
    start_date: str = "2025-12-01",
    end_date: str = "2025-12-31",
    output_path: str | Path = "saida_sped_out_2025-12.txt",
    client_library: str | None = None,
    output_encoding: str = "utf-8",
    revenue_code: str | None = None,
) -> Path:
    """Emite o SPED pelo fluxo homologado do ERP São Pedro.

    Os valores padrão preservam a execução histórica. Para a operação mensal,
    informe o banco, o período e o arquivo de saída pela linha de comando.
    """

    _log(f"[FAST] Iniciando geracao SPED (cwd={Path.cwd()})")

    extractor = SpedDataExtractor(db_path, client_library)

    # Carrega dados base
    company_info = extractor.get_company_info()
    selected_revenue_code = resolve_e116_revenue_code(company_info, revenue_code)
    _log("[FAST] Empresa carregada")
    accountant_info = extractor.get_accountant_info()
    _log("[FAST] Contador carregado")
    participants = extractor.get_participants()
    _log(f"[FAST] Participantes: {len(participants)}")
    products = extractor.get_products()
    # NormalizaÃ§Ãµes do 0200: trim de descriÃ§Ã£o; TIPO_ITEM (2 dÃ­gitos);
    # NCM (8 dÃ­gitos ou branco); CEST (7 dÃ­gitos ou branco); UNID_INV trim;
    # ALIQ_ICMS com atÃ© 2 casas decimais.
    normalized_products = []
    for product in products:
        try:
            normalized_products.append(normalize_product_mapping(product))
        except Exception:
            normalized_products.append(product)
    products = normalized_products
    _log(f"[FAST] Produtos: {len(products)}")
    units = extractor.get_units()
    _log(f"[FAST] Unidades: {len(units)}")
    invoices = extractor.get_invoices(start_date, end_date)
    _log(f"[FAST] Notas: {len(invoices)}")

    # Normaliza situação e remove inutilizadas.
    filtered_invoices = []
    for inv in invoices:
        cod_sit = normalize_document_status(inv.get("COD_SIT", ""))
        if cod_sit == "05":
            continue
        inv["COD_SIT"] = cod_sit
        # NFC-e: alinhar base e ICMS a zero para evitar inconsistÃªncias
        try:
            if str(inv.get("COD_MOD", "")).strip() == "65":
                inv["_ORIG_VL_BC_ICMS"] = inv.get("VL_BC_ICMS", 0)
                inv["_ORIG_VL_ICMS"] = inv.get("VL_ICMS", 0)
        except Exception:
            pass
        filtered_invoices.append(inv)

    # Remove notas de compra (entrada) com DT_E_S maior que a data final do 0000
    from datetime import datetime
    end_dt_0000 = parse_fiscal_date(end_date)
    if end_dt_0000:
        filtered_invoices = [
            inv
            for inv in filtered_invoices
            if not (
                str(inv.get("IND_OPER", "")).strip() == "0"
                and (entry_date := parse_fiscal_date(inv.get("DT_E_S", ""))) is not None
                and entry_date > end_dt_0000
            )
        ]

    # Mantem apenas participantes usados em C100 (exceto NFC-e 65) e somente notas regulares (00/01)
    used_parts = {
        str(inv.get("COD_PART", "")).strip()
        for inv in filtered_invoices
        if str(inv.get("COD_MOD", "")).strip() != "65"
        and str(inv.get("COD_PART", "")).strip() != ""
        and str(inv.get("COD_SIT", "")).strip() in {"00", "01"}
    }
    if used_parts:
        participants = [p for p in participants if str(p.get("COD_PART", "")).strip() in used_parts]

    # Determina itens e unidades realmente referenciados (para filtrar 0200 e 0190)
    used_item_codes: set[str] = set()
    used_units: set[str] = set()
    item_unit_map: dict[str, str] = {}
    # Preferir mÃ©todo por IDs
    get_by_ids = getattr(extractor, "get_invoice_items_by_ids", None)
    resolve_ids = getattr(extractor, "resolve_invoice_ids", None)
    for inv in filtered_invoices:
        cod_mod = str(inv.get("COD_MOD", "")).strip()
        if cod_mod == "65":
            continue  # NFC-e sem C170
        items: list[dict] = []
        if callable(get_by_ids):
            doc_id = inv.get("DOC_ID", "")
            venda_id = inv.get("VENDA_ID", "")
            if (not doc_id) and callable(resolve_ids):
                ids = resolve_ids(cod_mod, inv.get("SER", ""), inv.get("NUM_DOC", ""))
                doc_id = ids.get("DOC_ID", "")
                venda_id = ids.get("VENDA_ID", "")
            items = get_by_ids(cod_mod, doc_id, venda_id, inv.get("IND_OPER", ""), inv.get("ORIGEM", "")) or []
        else:
            # Fallback por nÃºmero
            items = extractor.get_invoice_items(inv.get("NUM_DOC", "")) or []
        for it in items:
            code = str(it.get("COD_ITEM", "")).strip()
            if code:
                used_item_codes.add(code)
            u = str(it.get("UNID", "")).strip()
            if u:
                used_units.add(u)
                if code:
                    item_unit_map.setdefault(code, u)

    if used_item_codes:
        products_map = {str(p.get("COD_ITEM", "")).strip(): p for p in products}
        missing = used_item_codes - set(products_map)
        for code in missing:
            products.append({
                "COD_ITEM": code,
                "DESCR_ITEM": f"ITEM {code}",
                "UNID_INV": "",
                "TIPO_ITEM": "00",
                "COD_NCM": "",
                "CEST": "",
                "ALIQ_ICMS": "",
            })
        products = [p for p in products if str(p.get("COD_ITEM", "")).strip() in used_item_codes]
    # Preenche UNID_INV faltante com unidade usada nos itens
    if item_unit_map:
        for p in products:
            try:
                code = str(p.get("COD_ITEM", "")).strip()
                if not code:
                    continue
                current_unit = str(p.get("UNID_INV", "")).strip()
                if (not current_unit) and code in item_unit_map:
                    p["UNID_INV"] = item_unit_map[code]
            except Exception:
                continue
    # Unidades efetivamente usadas = das notas (itens) âˆª das fichas 0200 filtradas
    if used_units:
        used_units.update({str(p.get("UNID_INV", "")).strip() for p in products if str(p.get("UNID_INV", "")).strip()})
        units = sorted({u for u in used_units if u})
        units = [{"UNID": u, "DESCR": "UNIDADE"} for u in units]

    # Monkey patches para evitar consultas desnecessarias em NFC-e (65)
    if hasattr(extractor, "get_invoice_items_by_ids"):
        _orig_get_items = extractor.get_invoice_items_by_ids

        def _fast_get_items(cod_mod: str, doc_id, venda_id, ind_oper=None, origem=None):
            # Mant?m consulta para 55 (para c?lculo do C190), mas n?o emitimos C170.
            if str(cod_mod).strip() == "65":
                return []
            items = _orig_get_items(cod_mod, doc_id, venda_id, ind_oper, origem)
            normalized_items = []
            for item in items:
                try:
                    normalized_items.append(normalize_fiscal_item_mapping(item))
                except Exception:
                    normalized_items.append(item)
            return normalized_items

        extractor.get_invoice_items_by_ids = _fast_get_items  # type: ignore

    if hasattr(extractor, "resolve_invoice_ids"):
        _orig_resolve = extractor.resolve_invoice_ids

        def _fast_resolve(cod_mod: str, serie: str, num_doc: str):
            if str(cod_mod).strip() == "65":
                # Para NFC-e nao usamos C170; evitar ping extra no banco
                return {"DOC_ID": None, "VENDA_ID": None}
            return _orig_resolve(cod_mod, serie, num_doc)

        extractor.resolve_invoice_ids = _fast_resolve  # type: ignore

    writer = SpedWriter()
    # Intercepta registros para ajustar C190 das NFC-e (65) sem consultar itens.
    _orig_add_register = writer.add_register

    def _add_register_intercept(code: str, data: dict):
        try:
            if code == "C100":
                # Guarda contexto da última nota C100
                chv = str(data.get("CHV_NFE", "")).strip()
                ser = str(data.get("SER", "")).strip()
                cod_mod_val = str(data.get("COD_MOD", "")).strip()
                # NFC-e: garantir IND_OPER/IND_EMIT preenchidos (saída, emissão própria)
                if cod_mod_val == "65":
                    if not str(data.get("IND_OPER", "")).strip():
                        data["IND_OPER"] = "1"
                    if not str(data.get("IND_EMIT", "")).strip():
                        data["IND_EMIT"] = "0"
                if len(chv) == 44:
                    ser_chv = chv[22:25]
                    if ser_chv and ser_chv != ser:
                        data["SER"] = ser_chv
                        ser = ser_chv
                writer._last_c100_mod = cod_mod_val
                writer._last_c100_emit = str(data.get("IND_EMIT", "")).strip()
                writer._last_c100_sit = str(data.get("COD_SIT", "")).strip()
                writer._last_c100_ctx = {
                    "IND_OPER": str(data.get("IND_OPER", "")).strip(),
                    "VL_OPR": str(data.get("VL_MERC", data.get("VL_DOC", "0"))),
                    "VL_BC_ICMS": str(data.get("VL_BC_ICMS", "0")),
                    "VL_ICMS": str(data.get("VL_ICMS", "0")),
                    "SER": ser,
                    "NUM_DOC": str(data.get("NUM_DOC", "")).strip(),
                    "CHV_NFE": chv,
                }
                # Para NFC-e (65), alinhar C100 com a estratégia de C190 (sem base/ICMS)
                if writer._last_c100_mod == "65":
                    try:
                        data["VL_BC_ICMS"] = "0.00"
                        data["VL_ICMS"] = "0.00"
                        for k in ["COD_PART", "VL_BC_ICMS_ST", "VL_ICMS_ST", "VL_IPI", "VL_PIS", "VL_COFINS", "VL_PIS_ST", "VL_COFINS_ST"]:
                            data[k] = ""
                    except Exception:
                        pass
            # Regra do PVA: Para NF-e emissão própria (IND_EMIT=0), não informar C170
            # (a menos que haja filhos C176/C177/C180/C181, que não geramos). Também omitir para NFC-e (65).
            if code == "C170":
                last_mod = getattr(writer, "_last_c100_mod", "")
                last_emit = getattr(writer, "_last_c100_emit", "")
                if last_mod == "65" or (last_mod == "55" and last_emit == "0"):
                    return
            elif code == "C190" and getattr(writer, "_last_c100_mod", "") == "65":
                # Constrói C190 a partir dos valores originais da NFC-e
                # Não gerar C190 para NFC-e cancelada/denegada (02/03/04)
                last_sit = getattr(writer, "_last_c100_sit", "")
                if last_sit in {"02", "03", "04"}:
                    return
                ctx = getattr(writer, "_last_c100_ctx", {})
                ind_oper = ctx.get("IND_OPER", "1")  # 1=Saída
                cfop = "5102" if ind_oper == "1" else "1102"
                # Resgata valores originais da nota correspondente
                ser = ctx.get("SER", "").strip()
                num = ctx.get("NUM_DOC", "").strip()
                chv_ctx = "".join(ch for ch in str(ctx.get("CHV_NFE", "")).strip() if ch.isdigit())
                ser_norm = ser.lstrip("0") or ser
                target = None
                for inv in filtered_invoices:
                    try:
                        ser_inv = str(inv.get("SER", "")).strip()
                        ser_inv_norm = ser_inv.lstrip("0") or ser_inv
                        if str(inv.get("COD_MOD", "")).strip() == "65" and \
                           ((chv_ctx and "".join(ch for ch in str(inv.get("CHV_NFE", inv.get("CHV", ""))).strip() if ch.isdigit()) == chv_ctx) or \
                            ((ser_inv == ser or ser_inv_norm == ser_norm) and str(inv.get("NUM_DOC", "")).strip() == num)) and \
                           str(inv.get("COD_SIT", "")).strip() in {"00", "01"}:
                            target = inv
                            break
                    except Exception:
                        continue
                # Cálculo da alíquota (quando houver base > 0)
                if target is not None:
                    bc = float(parse_sped_decimal(target.get("_ORIG_VL_BC_ICMS", target.get("VL_BC_ICMS", 0))))
                    icms = float(parse_sped_decimal(target.get("_ORIG_VL_ICMS", target.get("VL_ICMS", 0))))
                    vl_opr = float(parse_sped_decimal(target.get("VL_DOC", 0)))
                else:
                    bc = float(parse_sped_decimal(ctx.get("VL_BC_ICMS", "0")))
                    icms = float(parse_sped_decimal(ctx.get("VL_ICMS", "0")))
                    vl_opr = float(parse_sped_decimal(ctx.get("VL_OPR", "0")))
                aliq = (icms / bc * 100.0) if bc > 0 else 0.0
                new_data = {
                    "CST_ICMS": "000",
                    "CFOP": cfop,
                    "ALIQ_ICMS": f"{aliq:.2f}",
                    "VL_OPR": f"{vl_opr:.2f}",
                    "VL_BC_ICMS": f"{bc:.2f}",
                    "VL_ICMS": f"{icms:.2f}",
                    "VL_BC_ICMS_ST": "0",
                    "VL_ICMS_ST": "0",
                    "VL_RED_BC": "0",
                    "VL_IPI": "0",
                    "COD_OBS": "",
                }
                return _orig_add_register(code, new_data)
        except Exception:
            pass
        return _orig_add_register(code, data)
    writer.add_register = _add_register_intercept  # type: ignore

    _log("[FAST] Montando registros")
    writer.generate_sped_from_db(
        company_info=company_info,
        accountant_info=accountant_info,
        participants=participants,
        products=products,
        units=units,
        invoices=filtered_invoices,
        extractor=extractor,
        start_date=start_date,
        end_date=end_date,
        log_fn=_log,
        revenue_code=selected_revenue_code,
    )
    _log("[FAST] Montagem concluida")

    # Reconstroi o Bloco 9 garantindo totalizador de todos os cÃ³digos (ex.: 1010)
    lines = writer.to_lines()

    def _code_of(line: str) -> str:
        try:
            # formato: |CODE|...
            return line.split("|", 2)[1]
        except Exception:
            return ""

    # Remove Bloco 9 atual
    non9 = [ln for ln in lines if _code_of(ln) not in {"9001", "9900", "9990", "9999"}]

    # PÃ³s-processamento: saneia C100 canceladas/denegadas, trim de campos e ajusta E110 com base em C190
    def _split_fields(ln: str) -> list[str]:
        parts = ln.split("|")
        # garante pelo menos campo final vazio
        if not parts or parts[-1] != "":
            parts.append("")
        return parts

    def _join_fields(parts: list[str]) -> str:
        return "|".join(parts)

    # Soma VL_ICMS dos C190 por natureza (entrada x saÃ­da)
    def _parse_decimal(value) -> float:
        return float(parse_sped_decimal(value))

    total_debitos = 0.0
    total_creditos = 0.0
    # Recalcula a partir dos C190 (pós-ajustes), que é o que o PVA usa nas validações
    for ln in non9:
        if _code_of(ln) == "C190":
            try:
                p = _split_fields(ln)
                cfop = p[3] if len(p) > 3 else ""
                v_icms = _parse_decimal(p[7]) if len(p) > 7 else 0.0
                if cfop.startswith(("5", "6", "7", "8")):
                    total_debitos += v_icms
                elif cfop.startswith(("1", "2", "3", "4")):
                    total_creditos += v_icms
            except Exception:
                continue
    sld_ap_total = max(total_debitos - total_creditos, 0.0)
    current_c100_ok = True  # considera C190 apenas quando C100 atual é regular

    new_non9: list[str] = []
    for ln in non9:
        code = _code_of(ln)
        parts = _split_fields(ln)
        # Trim inÃ­cio/fim em todos os campos
        parts = [p.strip() if isinstance(p, str) else p for p in parts]
        if code == "C100":
            # COD_SIT em posiÃ§Ã£o 6; CHV_NFE em 9
            try:
                cod_sit = parts[6]
                current_c100_ok = cod_sit in {"00", "01"}
                if cod_sit in {"02", "03", "04"}:
                    # manter formato mínimo: IND_OPER, COD_MOD, COD_SIT e CHV_NFE
                    # para NFC-e (65), também manter IND_EMIT, SER e NUM_DOC e forçar IND_EMIT=0
                    cod_mod = parts[5]
                    keep = {2, 5, 6, 9}
                    if cod_mod == "65":
                        keep |= {3, 7, 8}
                        parts[3] = "0"
                    for idx in range(2, len(parts) - 1):
                        if idx not in keep:
                            parts[idx] = ""
                # Sempre limpa campos vetados para NFC-e (65)
                if len(parts) > 5 and parts[5] == "65":
                    if len(parts) > 4:
                        parts[4] = ""  # COD_PART
                    if len(parts) > 2 and not parts[2].strip():
                        parts[2] = "1"  # IND_OPER saída
                    for idx in (21, 22, 23, 24, 25, 26, 27):
                        if idx < len(parts):
                            parts[idx] = ""
            except Exception:
                pass
            try:
                if len(parts) > 5 and parts[5] == "65" and len(parts) > 2 and not parts[2].strip():
                    parts[2] = "1"
            except Exception:
                pass
        elif code == "C190":
            # Totais serÃ£o calculados a partir das notas; nÃ£o acumular via C190
            pass
        new_non9.append(_join_fields(parts))

    non9 = new_non9

    # Harmoniza unidades dos itens (C170) com o 0200 e deduplica C190 por chave (CST/CFOP/ALIQ) dentro de cada C100
    prod_unit_map = {
        str(p.get("COD_ITEM", "")).strip(): str(p.get("UNID_INV", "")).strip()
        for p in products
        if str(p.get("COD_ITEM", "")).strip()
    }

    def _fmt_num(x: float) -> str:
        return f"{x:.2f}".replace(".", ",")

    dedup_non9: list[str] = []
    i = 0
    while i < len(non9):
        ln = non9[i]
        code = _code_of(ln)
        if code != "C100":
            dedup_non9.append(ln)
            i += 1
            continue

        dedup_non9.append(ln)
        j = i + 1
        block_lines: list[str] = []
        while j < len(non9) and _code_of(non9[j]) != "C100":
            block_lines.append(non9[j])
            j += 1

        pre_lines: list[str] = []
        c170_lines: list[list[str]] = []
        c190_lines: list[str] = []
        for bl in block_lines:
            bl_code = _code_of(bl)
            if bl_code == "C170":
                parts = _split_fields(bl)
                try:
                    cod_item = parts[3].strip()
                    unit = parts[6].strip()
                    target_unit = prod_unit_map.get(cod_item, unit)
                    if target_unit:
                        parts[6] = target_unit
                    cst_val = parts[10].strip()
                    if cst_val in {"040", "041", "050", "051"}:
                        parts[13] = _fmt_num(0.0)
                        parts[14] = ""
                        parts[15] = _fmt_num(0.0)
                    bl = _join_fields(parts)
                    parts = _split_fields(bl)
                except Exception:
                    pass
                c170_lines.append(parts)
                pre_lines.append(_join_fields(parts))
            elif bl_code == "C190":
                c190_lines.append(bl)
            else:
                pre_lines.append(bl)

        dedup_non9.extend(pre_lines)

        # Se houver C170, recalcula C190 a partir deles para alinhar CFOP/CST/ALIQ
        if c170_lines:
            accum: dict[tuple[str, str, str], dict[str, float | str]] = {}
            order: list[tuple[str, str, str]] = []
            for parts in c170_lines:
                try:
                    cst = parts[10].strip()
                    cfop = parts[11].strip()
                    vl_item = _parse_decimal(parts[7]) if len(parts) > 7 else 0.0
                    vl_desc = _parse_decimal(parts[8]) if len(parts) > 8 else 0.0
                    vl_bc = _parse_decimal(parts[13]) if len(parts) > 13 else 0.0
                    vl_icms = _parse_decimal(parts[15]) if len(parts) > 15 else 0.0
                    vl_bc_st = _parse_decimal(parts[16]) if len(parts) > 16 else 0.0
                    vl_icms_st = _parse_decimal(parts[17]) if len(parts) > 17 else 0.0
                    vl_ipi = _parse_decimal(parts[24]) if len(parts) > 24 else 0.0
                    if cst == "020":
                        vl_red_bc = max(vl_item - vl_bc, 0.0)
                    else:
                        vl_red_bc = 0.0
                    vl_opr = max(vl_item - vl_desc, 0.0)
                    aliq_raw = parts[14].strip() if len(parts) > 14 else ""
                    if cst in {"040", "041", "050", "051"}:
                        aliq_val = 0.0
                        aliq_str = ""
                        vl_bc = 0.0
                        vl_icms = 0.0
                    else:
                        if aliq_raw == "" and vl_bc > 0 and vl_icms > 0:
                            aliq_val = (vl_icms / vl_bc) * 100.0
                        else:
                            aliq_val = _parse_decimal(aliq_raw)
                        aliq_str = _fmt_num(aliq_val)
                    key = (cst, cfop, aliq_str)
                    if key not in accum:
                        order.append(key)
                        accum[key] = {
                            "cst": cst,
                            "cfop": cfop,
                            "aliq": aliq_str,
                            "vl_opr": 0.0,
                            "vl_bc": 0.0,
                            "vl_icms": 0.0,
                            "vl_bc_st": 0.0,
                            "vl_icms_st": 0.0,
                            "vl_red_bc": 0.0,
                            "vl_ipi": 0.0,
                            "cod_obs": "",
                        }
                    accum[key]["vl_opr"] = float(accum[key]["vl_opr"]) + vl_opr
                    accum[key]["vl_bc"] = float(accum[key]["vl_bc"]) + vl_bc
                    accum[key]["vl_icms"] = float(accum[key]["vl_icms"]) + vl_icms
                    accum[key]["vl_bc_st"] = float(accum[key]["vl_bc_st"]) + vl_bc_st
                    accum[key]["vl_icms_st"] = float(accum[key]["vl_icms_st"]) + vl_icms_st
                    accum[key]["vl_red_bc"] = float(accum[key]["vl_red_bc"]) + vl_red_bc
                    accum[key]["vl_ipi"] = float(accum[key]["vl_ipi"]) + vl_ipi
                except Exception:
                    continue
            for key in order:
                data = accum[key]
                aliq_out = data["aliq"]
                vals = [
                    data["cst"],
                    data["cfop"],
                    aliq_out,
                    _fmt_num(float(data["vl_opr"])),
                    _fmt_num(float(data["vl_bc"])),
                    _fmt_num(float(data["vl_icms"])),
                    _fmt_num(float(data["vl_bc_st"])),
                    _fmt_num(float(data["vl_icms_st"])),
                    _fmt_num(float(data["vl_red_bc"])),
                    _fmt_num(float(data["vl_ipi"])),
                    data["cod_obs"],
                ]
                # Mantém aliq em branco quando aplicável (cst sem ICMS)
                if aliq_out == "":
                    vals[2] = ""
                dedup_non9.append("|C190|" + "|".join(vals) + "|")
        else:
            # Sem C170: deduplica os C190 originais (p. ex., NFC-e)
            accum: dict[tuple[str, str, str], dict[str, float | str]] = {}
            order: list[tuple[str, str, str]] = []
            for c190 in c190_lines:
                parts = _split_fields(c190)
                if len(parts) < 12:
                    continue
                cst = parts[2].strip()
                cfop = parts[3].strip()
                aliq_key = _fmt_num(_parse_decimal(parts[4]))
                key = (cst, cfop, aliq_key)
                if key not in accum:
                    order.append(key)
                    accum[key] = {
                        "cst": cst,
                        "cfop": cfop,
                        "aliq": aliq_key,
                        "vl_opr": 0.0,
                        "vl_bc": 0.0,
                        "vl_icms": 0.0,
                        "vl_bc_st": 0.0,
                        "vl_icms_st": 0.0,
                        "vl_red_bc": 0.0,
                        "vl_ipi": 0.0,
                        "cod_obs": parts[12].strip() if len(parts) > 12 else "",
                    }
                accum[key]["vl_opr"] = float(accum[key]["vl_opr"]) + _parse_decimal(parts[5]) if len(parts) > 5 else float(accum[key]["vl_opr"])
                accum[key]["vl_bc"] = float(accum[key]["vl_bc"]) + _parse_decimal(parts[6]) if len(parts) > 6 else float(accum[key]["vl_bc"])
                accum[key]["vl_icms"] = float(accum[key]["vl_icms"]) + _parse_decimal(parts[7]) if len(parts) > 7 else float(accum[key]["vl_icms"])
                accum[key]["vl_bc_st"] = float(accum[key]["vl_bc_st"]) + _parse_decimal(parts[8]) if len(parts) > 8 else float(accum[key]["vl_bc_st"])
                accum[key]["vl_icms_st"] = float(accum[key]["vl_icms_st"]) + _parse_decimal(parts[9]) if len(parts) > 9 else float(accum[key]["vl_icms_st"])
                accum[key]["vl_red_bc"] = float(accum[key]["vl_red_bc"]) + _parse_decimal(parts[10]) if len(parts) > 10 else float(accum[key]["vl_red_bc"])
                accum[key]["vl_ipi"] = float(accum[key]["vl_ipi"]) + _parse_decimal(parts[11]) if len(parts) > 11 else float(accum[key]["vl_ipi"])

            for key in order:
                data = accum[key]
                vals = [
                    data["cst"],
                    data["cfop"],
                    data["aliq"],
                    _fmt_num(float(data["vl_opr"])),
                    _fmt_num(float(data["vl_bc"])),
                    _fmt_num(float(data["vl_icms"])),
                    _fmt_num(float(data["vl_bc_st"])),
                    _fmt_num(float(data["vl_icms_st"])),
                    _fmt_num(float(data["vl_red_bc"])),
                    _fmt_num(float(data["vl_ipi"])),
                    data["cod_obs"],
                ]
                dedup_non9.append("|C190|" + "|".join(vals) + "|")
        i = j

    non9 = dedup_non9

    # Garante que VL_OPR em C190 n�o seja menor que a base (quando informada)
    fixed_non9: list[str] = []
    for ln in non9:
        if _code_of(ln) == "C190":
            parts = _split_fields(ln)
            try:
                vl_opr = _parse_decimal(parts[5]) if len(parts) > 5 else 0.0
                vl_bc = _parse_decimal(parts[6]) if len(parts) > 6 else 0.0
                if vl_bc > 0 and vl_opr < vl_bc:
                    parts[5] = _fmt_num(vl_bc)
                    ln = _join_fields(parts)
            except Exception:
                pass
        fixed_non9.append(ln)
    non9 = fixed_non9

    # Ajusta C100 para que VL_ICMS (e opcionalmente VL_BC_ICMS) iguale a soma dos C190 do documento
    def _fmt2(x: float) -> str:
        return f"{x:.2f}".replace('.', ',')

    adjusted_icms_non9: list[str] = []
    i = 0
    while i < len(non9):
        ln = non9[i]
        code = _code_of(ln)
        if code == "C100":
            parts = _split_fields(ln)
            # delimita até o próximo C100
            j = i + 1
            sum_bc = 0.0
            sum_icms_c190 = 0.0
            sum_ipi = 0.0
            sum_icms_c170 = 0.0
            sum_vl_item_c170 = 0.0
            has_c170 = False
            while j < len(non9) and _code_of(non9[j]) != "C100":
                child_code = _code_of(non9[j])
                if child_code == "C190":
                    p = _split_fields(non9[j])
                    try:
                        sum_bc += _parse_decimal(p[6])
                        sum_icms_c190 += _parse_decimal(p[7])
                        sum_ipi += _parse_decimal(p[11])
                    except Exception:
                        pass
                elif child_code == "C170":
                    p = _split_fields(non9[j])
                    try:
                        sum_icms_c170 += _parse_decimal(p[15])
                        sum_vl_item_c170 += _parse_decimal(p[7]) if len(p) > 7 else 0.0
                        has_c170 = True
                    except Exception:
                        pass
                j += 1
            # Ajusta apenas para documentos regulares (00/01)
            try:
                cod_sit = parts[6]
                cod_mod = parts[5] if len(parts) > 5 else ""
                if cod_sit in {"00", "01"}:
                    # 21: VL_BC_ICMS, 22: VL_ICMS
                    parts[21] = _fmt2(sum_bc)
                    icms_total = sum_icms_c170 if has_c170 else sum_icms_c190
                    if has_c170 and icms_total == 0.0 and sum_icms_c190 > 0.0:
                        icms_total = sum_icms_c190
                    parts[22] = _fmt2(icms_total)
                    # 16: VL_MERC deve cobrir a soma dos VL_ITEM dos C170 quando existirem
                    try:
                        current_vl_merc = _parse_decimal(parts[16]) if len(parts) > 16 else 0.0
                    except Exception:
                        current_vl_merc = 0.0
                    if has_c170 and sum_vl_item_c170 > 0.0:
                        parts[16] = _fmt2(max(current_vl_merc, sum_vl_item_c170))
                    # 25: VL_IPI (na definição: índice 23, mas aqui por ordem com campo final vazio)
                    if cod_mod == "65":
                        # NFC-e: limpar campos vetados (COD_PART, ST/IPI/PIS/COFINS/PIS_ST/COFINS_ST)
                        if len(parts) > 4:
                            parts[4] = ""
                        for idx_vetado in (23, 24, 25, 26, 27, 28, 29):
                            if len(parts) > idx_vetado:
                                parts[idx_vetado] = ""
                    else:
                        parts[25] = _fmt2(sum_ipi)
                else:
                    # Cancelada/denegada: manter apenas campos essenciais, limpar valores monetários
                    keep_indices = {1, 2, 3, 5, 6, 7, 8, 9}
                    for idx_field in range(len(parts)):
                        if idx_field not in keep_indices:
                            parts[idx_field] = ""
                ln = _join_fields(parts)
            except Exception:
                pass
            adjusted_icms_non9.append(ln)
            # copia os registros até o próximo C100
            for k in range(i + 1, j):
                adjusted_icms_non9.append(non9[k])
            i = j
        else:
            adjusted_icms_non9.append(ln)
            i += 1

    non9 = adjusted_icms_non9

    # Ajusta E110 conforme somatorio dos C190 e gera E116
    # Recalcula debitos/creditos a partir dos C190 (pos-ajustes)
    total_debitos = 0.0
    total_creditos = 0.0
    for ln in non9:
        if _code_of(ln) == "C190":
            p = _split_fields(ln)
            cfop = p[3] if len(p) > 3 else ""
            v_icms = _parse_decimal(p[7]) if len(p) > 7 else 0.0
            if cfop.startswith(("5", "6", "7", "8")):
                total_debitos += v_icms
            elif cfop.startswith(("1", "2", "3", "4")):
                total_creditos += v_icms
    sld_ap_total = max(total_debitos - total_creditos, 0.0)

    adjusted_non9: list[str] = []
    for ln in non9:
        code = _code_of(ln)
        if code == "E110":
            try:
                def fmt(x: float) -> str:
                    return (f"{x:.2f}").replace('.', ',')
                fields = [fmt(0.0)] * 14
                fields[0] = fmt(total_debitos)
                fields[1] = fmt(0.0)
                fields[2] = fmt(0.0)
                fields[3] = fmt(0.0)
                fields[4] = fmt(total_creditos)
                fields[5] = fmt(0.0)
                fields[6] = fmt(0.0)
                fields[7] = fmt(0.0)
                fields[8] = fmt(0.0)
                fields[9] = fmt(sld_ap_total)
                fields[10] = fmt(0.0)
                fields[11] = fmt(sld_ap_total)
                fields[12] = fmt(max(total_creditos - total_debitos, 0.0))
                fields[13] = fmt(0.0)
                ln = "|E110|" + "|".join(fields) + "|"
            except Exception:
                pass
        adjusted_non9.append(ln)

    non9 = adjusted_non9
    # Insere E116 sempre apos E110 (10 campos no total)
    from datetime import datetime, timedelta
    try:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        next_month = (end_dt.replace(day=1) + timedelta(days=32)).replace(day=1)
        vcto = next_month.replace(day=15)
        dt_vcto = vcto.strftime("%d%m%Y")
    except Exception:
        dt_vcto = ""
    try:
        mes_ref = datetime.strptime(end_date, "%Y-%m-%d").strftime("%m%Y")
    except Exception:
        mes_ref = ""
    cod_or = "000"
    cod_rec = selected_revenue_code
    # O escritor compartilhado já pode fornecer E116. O fluxo homologado o
    # substitui porque recalcula o saldo depois dos ajustes finais de C190.
    non9 = [ln for ln in non9 if _code_of(ln) != "E116"]
    inserted_non9 = []
    for ln in non9:
        inserted_non9.append(ln)
        if _code_of(ln) == "E110":
            vl_or = (f"{sld_ap_total:.2f}").replace('.', ',')
            e116_fields = [
                cod_or,
                vl_or,
                dt_vcto,
                cod_rec,
                "",  # NUM_PROC
                "",  # IND_PROC
                "",  # PROC
                "",  # TXT_COMPL
                mes_ref,
            ]
            inserted_non9.append("|E116|" + "|".join(e116_fields) + "|")
    non9 = inserted_non9

# Remover 0200 e 0150 nÃ£o referenciados com base nas linhas finais
    used_cod_item: set[str] = set()
    used_cod_part: set[str] = set()
    used_units_final: set[str] = set()
    for ln in non9:
        code = _code_of(ln)
        parts = _split_fields(ln)
        if code == "C170":
            # C170: COD_ITEM em parts[3]; UNID em parts[6]
            ci = parts[3].strip()
            if ci:
                used_cod_item.add(ci)
            un = parts[6].strip()
            if un:
                used_units_final.add(un)
        elif code == "C100":
            # C100: COD_PART em parts[4]; considerar apenas notas regulares (00/01)
            try:
                cod_sit = parts[6].strip()
                cp = parts[4].strip()
                if cp and cod_sit in {"00", "01"}:
                    used_cod_part.add(cp)
            except Exception:
                pass

    filtered_non9: list[str] = []
    for ln in non9:
        code = _code_of(ln)
        parts = _split_fields(ln)
        if code == "0200":
            cod_item = parts[2].strip()
            if cod_item and cod_item not in used_cod_item:
                continue  # remove 0200 nÃ£o referenciado
        elif code == "0150":
            cod_part = parts[2].strip()
            if cod_part and cod_part not in used_cod_part:
                continue  # remove 0150 nÃ£o referenciado
        elif code == "0190":
            unid = parts[2].strip()
            if unid and used_units_final and unid not in used_units_final:
                continue  # remove unidade nÃ£o usada
        filtered_non9.append(ln)

    non9 = filtered_non9

    # Garante presenÃ§a do 1010 no Bloco 1 (apÃ³s 1001), caso ausente
    has_1010 = any(_code_of(ln) == "1010" for ln in non9)
    if not has_1010:
        try:
            # insere apÃ³s primeira ocorrÃªncia de 1001
            idx_1001 = next(i for i, ln in enumerate(non9) if _code_of(ln) == "1001")
        except StopIteration:
            idx_1001 = None
        line_1010 = "|1010|" + "|".join(["N"] * 13) + "|"
        if idx_1001 is not None:
            non9 = non9[: idx_1001 + 1] + [line_1010] + non9[idx_1001 + 1 :]
        else:
            # sem 1001 explÃ­cito (pouco provÃ¡vel): coloca no inÃ­cio do bloco 1
            non9.append(line_1010)

    # Recalcula totalizadores por bloco (0990, B990, C990, D990, E990, G990, H990, K990, 1990)
    closer_by_block = {
        "0": "0990",
        "B": "B990",
        "C": "C990",
        "D": "D990",
        "E": "E990",
        "G": "G990",
        "H": "H990",
        "K": "K990",
        "1": "1990",
    }
    # Remove totalizadores existentes
    closers_set = set(closer_by_block.values())
    non9_wo_closers = [ln for ln in non9 if _code_of(ln) not in closers_set]

    # Agrupa por bloco
    blocks_order = ["0", "B", "C", "D", "E", "G", "H", "K", "1"]
    grouped: dict[str, list[str]] = {b: [] for b in blocks_order}
    for ln in non9_wo_closers:
        code = _code_of(ln)
        if not code:
            continue
        blk = code[0]
        if blk in grouped:
            grouped[blk].append(ln)
        else:
            # Registros fora dos blocos esperados permanecem na ordem
            grouped.setdefault(blk, []).append(ln)
            if blk not in blocks_order:
                blocks_order.append(blk)

    # ReconstrÃ³i non9 com totalizadores recalculados e na ordem dos blocos
    rebuilt_non9: list[str] = []
    for b in blocks_order:
        lines_b = grouped.get(b, [])
        if not lines_b:
            continue
        rebuilt_non9.extend(lines_b)
        closer = closer_by_block.get(b)
        if closer:
            # QTD_LIN = quantidade de linhas do bloco + 1 (o prÃ³prio totalizador)
            qtd = len(lines_b) + 1
            rebuilt_non9.append(f"|{closer}|{qtd}|")

    non9 = rebuilt_non9

    # Conta ocorrÃªncias por cÃ³digo (exceto Bloco 9)
    counts: dict[str, int] = {}
    for ln in non9:
        c = _code_of(ln)
        if not c:
            continue
        counts[c] = counts.get(c, 0) + 1

    # Bloco 9 reconstruÃ­do
    has_data = len(non9) > 0
    new9: list[str] = []
    new9.append(f"|9001|{'0' if has_data else '1'}|")

    base_codes = sorted(set(counts.keys()) | {"9001", "9990", "9999"})
    counts["9001"] = 1
    counts["9990"] = 1
    counts["9999"] = 1
    # 9900 aparece uma vez por cÃ³digo listado em 9900
    list_for_9900 = sorted(set(base_codes) | {"9900"})
    counts["9900"] = len(list_for_9900)
    for code in list_for_9900:
        new9.append(f"|9900|{code}|{counts.get(code, 0)}|")

    qtd_lin_9 = len(new9) + 2  # linhas já em new9 + o próprio 9990
    new9.append(f"|9990|{qtd_lin_9}|")

    # 9999 = total de linhas do arquivo (inclui 9999)
    total_lines = len(non9) + len(new9) + 1
    final_lines = non9 + new9 + [f"|9999|{total_lines}|"]
    # Garantia final: IND_OPER em NFC-e (65) não pode ficar vazio
    fixed_final: list[str] = []
    for ln in final_lines:
        if _code_of(ln) == "C100":
            parts = _split_fields(ln)
            try:
                if len(parts) > 5 and parts[5] == "65" and len(parts) > 2 and not parts[2].strip():
                    parts[2] = "1"
                    ln = _join_fields(parts)
            except Exception:
                pass
        fixed_final.append(ln)
    final_lines = fixed_final

    output_path = Path(output_path)
    output_path.write_text(
        "\n".join(final_lines) + "\n",
        encoding=normalize_output_encoding(output_encoding),
    )
    _log(f"[FAST] Arquivo gerado em {output_path}")
    print(f"Arquivo SPED gerado com sucesso: {output_path}")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Emite o SPED pelo fluxo homologado do ERP São Pedro.",
    )
    parser.add_argument("--database", default="DADOS.FDB", help="Caminho do banco Firebird.")
    parser.add_argument("--start-date", default="2025-12-01", help="Início do período (YYYY-MM-DD).")
    parser.add_argument("--end-date", default="2025-12-31", help="Fim do período (YYYY-MM-DD).")
    parser.add_argument("--output", default="saida_sped_out_2025-12.txt", help="Arquivo TXT de saída.")
    parser.add_argument(
        "--fbclient",
        help="Caminho do fbclient.dll compatível com o Firebird e com este Python.",
    )
    parser.add_argument(
        "--encoding",
        choices=SUPPORTED_OUTPUT_ENCODINGS,
        default="utf-8",
        help="Codificação do TXT de saída (default: utf-8).",
    )
    parser.add_argument(
        "--revenue-code",
        help="Código de receita do E116; se omitido, usa a empresa/UF quando configurada.",
    )
    args = parser.parse_args()
    main(
        args.database,
        args.start_date,
        args.end_date,
        args.output,
        args.fbclient,
        args.encoding,
        args.revenue_code,
    )



