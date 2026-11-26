"""
Archival Relic & 3D Reference Archive Service for Ori.
Scans dropped high-quality reference 3D models (including inside .zip packs and an optional
external archive folder/zip configured via RELIC_REFERENCE_ARCHIVE_DIR), saves individual
low-poly Blender build blueprints, and exports the infinitely expanding game-ready Custom Relic Library JSON.
Uses Python standard library only.
"""

import json
import logging
import re
import struct
import zipfile
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config.settings import BASE_DIR, settings

logger = logging.getLogger("Ori.RelicArchive")

SUPPORTED_MODEL_EXTS = {".glb", ".gltf", ".obj", ".fbx", ".blend", ".stl"}
ARCHIVE_DIR = BASE_DIR / "relic_archive"
REFERENCE_DIR = ARCHIVE_DIR / "reference_models"
BLUEPRINTS_DIR = ARCHIVE_DIR / "blender_blueprints"
LIBRARY_EXPORT_PATH = ARCHIVE_DIR / "custom_relic_library.json"


def _extract_tags_from_name(name: str) -> List[str]:
    """Derive clean lowercase keyword tags from a filename or archive path."""
    stem = Path(name).stem
    tokens = [tok.lower() for tok in re.split(r"[_\-\s\.]+", stem) if tok and len(tok) > 1]
    seen: List[str] = []
    for tok in tokens:
        if tok not in seen:
            seen.append(tok)
    return seen


def _scan_zip_models(zip_path: Path, rel_label: str) -> List[Dict[str, Any]]:
    """Inspect a .zip archive for supported 3D models without extracting it."""
    entries: List[Dict[str, Any]] = []
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in sorted(zf.namelist()):
                if member.endswith("/") or member.startswith("__MACOSX/") or "/__MACOSX/" in member:
                    continue
                m_ext = Path(member).suffix.lower()
                if m_ext not in SUPPORTED_MODEL_EXTS:
                    continue
                try:
                    size_kb = round(zf.getinfo(member).file_size / 1024.0, 2)
                except (KeyError, OSError):
                    size_kb = 0.0
                fname = Path(member).name
                entries.append({
                    "filename": fname,
                    "relative_path": f"{rel_label}::{member}",
                    "format": m_ext.lstrip("."),
                    "size_kb": size_kb,
                    "archive_container": rel_label,
                    "inferred_tags": _extract_tags_from_name(fname),
                })
    except (zipfile.BadZipFile, OSError) as e:
        logger.warning(f"Skipping unreadable archive {rel_label}: {e}")
    return entries


def _scan_directory(root_dir: Path, prefix: str = "") -> List[Dict[str, Any]]:
    """Recursively scan a directory for supported 3D models and .zip asset packs."""
    found: List[Dict[str, Any]] = []
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file() or path.name in (".gitkeep", "manifest.json"):
            continue
        ext = path.suffix.lower()
        rel = path.relative_to(root_dir).as_posix()
        label = f"{prefix}{rel}"
        if ext in SUPPORTED_MODEL_EXTS:
            try:
                size_kb = round(path.stat().st_size / 1024.0, 2)
            except OSError:
                size_kb = 0.0
            found.append({
                "filename": path.name,
                "relative_path": label,
                "format": ext.lstrip("."),
                "size_kb": size_kb,
                "archive_container": None,
                "inferred_tags": _extract_tags_from_name(path.name),
            })
        elif ext == ".zip":
            found.extend(_scan_zip_models(path, label))
    return found


