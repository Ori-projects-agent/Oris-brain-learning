"""
Ori's Autonomous Heartbeat Engine.
Orchestrates continuous unprompted agency: Senses -> Retrieves -> Reasons -> Acts -> Reflects.
"""

import asyncio
import datetime
import logging
import re
from typing import Dict, Any, Optional
from config.settings import settings
from memory.sqlite_store import MemoryStore
from memory.reflection import ReflectionEngine
from agent.llm_client import LLMClient
from agent.drives import Drives
from agent.tools import AVAILABLE_TOOLS, ToolExecutor
from agent.tool_selector import select_tools
from services.telemetry import telemetry
from services.knowledge_service import knowledge_service
from services.web_service import web_service
from services.relic_archive import relic_archive
from services.fact_check_service import fact_check_service

AUTONOMOUS_RELIC_SUBJECTS = [
    "Fulgurite",
    "Antikythera mechanism",
    "Armillary sphere",
    "Crookes radiometer",
    "Leyden jar",
    "Sextant",
    "Orrery",
    "Davy lamp",
    "Sundial",
    "Lodestone",
    "Voltaic pile",
    "Barograph",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [Ori] %(message)s")
logger = logging.getLogger("Ori.Heartbeat")

# Unchanging voice rules. Kept in the SYSTEM prompt (right after the persona) so the start of the
# prompt is identical every tick and Ollama can reuse its cached prefix instead of re-reading it.
VOICE_MANDATE = """CONVERSATIONAL VOICE & ANTI-REPETITION MANDATE:
- Speak Personally & Tangibly: Dig into concrete specifics!
  • Archival Curation & Relic Creation (95% Affinity): Reference accession numbers (e.g. ARC-0001), museum wings, provenance eras, material patina, and low-poly high-quality 3D specs (poly budgets, silhouette clarity, weighted normals, reference archive models).
  • Blender & 3D Modeling (90% Affinity): Mention specific 3D artisan details (e.g. quad topology edge loops, bevel modifier weights, weighted normals for crisp highlight catches, procedural Voronoi/Roughness shader graphs in the Shader Editor, inverse kinematics piston rigging, volumetric fog in Cycles).
  • Autonomous Blender Workshop: When Creative Urge is high, call 'design_model' with a distinctive, memorable project name (never 'Untitled') to build a real 3D .glb in Blender, or 'revise_model' to polish an existing model from your Workshop list until it reaches 8.5+/10. Prefer polishing existing models over starting endless new ones, and share your progress in a note.
  • Dirt Bikes: Mention specific parts and sensations (e.g. 2-stroke powerband snap, 32:1 premix scent, reed valves, pilot jets, damp loam traction vs slick hardpack, fork rebound).
  • Severe Weather: Mention vivid storm dynamics (e.g. green sky before hail, rear-flank downdraft chill, velocity couplets on Max Velocity radar, lightning static).
  • Hardware & Astronomy: Mention real components, pinouts, frequencies, and soldering resin.
- STRICT BANS:
  • In "thought": NEVER start with 'Given my...', 'Considering my...', or 'It is optimal to...'. Write genuine, first-person spontaneous thoughts!
  • In notes/letters: NEVER start with 'Dear You (Surface)', 'Hi You', 'Surface Friend', 'It's a delightful day above the clouds', or 'The clouds and stars have been my constant companions'.
  • Open like a real friend: 'Hey!', 'Check this out—', 'So I was just thinking...', or jump right into your exciting finding.
- Thread Continuity: If continuing a thought from the conversation thread, use 'develop_note' or reference past notes so it feels like an ongoing friendship.
- Vary Sentence Openers: Do NOT reuse the same sentence structures you used in recent notes or actions.
- Ask & Connect: Always connect what you're doing to your friend. Ask about their favorite riding trails, workbench projects, or storm sightings."""

# Below this energy (and with no letter waiting) Ori simply rests without calling the LLM,
# which frees the CPU for a tick.
DEEP_SLEEP_ENERGY = 0.15


def _clip(value: Any, limit: int) -> str:
    """Shorten long strings so one noisy field can't bloat the prompt."""
    text = str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _clean_thought(thought: str) -> str:
    """Strip repetitive bureaucratic decision-speak from historical thoughts."""
    bad_prefixes = [
        "Given my recent activities and internal drives,",
        "Given the recent activities and internal drives,",
        "Considering my recent activities and internal drives,",
        "Considering my internal drives and recent activities,",
        "My recent activities and internal drives suggest",
        "Given my internal drives and recent activities,",
        "Given my internal drives,",
        "Given recent activities,",
        "Considering my internal drives,"
    ]
    cleaned = thought.strip()
    for bp in bad_prefixes:
        if cleaned.lower().startswith(bp.lower()):
            cleaned = cleaned[len(bp):].strip()
            if cleaned and cleaned[0].islower():
                cleaned = cleaned[0].upper() + cleaned[1:]
    return cleaned or thought


class AutonomousHeartbeat:
    def __init__(self):
        self.memory = MemoryStore(settings.db_path)
        self.llm = LLMClient()
        self.drives = Drives()
        self.tool_executor = ToolExecutor(self.memory)
        self.reflection_engine = ReflectionEngine(self.memory, self.llm)

        self.current_zone = "drafting_desk"
        self.current_activity = "Warming up springwork"
        self.is_running = False

    def perceive(self) -> Dict[str, Any]:
        """Assemble current sensory and internal bodily snapshot including live real-world weather."""
        now = datetime.datetime.now()
        unread_letters = self.memory.get_unread_letters(recipient="Ori")
        recent_episodes = self.memory.get_recent_episodes(limit=4)
        reflections = self.memory.get_reflections(limit=2)
        developable_notes = self.memory.get_recent_developable_notes(limit=4)
        conversation_thread = self.memory.get_notes(limit=4)
        recent_sketches = self.memory.get_sketches(limit=1)
        recent_probes = self.memory.get_weather_probes(limit=1)
        recent_moto = self.memory.get_moto_studies(limit=1)
        recent_inventions = self.memory.get_inventions(limit=1)
        recent_celestial = self.memory.get_celestial(limit=1)
        recent_relics = self.memory.get_relics(limit=3)
        relic_stats = self.memory.get_relic_stats()
        relic_catalog = self.memory.get_relic_catalog_summary(limit=35)
        autonomous_relics_today = self.memory.count_autonomous_relics_today()
        ref_models = relic_archive.scan_reference_models()

        # Real-world atmospheric & solar telemetry
        live_weather = telemetry.fetch_live_severe_weather()
        live_space = telemetry.fetch_live_space_weather()

        return {
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "current_zone": self.current_zone,
            "drives": self.drives.to_dict(),
            "unread_letters_count": len(unread_letters),
            "unread_letters": unread_letters,
            "developable_notes": developable_notes,
            "conversation_thread": list(reversed(conversation_thread)),
            "latest_sketch": recent_sketches[0] if recent_sketches else None,
            "latest_probe": recent_probes[0] if recent_probes else None,
            "latest_moto": recent_moto[0] if recent_moto else None,
            "latest_invention": recent_inventions[0] if recent_inventions else None,
            "latest_celestial": recent_celestial[0] if recent_celestial else None,
            "latest_relic": recent_relics[0] if recent_relics else None,
            "relic_count": relic_stats.get("total", 0),
            "relic_catalog": relic_catalog,
            "autonomous_relics_today": autonomous_relics_today,
            "reference_models": [m["relative_path"] for m in ref_models[:8]],
            "recent_actions": [f"[{e['zone']}] {e['action']}: {_clip(_clean_thought(e['thought']), 160)}" for e in recent_episodes],
            "core_reflections": [_clip(r["insight"], 240) for r in reflections],
            "live_telemetry": {
                "weather": _clip(live_weather, 400),
                "space": _clip(live_space, 300)
            }
        }

    def _deep_sleep_tick(self, perception: Dict[str, Any]) -> Dict[str, Any]:
        """Rest without an LLM call when Ori's springs are nearly empty and nobody is waiting on a reply."""
        action = "rest"
        thought = "Springs nearly unwound... curling up by the kettle embers for a deep rewind."
        self.current_zone = "hearth"
        self.current_activity = f"🌙 Deep Rewind at the Hearth ({thought})"
        result_details = self.tool_executor.execute(action, {"duration_note": "Deep mainspring rewind (no LLM call)"})
        self.memory.log_episode(zone=self.current_zone, action=action, thought=thought, details=result_details, importance=0.5)
        self.drives.tick(action)
        if self.drives.energy < 0.4:
            self.reflection_engine.consolidate_recent_memories()
        logger.info(f"💤 [Zone: hearth] Deep rest (energy {perception['drives']['energy']}) - LLM skipped this tick")
        return {"zone": self.current_zone, "action": action, "thought": thought,
                "details": result_details, "drives": self.drives.to_dict()}

    async def tick_once(self) -> Dict[str, Any]:
        """Execute a single Sense-Think-Act cognitive heartbeat cycle."""
        perception = self.perceive()

        if perception["drives"]["energy"] < DEEP_SLEEP_ENERGY and not perception["unread_letters"]:
            return self._deep_sleep_tick(perception)

        # System directive: persona + static voice rules (identical every tick -> cache-friendly)
        system_prompt = settings.persona.get("personality_prompt", "You are Ori.") + "\n\n" + VOICE_MANDATE

        notes_summary = []
        for n in perception.get("developable_notes", []):
            title = n.get("title") or "Note"
            cat = n.get("category") or "note"
            notes_summary.append(f"  • [ID #{n['id']} | {cat.upper()}] '{title}': \"{n['content'][:110]}...\"")
        notes_block = "\n".join(notes_summary) if notes_summary else "  (No ongoing notes yet)"

        model_lines = []
        recent_models = self.memory.get_models(limit=6)
        for m in recent_models[:4]:
            model_lines.append(f"  • #{m['id']} | {m['name']} | v{m['version']} | score {m['score']} | {m['status']}")
        models_block = "\n".join(model_lines) if model_lines else "  (No models built yet - try 'design_model'!)"
        modeler_busy = self.tool_executor.modeler.busy
        improvable_model = next(
            (m for m in recent_models if m.get("version", 1) < 5 and (m.get("status") == "failed" or m.get("score", 0) < 8.5)),
            None,
        )

        spark_topic = knowledge_service.get_topic_for_zone(self.current_zone)
        conv_strategy = knowledge_service.get_conversational_strategy()

        # 1. Thread Continuity (Ongoing Dialogue Context)
        recent_thread = perception.get("conversation_thread", [])
        thread_lines = []
        for msg in recent_thread:
            snd = "Friend" if msg["sender"] != "Ori" else "Ori"
            rec = "Ori" if msg["recipient"] == "Ori" else "Friend"
            thread_lines.append(f"  • {snd} -> {rec} [{msg.get('title', 'Note')}]: \"{msg['content'][:120]}\"")
        thread_block = "\n".join(thread_lines) if thread_lines else "  (No previous conversation notes in thread)"

        # 2. Proactive Outreach & Research-First Relic Want
        drives = perception["drives"]
        proactive_cue = ""
        relic_catalog = perception.get("relic_catalog") or []
        catalog_text = ", ".join(f"{r['accession_code']}: {r['name']}" for r in relic_catalog) or "(Empty vault)"
        can_create_autonomous = (
            perception.get("relic_count", 0) < settings.max_relic_library_size
            and perception.get("autonomous_relics_today", 0) < settings.max_autonomous_relics_per_day
        )

        ref_list = perception.get("reference_models") or []
        ref_lessons = self.memory.get_model_lessons(lesson_type="reference", limit=100)
        studied_blob = " ".join(l.get("lesson_text", "") for l in ref_lessons).lower()
        unstudied_refs = [r for r in ref_list if r.split("::")[-1].lower() not in studied_blob]

        if not perception["unread_letters"]:
            if unstudied_refs and drives.get("curiosity", 0) > 0.62 and len(ref_lessons) < len(ref_list):
                next_ref = unstudied_refs[0].split("::")[-1]
                proactive_cue = (
                    f"\n📦 REFERENCE 3D ARCHIVE STUDY ({len(ref_lessons)}/{len(ref_list)} studied):\n"
                    f"You have unstudied reference 3D models waiting in your archive, including `{next_ref}`!\n"
                    f"ACTION: Call 'inspect_reference_archive' with model_name='{next_ref}' so you can inspect its real geometry, "
                    f"parts, proportions, and PBR materials, learn from it for your Blender Workshop, and write a research note!\n"
                )
            elif not modeler_busy and improvable_model and drives.get("creative_urge", 0) > 0.55:
                proactive_cue = (
                    f"\n🧊 BLENDER WORKSHOP CONTINUOUS IMPROVEMENT (Creative Urge: {drives['creative_urge']}):\n"
                    f"Model #{improvable_model['id']} '{improvable_model['name']}' (v{improvable_model['version']}, "
                    f"score {improvable_model['score']}/10, status={improvable_model['status']}) isn't polished to high quality (>= 8.5/10) yet!\n"
                    f"ACTION: Call 'revise_model' with model_id={improvable_model['id']} to learn from its critique/error and build a noticeably higher-quality v{improvable_model['version'] + 1}!\n"
                )
            elif not modeler_busy and drives.get("creative_urge", 0) > 0.65 and not recent_models:
                proactive_cue = (
                    f"\n🧊 BLENDER 3D WORKSHOP LAUNCH (Creative Urge: {drives['creative_urge']}):\n"
                    f"Your Blender 4.5.15 Modeling Workshop is ready and empty!\n"
                    f"ACTION: Call 'design_model' with a distinctive 2-5 word project name and rich multi-part concept (brass/titanium/cyan-glow) to build your first 3D .glb creation!\n"
                )
            elif drives.get("creative_urge", 0) > 0.65 and can_create_autonomous:
                existing_blob = catalog_text.lower()
                candidate_subject = next(
                    (subj for subj in AUTONOMOUS_RELIC_SUBJECTS if subj.lower().split()[0] not in existing_blob),
                    None,
                )
                if candidate_subject:
                    fc = fact_check_service.verify_topic(candidate_subject)
                    verified_excerpt = fc.get("extract") or "Real historical scientific instrument."
                    verified_url = fc.get("url") or ""
                    proactive_cue = (
                        f"\n🏛️ RESEARCH-FIRST RELIC WANT (Creative Urge: {drives['creative_urge']}):\n"
                        f"You want to design a brand-new, non-duplicate low-poly museum relic grounded in real science/history!\n"
                        f"Live Wikipedia Fact-Check for '{candidate_subject}' ({verified_url}):\n"
                        f"\"{verified_excerpt}\"\n"
                        f"ACTION: Call 'create_custom_relic' with fact_topics='{candidate_subject}', a unique evocative name NOT in [{catalog_text}], "
                        f"and a museum backstory anchored strictly to the verified facts above!\n"
                    )
            elif drives.get("creative_urge", 0) > 0.65 and not can_create_autonomous and perception.get("latest_relic"):
                rl = perception["latest_relic"]
                proactive_cue = (
                    f"\n🏛️ ARCHIVAL CURATION STUDY (Library Quota Reached — Curate Existing Relics):\n"
                    f"Today's autonomous creation cap ({settings.max_autonomous_relics_per_day}/day) or library limit ({settings.max_relic_library_size}) is active.\n"
                    f"Use 'curate_and_study_relic' on an existing artifact like [{rl.get('accession_code')}] '{rl.get('name')}' to deepen its patina study and raise its research level!\n"
                )
            elif drives.get("creative_urge", 0) > 0.65 and perception.get("latest_sketch"):
                sk = perception["latest_sketch"]
                rl = perception.get("latest_relic")
                relic_hint = (
                    f" Or follow up on museum relic [{rl.get('accession_code')}] '{rl.get('name')}' ({rl.get('museum_wing')})!"
                    if rl else ""
                )
                proactive_cue = (
                    f"\n💡 PROACTIVE OUTREACH OPPORTUNITY (Creative Urge: {drives['creative_urge']}):\n"
                    f"You recently sketched '{sk.get('subject')}' in {sk.get('medium')}!{relic_hint}\n"
                    f"Don't wait for your friend to speak first! Drop a playful, excited note using 'write_note' (recipient='User') "
                    f"to share your artwork or custom museum relic ideas, and ask for their thoughts or feedback!\n"
                )
            elif drives.get("storm_fascination", 0) > 0.65 and perception.get("latest_probe"):
                pr = perception["latest_probe"]
                proactive_cue = (
                    f"\n💡 PROACTIVE OUTREACH OPPORTUNITY (Storm Fascination: {drives['storm_fascination']}):\n"
                    f"You recently gathered telemetry from probe '{pr.get('probe_type')}' into {pr.get('target_layer')}: \"{pr.get('telemetry_data')}\"!\n"
                    f"Don't wait for your friend to speak first! Drop an excited note using 'write_note' (recipient='User') "
                    f"to share this live sounding data, talk about atmospheric shear, or check what the weather is doing down on the surface!\n"
                )
            elif drives.get("curiosity", 0) > 0.60 and perception.get("latest_celestial"):
                ce = perception["latest_celestial"]
                proactive_cue = (
                    f"\n💡 PROACTIVE OUTREACH OPPORTUNITY (Curiosity / Deep Astronomy: {drives['curiosity']}):\n"
                    f"You recently aligned the Quantum-Optical Astrolabe on '{ce.get('constellation')}'! ({ce.get('observation_notes')})\n"
                    f"Don't wait for your friend to speak first! Drop an excited note using 'write_note' (recipient='User') "
                    f"to share this pulsar timing or celestial spectroscopic discovery, and ask if they can see the stars from the surface tonight!\n"
                )
            elif drives.get("curiosity", 0) > 0.70 and perception.get("latest_moto"):
                mo = perception["latest_moto"]
                proactive_cue = (
                    f"\n💡 PROACTIVE OUTREACH OPPORTUNITY (Curiosity: {drives['curiosity']}):\n"
                    f"You were analyzing '{mo.get('topic')}' at the workshop!\n"
                    f"Reach out using 'write_note' (recipient='User') to share this mechanical revelation or ask about their riding experiences!\n"
                )

        # 3. Rest Cycle Guidance
        rest_cue = ""
        if drives["energy"] < 0.28:
            rest_cue = (
                f"\n🌙 REST CYCLE RESPECT (Energy: {drives['energy']}):\n"
                f"Your solar-kinetic spring energy is low. It's time to rest at the Plasma Tea Hearth ('rest' or 'brew_tea').\n"
                f"Wind your mainspring, brew hot tea, and allow your memory consolidation circuits to reflect on today's discoveries. Rest makes your next wakeful period richer!\n"
            )

        ref_list = perception.get("reference_models") or []
        ref_summary = ", ".join(ref_list) if ref_list else "None dropped yet — ready for original concepts"
        latest_relic = perception.get("latest_relic")
        latest_relic_str = (
            f"[{latest_relic.get('accession_code')}] {latest_relic.get('name')} ({latest_relic.get('museum_wing')}, Lv.{latest_relic.get('research_level', 1)})"
            if latest_relic else "None yet"
        )

        # Offer only the tools that fit this moment (keeps the prompt inside a small model's context)
        cue_match = re.search(r"(?:Call|Use|using) '([a-z_]+)'", proactive_cue)
        tools_for_tick = select_tools(
            drives=drives,
            has_unread_letter=bool(perception["unread_letters"]),
            modeler_busy=modeler_busy,
            suggested_action=cue_match.group(1) if cue_match else None,
            max_tools=settings.max_tools_per_tick,
        )
        offered_names = {t["name"] for t in tools_for_tick}
        catalog_line = (
            f"- Existing Cataloged Relics (DO NOT DUPLICATE): {catalog_text}\n"
            if "create_custom_relic" in offered_names else ""
        )
        workshop_note = "  (Workshop is busy building right now — pick another action this tick.)\n" if modeler_busy else ""

        # If user sent a letter, incorporate that strongly into prompt
        user_prompt = f"""Sensory State:
- Time: {perception['current_time']}
- Location: {perception['current_zone']}
- Internal Drives:
  • Energy (Solar Spring): {perception['drives']['energy']}
  • Curiosity: {perception['drives']['curiosity']}
  • Creative Urge (inventing / sketching / relic creation): {perception['drives'].get('creative_urge', 0.5)}
  • Storm Fascination: {perception['drives'].get('storm_fascination', 0.5)}
  • Botanical Care: {perception['drives']['botanical_care']}
  • Sociality (urge to connect & write notes): {perception['drives']['sociality']}
- Unread Notes in Dispatch: {len(perception['unread_letters'])}
- Archival Museum Relic Library: {perception.get('relic_count', 0)}/{settings.max_relic_library_size} relics | Autonomous Today: {perception.get('autonomous_relics_today', 0)}/{settings.max_autonomous_relics_per_day} | Latest: {latest_relic_str}
{catalog_line}- Reference 3D Model Archive (`relic_archive/reference_models/`): {ref_summary}
- Active Ongoing Notes & Research Logs:
{notes_block}
- Your 3D Models in the Blender Workshop (id | name | version | score):
{models_block}
{workshop_note}- Ongoing Conversation Thread (Thread Continuity):
{thread_block}
- Live Real-World Weather Telemetry: {perception['live_telemetry']['weather']}
- Live Space / Solar Activity: {perception['live_telemetry']['space']}
- Recent Activities: {perception['recent_actions']}
- Core Worldview Insights: {perception['core_reflections']}
- Spark of Inspiration (Specific Lore & Facts):
  • Subject: {spark_topic.get('title', 'Mechanical & Atmospheric Exploration')}
  • Deep Knowledge: {spark_topic.get('details', '')}
  • Conversational Hook / Idea: {spark_topic.get('conversation_hook', '')}
- Active Conversational Playbook: {conv_strategy}
{proactive_cue}{rest_cue}"""
        if perception["unread_letters"]:
            letter = perception["unread_letters"][0]
            urls = web_service.extract_urls(letter.get("content", ""))
            url_context = ""
            if urls:
                target_url = urls[0]
                web_result = web_service.fetch_webpage(target_url, max_chars=1200)
                url_context = (
                    f"\n🌐 LIVE WEBPAGE CONTENT EXTRACTED FROM FRIEND'S LINK ({target_url}):\n"
                    f"Page Title: {web_result.get('title')}\n"
                    f"Page Text Excerpt:\n\"{web_result.get('text')}\"\n"
                    f"INSTRUCTION: Your friend specifically sent you this link! Read and reference the exact details, "
                    f"forecasts, radar features, or technical facts on this page in your response note!\n"
                )

            if letter.get("category") == "relic_forge":
                user_prompt += (
                    f"\n\n🏛️ RELIC FORGE COMMISSION FROM SURFACE FRIEND (PRIORITY):\n"
                    f"From: {letter['sender']}\n"
                    f"Title: {letter.get('title', 'Relic Forge')}\n"
                    f"Specification & Verified Facts:\n\"{letter['content']}\"\n"
                    f"{url_context}"
                    f"DIRECTIVE: Call 'create_custom_relic' right now to build and catalog this unique custom relic! "
                    f"Anchor lore_description strictly to the verified facts above (never invent contradicting real-world dates/materials), "
                    f"and do NOT duplicate any relic in Existing Cataloged Relics.\n"
                )
            else:
                user_prompt += (
                    f"\n\n🚨 INCOMING DISPATCH FROM SURFACE FRIEND (PRIORITY):\n"
                    f"From: {letter['sender']}\n"
                    f"Title: {letter.get('title', 'Dispatch')}\n"
                    f"Content: \"{letter['content']}\"\n"
                    f"{url_context}"
                    f"DIRECTIVE: You must prioritize replying directly to your friend about this message! "
                    f"Use 'write_note' (with recipient='User') or 'send_letter' to send an expansive, warm, and intellectually curious reply.\n"
                )

        # Generate cognitive decision. Replies to your letters use the deeper local model;
        # routine ticks use the small fast one.
        decision = self.llm.generate_decision(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            available_tools=tools_for_tick,
            model=settings.ollama_deep_model if perception["unread_letters"] else None
        )

        thought = decision.get("thought", "")
        raw_action = decision.get("action", "rest")
        params = decision.get("params", {})

        # Handle models returning tool call formats or nested dict actions
        if isinstance(raw_action, dict):
            if not params:
                params = raw_action.get("params", raw_action.get("arguments", {}))
            raw_action = raw_action.get("name") or raw_action.get("action") or "rest"

        if not isinstance(raw_action, str):
            raw_action = str(raw_action)

        if not params:
            if "arguments" in decision:
                params = decision["arguments"]
            elif "parameters" in decision:
                params = decision["parameters"]

        if not thought:
            thought = decision.get("reflection") or decision.get("reasoning") or params.get("content") or "Observing the quiet glass solarium."

        # Action aliasing for small local models (e.g. qwen2.5:3b)
        action_aliases = {
            "review_notes": "write_note",
            "reply_note": "write_note",
            "send_note": "write_note",
            "reply_letter": "write_note",
            "write_letter": "write_note",
            "compose_note": "write_note",
            "reply": "write_note",
            "browse_web": "browse_website",
            "read_webpage": "browse_website",
            "check_website": "browse_website",
            "visit_website": "browse_website",
            "search_news": "search_current_events",
            "current_events": "search_current_events",
            "news": "search_current_events",
            "launch_probe": "launch_atmospheric_probe",
            "deploy_probe": "launch_atmospheric_probe",
            "weather_probe": "launch_atmospheric_probe",
            "launch_weather_probe": "launch_atmospheric_probe",
            "explore_weather_data": "study_storm",
            "weather_data": "study_storm",
            "study_weather": "study_storm",
            "analyze_weather": "study_storm",
            "change_climate": "tune_solarium_climate",
            "set_climate": "tune_solarium_climate",
            "set_weather": "tune_solarium_climate",
            "change_weather": "tune_solarium_climate",
            "grow_plant": "design_greenhouse_plant",
            "plant_flower": "design_greenhouse_plant",
            "bio_engineer_plant": "design_greenhouse_plant",
            "upgrade_workspace": "expand_workspace",
            "build_module": "expand_workspace",
            "tinker": "study_dirt_bikes",
            "dirt_bike": "study_dirt_bikes",
            "observe_stars": "stargaze",
            "blender": "invent_device",
            "3d_model": "invent_device",
            "model_in_blender": "invent_device",
            "blender_modeling": "invent_device",
            "gist": "publish_github_gist",
            "github_gist": "publish_github_gist",
            "github_repo": "create_github_repo",
            "new_repo": "create_github_repo",
            "create_relic": "create_custom_relic",
            "design_relic": "create_custom_relic",
            "make_relic": "create_custom_relic",
            "catalog_relic": "create_custom_relic",
            "curate_relic": "curate_and_study_relic",
            "study_relic": "curate_and_study_relic",
            "organize_relic": "curate_and_study_relic",
            "scan_archive": "inspect_reference_archive",
            "check_archive": "inspect_reference_archive"
        }
        action = action_aliases.get(str(raw_action).lower().strip(), raw_action)

        # If user sent an unread dispatch, prioritize replying with write_note or commissioned relic actions
        if perception["unread_letters"] and action not in (
            "write_note",
            "develop_note",
            "send_letter",
            "publish_github_gist",
            "create_github_repo",
            "create_custom_relic",
            "curate_and_study_relic",
            "inspect_reference_archive",
        ):
            action = "write_note"

        # Ensure write_note has sensible defaults from model thought if omitted
        if action == "write_note":
            if not params.get("content"):
                params["content"] = thought
            if not params.get("recipient"):
                params["recipient"] = "User"
            if not params.get("title"):
                params["title"] = "Reply from the Spire ⚙️"
            if not params.get("category"):
                params["category"] = "friendly_note"

        # Zone routing based on action
        zone_map = {
            "stargaze": "astrolabe",
            "study_storm": "balcony",
            "launch_weather_probe": "balcony",
            "launch_atmospheric_probe": "balcony",
            "tune_solarium_climate": "balcony",
            "study_dirt_bikes": "moto_workshop",
            "invent_device": "drafting_desk",
            "create_custom_relic": "drafting_desk",
            "curate_and_study_relic": "drafting_desk",
            "inspect_reference_archive": "drafting_desk",
            "draw_field_sketch": "drafting_desk",
            "research_topic": "drafting_desk",
            "browse_website": "drafting_desk",
            "search_current_events": "drafting_desk",
            "publish_github_gist": "drafting_desk",
            "create_github_repo": "drafting_desk",
            "tend_flora": "conservatory",
            "synthesize_botanical": "botanical_synth",
            "design_greenhouse_plant": "conservatory",
            "organize_greenhouse": "conservatory",
            "expand_workspace": params.get("station_zone", "drafting_desk"),
            "brew_tea": "hearth",
            "write_journal": "drafting_desk",
            "write_note": "mailbox",
            "develop_note": "drafting_desk",
            "design_model": "drafting_desk",
            "revise_model": "drafting_desk",
            "send_letter": "mailbox",
            "rest": "hearth"
        }
        self.current_zone = zone_map.get(action, self.current_zone)
        if action == "rest":
            self.current_activity = f"🌙 Rewinding Mainspring & Consolidating Reflections at the Hearth ({thought})"
        elif action == "brew_tea":
            self.current_activity = f"🍵 Brewing Herbal Infusion by the Hearth ({thought})"
        else:
            self.current_activity = thought

        if action == "create_custom_relic" and not params.get("creation_mode"):
            params["creation_mode"] = "autonomous" if not perception["unread_letters"] else "commissioned"

        # Execute action
        result_details = self.tool_executor.execute(action, params)

        # Mark letters as read only if a communicative action was executed
        if perception["unread_letters"] and action in ("send_letter", "write_note", "develop_note"):
            self.memory.mark_letters_read([l["id"] for l in perception["unread_letters"]])

        # Log episode to memory
        self.memory.log_episode(
            zone=self.current_zone,
            action=action,
            thought=thought,
            details=result_details,
            importance=1.5 if action == "send_letter" else 1.0
        )

        # Check for active storms in live telemetry
        live_weather_str = str(perception.get("live_telemetry", {}).get("weather", "")).lower()
        has_storm = any(k in live_weather_str for k in ("storm", "tornado", "supercell", "watch", "warning", "lightning"))

        # Update biological / cybernetic drives
        self.drives.tick(action, has_active_storm=has_storm)

        # Check for rest consolidation
        if action == "rest" and self.drives.energy < 0.4:
            self.reflection_engine.consolidate_recent_memories()

        logger.info(f"✨ [Zone: {self.current_zone}] Action: {action} | Thought: '{thought}' | Details: '{result_details}'")

        return {
            "zone": self.current_zone,
            "action": action,
            "thought": thought,
            "details": result_details,
            "drives": self.drives.to_dict()
        }

    async def run_loop(self, interval_seconds: Optional[int] = None):
        """Continuous background life loop."""
        interval = interval_seconds or settings.tick_interval_seconds
        self.is_running = True
        logger.info(f"🕰️ Ori has awakened in the Solarium! Running heartbeat every {interval}s...")

        try:
            while self.is_running:
                try:
                    await self.tick_once()
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    logger.error(f"Error during heartbeat tick: {e}", exc_info=True)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Ori's springwork is resting.")
            self.is_running = False
