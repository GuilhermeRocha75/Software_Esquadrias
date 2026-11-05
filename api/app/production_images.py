"""Logical OP image identities and verified, company-scoped private storage."""
from __future__ import annotations

import hashlib
from io import BytesIO
from pathlib import Path, PureWindowsPath
import unicodedata
import warnings
from uuid import UUID

from PIL import Image
from pydantic import Field, model_validator, TypeAdapter
from typing import Literal

from .production_assets import ProductionAsset
from .production_schemas import OPModel, TechnicalInput
from .production_service import canonical_json
from . import engine_bridge
from esquadrias_engine.catalog import MATERIALS


def finish_identity(value: str | None) -> str | None:
    """Normalize a finish label without selecting a different finish."""
    return unicodedata.normalize("NFC", value).strip().upper() if value and value.strip() else None


def model_identity(inputs: dict, finish: str | None) -> tuple[str, str | None]:
    """Return topology key and exact legacy basename, excluding sizes/prices/qty.

    This is image naming, not engineering. Missing files never trigger fallback
    to another model or finish. All technical inputs remain in the OP snapshot.
    """
    inputs = TypeAdapter(TechnicalInput).validate_python(inputs).model_dump(mode="json")
    family = inputs["family"]
    shutter = inputs.get("shutter")
    shutter_on = shutter.get("mode") != "SEM PERSIANA" if shutter is not None else bool(inputs.get("shutter_enabled"))
    grid = inputs.get("leaf_grid", {})
    topology = {key: inputs.get(key) for key in ("family", "leaf_system", "application", "leaf_count", "orientation", "module_mode", "panel_mode")}
    topology.update(screen=bool(inputs.get("screen_enabled")), shutter=shutter_on,
                    leaf_grid=[grid.get("vertical_transoms", 0), grid.get("horizontal_transoms", 0)],
                    fixed_grid=[inputs.get("vertical_transoms", 0), inputs.get("horizontal_transoms", 0)])
    suffix = ""
    for label, field in (("INFERIOR", "bottom_fixed_panel"), ("SUPERIOR", "top_fixed_panel")):
        panel = inputs.get(field)
        gr_prefix = "bottom" if label == "INFERIOR" else "top"
        if family == "GR" and inputs.get(f"{gr_prefix}_flag_height_mm", 0):
            panel = {"vertical_transoms": inputs.get(f"{gr_prefix}_flag_vertical_transoms", 0),
                     "horizontal_transoms": inputs.get(f"{gr_prefix}_flag_horizontal_transoms", 0)}
        dims = None if panel is None else [panel.get("vertical_transoms", 0), panel.get("horizontal_transoms", 0)]
        topology[field] = dims
        if dims is not None:
            suffix += (" + BANDEIRA " if not suffix else " E ") + label + f" ({dims[0]}{dims[1]})"
    key = family + "/" + hashlib.sha256(canonical_json(topology).encode("utf-8")).hexdigest()
    color = finish_identity(finish)
    if color is None:
        return key, None
    if family == "FX":
        name = f"PAINEL  FIXO - {inputs.get('vertical_transoms', 0)}{inputs.get('horizontal_transoms', 0)}"
    else:
        count = inputs.get("leaf_count", 1)
        application = "JANELA" if family == "MAXIM_AR" else inputs.get("application", "JANELA" if family == "CR" else "PORTA")
        name = f"{application} {count} {'FOLHA' if count == 1 else 'FOLHAS'} "
        name += {"CR": "DE CORRER", "MAXIM_AR": "MAXIM-AR", "GR": "DE GIRO"}[family]
        if family == "CR" and any(topology["leaf_grid"]):
            name += f" ({topology['leaf_grid'][0]}{topology['leaf_grid'][1]})"
        if family == "MAXIM_AR" and count != 1:
            name += " (V)" if inputs.get("orientation") == "VERTICAL" else " (H)"
        if shutter_on:
            name += " COM PERSIANA"
        if inputs.get("screen_enabled"):
            name += " + TELA MOSQUITEIRA" if family == "CR" else " + TELA"
        name += suffix
        if family == "GR":
            name += {"PAINEL COMPLETO": " COM PAINEL HORIZONTAL", "SUPERIOR VIDRO/INFERIOR PAINEL": " COM PARTE SUPERIOR DE VIDRO E INFERIOR DE PAINEL"}.get(inputs.get("panel_mode"), "")
    basename = f"{name} ({color}).jpg"
    if any(c in basename for c in "\\/:") or any(ord(c) < 32 for c in basename):
        raise ValueError("Descritor de imagem deve ser um nome técnico, sem caminho.")
    return key, basename