class RelicArchiveService:
    """Manages reference 3D model discovery, blueprint export, and museum library sync."""

    def __init__(self):
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
        BLUEPRINTS_DIR.mkdir(parents=True, exist_ok=True)

    def scan_reference_models(self) -> List[Dict[str, Any]]:
        """
        Inspect `relic_archive/reference_models/` and any optional external folder/.zip
        set in `settings.relic_reference_archive_dir`, updating `manifest.json`.
        """
        REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
        models = _scan_directory(REFERENCE_DIR)

        ext_source = (getattr(settings, "relic_reference_archive_dir", "") or "").strip()
        resolved_ext_str = None
        if ext_source:
            ext_path = Path(ext_source).expanduser()
            if not ext_path.exists() and not ext_path.is_absolute():
                home_candidate = Path.home() / ext_path
                if home_candidate.exists():
                    ext_path = home_candidate
            if ext_path.exists():
                resolved_ext_str = str(ext_path)
                if ext_path.is_file() and ext_path.suffix.lower() == ".zip":
                    models.extend(_scan_zip_models(ext_path, f"external::{ext_path.name}"))
                elif ext_path.is_dir() and ext_path.resolve() != REFERENCE_DIR.resolve():
                    models.extend(_scan_directory(ext_path, prefix="external::"))

        manifest = {
            "scanned_at": datetime.datetime.now().isoformat(),
            "external_source": resolved_ext_str or ext_source or None,
            "count": len(models),
            "models": models,
        }
        try:
            with open(REFERENCE_DIR / "manifest.json", "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        except OSError as e:
            logger.warning(f"Could not write reference manifest: {e}")

        return models

    def save_relic_blueprint(self, relic: Dict[str, Any]) -> str:
        """Save an individual JSON low-poly Blender build blueprint for a cataloged relic."""
        BLUEPRINTS_DIR.mkdir(parents=True, exist_ok=True)
        accession = str(relic.get("accession_code") or f"ARC-{relic.get('id', 0):04d}")
        raw_name = str(relic.get("name") or "custom_relic")
        slug = re.sub(r"[^a-z0-9]+", "_", raw_name.lower()).strip("_")[:40] or "relic"
        filename = f"{accession}_{slug}.json"
        target_path = BLUEPRINTS_DIR / filename

        payload = {
            "accession_code": accession,
            "name": relic.get("name", ""),
            "category": relic.get("category", ""),
            "era": relic.get("era", ""),
            "museum_wing": relic.get("museum_wing", ""),
            "rarity": relic.get("rarity", "Uncommon"),
            "curation_status": relic.get("curation_status", "Cataloged"),
            "research_level": relic.get("research_level", 1),
            "creation_mode": relic.get("creation_mode", "commissioned"),
            "verified_facts": relic.get("verified_facts", ""),
            "fact_sources": relic.get("fact_sources", []),
            "lore_description": relic.get("lore_description", ""),
            "study_notes": relic.get("study_notes", ""),
            "tags": relic.get("tags", []),
            "reference_model": relic.get("reference_model", "Original Concept"),
            "mesh_file": relic.get("mesh_file") or f"{accession}.glb",
            "lowpoly_spec": relic.get("lowpoly_spec", {}),
            "blender_workflow": relic.get("blender_workflow", ""),
            "exported_at": datetime.datetime.now().isoformat(),
        }
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return f"relic_archive/blender_blueprints/{filename}"

    def export_relic_library(
        self,
        relics: List[Dict[str, Any]],
        reference_models: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Export the complete Custom Relic Library JSON for museum collector game ingestion."""
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        refs = reference_models if reference_models is not None else self.scan_reference_models()
        payload = {
            "library_name": "Ori's Zenith Archival Relic Library",
            "exported_at": datetime.datetime.now().isoformat(),
            "total_relics": len(relics),
            "reference_models_available": len(refs),
            "relics": relics,
        }
        with open(LIBRARY_EXPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return "relic_archive/custom_relic_library.json"

    # ---------- Deep GLB/glTF Reference Inspection ----------

    def _resolve_model_location(self, relative_path: str) -> Optional[Dict[str, Any]]:
        """Resolve a manifest relative_path to a (Path, optional zip_member) tuple."""
        if "::" in relative_path:
            prefix, rest = relative_path.split("::", 1)
            if prefix == "external":
                ext_source = (getattr(settings, "relic_reference_archive_dir", "") or "").strip()
                if ext_source:
                    ext_path = Path(ext_source).expanduser()
                    if not ext_path.exists() and not ext_path.is_absolute():
                        home_candidate = Path.home() / ext_path
                        if home_candidate.exists():
                            ext_path = home_candidate
                    if ext_path.is_file() and ext_path.suffix.lower() == ".zip":
                        return {"path": ext_path, "zip_member": rest}
                    cand = ext_path / rest
                    if cand.is_file():
                        return {"path": cand, "zip_member": None}
            else:
                zpath = REFERENCE_DIR / prefix
                if zpath.is_file() and zpath.suffix.lower() == ".zip":
                    return {"path": zpath, "zip_member": rest}
        cand = REFERENCE_DIR / relative_path
        if cand.is_file():
            return {"path": cand, "zip_member": None}
        return None

    @staticmethod
    def _parse_gltf_json(gltf: Dict[str, Any]) -> Dict[str, Any]:
        meshes = gltf.get("meshes") or []
        nodes = gltf.get("nodes") or []
        accessors = gltf.get("accessors") or []
        materials = gltf.get("materials") or []

        part_names = [n.get("name") for n in nodes if n.get("name") and not n.get("name").startswith("Root")]
        if not part_names:
            part_names = [m.get("name") for m in meshes if m.get("name")]

        total_verts = 0
        total_tris = 0
        mins = [1e9, 1e9, 1e9]
        maxs = [-1e9, -1e9, -1e9]
        has_bounds = False

        for mesh in meshes:
            for prim in mesh.get("primitives") or []:
                attrs = prim.get("attributes") or {}
                pos_idx = attrs.get("POSITION")
                if isinstance(pos_idx, int) and 0 <= pos_idx < len(accessors):
                    acc = accessors[pos_idx]
                    total_verts += int(acc.get("count", 0))
                    mn, mx = acc.get("min"), acc.get("max")
                    if isinstance(mn, list) and isinstance(mx, list) and len(mn) == 3 and len(mx) == 3:
                        has_bounds = True
                        for i in range(3):
                            mins[i] = min(mins[i], float(mn[i]))
                            maxs[i] = max(maxs[i], float(mx[i]))
                idx_acc = prim.get("indices")
                if isinstance(idx_acc, int) and 0 <= idx_acc < len(accessors):
                    total_tris += int(accessors[idx_acc].get("count", 0)) // 3
                elif isinstance(pos_idx, int) and 0 <= pos_idx < len(accessors):
                    total_tris += int(accessors[pos_idx].get("count", 0)) // 3

        mat_summaries = []
        for mat in materials[:6]:
            pbr = mat.get("pbrMetallicRoughness") or {}
            textures = []
            if pbr.get("baseColorTexture"):
                textures.append("baseColor")
            if pbr.get("metallicRoughnessTexture"):
                textures.append("metalRough")
            if mat.get("normalTexture"):
                textures.append("normal")
            if mat.get("emissiveTexture"):
                textures.append("emissive")
            mat_summaries.append({
                "name": mat.get("name") or "Material",
                "metallic": round(float(pbr.get("metallicFactor", 1.0)), 2),
                "roughness": round(float(pbr.get("roughnessFactor", 1.0)), 2),
                "base_color": [round(float(c), 2) for c in (pbr.get("baseColorFactor") or [1, 1, 1, 1])[:3]],
                "emissive": [round(float(c), 2) for c in (mat.get("emissiveFactor") or [0, 0, 0])[:3]],
                "textures": textures,
            })

        bbox = [round(maxs[i] - mins[i], 3) for i in range(3)] if has_bounds else []
        return {
            "mesh_count": len(meshes),
            "node_count": len(nodes),
            "part_names": part_names[:8],
            "vertex_count": total_verts,
            "triangle_count": total_tris,
            "bbox": bbox,
            "material_count": len(materials),
            "materials": mat_summaries,
        }

    def inspect_model_details(self, relative_path: str) -> Dict[str, Any]:
        """Inspect geometry, proportions, and PBR materials from a .glb/.gltf reference model."""
        loc = self._resolve_model_location(relative_path)
        if not loc:
            return {"error": f"Reference file not found: {relative_path}"}
        fpath: Path = loc["path"]
        zmem: Optional[str] = loc["zip_member"]
        ext = Path(zmem or fpath.name).suffix.lower()
        if ext not in (".glb", ".gltf"):
            return {"note": f"Header inspection is supported for .glb/.gltf (file is {ext})"}

        try:
            if zmem:
                with zipfile.ZipFile(fpath, "r") as zf:
                    with zf.open(zmem) as f:
                        if ext == ".gltf":
                            gltf = json.loads(f.read(512 * 1024).decode("utf-8"))
                        else:
                            hdr = f.read(20)
                            if len(hdr) < 20 or hdr[:4] != b"glTF":
                                return {"error": "Invalid GLB header"}
                            json_len, chunk_type = struct.unpack("<II", hdr[12:20])
                            if chunk_type != 0x4E4F534A:
                                return {"error": "Missing GLB JSON chunk"}
                            gltf = json.loads(f.read(json_len).decode("utf-8"))
            else:
                with open(fpath, "rb") as f:
                    if ext == ".gltf":
                        gltf = json.loads(f.read(512 * 1024).decode("utf-8"))
                    else:
                        hdr = f.read(20)
                        if len(hdr) < 20 or hdr[:4] != b"glTF":
                            return {"error": "Invalid GLB header"}
                        json_len, chunk_type = struct.unpack("<II", hdr[12:20])
                        if chunk_type != 0x4E4F534A:
                            return {"error": "Missing GLB JSON chunk"}
                        gltf = json.loads(f.read(json_len).decode("utf-8"))
            return self._parse_gltf_json(gltf)
        except Exception as e:
            return {"error": f"Could not inspect {relative_path}: {e}"}

    def format_study_summary(self, entry: Dict[str, Any], info: Dict[str, Any]) -> Dict[str, str]:
        """Turn inspected GLB stats into a concise Blender lesson and a detailed research note."""
        fname = entry.get("filename") or entry.get("relative_path")
        tags = ", ".join(entry.get("inferred_tags") or [])
        if info.get("error") or info.get("note"):
            detail = info.get("error") or info.get("note")
            lesson = f"Ref '{fname}' ({entry.get('format', '?').upper()}, tags: {tags}): {detail}"
            return {"lesson": lesson, "note": lesson}

        bbox = info.get("bbox") or []
        bbox_str = f"{bbox[0]}x{bbox[1]}x{bbox[2]}m" if len(bbox) == 3 else "unbounded"
        mats_desc = []
        for m in (info.get("materials") or [])[:4]:
            tex = f" [{'+'.join(m['textures'])}]" if m.get("textures") else ""
            em = f", emissive={m['emissive']}" if any(v > 0 for v in (m.get("emissive") or [])) else ""
            mats_desc.append(f"{m['name']} (M={m['metallic']}, R={m['roughness']}{em}{tex})")
        mats_text = "; ".join(mats_desc) or "default material"
        parts_text = ", ".join(info.get("part_names") or []) or "unnamed sub-meshes"

        lesson = (
            f"Ref '{fname}': {info.get('mesh_count', 0)} meshes, {info.get('triangle_count', 0)} tris, "
            f"bbox {bbox_str}, {info.get('material_count', 0)} PBR mats ({mats_text[:110]})"
        )
        note = (
            f"Studied reference 3D model `{entry.get('relative_path')}` ({entry.get('size_kb', 0)} KB):\n"
            f"• Geometry: {info.get('mesh_count', 0)} mesh object(s), {info.get('vertex_count', 0):,} verts, "
            f"{info.get('triangle_count', 0):,} tris, bounding box {bbox_str}\n"
            f"• Named Parts: {parts_text}\n"
            f"• PBR Materials ({info.get('material_count', 0)}): {mats_text}\n"
            f"• Design Takeaway: Mirror its multi-part breakdown, {bbox_str} silhouette proportions, "
            f"and metallic/roughness contrast when writing Blender scripts."
        )
        return {"lesson": lesson, "note": note}


relic_archive = RelicArchiveService()
