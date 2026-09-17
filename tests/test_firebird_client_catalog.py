import struct

from sped_mensal.services.firebird_client import (
    client_architecture,
    detect_installed_clients,
    official_client_options,
)


def _write_pe(path, machine: int) -> None:
    payload = bytearray(128)
    payload[:2] = b"MZ"
    payload[0x3C:0x40] = struct.pack("<I", 64)
    payload[64:68] = b"PE\0\0"
    payload[68:70] = struct.pack("<H", machine)
    path.write_bytes(payload)


def test_catalog_has_official_urls_for_supported_windows_versions():
    options = official_client_options()

    assert {(option.version, option.architecture) for option in options} == {
        (version, architecture)
        for version in ("2.5.9", "3.0.14", "4.0.7", "5.0.4")
        for architecture in (32, 64)
    }
    assert all(option.source_url.startswith("https://github.com/FirebirdSQL/") for option in options)


def test_detects_pe_architecture_and_local_client(tmp_path):
    dll = tmp_path / "Firebird-3.0.14" / "bin" / "fbclient.dll"
    dll.parent.mkdir(parents=True)
    _write_pe(dll, 0x8664)

    assert client_architecture(dll) == 64
    found = detect_installed_clients([tmp_path])
    assert len(found) == 1
    assert found[0].architecture == 64
    assert found[0].path == dll.resolve()
