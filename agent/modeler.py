"""
Ori's Modeling Workshop brain.

Design loop:  concept -> LLM writes bpy script -> headless Blender builds it ->
stats/preview -> critique + score -> stored as a versioned model.
Revise loop:  previous script + critique (+ lessons from his best past work) -> improved script.
"""

import logging
import re
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

from agent.llm_client import LLMClient
from config.settings import settings, BASE_DIR
from memory.sqlite_store import MemoryStore
from services.blender_runner import run_blender_script

logger = logging.getLogger("Ori.Modeler")

OUTPUT_DIR = BASE_DIR / "web" / "generated_models"
MAX_ATTEMPTS = 3
TARGET_QUALITY_SCORE = 8.5
MAX_AUTO_REVISIONS = 3

CODER_SYSTEM = """You are Ori's 3D modeling hands: an expert Blender 4.5 Python (bpy) programmer.
Write ONE complete, self-contained script that builds the requested object procedurally.

HARD RULES:
- Output ONLY Python code inside a single ```python block. No explanations.
- Allowed imports ONLY: bpy, bmesh, math, random, mathutils, colorsys. No os/sys/open/exec/eval.
- Do NOT call bpy.ops.wm / export / import / render. Do NOT set up cameras, lights, or export: the harness does that.
- The scene is already empty. Build everything with bpy.ops.mesh.primitive_* and/or bmesh, then move/scale/rotate.
- Model should sit with its base near Z=0, be centered on X/Y, and be roughly 0.2 to 2 meters in size.
- Use several distinct parts (aim for 5+ mesh objects) so it looks designed, not a single blob.
- Add polish: Bevel modifiers (bpy.ops.object.modifier_add(type='BEVEL')), bpy.ops.object.shade_smooth(), and sensible proportions.
- Give EVERY part a material built with nodes: mat.use_nodes = True; bsdf = mat.node_tree.nodes["Principled BSDF"];
  set bsdf.inputs["Base Color"].default_value = (r,g,b,1), ["Metallic"], ["Roughness"]. Use brass/titanium/dark-steel/cyan-glow palettes for Ori's style.
- Blender 4.x API notes: no mesh.use_auto_smooth; Principled input is "Specular IOR Level" not "Specular"; "Emission Color"/"Emission Strength" for glow.
- Use bpy.context.active_object right after creating a primitive; always apply modifiers via bpy.ops.object.modifier_apply only if needed.
- Name objects meaningfully (obj.name = "...")."""


GENERIC_NAMES = {
    "", "untitled", "untitled gadget", "untitled model", "untitled project",
    "new model", "3d model", "model", "object", "gadget", "device", "design", "thing",
}
STOP_WORDS = {"a", "an", "the", "of", "for", "with", "and", "to", "in", "on", "build", "create", "design", "make", "3d", "model"}


