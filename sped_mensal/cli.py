"""Interface de linha de comando para geração do arquivo SPED."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from .database import SpedDataExtractor
from .providers import FirebirdSaoPedroProvider
from .services import build_capture_summary
from .validation import validate_provider, validate_sped_file
from .writer import SpedWriter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Gera um arquivo SPED EFD ICMS/IPI a partir de um banco de dados Firebird.",
    )
    parser.add_argument(
        "--database",
        required=True,
        type=Path,
        help="Caminho para o arquivo do banco de dados Firebird (.fdb).",
    )
    parser.add_argument(
        "--start-date",
        required=True,
        type=str,
        help="Data inicial do período (formato: YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        type=str,
        help="Data final do período (formato: YYYY-MM-DD).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("saida_sped.txt"),
        help="Caminho do arquivo de saída (default: saida_sped.txt).",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Valida os dados fiscais sem gerar ou alterar arquivos SPED.",
    )
    parser.add_argument(
        "--validation-report",
        type=Path,
        help="Grava o relatório de pré-validação em JSON.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.validate_only or args.validation_report:
        provider = FirebirdSaoPedroProvider(str(args.database))
        report = validate_provider(provider, args.start_date, args.end_date)
        print(
            f"Pré-validação concluída: {report.error_count} erro(s), "
            f"{report.warning_count} aviso(s), {report.invoice_count} documento(s)."
        )
        for issue in report.issues:
            print(
                f"[{issue.severity.value.upper()}] {issue.sped_record}.{issue.field} "
                f"em {issue.source_ref}: {issue.message}"
            )
        if args.validation_report:
            args.validation_report.parent.mkdir(parents=True, exist_ok=True)
            args.validation_report.write_text(
                json.dumps(report.to_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(f"Relatório gravado em {args.validation_report.resolve()}")
        if args.validate_only:
            return 0 if report.is_valid else 1

    # Extrai dados do banco
    extractor = SpedDataExtractor(str(args.database))
    company_info = extractor.get_company_info()
    accountant_info = extractor.get_accountant_info()
    participants = extractor.get_participants()
    products = extractor.get_products()
    units = extractor.get_units()
    invoices = extractor.get_invoices(args.start_date, args.end_date)

    # Gera o SPED
    writer = SpedWriter()
    writer.generate_sped_from_db(
        company_info, accountant_info, participants, products, units, invoices, extractor, args.start_date, args.end_date
    )
    writer.write(args.output)

    print(f"Arquivo SPED gerado com sucesso em {args.output.resolve()}")
    return 0


def main_capture_map(argv: Optional[Sequence[str]] = None) -> int:
    """Exibe o mapa do capturador de referência sem abrir o banco."""

    parser = argparse.ArgumentParser(description="Mostra o mapa de captura do conector Firebird São Pedro.")
    parser.add_argument("--format", choices=("table", "json"), default="table")
    args = parser.parse_args(argv)
    mappings = FirebirdSaoPedroProvider("DADOS.FDB").describe_capture()
    if args.format == "json":
        print(json.dumps([
            {
                "entity": mapping.entity,
                "fiscal_field": mapping.fiscal_field,
                "source": mapping.source,
                "sped_targets": mapping.sped_targets,
                "note": mapping.note,
            }
            for mapping in mappings
        ], ensure_ascii=False, indent=2))
        return 0

    print(f"{'Dado fiscal':<18} {'Origem':<72} Destino SPED")
    print("-" * 120)
    for mapping in mappings:
        print(f"{mapping.entity + '.' + mapping.fiscal_field:<18} {mapping.source:<72} {', '.join(mapping.sped_targets)}")
    return 0


def main_validate_sped(argv: Optional[Sequence[str]] = None) -> int:
    """Valida a estrutura de um TXT SPED já gerado."""

    parser = argparse.ArgumentParser(description="Valida a estrutura de um arquivo TXT SPED.")
    parser.add_argument("file", type=Path, help="Arquivo TXT SPED para validação.")
    parser.add_argument("--report", type=Path, help="Destino opcional do relatório JSON.")
    args = parser.parse_args(argv)
    report = validate_sped_file(args.file)
    print(f"Validação concluída: {report.error_count} erro(s), {report.warning_count} aviso(s).")
    for issue in report.issues:
        print(f"[{issue.severity.value.upper()}] {issue.source_ref} {issue.sped_record}.{issue.field}: {issue.message}")
    if args.report:
        args.report.write_text(json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Relatório gravado em {args.report.resolve()}")
    return 0 if report.is_valid else 1


def main_capture_summary(argv: Optional[Sequence[str]] = None) -> int:
    """Mostra uma prévia tipada dos dados capturados no período."""

    parser = argparse.ArgumentParser(description="Resume os dados capturados de um período fiscal.")
    parser.add_argument("--database", required=True, type=Path, help="Caminho do banco Firebird.")
    parser.add_argument("--start-date", required=True, help="Início do período (YYYY-MM-DD).")
    parser.add_argument("--end-date", required=True, help="Fim do período (YYYY-MM-DD).")
    parser.add_argument("--format", choices=("table", "json"), default="table")
    parser.add_argument("--output", type=Path, help="Arquivo JSON opcional para salvar a prévia.")
    args = parser.parse_args(argv)
    summary = build_capture_summary(
        FirebirdSaoPedroProvider(str(args.database)), args.start_date, args.end_date
    )
    payload = summary.to_dict()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Prévia gravada em {args.output.resolve()}")
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    print(f"Empresa: {summary.company.name} | CNPJ: {summary.company.cnpj}")
    print(f"Período: {summary.start_date} a {summary.end_date}")
    print(
        f"Produtos: {summary.product_count} | Participantes: {summary.participant_count} | "
        f"Documentos: {summary.document_count} | Total: {summary.document_total:.2f}"
    )
    print("NUM_DOC       ORIGEM       MODELO  SÉRIE  EMISSÃO       TOTAL")
    print("-" * 72)
    for document in summary.documents:
        print(
            f"{document.number:<13} {document.origin:<12} {document.model:<7} "
            f"{document.series:<6} {document.issue_date:<13} {document.total:.2f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
