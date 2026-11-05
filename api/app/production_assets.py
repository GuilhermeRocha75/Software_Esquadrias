"""Company-scoped logical asset index. Never reads customer files or paths."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath
import re
from uuid import UUID


@dataclass(frozen=True)
class ProductionAsset:
    """Registered asset metadata; content/hash verification belongs to Phase B."""

    key: str
    relative_path: str
    sha256: str

    def __post_init__(self):
        path = self.relative_path
        if (not self.key.strip() or not path or "\\" in path or ":" in path
                or PurePosixPath(path).is_absolute() or PureWindowsPath(path).drive
                or any(part in {"", ".", ".."} for part in path.split("/"))
                or not re.fullmatch(r"[0-9a-f]{64}", self.sha256)):
            raise ValueError("Asset exige chave, caminho relativo seguro e SHA-256 hexadecimal.")


@dataclass(frozen=True)
class ProductionAssetIndex:
    """Immutable metadata index belonging to exactly one company."""

    company_id: UUID
    entries: tuple[ProductionAsset, ...] = ()

    def __post_init__(self):
        if len({entry.key for entry in self.entries}) != len(self.entries):
            raise ValueError("Chave de asset duplicada.")

    def find(self, key: str) -> ProductionAsset | None:
        """Return registered metadata for an exact logical key, or None."""
        return next((entry for entry in self.entries if entry.key == key), None)