class Modeler:
    def __init__(self, memory: MemoryStore):
        self.memory = memory
        self.llm = LLMClient()
        self.lock = threading.Lock()
        self.busy = False
        self.status = "idle"

    # ---------- helpers ----------

    @staticmethod
    def _is_generic_name(name: str) -> bool:
        cleaned = re.sub(r"[^a-z0-9 ]+", "", (name or "").lower()).strip()
        return cleaned in GENERIC_NAMES or cleaned.startswith("untitled")

    @staticmethod
    def _fallback_name_from_concept(concept: str) -> str:
        words = [w for w in re.findall(r"[A-Za-z0-9-]+", concept or "") if w.lower() not in STOP_WORDS]
        picked = words[:5] if words else ["Solarium", "Prototype"]
        return " ".join(w.capitalize() for w in picked)[:48].strip()

    def _generate_project_name(self, concept: str) -> str:
        existing = [m["name"] for m in self.memory.get_models(limit=15) if m.get("name")]
        avoid = f"\nAvoid reusing these existing names: {', '.join(existing)}" if existing else ""
        prompt = (
            "Invent ONE crisp, evocative 2-to-5-word project title for Ori's Blender 3D creation.\n"
            "Return ONLY the title text. No quotes, no markdown, no trailing period, never use 'Untitled'.\n"
            f"Concept: {concept[:400]}{avoid}"
        )
        try:
            raw = self.llm.generate_text(
                "You name Ori's clockwork, storm-tech, botanical, and moto 3D creations with memorable workshop titles.",
                prompt,
                timeout=60,
                temperature=0.7,
            )
            candidate = raw.strip().splitlines()[0].strip().strip("\"'`*#:- ")
            if candidate and not self._is_generic_name(candidate) and len(candidate) <= 55:
                return candidate
        except Exception as e:
            logger.debug(f"Auto-naming fallback triggered: {e}")
        return self._fallback_name_from_concept(concept)

    @staticmethod
    def _slug(text: str) -> str:
        s = re.sub(r"[^a-z0-9]+", "_", (text or "model").lower()).strip("_")
        return (s[:32] or "model")

    @staticmethod
    def _extract_code(text: str) -> str:
        m = re.search(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
        if m:
            return m.group(1).strip()
        return text.strip().strip("`")

    @staticmethod
    def _score(stats: Dict[str, Any]) -> float:
        objs = stats.get("mesh_objects", 0)
        verts = stats.get("vertices", 0)
        mats = stats.get("materials", 0)
        mods = stats.get("modifiers", 0) + stats.get("bevels", 0)
        smooth = stats.get("smooth_faces", 0)
        bbox = stats.get("bbox", [0, 0, 0]) or [0, 0, 0]
        big = max(bbox)
        small = min(bbox)
        s = min(objs, 6) / 6 * 2.5
        s += 2.0 if 1200 <= verts <= 150000 else (1.2 if verts >= 400 else (0.5 if verts >= 100 else 0))
        s += min(mats, 4) / 4 * 2.0
        s += (0.9 if mods >= 2 else (0.45 if mods >= 1 else 0)) + (0.6 if smooth > 0 else 0)
        s += 1.0 if (0.15 <= big <= 4.0 and small >= 0.03) else (0.5 if 0.1 <= big <= 5.0 else 0)
        s += 1.0 if stats.get("render_ok") else 0
        return round(min(s, 10.0), 1)

    def _lessons_block(self) -> str:
        techs = self.memory.get_model_lessons(lesson_type="technique", limit=4)
        refs = self.memory.get_model_lessons(lesson_type="reference", limit=3)
        pitfalls = self.memory.get_model_lessons(lesson_type="pitfall", limit=4)
        fallback = self.memory.get_best_model_lessons(limit=2) if not techs else []
        parts = []
        if techs:
            parts.append("LEARNED BLENDER TECHNIQUES (apply these):\n" + "\n".join(f"- {t['lesson_text']}" for t in techs))
        elif fallback:
            parts.append("LESSONS FROM YOUR BEST PAST MODELS:\n" + "\n".join(f"- {l}" for l in fallback))
        if refs:
            parts.append("REFERENCE ARCHIVE 3D STUDIES (borrow proportions, multi-part counts & PBR palettes):\n" + "\n".join(f"- {r['lesson_text']}" for r in refs))
        if pitfalls:
            parts.append("AVOID THESE PAST PITFALLS:\n" + "\n".join(f"- {p['lesson_text']}" for p in pitfalls))
        return ("\n" + "\n".join(parts) + "\n") if parts else ""

    def _distill_lesson(self, lesson_type: str, context: str, model_id: int, score_impact: float):
        """Extract one reusable 1-sentence Blender/3D lesson so Ori improves across models."""
        prompt = (
            f"Lesson type: {lesson_type.upper()}\nContext:\n{context[:1800]}\n\n"
            "Write ONE concrete, reusable 1-sentence rule for writing better Blender 4.5 Python (bpy) models "
            "(either a technique that improved silhouette/materials/polish, or an exact API/geometry mistake to avoid)."
        )
        try:
            raw = self.llm.generate_text(
                "You distill concise, practical Blender 4.5 procedural modeling lessons.",
                prompt,
                timeout=90,
                temperature=0.3,
            )
            line = raw.strip().splitlines()[0].strip("- *\"'")
            if line:
                self.memory.add_model_lesson(lesson_type, line, source_model_id=model_id, score_impact=score_impact)
        except Exception as e:
            logger.debug(f"Lesson distillation skipped: {e}")

    def _critique(self, concept: str, stats: Dict[str, Any], code: str) -> str:
        prompt = (
            f"Concept: {concept}\nGeometry stats: {stats}\n\nScript:\n{code[:3500]}\n\n"
            "As a critical 3D art director, give EXACTLY 3 short, concrete improvements for the next revision "
            "(proportions, extra parts, bevels, materials, silhouette). One line each, starting with '- '."
        )
        try:
            return self.llm.generate_text(
                "You are a concise, constructive 3D art director.", prompt, timeout=240, temperature=0.4
            ).strip()
        except Exception as e:
            return f"- (critique unavailable: {e})"

    # ---------- core build loop ----------

    def _build(self, concept: str, name: str, version: int, parent_id: Optional[int],
               prior_script: str = "", prior_critique: str = "", focus: str = "") -> Dict[str, Any]:
        slug = f"{self._slug(name)}_v{version}_{int(time.time())}"
        user_prompt = f"Design this object: {concept}\n"
        user_prompt += self._lessons_block()
        if prior_script:
            user_prompt += (
                f"\nThis is REVISION v{version}. Improve the previous script below. "
                f"Fix the critique and add polish; keep what works.\n"
                f"Critique to address:\n{prior_critique}\n"
                f"Extra focus: {focus or 'overall polish and detail'}\n\n"
                f"PREVIOUS SCRIPT:\n```python\n{prior_script[:6000]}\n```\n"
            )

        last_error = ""
        code = ""
        result: Dict[str, Any] = {}
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.status = f"Writing script for '{name}' v{version} (attempt {attempt}/{MAX_ATTEMPTS})..."
            prompt = user_prompt
            if last_error:
                prompt += (
                    f"\nYour previous attempt FAILED with this error. Fix it and return the full corrected script:\n"
                    f"{last_error}\n\nFAILED SCRIPT:\n```python\n{code[:5000]}\n```\n"
                )
            try:
                raw = self.llm.generate_text(CODER_SYSTEM, prompt, model=settings.ollama_code_model, timeout=480)
            except Exception as e:
                last_error = f"LLM error: {e}"
                result = {"ok": False, "error": last_error, "stats": {}, "fatal": True}
                break

            code = self._extract_code(raw)
            self.status = f"Building '{name}' v{version} in Blender (attempt {attempt}/{MAX_ATTEMPTS})..."
            result = run_blender_script(code, slug, OUTPUT_DIR)
            if result["ok"]:
                break
            last_error = result.get("error", "unknown error")
            logger.warning(f"Model build attempt {attempt} failed: {last_error[:200]}")
            if result.get("fatal"):
                break

        if result.get("ok"):
            stats = result["stats"]
            score = self._score(stats)
            self.status = f"Critiquing '{name}' v{version}..."
            critique = self._critique(concept, stats, code)
            rel_glb = f"/generated_models/{Path(result['glb']).name}"
            rel_png = f"/generated_models/{Path(result['png']).name}" if result.get("png") else ""
            model_id = self.memory.add_model(
                name=name, version=version, parent_id=parent_id, concept=concept, script=code,
                glb_path=rel_glb, preview_path=rel_png, stats=stats, critique=critique,
                score=score, status="built", error=""
            )
            if score >= TARGET_QUALITY_SCORE or version >= 2:
                self._distill_lesson(
                    "technique",
                    f"Model '{name}' v{version} scored {score}/10 with stats={stats}. Critique={critique}\nScript snippet:\n{code[:1200]}",
                    model_id,
                    score,
                )
            return {"ok": True, "id": model_id, "name": name, "version": version, "score": score,
                    "stats": stats, "critique": critique, "script": code}

        model_id = self.memory.add_model(
            name=name, version=version, parent_id=parent_id, concept=concept, script=code,
            glb_path="", preview_path="", stats=result.get("stats", {}), critique="",
            score=0.0, status="failed", error=last_error[:1500]
        )
        self._distill_lesson("pitfall", f"Build '{name}' v{version} failed with error:\n{last_error[:800]}", model_id, 1.0)
        return {"ok": False, "id": model_id, "name": name, "version": version, "error": last_error}

    # ---------- public API ----------

    def design(self, concept: str, name: str = "", target_score: float = TARGET_QUALITY_SCORE,
               max_revisions: int = MAX_AUTO_REVISIONS) -> Dict[str, Any]:
        """Build v1 and automatically polish/revise until hitting target_score or max_revisions."""
        with self.lock:
            self.busy = True
            try:
                clean_name = (name or "").strip()
                if self._is_generic_name(clean_name):
                    self.status = "Naming new 3D project..."
                    clean_name = self._generate_project_name(concept)
                res = self._build(concept, clean_name, 1, None)
                best = res
                rev = 0
                while res.get("ok") and res.get("score", 0) < target_score and rev < max_revisions:
                    rev += 1
                    self.status = f"Auto-polishing '{clean_name}' → v{res['version'] + 1} (current {res['score']}/10, target {target_score})..."
                    next_res = self._build(
                        concept,
                        clean_name,
                        res["version"] + 1,
                        res["id"],
                        prior_script=res.get("script", ""),
                        prior_critique=res.get("critique", ""),
                        focus="Address all critique points, add bevels/smooth shading, extra sub-parts, and richer PBR material contrast",
                    )
                    if not next_res.get("ok"):
                        break
                    res = next_res
                    if res.get("score", 0) >= best.get("score", 0):
                        best = res
                return best if best.get("ok") else res
            finally:
                self.busy = False
                self.status = "idle"

    def revise(self, model_id: int, focus: str = "") -> Dict[str, Any]:
        parent = self.memory.get_model(model_id)
        if not parent:
            return {"ok": False, "error": f"No model with id {model_id}"}
        with self.lock:
            self.busy = True
            try:
                res = self._build(
                    parent["concept"], parent["name"], parent["version"] + 1, parent["id"],
                    prior_script=parent.get("script", ""),
                    prior_critique=parent.get("critique") or parent.get("error") or "",
                    focus=focus,
                )
            finally:
                self.busy = False
                self.status = "idle"
        return res
