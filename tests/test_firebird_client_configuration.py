import pytest

from sped_mensal.database import DatabaseConnection, SpedDataExtractor
from sped_mensal.providers import FirebirdSaoPedroProvider
from sped_mensal.providers.firebird_corrections import FirebirdCompraCorrectionExecutor


def test_extractor_keeps_explicit_firebird_client_path():
    extractor = SpedDataExtractor("DADOS.FDB", r"C:\Firebird\fbclient.dll")

    assert extractor.db.client_library == r"C:\Firebird\fbclient.dll"


def test_provider_passes_explicit_firebird_client_path_to_extractor():
    provider = FirebirdSaoPedroProvider("DADOS.FDB", r"C:\Firebird\fbclient.dll")

    assert provider.client_library == r"C:\Firebird\fbclient.dll"
    assert provider._extractor.db.client_library == r"C:\Firebird\fbclient.dll"


def test_correction_executor_keeps_explicit_firebird_client_path():
    executor = FirebirdCompraCorrectionExecutor("DADOS.FDB", r"C:\Firebird\fbclient.dll")

    assert executor.client_library == r"C:\Firebird\fbclient.dll"


def test_rejects_switching_client_library_in_the_same_process(monkeypatch):
    loaded = DatabaseConnection._canonical_client_path(r"C:\Firebird25\fbclient.dll")
    monkeypatch.setattr(DatabaseConnection, "_client_loaded", True)
    monkeypatch.setattr(DatabaseConnection, "_loaded_client_path", loaded)
    connection = DatabaseConnection("DADOS.FDB", client_library=r"C:\Firebird30\fbclient.dll")

    with pytest.raises(RuntimeError, match="encerre e execute o aplicativo novamente"):
        connection._ensure_client_loaded()
