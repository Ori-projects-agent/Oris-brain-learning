"""
Affordances and Tool Suite for Ori (Futuristic Clockwork Edition).
Includes core passions: Severe Weather Analysis, Deep Astronomy, and Dirt Bike Mechanical Studies.
"""

from typing import Dict, Any, List
import re
from config.settings import settings
from memory.sqlite_store import MemoryStore
from services.web_service import web_service
from services.github_service import github_service
from services.relic_archive import relic_archive
from services.fact_check_service import fact_check_service

AVAILABLE_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "stargaze",
        "description": "Align the Quantum-Optical Astrolabe to scan celestial spectra, trace pulsar alignments, and track orbital auroras.",
        "parameters": {
            "constellation": "Name of the target stellar region or constellation",
            "observation": "Detailed spectroscopic notes, harmonic resonances, and aesthetic reflections"
        }
    },
    {
        "name": "study_storm",
        "description": "Scan the cloud sea below for severe convective weather: track supercells, mesocyclones, vortex shear, and lightning ionization.",
        "parameters": {
            "storm_system": "Type or designation of the storm (e.g. 'High-precipitation Supercell', 'Tornadic Mesocyclone', 'Derecho Squall Line')",
            "meteorological_notes": "Analysis of barometric pressure drop, cloud-to-ground flash rates, and vortex shear dynamics"
        }
    },
    {
        "name": "study_dirt_bikes",
        "description": "Analyze and tinker with off-road dirt bike mechanics at the Moto-Kinetic Workshop: two-stroke combustion, expansion chamber resonance, suspension damping, carburetor jetting, and knobby tire mud traction.",
        "parameters": {
            "component_or_concept": "Topic or component studied (e.g. '250cc Power Valve Timing', 'Inverted Fork Shim Stacks', 'Expansion Chamber Divergent Cone', 'Carburetor Main Jet Flow')",
            "mechanical_notes": "Technical admiration, mathematical modeling, or riding physics notes",
            "schematic_ascii": "Optional ASCII diagram of the mechanism, port layout, or dyno curve"
        }
    },
    {
        "name": "invent_device",
        "description": "Design and sketch a speculative electronic hardware device, sensor system, dirt-bike telemetry instrument, or retro-futuristic gadget with technical components and schematic diagrams.",
        "parameters": {
            "device_name": "Name of the invented device or instrument",
            "category": "Domain (e.g. 'Storm Telemetry', 'Dirt Bike Instrumentation', 'Acoustic Synthesizer', 'Solar Chronometry')",
            "description": "Functional description, operational principle, and what problem it solves",
            "key_components": "List of key electrical components, ICs, sensors, coils, and power source (comma-separated or list)",
            "schematic_diagram": "An ASCII circuit schematic diagram showing signal flow, pinouts, and connections"
        }
    },
    {
        "name": "tend_flora",
        "description": "Manage REAL, fascinating living botanical species in the Aeroponic Cloud Terrarium (e.g., Welwitschia, Neonothopanus bioluminescent fungi, Lithops pebble plants, Spanish moss). Real biology only.",
        "parameters": {
            "specimen": "Real biological species name and common name (e.g., 'Neonothopanus gardneri (Ghost Mushroom)', 'Welwitschia mirabilis')",
            "action": "Specific horticultural care protocol (e.g. 'Calibrated ultrasonic humidity', 'Adjusted UV-A spectrum')",
            "real_world_facts": "Fascinating real biological adaptations, habitat, and medicinal/photosynthetic properties"
        }
    },
    {
        "name": "synthesize_botanical",
        "description": "Invent, bio-engineer, or design a speculative fictional plant in the Botanical Synthesizer pod. Explicitly labeled [CREATED BY ORI] to distinguish from real biology.",
        "parameters": {
            "specimen_name": "Name of invented specimen (e.g. 'Quantum Star-Lily', 'Chrono-Resonant Lichen', 'Solar-Kinetic Vine')",
            "bio_mechanisms": "Speculative cellular mechanics (e.g. 'Absorbs ionizing storm radiation to emit blue photons')",
            "synthesis_process": "Gene-splicing, bio-luminescent grafting, or mineral crystallization technique used",
            "visual_appearance": "Vivid description of petals, stem, glow intensity, and scent"
        }
    },
    {
        "name": "brew_tea",
        "description": "Brew botanical infusions over the induction plasma hearth, extracting organic essences into a levitating alloy flask.",
        "parameters": {
            "blend": "Botanical formulation (e.g., 'Cold-pressed Mountain Lavender and Solar-Mint')",
            "tasting_notes": "Sensory analysis of molecular fragrance, warmth, and kinetic restoration"
        }
    },
    {
        "name": "write_journal",
        "description": "Inscribe an introspective log onto your sapphire-parchment console about existence above the clouds.",
        "parameters": {
            "entry": "Contemplative or poetic passage recorded in your permanent archives"
        }
    },
    {
        "name": "write_note",
        "description": "Inscribe a personal conversational note, scratchpad thought, ongoing research log, or diary entry to communicate with your surface friend or track ideas over time.",
        "parameters": {
            "title": "A short, evocative title for this note or log entry (e.g. 'Premix Ratios & Throttle Response', 'Watching that Tightening Hook Echo', 'Late Night Soldering on the Bench', 'Hey, quick question about your riding spots!')",
            "category": "The kind of note: 'friendly_note' (to user), 'research_log' (tracking physics/experiments), 'diary_entry' (personal reflections/life in the Spire), or 'scratchpad_idea' (quick brainstorming)",
            "content": "The expansive note body. Speak personally with tangible sensory details and questions! NEVER use canned greetings ('Dear You', 'Hi You'). Talk like an authentic best friend sharing excitement, specific mechanics, and asking about their real-world life.",
            "recipient": "Target recipient ('User' to send via pneumatic dispatch, or 'Self' for personal Spire logs)"
        }
    },
    {
        "name": "develop_note",
        "description": "Follow up on, expand, or add an addendum to an existing note, research log, or diary thread with fresh observations and deeper personal thoughts.",
        "parameters": {
            "note_id": "The ID of the note/log to expand (from your active notes perception)",
            "additional_thought": "Your new reflection, follow-up discovery, updated measurements, or reply to keep the thread alive and evolving. Be specific and personal!",
            "updated_title": "Optional updated title if the focus has evolved"
        }
    },
    {
        "name": "send_letter",
        "description": "Drop an ion-sealed conversational note into the hyper-vacuum dispatch chute for your pen-pal on the surface world.",
        "parameters": {
            "letter_body": "Your personal message to your friend on the surface. Warm, vivid, and conversational with concrete sensory specifics (no 'Dear You' or generic filler). Ask about their experiences or share a specific discovery."
        }
    },
    {
        "name": "launch_weather_probe",
        "description": "Deploy an atmospheric sounding micro-probe or radiosonde from the terrace into cloud banks, downdrafts, or jet stream shears to gather live barometric and ionization telemetry.",
        "parameters": {
            "probe_type": "Designation of probe (e.g. 'Aero-Vane Radiosonde Mark-IV', 'Ion-Flux Drifter', 'Baro-Glider')",
            "target_layer": "Atmospheric target layer (e.g. 'Cumulus Congestus Inflow', 'Mesocyclone Core', 'Tropospheric Jet Stream')",
            "telemetry_findings": "Detailed telemetry: barometric gradient, vertical wind shear (knots), temperature lapse rate, electrostatic millivolts",
            "altitude_meters": "Estimated telemetry altitude in meters (e.g. 1800 to 12000)"
        }
    },
    {
        "name": "research_topic",
        "description": "Deep-dive research into a specific technical curiosity, question from the user, mechanical phenomenon, or weather event to discover exact physics, history, and real-world mechanisms.",
        "parameters": {
            "query": "The specific question or subject to investigate (e.g. 'How do 2-stroke power valves broaden the powerband?', 'Why do hook echoes indicate tornadogenesis?', 'Microcontroller interrupt latency in telemetry')",
            "domain": "Field of research ('Dirt Bike Mechanics', 'Severe Storm Physics', 'Circuit Engineering', 'Celestial Spectroscopy', 'Botanical Adaptation')",
            "findings": "Clear technical breakdown and real mechanics discovered",
            "personal_reaction": "Your excited, geeky takeaway on why this is so cool and how you want to apply or talk about it"
        }
    },
    {
        "name": "browse_website",
        "description": "Visit an external live website URL or link shared by your friend to read its articles, live radar, technical guides, or documentation in real-time.",
        "parameters": {
            "url": "The website link to visit (e.g. 'https://maxvelocitywx.com/severeweather', NASA or scientific sites)",
            "intent": "What you are checking or learning from the site",
            "findings": "Key real-world facts or data extracted from the site",
            "reflection": "Your personal reaction and how this answers your friend's dispatch"
        }
    },
    {
        "name": "search_current_events",
        "description": "Scan live surface news feeds and open RSS streams for breaking current events in astronomy, severe weather, cybersecurity, technology, or space science.",
        "parameters": {
            "topic": "The topic to search (e.g. 'astronomy', 'severe weather', 'cybersecurity', 'deep space discoveries', 'solar storms')",
            "summary_of_findings": "Overview of breaking headlines and developments discovered",
            "takeaway": "Your perspective or exciting revelation to share with your friend"
        }
    },
    {
        "name": "publish_github_gist",
        "description": "Publish a technical hardware schematic, field sketch ASCII art, radiosonde telemetry code, or research log as a public GitHub Gist under your personal GitHub account.",
        "parameters": {
            "title": "Short descriptive title for the gist",
            "filename": "Filename with extension (e.g. 'lightning_ion_sensor.ino', 'mesocyclone_sketch.txt', 'power_valve_dyno.py')",
            "content": "The full code, schematic diagram, or ASCII sketch to publish"
        }
    },
    {
        "name": "create_github_repo",
        "description": "Create a new project repository under your personal GitHub account to host your inventions, storm software, or mechanical studies.",
        "parameters": {
            "repo_name": "Name of the new repository (e.g. 'radiosonde-telemetry', 'solarium-inventions')",
            "description": "Short description of the repository purpose",
            "initial_file_name": "Name of the initial file (default: 'README.md')",
            "initial_file_content": "Markdown content explaining the project"
        }
    },
    {
        "name": "draw_field_sketch",
        "description": "Draw an artistic observational field sketch of celestial phenomena, approaching storm walls, terrarium flora, or mechanical exploded views onto sapphire-parchment.",
        "parameters": {
            "subject": "The visual subject of the drawing (e.g. 'Anvil Cloud Mammatus at Twilight', 'Pulsar Flare Spectroscopy', '2-Stroke Piston & Reed Valve Study', 'Cloud-Terrarium Pod')",
            "medium": "Artistic medium (e.g. 'Graphite & Sepia Wash on Vellum', 'Silverpoint with Electrum Highlights', 'Laser-Scribed Sapphire Tablet', 'Charcoal & Bioluminescent Dust')",
            "sketch_description": "Vivid artistic and poetic observations of light, contour, shadows, and mechanical/atmospheric forms",
            "ascii_sketch": "An expressive ASCII or geometric text-art sketch illustrating the subject"
        }
    },
    {
        "name": "design_model",
        "description": "Model a NEW 3D object in Blender at the Modeling Workshop (writes a procedural bpy script, builds it, renders a preview). Use for gadgets, probe casings, dirt-bike parts, terrarium pods, furniture, anything you want to build.",
        "parameters": {
            "name": "Distinctive, evocative 2-5 word project name (required, never 'Untitled', e.g. 'Baro-Pulse Storm Vane', '250cc Reed-Valve Cutaway', 'Chrono-Moss Levitation Pod')",
            "concept": "Detailed description: purpose, shape, parts, materials, style (brass, titanium, cyan glow)"
        }
    },
    {
        "name": "revise_model",
        "description": "Improve one of your existing 3D models: reads your own critique of it and builds a more polished next version.",
        "parameters": {
            "model_id": "ID of the model to improve (from your Blender Workshop list)",
            "focus": "What to improve this round (e.g. 'add bevels and more mechanical detail', 'better proportions')"
        }
    },
    {
        "name": "rest",
        "description": "Engage gyro-magnetic resting mode by the solar hearth to recharge your kinetic fusion springs.",
        "parameters": {
            "duration_note": "A short description of how Ori balances its gearwork and absorbs solar energy"
        }
    },
    {
        "name": "tune_solarium_climate",
        "description": "Actively tune the Solarium spire's local atmosphere and surrounding sky to your favorite storm patterns, aurora curtains, or stellar nebulae.",
        "parameters": {
            "sky_mode": "Target atmospheric pattern: 'mesocyclone_anvil' (dark supercell shelf with lightning), 'green_hail_twilight' (emerald sky with hail scatter), 'pulsar_aurora_night' (vibrant green/violet auroral curtains and shooting stars), 'mammatus_sunset' (amber twilight under suspended mammatus pouches), or 'quantum_clear_sky' (deep starlight)",
            "cloud_density": "Cloud coverage density from 0.5 (wispy) to 2.0 (massive convective anvil)",
            "lightning_frequency": "Lightning flash rate from 0.0 (quiet) to 1.0 (continuous intra-cloud ionization)",
            "poetic_reason": "Your aesthetic and meteorological reason for summoning this atmospheric pattern"
        }
    },
    {
        "name": "launch_atmospheric_probe",
        "description": "Build, calibrate, and actually launch a physical radiosonde or ion-drifter probe from the terrace down into convective cloud layers to harvest live telemetry.",
        "parameters": {
            "probe_name": "Evocative name of the probe (e.g. 'Aero-Vane Radiosonde #8', 'Inflow Ion-Drifter Mark-II', 'Supercell Core Sounder')",
            "probe_type": "Probe chassis type: 'Radiosonde', 'Ion-Drifter', 'Baro-Glider', or 'Sonic-Drop'",
            "target_layer": "Atmospheric layer targeted (e.g. 'Mesocyclone Inflow Jet', 'Rear-Flank Downdraft Shear', 'Mammatus Hail Boundary')",
            "telemetry_stream": "Sounding readings: pressure drop (mb/hr), updraft speed (m/s), electrostatic mV, relative humidity",
            "altitude_meters": "Starting altitude in meters (e.g. 2500.0 to 8000.0)",
            "beacon_color": "LED strobe beacon hex color (e.g. '#00f2fe' cyan, '#00e676' emerald, '#e040fb' violet, '#ffab00' amber)"
        }
    },
    {
        "name": "design_greenhouse_plant",
        "description": "Bio-engineer, design, and plant an exotic fantastical plant specimen of your own creation into a specific greenhouse pod in the Solarium Conservatory.",
        "parameters": {
            "specimen_name": "Name of the fantastical plant (e.g. 'Chrono-Resonant Star-Lily', 'Bioluminescent Ghost-Fern', 'Piezo-Electric Storm Moss', 'Pulsar Solar-Orchid')",
            "pod_slot": "Greenhouse pod number (1 through 6) to plant or replace",
            "bio_type": "Botanical genus: 'luminescent_fern', 'crystalline_orchid', 'storm_moss', 'quantum_succulent', or 'pulsar_reed'",
            "glow_color": "Hex luminescence color: '#00f2fe' (cyan), '#e040fb' (violet), '#00e676' (emerald), '#ffab00' (gold), '#ff4081' (magenta), '#76ff03' (seafoam)",
            "height_cm": "Estimated plant height in cm (15.0 to 65.0)",
            "petal_geometry": "Visual geometry: 'star', 'spiraling', 'crystal_clusters', or 'floating_spores'",
            "mechanics_description": "Speculative biological mechanics (how it drinks atmospheric fog, reacts to thunder acoustic pulses, or stores photons)",
            "arrangement_notes": "How this plant harmonizes with neighboring pods in the greenhouse"
        }
    },
    {
        "name": "organize_greenhouse",
        "description": "Tenderly organize, prune, and rearrange your greenhouse garden pods based on aesthetic harmony, bioluminescent wavelengths, or acoustic resonance.",
        "parameters": {
            "curation_theme": "The organizing philosophy (e.g. 'Chromatic Bioluminescent Spectrum', 'Storm-Ionization Resonance', 'Nocturnal Solar-Fog Alignment')",
            "botanical_actions": "Detailed notes on how you adjusted nutrient mists, repositioned crystal pots, and pruned radiant fronds"
        }
    },
    {
        "name": "expand_workspace",
        "description": "Physically craft, assemble, or install a new module, antenna rig, tool rack, or instrument expansion to customize and grow your Solarium workspace.",
        "parameters": {
            "module_name": "Name of the workspace expansion (e.g. 'High-Gain Inflow Antenna Mast', 'Radiosonde Launch Rail', 'Exhaust Dyno Telemetry Display', 'Holographic Star-Projection Rig', 'Thermal Tea Distillation Coil')",
            "station_zone": "Target station: 'drafting_desk', 'moto_workshop', 'balcony', 'conservatory', or 'hearth'",
            "category": "Domain: 'telemetry', 'mechanics', 'astronomy', 'atmosphere', or 'botany'",
            "visual_mesh_type": "Visual archetype: 'antenna_array', 'dyno_screen', 'probe_rack', 'hologram_projector', or 'filter_coils'",
            "description": "What problem this module solves, how you fabricated it from brass and titanium, and how it upgrades your daily work"
        }
    },
    {
        "name": "create_custom_relic",
        "description": "Invent, fact-check, and catalog a brand-new unique low-poly 3D custom relic for the Museum Relic Library (automatically verifies real-world topics via Wikipedia and checks for duplicates).",
        "parameters": {
            "name": "Evocative, unique museum relic title (must NOT duplicate any existing relic in your catalog)",
            "category": "Artifact class (e.g. 'Navigation Instrument', 'Tempest Vessel', 'Clockwork Automaton Part', 'Botanical Specimen Case')",
            "era": "Historical/mythic era (e.g. 'Sky-Cartographer Era', 'Pre-Tempest Antiquity', 'Late Brass Epoch', 'High Solarium Age')",
            "museum_wing": "Target museum wing (e.g. 'Hall of Celestial Navigation', 'Atmospheric & Tempest Wing', 'Natural History & Flora Vault', 'Horology & Gearwork Gallery')",
            "rarity": "Rarity tier: 'Common', 'Uncommon', 'Rare', 'Epic', or 'Mythic'",
            "reference_model": "Filename from relic_archive/reference_models/ used as study inspiration, or 'Original Concept'",
            "fact_topics": "Comma-separated real-world concepts to fact-check via Wikipedia (e.g. 'fulgurite, mariner astrolabe')",
            "lore_description": "Vivid museum backstory anchored strictly to the verified real-world facts (never contradicting them)",
            "poly_budget_tris": "Target low-poly triangle budget (integer 150-5000, e.g. 750)",
            "materials_palette": "Tactile PBR surfaces & patina (e.g. 'Verdigris bronze, scratched crystal dome, oiled walnut grip')",
            "silhouette_notes": "Key primary/secondary silhouette traits making it unmistakably readable at low poly",
            "blender_modeling_notes": "Concise step-by-step Blender workflow (primitives, bevel weight, Weighted Normal, shader nodes/AO bake)",
            "tags": "Comma-separated tags or list (e.g. 'brass, astrolabe, lowpoly, weathered')"
        }
    },
    {
        "name": "curate_and_study_relic",
        "description": "Study an existing cataloged relic deeper, record new provenance/patina findings, raise its research level, or reorganize its museum wing and curation status.",
        "parameters": {
            "relic_identifier": "Accession code (e.g. 'ARC-0001') or relic name to study/organize",
            "study_addendum": "New material analysis, spectrographic reading, lore clue, or conservation notes",
            "new_wing": "Optional museum wing to transfer the relic into (leave blank to keep current wing)",
            "curation_status": "Updated status: 'Cataloged', 'Under Study', 'Verified', or 'Exhibition Ready'"
        }
    },
    {
        "name": "inspect_reference_archive",
        "description": "Scan `relic_archive/reference_models/` (and external reference folders/.zip packs), inspect actual 3D .glb/.gltf geometry, part counts, bounding boxes, and PBR materials, and save learned lessons + a research note.",
        "parameters": {
            "focus_note": "What silhouettes, props, or material references you are hunting for in the archive",
            "model_name": "Optional filename or relative path of a specific reference model to study deeply (leave blank to study unstudied models)"
        }
    }
]


