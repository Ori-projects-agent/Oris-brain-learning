"""
Headless Blender runner for Ori's Modeling Workshop.

Takes a Blender Python (bpy) script written by the LLM, statically checks it for
unsafe constructs, runs it in `blender --background`, and returns the exported
.glb, a preview render (.png) and geometry statistics (.json).
"""

import ast
import json
import logging
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Tuple

from config.settings import settings

logger = logging.getLogger("Ori.BlenderRunner")

ALLOWED_IMPORTS = {"bpy", "bmesh", "math", "random", "mathutils", "colorsys"}
FORBIDDEN_CALLS = {"exec", "eval", "compile", "open", "__import__", "input", "breakpoint", "exit", "quit"}
FORBIDDEN_OPS_PREFIXES = (
    "bpy.ops.wm", "bpy.ops.script", "bpy.ops.preferences", "bpy.ops.import_scene",
    "bpy.ops.export_scene", "bpy.ops.render", "bpy.ops.file", "bpy.ops.screen",
)

WRAPPER_TEMPLATE = r'''
import bpy, sys, os, json, math, traceback

_args = sys.argv[sys.argv.index("--") + 1:]
_user_script, _glb_path, _png_path, _json_path = _args[:4]
_stats = {"mesh_objects": 0, "vertices": 0, "faces": 0, "materials": 0,
          "modifiers": 0, "bevels": 0, "smooth_faces": 0,
          "bbox": [0, 0, 0], "render_ok": False, "error": None}

def _write_stats():
    with open(_json_path, "w", encoding="utf-8") as f:
        json.dump(_stats, f)

def _finish():
    import mathutils
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("Script created no mesh objects")
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mins = [1e9] * 3
    maxs = [-1e9] * 3
    mats = set()
    for o in meshes:
        ev = o.evaluated_get(depsgraph)
        me = ev.to_mesh()
        _stats["vertices"] += len(me.vertices)
        _stats["faces"] += len(me.polygons)
        _stats["smooth_faces"] += sum(1 for p in me.polygons if p.use_smooth)
        ev.to_mesh_clear()
        _stats["modifiers"] += len(o.modifiers)
        _stats["bevels"] += sum(1 for m in o.modifiers if m.type == "BEVEL")
        for m in o.data.materials:
            if m:
                mats.add(m.name)
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            for i in range(3):
                mins[i] = min(mins[i], w[i])
                maxs[i] = max(maxs[i], w[i])
    _stats["mesh_objects"] = len(meshes)
    _stats["materials"] = len(mats)
    _stats["bbox"] = [round(maxs[i] - mins[i], 4) for i in range(3)]
    center = mathutils.Vector([(mins[i] + maxs[i]) / 2 for i in range(3)])
    size = max(_stats["bbox"]) or 1.0

    bpy.ops.export_scene.gltf(filepath=_glb_path, export_format="GLB", export_apply=True)

    try:
        scene = bpy.context.scene
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        scene.render.resolution_x = 640
        scene.render.resolution_y = 640
        scene.render.filepath = _png_path
        scene.render.image_settings.file_format = "PNG"
        scene.world = bpy.data.worlds.new("OriWorld")
        scene.world.color = (0.05, 0.07, 0.12)
        cam_data = bpy.data.cameras.new("OriCam")
        cam = bpy.data.objects.new("OriCam", cam_data)
        scene.collection.objects.link(cam)
        cam.location = center + mathutils.Vector((size * 1.6, -size * 1.9, size * 1.1))
        target = bpy.data.objects.new("OriTarget", None)
        target.location = center
        scene.collection.objects.link(target)
        track = cam.constraints.new(type="TRACK_TO")
        track.target = target
        track.track_axis = "TRACK_NEGATIVE_Z"
        track.up_axis = "UP_Y"
        scene.camera = cam
        bpy.ops.render.render(write_still=True)
        _stats["render_ok"] = os.path.exists(_png_path)
    except Exception as render_err:
        _stats["render_error"] = str(render_err)

try:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with open(_user_script, "r", encoding="utf-8") as _f:
        _src = _f.read()
    exec(compile(_src, "ori_design.py", "exec"), {"__name__": "__main__"})
    _finish()
except Exception:
    _stats["error"] = traceback.format_exc()[-1500:]
_write_stats()
if _stats["error"]:
    sys.exit(1)
'''