class ImageSelector(OPModel):
    """Exact model/finish or profile/finish identity, independent of file paths."""
    kind: Literal["MODEL_SKETCH", "PROFILE_SECTION"]
    model_key: str | None = None
    code: str | None = None
    finish_key: str | None = None

    @model_validator(mode="after")
    def identity_is_complete(self):
        if self.kind == "MODEL_SKETCH" and (not self.model_key or not self.finish_key or self.code is not None):
            raise ValueError("Croqui exige modelo e acabamento explícitos.")
        if self.kind == "PROFILE_SECTION" and (not self.code or self.code == "0" or self.model_key is not None):
            raise ValueError("Seção exige código de perfil válido.")
        if self.kind == "PROFILE_SECTION" and (self.code not in MATERIALS or MATERIALS[self.code].unit != "m"):
            raise ValueError("Código de seção não pertence ao catálogo técnico de perfis.")
        if self.finish_key is not None and self.finish_key != finish_identity(self.finish_key):
            raise ValueError("Acabamento deve usar a identidade normalizada.")
        return self

    def key(self) -> str:
        """Canonical exact key; no wildcard model matching."""
        return canonical_json(self.model_dump(mode="json"))


class StoredProductionImage(OPModel):
    """Verified original file metadata. Neutral sections follow the legacy VBA."""
    selector: ImageSelector
    relative_path: str
    sha256: str
    media_type: Literal["image/jpeg", "image/png", "image/webp"]
    width_px: int = Field(gt=0)
    height_px: int = Field(gt=0)
    finish_policy: Literal["EXACT", "NEUTRAL_LEGACY_SECTION"]

    @model_validator(mode="after")
    def safe_metadata(self):
        ProductionAsset(self.selector.key(), self.relative_path, self.sha256)
        if any(ord(c) < 32 for c in self.relative_path):
            raise ValueError("Caminho contém caracteres de controle.")
        neutral = self.finish_policy == "NEUTRAL_LEGACY_SECTION"
        if neutral != (self.selector.kind == "PROFILE_SECTION" and self.selector.finish_key is None):
            raise ValueError("Seção neutra exige política explícita; croqui não aceita fallback de cor.")
        return self


class ProductionImageManifest(OPModel):
    """Private import manifest for exactly one company."""
    schema_version: Literal["OP_IMAGES_0.1.0"] = "OP_IMAGES_0.1.0"
    company_id: UUID
    source_workbook_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    entries: tuple[StoredProductionImage, ...] = ()

    @model_validator(mode="after")
    def unique_selectors(self):
        if len({entry.selector.key() for entry in self.entries}) != len(self.entries):
            raise ValueError("Identidade de imagem duplicada.")
        return self


class LayoutImage(OPModel):
    """Renderer-ready reference; no absolute/local source path is exposed."""
    selector: ImageSelector | None
    status: Literal["VERIFIED", "MISSING_ASSET", "MISSING_TECHNICAL_DATA", "INVALID_ASSET"]
    relative_path: str | None = None
    sha256: str | None = None
    media_type: str | None = None
    width_px: int | None = None
    height_px: int | None = None
    finish_policy: str | None = None