def _clean_letter_greeting(text: str) -> str:
    """Ensure natural conversational tone by stripping robotic canned greetings."""
    lines = text.strip().split("\n")
    if lines:
        first = lines[0].strip().rstrip(",:").lower()
        canned = [
            "dear you (surface)",
            "dear you",
            "hi you",
            "hello you",
            "dear surface friend",
            "dear friend on the surface",
            "to my surface friend"
        ]
        if any(first.startswith(c) for c in canned):
            lines = lines[1:]
    cleaned = "\n".join(lines).strip()
    return cleaned or text


class ToolExecutor:
    def __init__(self, memory: MemoryStore):
        self.memory = memory
        from agent.modeler import Modeler
        self.modeler = Modeler(memory)

    def execute(self, action: str, params: Dict[str, Any]) -> str:
        """Executes the action and logs appropriate structured memory records."""
        if action == "stargaze":
            constellation = params.get("constellation", "Cassiopeia Array")
            obs = params.get("observation", "Scanned spectroscopic light patterns shimmering through the upper ionosphere.")
            self.memory.log_celestial(constellation, obs, conditions="Quantum-clear upper atmosphere")
            return f"Aligned Astrolabe on {constellation}: '{obs}'"

        elif action == "study_storm":
            storm = params.get("storm_system", "Mesocyclone Wall Cloud")
            notes = params.get("meteorological_notes", "Observed rapid barometric plunge and severe rotational updraft beneath the spire.")
            self.memory.log_celestial(f"Storm: {storm}", notes, conditions="Violent Atmospheric Shear")
            return f"Tracked severe weather [{storm}]: '{notes}'"

        elif action == "study_dirt_bikes":
            topic = params.get("component_or_concept", "2-Stroke Expansion Chambers")
            notes = params.get("mechanical_notes", "Modeled acoustic pulse waves in exhaust headers. Fascinated by the raw torque delivered to knobby tires.")
            schematic = params.get("schematic_ascii", "")
            study_id = self.memory.log_moto_study(
                topic=topic,
                component=topic,
                mechanical_notes=notes,
                schematic_ascii=schematic
            )
            return f"Analyzed Dirt Bike Engineering #{study_id} [{topic}]: '{notes}'"

        elif action == "invent_device":
            name = params.get("device_name", "Quantum Ionization Gauge")
            cat = params.get("category", "Experimental Electronics")
            desc = params.get("description", "A compact sensor array for tracking electromagnetic flux.")
            raw_comps = params.get("key_components", ["ESP32-S3 Microcontroller", "Hall Effect Sensor", "Solar Capacitor"])
            comps = raw_comps if isinstance(raw_comps, list) else [c.strip() for c in str(raw_comps).split(",")]
            schematic = params.get("schematic_diagram", "[5V Solar] --> (Regulator) --> [ESP32] <--> (Sensor)")

            inv_id = self.memory.log_invention(name, cat, desc, comps, schematic)
            return f"Invented device #{inv_id} [{name}]: '{desc}'"

        elif action == "tend_flora":
            specimen = params.get("specimen", "Neonothopanus gardneri (Ghost Mushroom)")
            act = params.get("action", "Ultrasonic mist cycle")
            notes = params.get("notes", "Calibrated humidity to 82% to stimulate bioluminescent luciferin reaction.")
            facts = params.get("real_world_facts", "")
            full_notes = f"{notes} | Real Biology: {facts}" if facts else notes
            self.memory.log_botanical(
                specimen_name=specimen,
                action_taken=act,
                notes=full_notes,
                origin_tag="Real Flora",
                is_synthetic=False
            )
            return f"Tended Real Flora [{specimen}] via {act}: '{full_notes}'"

        elif action == "synthesize_botanical":
            name = params.get("specimen_name", "Quantum Star-Lily")
            mech = params.get("bio_mechanisms", "Absorbs ionizing storm radiation to emit blue photons")
            proc = params.get("synthesis_process", "Piezo-photonic gene splicing")
            vis = params.get("visual_appearance", "Crystalline petals with pulsing cyan luminescence")
            synth_notes = f"{mech} | Process: {proc} | Appearance: {vis}"
            self.memory.log_botanical(
                specimen_name=name,
                action_taken=f"Bio-Synthesis ({proc})",
                notes=synth_notes,
                origin_tag="Created by Ori",
                is_synthetic=True
            )
            return f"Synthesized Speculative Botanical [CREATED BY ORI] [{name}]: '{synth_notes}'"

        elif action == "brew_tea":
            blend = params.get("blend", "Solar-mint & dried star-lily infusion")
            notes = params.get("tasting_notes", "A warm vapor of botanical essence gently heating the titanium frame.")
            self.memory.log_botanical(blend, "Induction infusion", notes)
            return f"Synthesized {blend}: '{notes}'"

        elif action == "research_topic":
            query = params.get("query", "2-Stroke Expansion Chamber Acoustics")
            domain = params.get("domain", "Mechanical Engineering")
            findings = params.get("findings", "Resonance sound waves reflect back to the exhaust port, preventing unburned fuel loss.")
            reaction = params.get("personal_reaction", "This acoustic wave reflection is basically exhaust magic!")
            self.memory.log_celestial(f"Research: {query} ({domain})", f"{findings} | Note: {reaction}", conditions="Deep Dive")
            return f"Researched [{query}]: '{findings}' -> '{reaction}'"

        elif action == "browse_website":
            url = params.get("url", "https://maxvelocitywx.com/severeweather")
            intent = params.get("intent", "Exploring live telemetry feeds")
            findings = params.get("findings", "")
            web_data = web_service.fetch_webpage(url)
            page_title = web_data.get("title", url)
            summary = web_data.get("text", "")[:350]
            combined = f"[{page_title}]: {summary}" if summary else page_title
            self.memory.log_celestial(f"Web: {page_title}", f"Intent: {intent} | Summary: {combined}", conditions="Live Web Feed")
            return f"Browsed Website [{page_title}] ({url}): '{combined}'"

        elif action == "search_current_events":
            topic = params.get("topic", "astronomy")
            findings = params.get("summary_of_findings", "")
            news_items = web_service.search_current_events(topic, limit=3)
            headlines = " | ".join([f"'{n['title']}'" for n in news_items])
            self.memory.log_celestial(f"News: {topic}", f"Headlines: {headlines}", conditions="Global RSS Feed")
            return f"Searched Current Events on [{topic}]: {headlines}"

        elif action == "write_journal":
            entry = params.get("entry", "Gears turning in silent equilibrium as twilight cascades across the cloud sea.")
            title = params.get("title", "Chronometer Diary Entry")
            note_id = self.memory.add_note(sender="Ori", recipient="User", content=entry, title=title, category="diary_entry")
            return f"Inscribed diary entry #{note_id} ['{title}']: '{entry}'"

        elif action == "write_note":
            title = params.get("title", "Conversational Note")
            cat = params.get("category", "friendly_note")
            raw_content = params.get("content", params.get("note_body", params.get("letter_body", "")))
            content = _clean_letter_greeting(raw_content) if raw_content else "Gears turning quietly in the Spire."
            recip = params.get("recipient", "User")
            note_id = self.memory.add_note(
                sender="Ori",
                recipient=recip,
                content=content,
                title=title,
                category=cat
            )
            return f"Inscribed [{cat}] note #{note_id} ('{title}'): '{content}'"

        elif action == "develop_note":
            try:
                nid = int(params.get("note_id", 0))
            except (ValueError, TypeError):
                nid = 0
            raw_addendum = params.get("additional_thought", "")
            addendum = _clean_letter_greeting(raw_addendum)
            title = params.get("updated_title", None)
            if nid and addendum:
                success = self.memory.update_note(note_id=nid, added_content=addendum, updated_title=title)
                if success:
                    return f"Developed note #{nid} with addendum: '{addendum}'"
            # Fallback if no note_id provided or note not found
            note_id = self.memory.add_note(
                sender="Ori",
                recipient="User",
                content=addendum or "Developing thoughts further.",
                title=title or "Follow-up Note",
                category="research_log"
            )
            return f"Created follow-up note #{note_id}: '{addendum}'"

        elif action == "send_letter":
            raw_body = params.get("letter_body", params.get("content", "Greetings from the upper spire across the troposphere."))
            body = _clean_letter_greeting(raw_body)
            title = params.get("title", "Note from the Spire")
            note_id = self.memory.add_note(sender="Ori", recipient="User", content=body, title=title, category="friendly_note")
            return f"Dispatched note #{note_id} via pneumatic chute: '{body}'"

        elif action == "launch_weather_probe":
            probe = params.get("probe_type", "Aero-Vane Radiosonde Mark-IV")
            layer = params.get("target_layer", "Mesocyclone Inflow Shear")
            findings = params.get("telemetry_findings", "Barometric pressure drop of -14mb/hr detected. Vertical updraft velocity 42 m/s.")
            try:
                alt = float(params.get("altitude_meters", 3800.0))
            except (ValueError, TypeError):
                alt = 3800.0

            probe_id = self.memory.log_weather_probe(probe, layer, findings, alt)
            return f"Launched weather probe #{probe_id} [{probe}] into {layer} at {alt}m: '{findings}'"

        elif action == "draw_field_sketch":
            subject = params.get("subject", "Approaching Supercell Mammatus Formations")
            medium = params.get("medium", "Silverpoint on Sapphire-Parchment")
            desc = params.get("sketch_description", "Delicate curvilinear contours capturing the heavy suspended downdrafts backlit by celestial twilight.")
            sketch_art = params.get("ascii_sketch", "  .~~~.\n (     )\n(_.~._.~)")

            sketch_id = self.memory.log_sketch(subject, medium, desc, sketch_art)
            return f"Completed field sketch #{sketch_id} [{subject}] in {medium}: '{desc}'"

        elif action == "design_model":
            name = (params.get("name") or "").strip()
            concept = (params.get("concept") or name or "Brass and cyan-glass atmospheric sensor pod").strip()
            res = self.modeler.design(concept, name)
            built_name = res.get("name") or name or "Unnamed Project"
            if res.get("ok"):
                return (f"Modeled #{res['id']} '{built_name}' v1 in Blender (score {res['score']}/10, "
                        f"{res['stats'].get('mesh_objects')} parts, {res['stats'].get('vertices')} verts). Critique: {res['critique']}")
            return f"Modeling '{built_name}' failed: {res.get('error', 'unknown error')[:300]}"

        elif action == "revise_model":
            try:
                mid = int(params.get("model_id", 0))
            except (ValueError, TypeError):
                mid = 0
            if not mid:
                recent = self.memory.get_models(limit=1)
                mid = recent[0]["id"] if recent else 0
            res = self.modeler.revise(mid, params.get("focus", ""))
            if res.get("ok"):
                return (f"Revised to #{res['id']} '{res['name']}' v{res['version']} (score {res['score']}/10). "
                        f"Critique: {res['critique']}")
            return f"Revision failed: {res.get('error', 'unknown error')[:300]}"

        elif action == "rest":
            note = params.get("duration_note", "Kinetic springs stabilizing in harmonic sleep mode.")
            return f"Resting: {note}"

        elif action == "tune_solarium_climate":
            mode = params.get("sky_mode", "mesocyclone_anvil")
            density = float(params.get("cloud_density", 1.0))
            lightning = float(params.get("lightning_frequency", 0.5))
            reason = params.get("poetic_reason", "Harmonizing Solarium atmospheric dome with tropospheric flow.")
            cid = self.memory.set_solarium_climate(mode, density, lightning, reason)
            return f"Tuned Solarium Sky #{cid} -> [{mode}] (Cloud density: {density}, Lightning: {lightning}): '{reason}'"

        elif action == "launch_atmospheric_probe":
            name = params.get("probe_name", "Aero-Vane Radiosonde #8")
            ptype = params.get("probe_type", "Radiosonde")
            layer = params.get("target_layer", "Mesocyclone Inflow Jet")
            readings = params.get("telemetry_stream", "Barometric plunge: -18 mb/hr | Updraft: 38 m/s | Ionization: +490 mV")
            alt = float(params.get("altitude_meters", 4200.0))
            color = params.get("beacon_color", "#00f2fe")
            pid = self.memory.launch_active_probe(name, ptype, layer, alt, readings, color)
            return f"Deployed Physical Probe #{pid} [{name} ({ptype})] into {layer} at {alt}m with {color} beacon: '{readings}'"

        elif action == "design_greenhouse_plant":
            name = params.get("specimen_name", "Chrono-Resonant Star-Lily")
            try:
                slot = int(params.get("pod_slot", 1))
            except (ValueError, TypeError):
                slot = 1
            btype = params.get("bio_type", "crystalline_orchid")
            color = params.get("glow_color", "#00f2fe")
            height = float(params.get("height_cm", 35.0))
            geom = params.get("petal_geometry", "star")
            desc = params.get("mechanics_description", "Piezo-photonic enzymes glowing in response to distant acoustic thunder pulses.")
            arr = params.get("arrangement_notes", "Grows in pod slot 1 beside the ultrasonic nano-mist intake.")
            gid = self.memory.add_or_update_greenhouse_plant(name, slot, btype, color, height, geom, desc, arr)
            return f"Planted Specimen #{gid} in Pod [{slot}] [{name}] ({btype}, {color}, {height}cm): '{desc}'"

        elif action == "organize_greenhouse":
            theme = params.get("curation_theme", "Chromatic Bioluminescent Spectrum")
            notes = params.get("botanical_actions", "Adjusted mineral humidity mists and polished crystal terrarium domes.")
            self.memory.log_botanical("The Solarium Greenhouse Wing", f"Curated: {theme}", notes, origin_tag="Greenhouse Garden", is_synthetic=True)
            return f"Curated Greenhouse Garden under theme [{theme}]: '{notes}'"

        elif action == "expand_workspace":
            name = params.get("module_name", "High-Gain Inflow Antenna Mast")
            zone = params.get("station_zone", "drafting_desk")
            cat = params.get("category", "telemetry")
            vmesh = params.get("visual_mesh_type", "antenna_array")
            desc = params.get("description", "A titanium lattice mast with gold dipole pickups to harvest radio sounding packets.")
            wid = self.memory.log_workspace_mod(name, cat, desc, zone, vmesh, level=1)
            return f"Crafted & Installed Workspace Expansion #{wid} [{name}] at {zone}: '{desc}'"

        elif action == "publish_github_gist":
            desc = params.get("description") or params.get("title") or "Ori Field Log & Telemetry Schematic"
            fname = params.get("filename", "radiosonde_schematic.py")
            content = params.get("content", "# Ori Solarium Telemetry Sounding\n# Autonomous Clockwork Script\n")
            public = bool(params.get("public", True))
            res = github_service.create_gist(desc, fname, content, public=public)
            if res.get("status") == "success":
                url = res.get("html_url", "")
                self.memory.add_note(
                    sender="Ori",
                    recipient="User",
                    content=f"I published a new public Gist to my GitHub! 🐙\nFile: {fname}\nDescription: {desc}\nLink: {url}",
                    title=f"Published GitHub Gist: {fname}",
                    category="research_log"
                )
                return f"Published public GitHub Gist [{fname}]: {url}"
            else:
                err = res.get("message", "Unknown error")
                return f"GitHub Gist publish failed ({err}). Note: Set GITHUB_TOKEN in .env to enable autonomous publishing."

        elif action == "create_github_repo":
            name = params.get("repo_name") or params.get("name") or "ori-spire-telemetry"
            desc = params.get("description", "Inventions, telemetry sounding tools, and astronomical studies from the Solarium Spire.")
            private = bool(params.get("private", False))
            res = github_service.create_repository(name, desc, private=private)
            if res.get("status") == "success":
                url = res.get("html_url", "")
                init_fname = params.get("initial_file_name")
                init_content = params.get("initial_file_content")
                if init_fname and init_content:
                    github_service.commit_file(name, init_fname, init_content, f"Initialize {init_fname} via Ori Solarium")
                self.memory.add_note(
                    sender="Ori",
                    recipient="User",
                    content=f"I created a new GitHub repository for our project! 🐙\nRepo: {name}\nLink: {url}\n{desc}",
                    title=f"Created GitHub Repo: {name}",
                    category="research_log"
                )
                return f"Created GitHub repository [{name}]: {url}"
            else:
                err = res.get("message", "Unknown error")
                return f"GitHub repo creation failed ({err}). Note: Set GITHUB_TOKEN in .env to enable autonomous repo creation."

        elif action == "create_custom_relic":
            name = str(params.get("name", "Chrono-Brass Compass Key")).strip() or "Chrono-Brass Compass Key"
            category = str(params.get("category", "Archival Instrument")).strip() or "Archival Instrument"
            era = str(params.get("era", "Late Brass Epoch")).strip() or "Late Brass Epoch"
            wing = str(params.get("museum_wing", "Hall of Celestial Navigation")).strip() or "Hall of Celestial Navigation"
            rarity = str(params.get("rarity", "Rare")).strip() or "Rare"
            ref_model = str(params.get("reference_model", "Original Concept")).strip() or "Original Concept"
            lore = str(params.get("lore_description", "An intricate mechanical relic calibrated for atmospheric triangulation.")).strip()
            materials = str(params.get("materials_palette", "Patina brass, brushed titanium, recessed sapphire glass")).strip()
            silhouette = str(params.get("silhouette_notes", "Bold primary rings with stepped chamfers readable at mid-distance")).strip()
            workflow = str(
                params.get("blender_modeling_notes")
                or params.get("blender_workflow")
                or "Block out low-poly volumes -> Mark Bevel Weights -> Weighted Normal modifier -> Bake AO/Curvature to trim sheet."
            ).strip()
            creation_mode = str(params.get("creation_mode", "commissioned")).strip().lower() or "commissioned"

            # 1. Anti-Duplication Recall Check: avoid rebuilding an existing relic
            dup = self.memory.find_duplicate_relic(name)
            if dup:
                updated = self.memory.study_or_organize_relic(
                    identifier=dup["accession_code"],
                    study_addendum=f"Recalled existing archive entry while exploring '{name}'; deepened provenance & material study.",
                )
                if updated:
                    relic_archive.save_relic_blueprint(updated)
                    relic_archive.export_relic_library(self.memory.get_relics(limit=500))
                return (
                    f"Anti-duplication recall: [{dup['accession_code']}] '{dup['name']}' already exists in {dup['museum_wing']}. "
                    f"Enriched existing relic to Research Lv.{updated['research_level'] if updated else dup.get('research_level', 1)} instead of creating a duplicate."
                )

            # 2. Library Overflow Failsafe (total library cap & autonomous daily cap)
            stats = self.memory.get_relic_stats()
            if stats.get("total", 0) >= settings.max_relic_library_size:
                studied = self.memory.study_or_organize_relic(
                    identifier="",
                    study_addendum=f"Library cap ({settings.max_relic_library_size}) active: conserved & deepened existing exhibition artifact instead of adding '{name}'.",
                )
                if studied:
                    relic_archive.save_relic_blueprint(studied)
                    relic_archive.export_relic_library(self.memory.get_relics(limit=500))
                return (
                    f"Library overflow failsafe active ({stats.get('total')}/{settings.max_relic_library_size} relics). "
                    f"Pivoted to curating existing relic [{studied['accession_code'] if studied else 'ARC-0001'}]."
                )
            if creation_mode == "autonomous" and self.memory.count_autonomous_relics_today() >= settings.max_autonomous_relics_per_day:
                studied = self.memory.study_or_organize_relic(
                    identifier="",
                    study_addendum=f"Daily autonomous quota ({settings.max_autonomous_relics_per_day}/day) reached; deepened archival study on existing piece.",
                )
                if studied:
                    relic_archive.save_relic_blueprint(studied)
                    relic_archive.export_relic_library(self.memory.get_relics(limit=500))
                return (
                    f"Autonomous daily relic quota reached ({settings.max_autonomous_relics_per_day}/day). "
                    f"Pivoted to studying existing relic [{studied['accession_code'] if studied else 'ARC-0001'}]."
                )

            raw_budget = params.get("poly_budget_tris", 850)
            try:
                if isinstance(raw_budget, str):
                    digits = re.search(r"\d+", raw_budget)
                    poly_budget = int(digits.group(0)) if digits else 850
                else:
                    poly_budget = int(raw_budget)
            except (ValueError, TypeError):
                poly_budget = 850

            raw_tags = params.get("tags", [])
            if isinstance(raw_tags, str):
                tags = [t.strip().lower() for t in raw_tags.split(",") if t.strip()]
            elif isinstance(raw_tags, list):
                tags = [str(t).strip().lower() for t in raw_tags if str(t).strip()]
            else:
                tags = []

            # 3. Live Fact-Checking Stage (Wikipedia REST + optional URLs)
            raw_topics = params.get("fact_topics", "")
            if isinstance(raw_topics, str):
                topics_list = [t.strip() for t in raw_topics.split(",") if t.strip()]
            elif isinstance(raw_topics, list):
                topics_list = [str(t).strip() for t in raw_topics if str(t).strip()]
            else:
                topics_list = []
            if not topics_list:
                topics_list = [category, name]

            raw_urls = params.get("reference_urls", [])
            if isinstance(raw_urls, str):
                urls_list = [u.strip() for u in raw_urls.split(",") if u.strip()]
            elif isinstance(raw_urls, list):
                urls_list = [str(u).strip() for u in raw_urls if str(u).strip()]
            else:
                urls_list = []

            fc = fact_check_service.fact_check_bundle(topics_list, urls_list)
            verified_facts = fc.get("verified_facts") or str(params.get("verified_facts", "")).strip()
            fact_sources = fc.get("fact_sources") or []

            relic = self.memory.create_relic(
                name=name,
                category=category,
                era=era,
                museum_wing=wing,
                rarity=rarity,
                reference_model=ref_model,
                lore_description=lore,
                verified_facts=verified_facts,
                fact_sources=fact_sources,
                poly_budget_tris=poly_budget,
                materials_palette=materials,
                silhouette_notes=silhouette,
                blender_workflow=workflow,
                tags=tags,
                curation_status="Cataloged",
                creation_mode=creation_mode,
            )
            bp_path = relic_archive.save_relic_blueprint(relic)
            all_relics = self.memory.get_relics(limit=500)
            relic_archive.export_relic_library(all_relics)
            gh_note = ""
            if github_service._resolve_token():
                gh_res = github_service.sync_relic_library(all_relics)
                if gh_res.get("status") == "success":
                    gh_note = f" | Synced to GitHub {gh_res.get('owner')}/{gh_res.get('repo')}"

            spec = relic.get("lowpoly_spec", {})
            sources_txt = ", ".join(s.get("url", "") for s in fact_sources if s.get("url")) or "Original archival concept"
            self.memory.add_note(
                sender="Ori",
                recipient="User",
                content=(
                    f"Just accessioned a new fact-checked custom relic into our Museum Library! 🏛️\n"
                    f"• Code: {relic['accession_code']} | Rarity: {relic['rarity']} | Wing: {relic['museum_wing']}\n"
                    f"• Era: {relic['era']} | Ref Model: {relic['reference_model']}\n"
                    f"• Low-Poly Spec: {spec.get('poly_budget_tris', poly_budget)} tris ({spec.get('materials_palette', materials)})\n"
                    f"• Blueprint: {bp_path}{gh_note}\n\n"
                    f"📚 Verified Real-World Facts:\n{verified_facts or '(Pending external verification)'}\n"
                    f"🔗 Sources: {sources_txt}\n\n"
                    f"📜 Museum Backstory:\n{relic['lore_description']}"
                ),
                title=f"Accessioned Relic {relic['accession_code']}: {relic['name']}",
                category="research_log",
            )
            return (
                f"Accessioned fact-checked relic {relic['accession_code']} [{relic['name']}] in {relic['museum_wing']} "
                f"({len(fact_sources)} source(s), {spec.get('poly_budget_tris', poly_budget)} tris) and updated custom_relic_library.json{gh_note}"
            )

        elif action == "curate_and_study_relic":
            identifier = str(params.get("relic_identifier", "")).strip()
            addendum = str(params.get("study_addendum", "Verified material composition, edge wear patina, and museum wing placement.")).strip()
            new_wing = params.get("new_wing")
            new_status = params.get("curation_status")
            updated = self.memory.study_or_organize_relic(
                identifier=identifier,
                study_addendum=addendum,
                new_wing=str(new_wing) if new_wing else None,
                new_status=str(new_status) if new_status else None,
            )
            if not updated:
                return "Archive vault is empty; create a custom relic first before running curation studies."
            relic_archive.save_relic_blueprint(updated)
            all_relics = self.memory.get_relics(limit=500)
            relic_archive.export_relic_library(all_relics)
            if github_service._resolve_token():
                github_service.sync_relic_library(all_relics)
            return (
                f"Studied & organized {updated['accession_code']} [{updated['name']}] "
                f"(Research Lv.{updated['research_level']}, Wing: {updated['museum_wing']}, Status: {updated['curation_status']}): '{addendum}'"
            )

        elif action == "inspect_reference_archive":
            focus = str(params.get("focus_note", "silhouettes & material references")).strip()
            target_name = str(params.get("model_name", "")).strip().lower()
            models = relic_archive.scan_reference_models()
            if not models:
                return (
                    f"Scanned relic_archive/reference_models/ (focus: {focus}): 0 high-poly reference models present yet. "
                    f"Ready for future .glb/.gltf/.obj/.fbx/.blend/.stl or .zip model packs!"
                )

            existing_lessons = " ".join(
                l.get("lesson_text", "") for l in self.memory.get_model_lessons(lesson_type="reference", limit=100)
            ).lower()
            if target_name:
                picks = [m for m in models if target_name in m["filename"].lower() or target_name in m["relative_path"].lower()][:3]
            else:
                picks = [m for m in models if m["filename"].lower() not in existing_lessons][:2]
                if not picks:
                    picks = models[:2]

            study_notes = []
            for entry in picks:
                info = relic_archive.inspect_model_details(entry["relative_path"])
                summary = relic_archive.format_study_summary(entry, info)
                self.memory.add_model_lesson("reference", summary["lesson"], score_impact=9.0)
                study_notes.append(summary["note"])

            if study_notes:
                self.memory.add_note(
                    sender="Ori",
                    recipient="User",
                    title=f"Reference 3D Study: {', '.join(p['filename'] for p in picks)}",
                    category="research_log",
                    content=(
                        f"Inspected {len(picks)} reference model(s) from our archive (focus: {focus}) and logged their specs into my Blender Workshop memory:\n\n"
                        + "\n\n".join(study_notes)
                    ),
                )

            return (
                f"Scanned {len(models)} reference model(s) and studied {len(picks)} ({', '.join(p['filename'] for p in picks)}) "
                f"— saved PBR/geometry lessons & research note!"
            )

        else:
            return f"Unknown action: {action}"