def resolve_blender_exe() -> Path:
    raw = (settings.blender_path or "").strip().strip('"')
    if not raw:
        raise FileNotFoundError("BLENDER_PATH is not set in .env")
    p = Path(raw)
    if p.is_file():
        return p
    candidate = p / "blender.exe"
    if candidate.is_file():
        return candidate
    raise FileNotFoundError(f"blender.exe not found at '{raw}'. Set BLENDER_PATH in .env to the folder containing blender.exe.")


def scan_script(code: str) -> Tuple[bool, str]:
    """Static safety check of LLM-written Blender code."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, f"SyntaxError: {e}"

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] not in ALLOWED_IMPORTS:
                    return False, f"Import of '{alias.name}' is not allowed (allowed: {sorted(ALLOWED_IMPORTS)})"
        elif isinstance(node, ast.ImportFrom):
            if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS:
                return False, f"Import from '{node.module}' is not allowed (allowed: {sorted(ALLOWED_IMPORTS)})"
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
            return False, f"Call to '{node.func.id}()' is not allowed"
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                return False, f"Dunder attribute '{node.attr}' is not allowed"
            try:
                chain = ast.unparse(node)
            except Exception:
                chain = ""
            if chain.startswith(FORBIDDEN_OPS_PREFIXES):
                return False, f"Operator '{chain}' is not allowed"
    return True, "ok"


def run_blender_script(code: str, slug: str, out_dir: Path, timeout: int = 180) -> Dict[str, Any]:
    """Run a design script in headless Blender. Returns dict with ok, error, glb, png, stats."""
    ok, reason = scan_script(code)
    if not ok:
        return {"ok": False, "error": f"Rejected by safety scan: {reason}", "stats": {}}

    try:
        exe = resolve_blender_exe()
    except FileNotFoundError as e:
        return {"ok": False, "error": str(e), "stats": {}, "fatal": True}

    out_dir.mkdir(parents=True, exist_ok=True)
    glb_path = out_dir / f"{slug}.glb"
    png_path = out_dir / f"{slug}.png"

    with tempfile.TemporaryDirectory(prefix="ori_blender_") as tmp:
        tmp_dir = Path(tmp)
        user_file = tmp_dir / "design.py"
        wrapper_file = tmp_dir / "wrapper.py"
        json_file = tmp_dir / "stats.json"
        user_file.write_text(code, encoding="utf-8")
        wrapper_file.write_text(WRAPPER_TEMPLATE, encoding="utf-8")

        cmd = [
            str(exe), "--background", "--factory-startup",
            "--python", str(wrapper_file),
            "--", str(user_file), str(glb_path), str(png_path), str(json_file),
        ]
        logger.info(f"Running Blender for '{slug}'...")
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(tmp_dir))
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"Blender timed out after {timeout}s (script too heavy or stuck in a loop)", "stats": {}}
        except Exception as e:
            return {"ok": False, "error": f"Could not launch Blender: {e}", "stats": {}, "fatal": True}

        stats: Dict[str, Any] = {}
        if json_file.exists():
            try:
                stats = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception:
                stats = {}

        err = stats.get("error")
        if not err and proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "Blender exited with an error")[-1200:]
        if not err and not glb_path.exists():
            err = "Blender finished but no .glb was exported"

        return {
            "ok": err is None,
            "error": err,
            "glb": str(glb_path) if glb_path.exists() else "",
            "png": str(png_path) if png_path.exists() else "",
            "stats": stats,
        }
