"""
Persistent Multi-Tier Memory Engine using SQLite.
Stores episodes, daily reflections, correspondence, celestial sightings, and botanical records.
"""

import json
import sqlite3
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class MemoryStore:
    def __init__(self, db_path: str = "ori_memory.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Episodic memory stream (observations, thoughts, actions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    zone TEXT NOT NULL,
                    action TEXT NOT NULL,
                    thought TEXT,
                    details TEXT,
                    importance REAL DEFAULT 1.0
                )
            """)

            # Higher-order daily reflections (synthesized insights)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reflections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    insight TEXT NOT NULL,
                    source_episode_ids TEXT
                )
            """)

            # Celestial observations
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS celestial_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    constellation TEXT NOT NULL,
                    observation_notes TEXT NOT NULL,
                    atmospheric_conditions TEXT
                )
            """)

            # Botanical / Greenhouse care logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS botanical_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    specimen_name TEXT NOT NULL,
                    action_taken TEXT NOT NULL,
                    notes TEXT
                )
            """)

            # Mailbox Correspondence (user <-> Ori)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS correspondence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    is_read INTEGER DEFAULT 0
                )
            """)

            # Electronic Inventions & Speculative Hardware Schematics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    components_json TEXT,
                    schematic_diagram TEXT
                )
            """)

            # Field Sketches & Observational Art Studies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sketches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    medium TEXT NOT NULL,
                    description TEXT NOT NULL,
                    ascii_sketch TEXT,
                    zone TEXT
                )
            """)

            # Atmospheric Weather Probes & Soundings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS weather_probes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    probe_type TEXT NOT NULL,
                    target_layer TEXT NOT NULL,
                    telemetry_data TEXT NOT NULL,
                    altitude_m REAL DEFAULT 3500.0,
                    status TEXT DEFAULT 'Transmitting'
                )
            """)

            # Dirt Bike Mechanical Workshop Studies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS moto_studies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    component TEXT NOT NULL,
                    mechanical_notes TEXT NOT NULL,
                    schematic_ascii TEXT
                )
            """)

            # Workspace Expansions & Solarium Modifications
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workspace_mods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    module_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT NOT NULL,
                    station_zone TEXT NOT NULL,
                    visual_mesh_type TEXT NOT NULL,
                    level INTEGER DEFAULT 1
                )
            """)

            # Solarium Micro-Climate & Dynamic Sky State
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS solarium_climate (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sky_mode TEXT NOT NULL,
                    cloud_density REAL DEFAULT 1.0,
                    lightning_frequency REAL DEFAULT 0.5,
                    notes TEXT NOT NULL
                )
            """)

            # Fantastical Greenhouse Exotic Plant Specimen Collection
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS greenhouse_plants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    specimen_name TEXT NOT NULL,
                    pod_slot INTEGER NOT NULL UNIQUE,
                    bio_type TEXT NOT NULL,
                    glow_color TEXT NOT NULL,
                    height_cm REAL DEFAULT 35.0,
                    petal_geometry TEXT DEFAULT 'star',
                    mechanics_description TEXT NOT NULL,
                    arrangement_notes TEXT
                )
            """)

            # Live Atmospheric Probes & Radiosonde Drifters
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS active_probes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    probe_name TEXT NOT NULL,
                    probe_type TEXT NOT NULL,
                    target_layer TEXT NOT NULL,
                    launch_time TEXT NOT NULL,
                    altitude_m REAL DEFAULT 3500.0,
                    status TEXT DEFAULT 'descending',
                    telemetry_stream TEXT,
                    heading_deg REAL DEFAULT 180.0,
                    beacon_color TEXT DEFAULT '#00f2fe'
                )
            """)

            # Modeling Workshop: versioned Blender models designed by Ori
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    name TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    parent_id INTEGER,
                    concept TEXT,
                    script TEXT,
                    glb_path TEXT,
                    preview_path TEXT,
                    stats_json TEXT,
                    critique TEXT,
                    score REAL DEFAULT 0,
                    status TEXT DEFAULT 'built',
                    error TEXT
                )
            """)

            # Persistent learned Blender techniques and pitfalls from past builds
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS model_lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    lesson_type TEXT NOT NULL,
                    lesson_text TEXT NOT NULL,
                    source_model_id INTEGER,
                    score_impact REAL DEFAULT 0.0
                )
            """)

            # Ensure botanical_logs has origin_tag and is_synthetic columns
            try:
                cursor.execute("ALTER TABLE botanical_logs ADD COLUMN origin_tag TEXT DEFAULT 'Real Flora'")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE botanical_logs ADD COLUMN is_synthetic INTEGER DEFAULT 0")
            except Exception:
                pass

            # Ensure correspondence has title, category, and updated_at columns
            try:
                cursor.execute("ALTER TABLE correspondence ADD COLUMN title TEXT DEFAULT 'Conversational Note'")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE correspondence ADD COLUMN category TEXT DEFAULT 'friendly_note'")
            except Exception:
                pass
            try:
                cursor.execute("ALTER TABLE correspondence ADD COLUMN updated_at TEXT")
            except Exception:
                pass

            # Seed default exotic greenhouse plants if empty
            cursor.execute("SELECT COUNT(*) FROM greenhouse_plants")
            if cursor.fetchone()[0] == 0:
                initial_plants = [
                    (
                        datetime.datetime.now().isoformat(), "Aetherial Starlight Fern", 1, "photovoltaic_flora",
                        "#00f2fe", 42.0, "fractal_spiral",
                        "Absorbs cosmic microwave rays to oscillate harmonic bioluminescent pulses across its silver fronds.",
                        "Flanked near northern optical collector for celestial ray exposure."
                    ),
                    (
                        datetime.datetime.now().isoformat(), "Thunder-Bloom Bell", 2, "electro-receptive_orchid",
                        "#f5c862", 55.0, "bell",
                        "Detects mesocyclone electrostatic charge and chimes like a bronze bell when lightning strikes.",
                        "Positioned facing the Atmospheric Terrace storm corridor."
                    ),
                    (
                        datetime.datetime.now().isoformat(), "Cryo-Moss Nebula", 3, "aeroponic_lichen",
                        "#38ef7d", 20.0, "spore_cloud",
                        "Exudes supercooled ice mist that maintains microclimate humidity across the garden wing.",
                        "Grounded in center pod reservoir to stabilize humidity."
                    ),
                    (
                        datetime.datetime.now().isoformat(), "Pulsar-Crown Dahlia", 4, "radio-sensitive_angiosperm",
                        "#e040fb", 65.0, "crystal_star",
                        "Its crystalline petals rotate in synchrony with Crab Nebula pulsar frequency.",
                        "Interfaced with the Astrolabe telemetry bridge."
                    ),
                    (
                        datetime.datetime.now().isoformat(), "Obsidian Solar Thistle", 5, "thermal-kinetic_succulent",
                        "#ff7043", 30.0, "concentric_rings",
                        "Harvests low-angle twilight infrared radiation to store heat in miniature coiled springs.",
                        "Placed in high thermal-gradient slot."
                    ),
                    (
                        datetime.datetime.now().isoformat(), "Harmonic Nimbus Lily", 6, "acoustic_hydrophyte",
                        "#00e5ff", 48.0, "hexagonal",
                        "Floats on aeroponic vapor cushions, purifying trace ozone into sweet petrichor mist.",
                        "Softening airflow intake on eastern wing."
                    )
                ]
                cursor.executemany(
                    """
                    INSERT INTO greenhouse_plants (
                        timestamp, specimen_name, pod_slot, bio_type, glow_color,
                        height_cm, petal_geometry, mechanics_description, arrangement_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    initial_plants
                )

            # Seed default active probes if empty
            cursor.execute("SELECT COUNT(*) FROM active_probes")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.datetime.now().isoformat()
                initial_probes = [
                    (
                        now_str, "Zephyr-7 Penetrator", "mesocyclone_penetrator", "Mid-Troposphere Mesocyclone Core",
                        now_str, 5400.0, "descending",
                        "Temp: -18.4°C | Press: 495 hPa | Updraft: +28.5 m/s | Hail Core Reflectivity: 62 dBZ",
                        185.0, "#00f2fe"
                    ),
                    (
                        now_str, "Nimbus-1 Stratosounder", "infrasonic_radiosonde", "Stratospheric Inversion Layer",
                        now_str, 8100.0, "descending",
                        "Temp: -48.2°C | Press: 290 hPa | Gravity Wave Oscillation: 4.2 mHz | Ozone: Active",
                        142.0, "#e040fb"
                    )
                ]
                cursor.executemany(
                    """
                    INSERT INTO active_probes (
                        timestamp, probe_name, probe_type, target_layer, launch_time,
                        altitude_m, status, telemetry_stream, heading_deg, beacon_color
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    initial_probes
                )

            # Seed default workspace mods if empty
            cursor.execute("SELECT COUNT(*) FROM workspace_mods")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.datetime.now().isoformat()
                initial_mods = [
                    (
                        now_str, "Auxiliary Radiosonde Telemetry Terminal", "telemetry_array",
                        "Twin helical brass antenna feeding live probe telemetry into the Drafting Console.",
                        "drafting_desk", "brass_gilded_antenna", 1
                    ),
                    (
                        now_str, "Pneumatic Ejection Sounding Rail", "launch_gantry",
                        "Electromagnetic booster rail extending over the cloud sea to launch atmospheric probes into anvil heads.",
                        "balcony", "titanium_rail_with_electrum_coils", 1
                    )
                ]
                cursor.executemany(
                    """
                    INSERT INTO workspace_mods (
                        timestamp, module_name, category, description, station_zone, visual_mesh_type, level
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    initial_mods
                )

            # Infinitely Expanding Custom Museum Relic Library
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    accession_code TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    era TEXT NOT NULL,
                    museum_wing TEXT NOT NULL,
                    rarity TEXT DEFAULT 'Uncommon',
                    reference_model TEXT DEFAULT 'Original Concept',
                    lore_description TEXT NOT NULL,
                    study_notes TEXT,
                    research_level INTEGER DEFAULT 1,
                    lowpoly_spec_json TEXT,
                    blender_workflow TEXT,
                    tags_json TEXT,
                    curation_status TEXT DEFAULT 'Cataloged'
                )
            """)

            cursor.execute("SELECT COUNT(*) FROM relics")
            if cursor.fetchone()[0] == 0:
                now_str = datetime.datetime.now().isoformat()
                starter_relics = [
                    (
                        "ARC-0001", now_str, "Astrolabe Compass of the Cloud Cartographer",
                        "Astrolabe Instrument", "Sky-Cartographer Era", "Hall of Celestial Navigation",
                        "Rare", "Original Concept",
                        "A pocket-sized celestial brass gimbal calibrated to triangulate spire altitudes above unbroken cloud decks using dual sapphire sighting vanes.",
                        f"[{now_str[:10]}] Initial accession scan completed. Weighted normals verify crisp chamfered dial rings.",
                        1,
                        json.dumps({
                            "poly_budget_tris": 680,
                            "materials_palette": "Brushed electrum, recessed sapphire lens, etched brass gimbal",
                            "silhouette_notes": "Concentric stepped rings with proud pointer needles for instant mid-range readability",
                            "target_style": "Low-Poly High-Quality Game Asset",
                            "pbr_workflow": "Weighted Normals + Procedural/Baked PBR"
                        }),
                        "Start from an 18-segment cylinder, inset top bevels, mirror dual sight posts, add Weighted Normal + Bevel (Weight) modifier.",
                        json.dumps(["astronomy", "navigation", "brass", "lowpoly"]),
                        "Exhibition Ready"
                    ),
                    (
                        "ARC-0002", now_str, "Barometric Storm-Glass Resonator",
                        "Storm Artifact", "Pre-Tempest Antiquity", "Atmospheric & Tempest Wing",
                        "Epic", "Original Concept",
                        "An evacuated smoked-crystal vessel wrapped in an oxidized copper coil whose internal storm crystals chime just before barometric pressure plunges.",
                        f"[{now_str[:10]}] Acoustic coil resonance measured; mild verdigris patina preserved along lower copper solder joints.",
                        1,
                        json.dumps({
                            "poly_budget_tris": 920,
                            "materials_palette": "Smoked crystal vial, patina copper coil, storm-crystal suspension",
                            "silhouette_notes": "Hexagonal cage frame silhouetting glowing central crystal core",
                            "target_style": "Low-Poly High-Quality Game Asset",
                            "pbr_workflow": "Weighted Normals + Procedural/Baked PBR"
                        }),
                        "Block out hex cage with 6-sided primitives, array coil wraps with Screw modifier baked to low-poly strip, assign Principled glass Transmission.",
                        json.dumps(["weather", "barometer", "glass", "lowpoly"]),
                        "Verified"
                    ),
                    (
                        "ARC-0003", now_str, "Clockwork Botanist's Spore Vial",
                        "Botanical Vessel", "Late Brass Epoch", "Natural History & Flora Vault",
                        "Uncommon", "Original Concept",
                        "A hermetically sealed specimen capsule with a ratcheting iris cap designed to keep bioluminescent cloud-moss spores viable across high-altitude flights.",
                        f"[{now_str[:10]}] Spore capsule seal intact; emerald bioluminescence remains responsive to ambient vibration.",
                        1,
                        json.dumps({
                            "poly_budget_tris": 440,
                            "materials_palette": "Aged bronze cap, ribbed glass cylinder, emissive emerald moss core",
                            "silhouette_notes": "Chunky knurled valve cap tapering into a glowing glass ampoule",
                            "target_style": "Low-Poly High-Quality Game Asset",
                            "pbr_workflow": "Weighted Normals + Procedural/Baked PBR"
                        }),
                        "Model 12-sided ampoule body, extrude knurled collar bands, bake ambient occlusion into vertex colors + roughness ramp.",
                        json.dumps(["botany", "bioluminescent", "vessel", "lowpoly"]),
                        "Cataloged"
                    ),
                ]
                cursor.executemany(
                    """
                    INSERT INTO relics (
                        accession_code, timestamp, name, category, era, museum_wing, rarity,
                        reference_model, lore_description, study_notes, research_level,
                        lowpoly_spec_json, blender_workflow, tags_json, curation_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    starter_relics
                )

            # Migrate relics table with separated verified_facts, fact_sources_json, and creation_mode
            for col_sql in (
                "ALTER TABLE relics ADD COLUMN verified_facts TEXT DEFAULT ''",
                "ALTER TABLE relics ADD COLUMN fact_sources_json TEXT DEFAULT '[]'",
                "ALTER TABLE relics ADD COLUMN creation_mode TEXT DEFAULT 'commissioned'",
            ):
                try:
                    cursor.execute(col_sql)
                except Exception:
                    pass

            # Backfill starter verified facts on ARC-0001..ARC-0003 if empty
            starter_facts_seed = {
                "ARC-0001": (
                    "• Mariner's astrolabe: An inclinometer used by 15th–17th century navigators to determine latitude by measuring the altitude of the sun or Polaris, cast heavily in brass so wind would not sway it at sea.",
                    json.dumps([{"title": "Wikipedia — Mariner's astrolabe", "url": "https://en.wikipedia.org/wiki/Mariner%27s_astrolabe", "source_type": "wikipedia"}]),
                ),
                "ARC-0002": (
                    "• Storm glass (FitzRoy barometer): A 19th-century weather instrument containing a sealed camphor, potassium nitrate, and ammonium chloride solution whose crystallization shifts with temperature and barometric trends.",
                    json.dumps([{"title": "Wikipedia — Storm glass", "url": "https://en.wikipedia.org/wiki/Storm_glass", "source_type": "wikipedia"}]),
                ),
                "ARC-0003": (
                    "• Bioluminescence: Light emission by living organisms via luciferin oxidation catalyzed by luciferase enzymes, observed in forest fungi such as Neonothopanus gardneri (~530 nm green glow).",
                    json.dumps([{"title": "Wikipedia — Bioluminescence", "url": "https://en.wikipedia.org/wiki/Bioluminescence", "source_type": "wikipedia"}]),
                ),
            }
            for code, (facts_txt, src_json) in starter_facts_seed.items():
                cursor.execute(
                    "UPDATE relics SET verified_facts = ?, fact_sources_json = ? WHERE accession_code = ? AND (verified_facts IS NULL OR verified_facts = '')",
                    (facts_txt, src_json, code),
                )

            conn.commit()

    def log_episode(
        self,
        zone: str,
        action: str,
        thought: str,
        details: str = "",
        importance: float = 1.0
    ) -> int:
        """Record an episodic memory event."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO episodes (timestamp, zone, action, thought, details, importance)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, zone, action, thought, details, importance)
            )
            conn.commit()
            return cursor.lastrowid

    def get_recent_episodes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch the most recent episodic events."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM episodes ORDER BY id DESC LIMIT ?
                """,
                (limit,)
            )
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]

    def log_reflection(self, insight: str, source_episode_ids: str = "") -> int:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reflections (timestamp, insight, source_episode_ids) VALUES (?, ?, ?)",
                (now, insight, source_episode_ids)
            )
            conn.commit()
            return cursor.lastrowid

    def get_reflections(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM reflections ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in reversed(cursor.fetchall())]

    def log_celestial(self, constellation: str, notes: str, conditions: str = "Clear cloud-sea"):
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO celestial_logs (timestamp, constellation, observation_notes, atmospheric_conditions) VALUES (?, ?, ?, ?)",
                (now, constellation, notes, conditions)
            )
            conn.commit()

    def get_celestial(self, limit: int = 5) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM celestial_logs ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def log_botanical(
        self,
        specimen_name: str,
        action_taken: str,
        notes: str,
        origin_tag: str = "Real Flora",
        is_synthetic: bool = False
    ):
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO botanical_logs (timestamp, specimen_name, action_taken, notes, origin_tag, is_synthetic)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, specimen_name, action_taken, notes, origin_tag, 1 if is_synthetic else 0)
            )
            conn.commit()

    def get_real_botanicals(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM botanical_logs WHERE is_synthetic = 0 OR is_synthetic IS NULL ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def get_synthetic_botanicals(self, limit: int = 15) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM botanical_logs WHERE is_synthetic = 1 ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def log_moto_study(
        self,
        topic: str,
        component: str,
        mechanical_notes: str,
        schematic_ascii: str = ""
    ) -> int:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO moto_studies (timestamp, topic, component, mechanical_notes, schematic_ascii)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, topic, component, mechanical_notes, schematic_ascii)
            )
            conn.commit()
            return cursor.lastrowid

    def get_moto_studies(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM moto_studies ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def add_model(
        self,
        name: str,
        version: int,
        parent_id: Any,
        concept: str,
        script: str,
        glb_path: str,
        preview_path: str,
        stats: Dict[str, Any],
        critique: str,
        score: float,
        status: str = "built",
        error: str = ""
    ) -> int:
        import json as _json
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO models (timestamp, name, version, parent_id, concept, script, glb_path,
                                    preview_path, stats_json, critique, score, status, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (now, name, version, parent_id, concept, script, glb_path, preview_path,
                 _json.dumps(stats or {}), critique, score, status, error)
            )
            conn.commit()
            return cursor.lastrowid

    def _model_row(self, row) -> Dict[str, Any]:
        import json as _json
        d = dict(row)
        try:
            d["stats"] = _json.loads(d.get("stats_json") or "{}")
        except Exception:
            d["stats"] = {}
        return d

    def get_models(self, limit: int = 30, include_script: bool = False) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM models ORDER BY id DESC LIMIT ?", (limit,))
            rows = [self._model_row(r) for r in cursor.fetchall()]
        if not include_script:
            for r in rows:
                r.pop("script", None)
        return rows

    def get_model(self, model_id: int) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM models WHERE id = ?", (model_id,))
            row = cursor.fetchone()
            return self._model_row(row) if row else {}

    def get_best_model_lessons(self, limit: int = 3) -> List[str]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT critique FROM models WHERE status = 'built' AND critique != '' ORDER BY score DESC, id DESC LIMIT ?",
                (limit,)
            )
            return [r["critique"].replace("\n", " ")[:300] for r in cursor.fetchall()]

    def add_model_lesson(
        self,
        lesson_type: str,
        lesson_text: str,
        source_model_id: Any = None,
        score_impact: float = 0.0
    ) -> int:
        now = datetime.datetime.now().isoformat()
        clean_text = (lesson_text or "").strip()[:300]
        if not clean_text:
            return 0
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO model_lessons (timestamp, lesson_type, lesson_text, source_model_id, score_impact)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, lesson_type, clean_text, source_model_id, score_impact)
            )
            conn.commit()
            return cursor.lastrowid

    def get_model_lessons(self, lesson_type: str = None, limit: int = 5) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if lesson_type:
                cursor.execute(
                    "SELECT * FROM model_lessons WHERE lesson_type = ? ORDER BY score_impact DESC, id DESC LIMIT ?",
                    (lesson_type, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM model_lessons ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
            return [dict(r) for r in cursor.fetchall()]

    def add_note(
        self,
        sender: str,
        recipient: str,
        content: str,
        title: str = "Conversational Note",
        category: str = "friendly_note"
    ) -> int:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO correspondence (timestamp, sender, recipient, content, is_read, title, category, updated_at)
                VALUES (?, ?, ?, ?, 0, ?, ?, ?)
                """,
                (now, sender, recipient, content, title, category, now)
            )
            conn.commit()
            return cursor.lastrowid

    def update_note(self, note_id: int, added_content: str, updated_title: str = None) -> bool:
        """Appends thoughts to an ongoing note/research log/diary entry to track and develop ideas over time."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content, title FROM correspondence WHERE id = ?", (note_id,))
            row = cursor.fetchone()
            if not row:
                return False
            existing_content = row["content"]
            new_content = f"{existing_content}\n\n[Addendum {now[:16]}]:\n{added_content}"
            new_title = updated_title if updated_title else (row["title"] or "Conversational Note")
            cursor.execute(
                """
                UPDATE correspondence
                SET content = ?, title = ?, updated_at = ?
                WHERE id = ?
                """,
                (new_content, new_title, now, note_id)
            )
            conn.commit()
            return True

    def get_notes(self, limit: int = 50, category: str = None) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if category:
                cursor.execute(
                    "SELECT * FROM correspondence WHERE category = ? ORDER BY id DESC LIMIT ?",
                    (category, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM correspondence ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
            return [dict(r) for r in reversed(cursor.fetchall())]

    def get_recent_developable_notes(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent notes that Ori or user created to allow developing them further."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM correspondence ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def add_letter(self, sender: str, recipient: str, content: str, title: str = "Conversational Note", category: str = "friendly_note") -> int:
        return self.add_note(sender=sender, recipient=recipient, content=content, title=title, category=category)

    def get_unread_letters(self, recipient: str = "Ori") -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM correspondence WHERE recipient = ? AND is_read = 0 ORDER BY id ASC",
                (recipient,)
            )
            return [dict(r) for r in cursor.fetchall()]

    def mark_letters_read(self, letter_ids: List[int]):
        if not letter_ids:
            return
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ",".join("?" * len(letter_ids))
            cursor.execute(f"UPDATE correspondence SET is_read = 1 WHERE id IN ({placeholders})", letter_ids)
            conn.commit()

    def get_all_letters(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM correspondence ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [dict(r) for r in reversed(cursor.fetchall())]

    def log_invention(
        self,
        title: str,
        category: str,
        description: str,
        components: List[str] = None,
        schematic: str = ""
    ) -> int:
        now = datetime.datetime.now().isoformat()
        comp_json = json.dumps(components or [])
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO inventions (timestamp, title, category, description, components_json, schematic_diagram)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, title, category, description, comp_json, schematic)
            )
            conn.commit()
            return cursor.lastrowid

    def get_inventions(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM inventions ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                item = dict(r)
                try:
                    item["components"] = json.loads(item.get("components_json", "[]"))
                except Exception:
                    item["components"] = []
                result.append(item)
            return result

    def log_sketch(
        self,
        subject: str,
        medium: str,
        description: str,
        ascii_sketch: str = "",
        zone: str = "drafting_desk"
    ) -> int:
        """Record an observational field sketch."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO sketches (timestamp, subject, medium, description, ascii_sketch, zone)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, subject, medium, description, ascii_sketch, zone)
            )
            conn.commit()
            return cursor.lastrowid

    def get_sketches(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieve recent field sketches."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sketches ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def log_weather_probe(
        self,
        probe_type: str,
        target_layer: str,
        telemetry_data: str,
        altitude_m: float = 3500.0,
        status: str = "Transmitting"
    ) -> int:
        """Record an atmospheric weather probe launch and its sounding telemetry."""
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO weather_probes (timestamp, probe_type, target_layer, telemetry_data, altitude_m, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (now, probe_type, target_layer, telemetry_data, altitude_m, status)
            )
            conn.commit()
            return cursor.lastrowid

    def get_weather_probes(self, limit: int = 15) -> List[Dict[str, Any]]:
        """Retrieve recent atmospheric probe telemetry soundings."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM weather_probes ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Workspace Expansions & Upgrades
    # ------------------------------------------------------------------
    def log_workspace_mod(
        self,
        module_name: str,
        category: str,
        description: str,
        station_zone: str,
        visual_mesh_type: str,
        level: int = 1
    ) -> int:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO workspace_mods (timestamp, module_name, category, description, station_zone, visual_mesh_type, level)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (now, module_name, category, description, station_zone, visual_mesh_type, level)
            )
            conn.commit()
            return cursor.lastrowid

    def get_workspace_mods(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM workspace_mods ORDER BY id ASC")
            return [dict(r) for r in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Solarium Dynamic Climate & Micro-Weather
    # ------------------------------------------------------------------
    def set_solarium_climate(
        self,
        sky_mode: str,
        cloud_density: float = 1.0,
        lightning_frequency: float = 0.5,
        notes: str = ""
    ) -> int:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO solarium_climate (timestamp, sky_mode, cloud_density, lightning_frequency, notes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (now, sky_mode, cloud_density, lightning_frequency, notes)
            )
            conn.commit()
            return cursor.lastrowid

    def get_solarium_climate(self) -> Dict[str, Any]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM solarium_climate ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {
                "sky_mode": "mesocyclone_anvil",
                "cloud_density": 1.0,
                "lightning_frequency": 0.6,
                "notes": "Mesocyclone anvil cloud shelf with low-angle twilight"
            }

    # ------------------------------------------------------------------
    # Fantastical Exotic Greenhouse Plants & Organization
    # ------------------------------------------------------------------
    def add_or_update_greenhouse_plant(
        self,
        specimen_name: str,
        pod_slot: int,
        bio_type: str,
        glow_color: str,
        height_cm: float = 35.0,
        petal_geometry: str = "star",
        mechanics_description: str = "",
        arrangement_notes: str = ""
    ) -> int:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO greenhouse_plants (
                    timestamp, specimen_name, pod_slot, bio_type, glow_color,
                    height_cm, petal_geometry, mechanics_description, arrangement_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pod_slot) DO UPDATE SET
                    timestamp = excluded.timestamp,
                    specimen_name = excluded.specimen_name,
                    bio_type = excluded.bio_type,
                    glow_color = excluded.glow_color,
                    height_cm = excluded.height_cm,
                    petal_geometry = excluded.petal_geometry,
                    mechanics_description = excluded.mechanics_description,
                    arrangement_notes = excluded.arrangement_notes
                """,
                (now, specimen_name, pod_slot, bio_type, glow_color, height_cm, petal_geometry, mechanics_description, arrangement_notes)
            )
            conn.commit()
            return cursor.lastrowid

    def get_greenhouse_plants(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM greenhouse_plants ORDER BY pod_slot ASC")
            return [dict(r) for r in cursor.fetchall()]

    # ------------------------------------------------------------------
    # Physical Active Probes & Flight Telemetry
    # ------------------------------------------------------------------
    def launch_active_probe(
        self,
        probe_name: str,
        probe_type: str,
        target_layer: str,
        altitude_m: float = 4200.0,
        telemetry_stream: str = "",
        beacon_color: str = "#00f2fe",
        heading_deg: float = 180.0
    ) -> int:
        now = datetime.datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO active_probes (
                    timestamp, probe_name, probe_type, target_layer, launch_time,
                    altitude_m, status, telemetry_stream, heading_deg, beacon_color
                ) VALUES (?, ?, ?, ?, ?, ?, 'descending', ?, ?, ?)
                """,
                (now, probe_name, probe_type, target_layer, now, altitude_m, telemetry_stream, heading_deg, beacon_color)
            )
            conn.commit()
            # Also log into legacy weather_probes table for historical consistency
            cursor.execute(
                """
                INSERT INTO weather_probes (timestamp, probe_type, target_layer, telemetry_data, altitude_m, status)
                VALUES (?, ?, ?, ?, ?, 'Transmitting')
                """,
                (now, f"{probe_name} ({probe_type})", target_layer, telemetry_stream, altitude_m)
            )
            conn.commit()
            return cursor.lastrowid

    def get_active_probes(self, limit: int = 8) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM active_probes ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def update_probe_telemetry(self, probe_id: int, altitude_m: float, status: str, telemetry_stream: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE active_probes
                SET altitude_m = ?, status = ?, telemetry_stream = ?
                WHERE id = ?
                """,
                (altitude_m, status, telemetry_stream, probe_id)
            )
            conn.commit()

    # ------------------------------------------------------------------
    # Archival Curator: Infinitely Expanding Custom Museum Relic Library
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_relic_row(row: sqlite3.Row) -> Dict[str, Any]:
        d = dict(row)
        try:
            d["lowpoly_spec"] = json.loads(d.get("lowpoly_spec_json") or "{}")
        except (TypeError, json.JSONDecodeError):
            d["lowpoly_spec"] = {}
        try:
            d["tags"] = json.loads(d.get("tags_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            d["tags"] = []
        try:
            d["fact_sources"] = json.loads(d.get("fact_sources_json") or "[]")
        except (TypeError, json.JSONDecodeError):
            d["fact_sources"] = []
        d["verified_facts"] = d.get("verified_facts") or ""
        d["creation_mode"] = d.get("creation_mode") or "commissioned"
        d["mesh_file"] = f"{d.get('accession_code') or 'ARC-0000'}.glb"
        return d

    @staticmethod
    def _normalize_relic_tokens(text: str) -> set:
        import re
        stop = {"the", "of", "a", "an", "and", "for", "with", "in", "to", "by", "relic"}
        tokens = [t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 1 and t not in stop]
        return set(tokens)

    def find_duplicate_relic(self, name: str) -> Optional[Dict[str, Any]]:
        """Check existing relics for exact or high-similarity duplicate titles so Ori recalls prior builds."""
        target_clean = " ".join((name or "").lower().split())
        target_tokens = self._normalize_relic_tokens(name)
        if not target_clean:
            return None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM relics ORDER BY id DESC")
            for row in cursor.fetchall():
                existing_name = " ".join((row["name"] or "").lower().split())
                if existing_name == target_clean:
                    return self._parse_relic_row(row)
                if target_tokens:
                    existing_tokens = self._normalize_relic_tokens(row["name"])
                    if existing_tokens:
                        union = target_tokens | existing_tokens
                        inter = target_tokens & existing_tokens
                        if union and (len(inter) / len(union)) >= 0.70:
                            return self._parse_relic_row(row)
        return None

    def get_relic_catalog_summary(self, limit: int = 40) -> List[Dict[str, Any]]:
        """Return compact catalog summary (code, name, wing, category) for anti-duplication recall."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT accession_code, name, category, museum_wing, research_level FROM relics ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(r) for r in cursor.fetchall()]

    def count_autonomous_relics_today(self) -> int:
        """Count how many relics Ori created autonomously today (for overflow failsafe)."""
        today_prefix = datetime.datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COUNT(*) FROM relics WHERE timestamp LIKE ? AND creation_mode = 'autonomous'",
                (f"{today_prefix}%",),
            )
            return int(cursor.fetchone()[0])

    def create_relic(
        self,
        name: str,
        category: str,
        era: str,
        museum_wing: str,
        rarity: str = "Uncommon",
        reference_model: str = "Original Concept",
        lore_description: str = "",
        verified_facts: str = "",
        fact_sources: Optional[List[Dict[str, str]]] = None,
        study_notes: str = "",
        poly_budget_tris: int = 800,
        materials_palette: str = "",
        silhouette_notes: str = "",
        blender_workflow: str = "",
        tags: Optional[List[str]] = None,
        curation_status: str = "Cataloged",
        creation_mode: str = "commissioned",
    ) -> Dict[str, Any]:
        """Catalog a brand-new custom low-poly high-quality relic into the expanding museum library."""
        now = datetime.datetime.now().isoformat()
        try:
            int_budget = max(150, min(5000, int(poly_budget_tris)))
        except (ValueError, TypeError):
            int_budget = 800

        lowpoly_spec = {
            "poly_budget_tris": int_budget,
            "materials_palette": materials_palette or "Patina brass, brushed iron, warm sapphire glass",
            "silhouette_notes": silhouette_notes or "Readable three-stage stepped silhouette with crisp chamfered edges",
            "target_style": "Low-Poly High-Quality Game Asset",
            "pbr_workflow": "Weighted Normals + Procedural/Baked PBR",
        }
        clean_tags = [str(t).strip().lower() for t in (tags or []) if str(t).strip()]
        initial_study = study_notes.strip() or f"[{now[:10]}] Accessioned into {museum_wing} ({int_budget} tris target)."

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM relics")
            next_num = cursor.fetchone()[0]
            accession_code = f"ARC-{next_num:04d}"
            while True:
                cursor.execute("SELECT 1 FROM relics WHERE accession_code = ?", (accession_code,))
                if cursor.fetchone() is None:
                    break
                next_num += 1
                accession_code = f"ARC-{next_num:04d}"

            cursor.execute(
                """
                INSERT INTO relics (
                    accession_code, timestamp, name, category, era, museum_wing, rarity,
                    reference_model, lore_description, verified_facts, fact_sources_json,
                    study_notes, research_level, lowpoly_spec_json, blender_workflow,
                    tags_json, curation_status, creation_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    accession_code,
                    now,
                    name,
                    category,
                    era,
                    museum_wing,
                    rarity,
                    reference_model,
                    lore_description,
                    verified_facts or "",
                    json.dumps(fact_sources or []),
                    initial_study,
                    1,
                    json.dumps(lowpoly_spec),
                    blender_workflow or "Block out primary silhouette -> Bevel (Weight) -> Weighted Normal -> Unwrap & Bake AO/Curvature.",
                    json.dumps(clean_tags),
                    curation_status,
                    creation_mode,
                ),
            )
            new_id = cursor.lastrowid
            conn.commit()
            cursor.execute("SELECT * FROM relics WHERE id = ?", (new_id,))
            return self._parse_relic_row(cursor.fetchone())

    def study_or_organize_relic(
        self,
        identifier: str,
        study_addendum: str,
        new_wing: Optional[str] = None,
        new_status: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Deepen archival research on a relic, increment research level, or reorganize its wing/status."""
        now_date = datetime.datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            row = None
            ident = str(identifier or "").strip()

            if ident:
                cursor.execute("SELECT * FROM relics WHERE UPPER(accession_code) = UPPER(?)", (ident,))
                row = cursor.fetchone()
                if row is None and ident.isdigit():
                    cursor.execute("SELECT * FROM relics WHERE id = ?", (int(ident),))
                    row = cursor.fetchone()
                if row is None:
                    cursor.execute("SELECT * FROM relics WHERE LOWER(name) LIKE ? ORDER BY id DESC LIMIT 1", (f"%{ident.lower()}%",))
                    row = cursor.fetchone()

            if row is None:
                cursor.execute("SELECT * FROM relics ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()

            if row is None:
                return None

            existing = dict(row)
            prev_notes = (existing.get("study_notes") or "").strip()
            note_line = f"[{now_date}] {study_addendum.strip()}"
            updated_notes = f"{prev_notes}\n{note_line}".strip() if prev_notes else note_line
            next_level = int(existing.get("research_level") or 1) + 1
            wing = new_wing.strip() if new_wing and new_wing.strip() else existing["museum_wing"]
            status = new_status.strip() if new_status and new_status.strip() else existing["curation_status"]

            cursor.execute(
                """
                UPDATE relics
                SET study_notes = ?, research_level = ?, museum_wing = ?, curation_status = ?
                WHERE id = ?
                """,
                (updated_notes, next_level, wing, status, existing["id"]),
            )
            conn.commit()
            cursor.execute("SELECT * FROM relics WHERE id = ?", (existing["id"],))
            return self._parse_relic_row(cursor.fetchone())

    def get_relics(
        self,
        limit: int = 100,
        wing: Optional[str] = None,
        rarity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve curated relics from the infinitely expanding library with optional filters."""
        clauses = []
        params: List[Any] = []
        if wing:
            clauses.append("LOWER(museum_wing) = LOWER(?)")
            params.append(wing.strip())
        if rarity:
            clauses.append("LOWER(rarity) = LOWER(?)")
            params.append(rarity.strip())

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM relics {where_sql} ORDER BY id DESC LIMIT ?"
        params.append(limit)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [self._parse_relic_row(r) for r in cursor.fetchall()]

    def get_relic_stats(self) -> Dict[str, Any]:
        """Compute summary counts by museum wing and rarity for curator & game integration."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM relics")
            total = cursor.fetchone()[0]

            cursor.execute("SELECT museum_wing, COUNT(*) as cnt FROM relics GROUP BY museum_wing")
            by_wing = {r["museum_wing"]: r["cnt"] for r in cursor.fetchall()}

            cursor.execute("SELECT rarity, COUNT(*) as cnt FROM relics GROUP BY rarity")
            by_rarity = {r["rarity"]: r["cnt"] for r in cursor.fetchall()}

            return {"total": total, "by_wing": by_wing, "by_rarity": by_rarity}
