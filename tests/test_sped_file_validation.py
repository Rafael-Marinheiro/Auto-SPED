from sped_mensal.validation import validate_sped_lines


def test_sped_file_validation_detects_the_common_pva_errors():
    lines = [
        "|0000|020|0|01082026|31082026|Empresa|123| |RN|2402709|||A|1|",
        "|0001|0|",
        "|C001|0|",
        "|C100|0|1|1|55|00|1||chave|01082026|01082026|10|0|0|0|10|0|0|0|0|0|0|0|0|0|0|0|0|0|",
        "|C100|0|1|1|55|00|1||chave|01082026|01082026|10|0|0|0|10|0|0|0|0|0|0|0|0|0|0|0|0|0|",
        "|C170|1|P||1|UN|10|0|0||1102|",
        "|C190||1102|0|10|0|0|0|0|0|0|0||",
        "|C990|7|",
        "|9001|0|",
        "|9900|0000|1|",
        "|9990|3|",
        "|9999|11|",
    ]

    report = validate_sped_lines(lines)
    codes = {issue.code for issue in report.issues}

    assert "c100.num_doc.required" in codes
    assert "c100.key.duplicate" in codes
    assert "c170.cst.required" in codes
    assert "c190.cst.required" in codes
    assert "block9.count.invalid" in codes
    assert "file.9999.count.invalid" in codes


def test_sped_file_validation_accepts_a_minimal_consistent_file():
    lines = [
        "|0000|020|0|01082026|31082026|Empresa|123||RN|2402709|||A|1|",
        "|0001|1|",
        "|C001|1|",
        "|C990|2|",
        "|9001|0|",
        "|9900|0000|1|",
        "|9990|4|",
        "|9999|8|",
    ]

    report = validate_sped_lines(lines)

    assert report.is_valid
