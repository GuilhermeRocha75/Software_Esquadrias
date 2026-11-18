"""Add original sketches to an existing private OP image library."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from api.app.production_images import (
    ImageSelector, ProductionImageManifest, StoredProductionImage, image_metadata,
)


def import_sketches(source: Path, manifest_path: Path) -> int:
    manifest_path = manifest_path.resolve(strict=True)
    original = manifest_path.read_bytes()
    manifest = ProductionImageManifest.model_validate_json(original)
    root = manifest_path.parent
    entries = {entry.selector.key(): entry for entry in manifest.entries}
    imported = 0
    for path in sorted(source.iterdir()):
        if not path.is_file() or path.suffix.lower() != ".jpg":
            continue
        name = path.stem + ".jpg"
        if not any(marker in name for marker in ("MAXIM-AR", "DE GIRO", "PAINEL  FIXO -")):
            continue
        finish = next((color for color in ("BRANCO", "PRETO")
                       if name.endswith(f" ({color}).jpg")), None)
        if finish is None:
            continue
        if path.stat().st_size > 20_000_000:
            raise ValueError("Imagem acima do limite.")
        data = path.read_bytes()
        media, width, height = image_metadata(data)
        digest = hashlib.sha256(data).hexdigest()
        relative = f"objects/{digest}.jpg"
        destination = root / relative
        destination.parent.mkdir(exist_ok=True)
        if not destination.resolve().is_relative_to(root):
            raise ValueError("Destino fora da biblioteca.")
        entry = StoredProductionImage(
            selector=ImageSelector(kind="MODEL_SKETCH",
                model_key="LEGACY/" + hashlib.sha256(name.encode("utf-8")).hexdigest(),
                finish_key=finish),
            relative_path=relative, sha256=digest, media_type=media,
            width_px=width, height_px=height, finish_policy="EXACT",
            source_basename=name)
        if destination.exists():
            if destination.read_bytes() != data:
                raise ValueError("Objeto existente com conteúdo divergente.")
        else:
            destination.write_bytes(data)
        entries[entry.selector.key()] = entry
        imported += 1
    if not imported:
        raise ValueError("Nenhum croqui compatível encontrado na pasta.")
    updated = ProductionImageManifest(
        company_id=manifest.company_id,
        source_workbook_sha256=manifest.source_workbook_sha256,
        entries=tuple(entries.values()))
    # Stop the API before import. Replace the manifest only after all images validate.
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=root, delete=False) as temp:
        temporary = Path(temp.name)
        temp.write(updated.model_dump_json(indent=2) + "\n")
    try:
        if manifest_path.read_bytes() != original:
            raise ValueError("A biblioteca mudou durante a importação. Repita com a API parada.")
        os.replace(temporary, manifest_path)
    finally:
        temporary.unlink(missing_ok=True)
    return imported


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / ".private/op-b1/images/manifest.json")
    args = parser.parse_args()
    print(f"{import_sketches(args.source_dir, args.manifest)} croquis importados.")