def image_metadata(data: bytes) -> tuple[str, int, int]:
    """Decode/verify a bounded raster; SVG, files disguised as JPEG and bombs fail."""
    if not data or len(data) > 20_000_000:
        raise ValueError("Arquivo de imagem vazio ou acima do limite.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as img:
                if img.format not in {"JPEG", "PNG", "WEBP"} or img.width * img.height > 25_000_000:
                    raise ValueError("Formato/dimensões de imagem não suportados.")
                media = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}[img.format]
                size = img.size
                img.verify()
            with Image.open(BytesIO(data)) as img:
                img.load()
        return media, size[0], size[1]
    except (OSError, SyntaxError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError("Imagem inválida.") from exc


class ProductionImageStore:
    """Server-owned private root; files are checked again on every resolution."""
    def __init__(self, root: Path, manifest: ProductionImageManifest):
        self.root = root.resolve(strict=True)
        self.manifest = manifest

    def read_verified(self, entry: StoredProductionImage) -> bytes:
        """Check containment, bytes, digest, format and size before returning bytes."""
        path = (self.root / entry.relative_path).resolve(strict=True)
        if not path.is_relative_to(self.root) or not path.is_file():
            raise ValueError("Imagem fora do armazenamento privado.")
        if path.stat().st_size > 20_000_000:
            raise ValueError("Imagem acima do limite.")
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != entry.sha256:
            raise ValueError("Hash da imagem diverge do manifest.")
        if image_metadata(data) != (entry.media_type, entry.width_px, entry.height_px):
            raise ValueError("Metadados da imagem divergentes.")
        return data

    def resolve(self, selector: ImageSelector, company_id: UUID) -> LayoutImage:
        """Match exact identity; only explicitly neutral profile sections may fallback."""
        if company_id != self.manifest.company_id:
            raise ValueError("Manifest de imagens pertence a outra empresa.")
        entry = next((e for e in self.manifest.entries if e.selector == selector), None)
        if entry is None and selector.kind == "PROFILE_SECTION":
            neutral = ImageSelector(kind="PROFILE_SECTION", code=selector.code)
            entry = next((e for e in self.manifest.entries if e.selector == neutral and e.finish_policy == "NEUTRAL_LEGACY_SECTION"), None)
        if entry is None:
            return LayoutImage(selector=selector, status="MISSING_ASSET")
        try:
            self.read_verified(entry)
        except (ValueError, OSError):
            return LayoutImage(selector=selector, status="INVALID_ASSET")
        return LayoutImage(selector=selector, status="VERIFIED", **entry.model_dump(exclude={"selector"}))


def import_legacy_images(
    legacy_root: Path, output_root: Path, company_id: UUID,
    source_workbook_sha256: str, model_bindings: tuple[tuple[ImageSelector, str], ...],
    profile_codes: tuple[str, ...],
) -> tuple[ProductionImageManifest, tuple[str, ...]]:
    """Copy only explicitly selected originals into an ignored private root.

    Models bind exact technical basenames; profiles use code.jpg, as OP1 does.
    Unknown/missing files are listed, never substituted. Copies preserve bytes.
    """
    source = legacy_root.resolve(strict=True)
    output = output_root.resolve()
    repo = Path(__file__).resolve().parents[2]
    # Prevent accidental public imports; outside-repo roots are also permitted.
    if output.is_relative_to(repo) and not output.is_relative_to(repo / ".private"):
        raise ValueError("Importação no repositório exige raiz .private ignorada pelo Git.")
    if output.is_relative_to(source):
        raise ValueError("Destino não pode alterar a biblioteca de origem.")
    output.mkdir(parents=True, exist_ok=True)
    entries, missing = [], []
    bindings = [(selector, "CROQUIS", name, "EXACT") for selector, name in model_bindings]
    bindings += [(ImageSelector(kind="PROFILE_SECTION", code=code), "CROQUIS_PERFIS", code + ".jpg", "NEUTRAL_LEGACY_SECTION") for code in profile_codes]
    seen = set()
    for selector, folder, basename, policy in bindings:
        if selector.key() in seen:
            continue
        seen.add(selector.key())
        if not basename or any(c in basename for c in "\\/:") or PureWindowsPath(basename).drive or basename in {".", "..", "0.jpg"}:
            raise ValueError("Nome de origem não é um identificador técnico seguro.")
        matches = [p for p in (source / folder).iterdir() if p.name.casefold() == basename.casefold()] if (source / folder).is_dir() else []
        if len(matches) != 1:
            missing.append(selector.key())
            continue
        path = matches[0].resolve(strict=True)
        if not path.is_relative_to(source) or not path.is_file():
            raise ValueError("Origem da imagem fora da biblioteca autorizada.")
        if path.stat().st_size > 20_000_000:
            raise ValueError("Imagem acima do limite.")
        data = path.read_bytes()
        media, width, height = image_metadata(data)
        digest = hashlib.sha256(data).hexdigest()
        suffix = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[media]
        relative = f"objects/{digest}{suffix}"
        destination = output / relative
        destination.parent.mkdir(exist_ok=True)
        if not destination.resolve().is_relative_to(output):
            raise ValueError("Destino de objeto fora do armazenamento privado.")
        if destination.exists() and destination.read_bytes() != data:
            raise ValueError("Objeto existente não corresponde ao hash.")
        destination.write_bytes(data)
        entries.append(StoredProductionImage(selector=selector, relative_path=relative, sha256=digest,
                                             media_type=media, width_px=width, height_px=height, finish_policy=policy))
    return ProductionImageManifest(company_id=company_id, source_workbook_sha256=source_workbook_sha256,
                                   entries=tuple(entries)), tuple(missing)
