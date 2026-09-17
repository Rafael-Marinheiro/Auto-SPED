"""Catálogo, detecção e instalação local do cliente Firebird.

Os binários nunca fazem parte do repositório. Quando solicitado, o módulo baixa
o kit ZIP oficial e o extrai para o perfil local do usuário.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import struct
from tempfile import TemporaryDirectory
from typing import Callable, Iterable
from urllib.request import urlretrieve
from zipfile import ZipFile


ProgressCallback = Callable[[int, int | None], None]


@dataclass(frozen=True)
class FirebirdClientOption:
    """Uma biblioteca instalada ou um kit oficial disponível para download."""

    version: str
    architecture: int
    source_url: str | None = None
    path: Path | None = None
    end_of_life: bool = False

    @property
    def label(self) -> str:
        status = " (fim de vida)" if self.end_of_life else ""
        origin = "instalado" if self.path else "download oficial"
        return f"Firebird {self.version} — {self.architecture} bits — {origin}{status}"


_OFFICIAL_RELEASES = (
    ("2.5.9", 32, "https://github.com/FirebirdSQL/firebird/releases/download/R2_5_9/Firebird-2.5.9.27139-0_Win32.zip", True),
    ("2.5.9", 64, "https://github.com/FirebirdSQL/firebird/releases/download/R2_5_9/Firebird-2.5.9.27139-0_x64.zip", True),
    ("3.0.14", 32, "https://github.com/FirebirdSQL/firebird/releases/download/v3.0.14/Firebird-3.0.14.33856-0-Win32.zip", False),
    ("3.0.14", 64, "https://github.com/FirebirdSQL/firebird/releases/download/v3.0.14/Firebird-3.0.14.33856-0-x64.zip", False),
    ("4.0.7", 32, "https://github.com/FirebirdSQL/firebird/releases/download/v4.0.7/Firebird-4.0.7.3271-0-Win32.zip", False),
    ("4.0.7", 64, "https://github.com/FirebirdSQL/firebird/releases/download/v4.0.7/Firebird-4.0.7.3271-0-x64.zip", False),
    ("5.0.4", 32, "https://github.com/FirebirdSQL/firebird/releases/download/v5.0.4/Firebird-5.0.4.1812-0-windows-x86.zip", False),
    ("5.0.4", 64, "https://github.com/FirebirdSQL/firebird/releases/download/v5.0.4/Firebird-5.0.4.1812-0-windows-x64.zip", False),
)


def python_architecture() -> int:
    """Retorna a arquitetura do interpretador que carregará o fbclient."""
    return struct.calcsize("P") * 8


def official_client_options() -> tuple[FirebirdClientOption, ...]:
    """Lista kits ZIP Windows do projeto Firebird, sem baixar nada."""
    options: list[FirebirdClientOption] = []
    for version, architecture, url, end_of_life in _OFFICIAL_RELEASES:
        options.append(FirebirdClientOption(version, architecture, url, end_of_life=end_of_life))
    return tuple(options)


def client_architecture(path: Path) -> int | None:
    """Lê o cabeçalho PE para identificar DLL Windows de 32 ou 64 bits."""
    try:
        with path.open("rb") as binary:
            if binary.read(2) != b"MZ":
                return None
            binary.seek(0x3C)
            pe_offset = struct.unpack("<I", binary.read(4))[0]
            binary.seek(pe_offset)
            if binary.read(4) != b"PE\0\0":
                return None
            machine = struct.unpack("<H", binary.read(2))[0]
    except (OSError, struct.error):
        return None
    return {0x14C: 32, 0x8664: 64}.get(machine)


def default_client_directory() -> Path:
    """Pasta local, fora do projeto, para kits baixados pelo usuário."""
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".auto-sped")
    return Path(base) / "Auto-SPED" / "firebird-clients"


def detect_installed_clients(search_roots: Iterable[Path] | None = None) -> tuple[FirebirdClientOption, ...]:
    """Encontra DLLs de instalações comuns sem tentar carregá-las."""
    if search_roots is None:
        roots = [
            Path(os.environ.get("ProgramFiles", r"C:\\Program Files")) / "Firebird",
            Path(os.environ.get("ProgramFiles(x86)", r"C:\\Program Files (x86)")) / "Firebird",
            default_client_directory(),
        ]
    else:
        roots = list(search_roots)

    found: list[FirebirdClientOption] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for dll in root.rglob("fbclient.dll"):
            resolved = dll.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            architecture = client_architecture(resolved) or 0
            version = next(
                (release[0] for release in _OFFICIAL_RELEASES if release[0] in str(resolved)),
                "detectada",
            )
            found.append(FirebirdClientOption(version, architecture, path=resolved))
    return tuple(sorted(found, key=lambda option: str(option.path).lower()))


def _safe_extract(zip_file: ZipFile, destination: Path) -> None:
    root = destination.resolve()
    for member in zip_file.infolist():
        candidate = (destination / member.filename).resolve()
        if os.path.commonpath((str(root), str(candidate))) != str(root):
            raise ValueError("O arquivo oficial contém um caminho inválido para extração.")
    zip_file.extractall(destination)


def download_official_client(
    option: FirebirdClientOption,
    destination_root: Path | None = None,
    progress: ProgressCallback | None = None,
) -> Path:
    """Baixa e extrai um kit oficial, retornando o caminho do ``fbclient.dll``.

    A função aceita somente opções do catálogo oficial e não executa instaladores.
    """
    official = {entry.source_url for entry in official_client_options()}
    if not option.source_url or option.source_url not in official:
        raise ValueError("Selecione uma versão disponível no catálogo oficial Firebird.")
    if option.architecture != python_architecture():
        raise ValueError(
            f"O Python atual é {python_architecture()} bits; selecione um cliente "
            f"de {python_architecture()} bits."
        )

    root = destination_root or default_client_directory()
    destination = root / f"firebird-{option.version}" / f"win{option.architecture}"
    existing = next(destination.rglob("fbclient.dll"), None) if destination.exists() else None
    if existing:
        return existing.resolve()

    def report(count: int, block_size: int, total_size: int) -> None:
        if progress:
            progress(count * block_size, total_size if total_size > 0 else None)

    with TemporaryDirectory(prefix="auto-sped-firebird-") as temp_dir:
        archive = Path(temp_dir) / "firebird.zip"
        urlretrieve(option.source_url, archive, reporthook=report)
        target_temp = Path(temp_dir) / "extracted"
        target_temp.mkdir()
        with ZipFile(archive) as zip_file:
            _safe_extract(zip_file, target_temp)
        client = next(target_temp.rglob("fbclient.dll"), None)
        if not client:
            raise FileNotFoundError("O kit baixado não contém fbclient.dll.")
        if client_architecture(client) not in {None, option.architecture}:
            raise ValueError("A arquitetura da DLL baixada diverge da versão selecionada.")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            shutil.rmtree(destination)
        shutil.move(str(target_temp), str(destination))
    return next(destination.rglob("fbclient.dll")).resolve()
