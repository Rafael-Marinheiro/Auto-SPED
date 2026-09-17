from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sped_mensal.writer import SpedConfig, SpedWriter


DATA_PATH = Path(__file__).parent.parent / "data" / "exemplo_sped.json"


def load_writer() -> SpedWriter:
    config = SpedConfig.from_json(DATA_PATH)
    writer = SpedWriter()
    writer.extend_from_config(config)
    return writer


def parse_line(line: str) -> list[str]:
    return line.strip().strip("|").split("|")


def test_generate_lines_structure():
    writer = load_writer()
    lines = writer.to_lines()

    assert lines[0].startswith("|0000|")
    assert lines[-2].startswith("|9990|")
    assert lines[-1].startswith("|9999|")

    total_reported = int(parse_line(lines[-1])[1])
    assert total_reported == len(lines)

    idx_9001 = next(i for i, line in enumerate(lines) if line.startswith("|9001|"))
    qtd_lin_9 = int(parse_line(lines[-2])[1])
    # QTD_LIN_9 abrange do 9001 ao 9999, inclusive.
    assert qtd_lin_9 == len(lines[idx_9001:])


def test_control_register_counts():
    writer = load_writer()
    lines = writer.to_lines()

    counts = {"9900": {}}
    for line in lines:
        parts = parse_line(line)
        if parts[0] == "9900":
            counts["9900"][parts[1]] = int(parts[2])

    assert counts["9900"]["0000"] == 1
    assert counts["9900"]["C100"] == 1
    assert counts["9900"]["C170"] == 1
    assert counts["9900"]["0990"] == 1
    assert counts["9900"]["C990"] == 1

    # total de registros 9900 deve corresponder ao valor informado para o próprio código 9900
    qtd_9900 = sum(1 for line in lines if line.startswith("|9900|"))
    assert counts["9900"]["9900"] == qtd_9900
