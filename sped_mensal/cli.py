"""Interface de linha de comando para geração do arquivo SPED."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from .database import SpedDataExtractor
from .providers import FirebirdSaoPedroProvider
from .validation import validate_provider
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


if __name__ == "__main__":
    raise SystemExit(main())
