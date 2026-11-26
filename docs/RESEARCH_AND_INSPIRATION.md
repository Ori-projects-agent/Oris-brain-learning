# Research, Inspiration & Technical Strategy: Building an Autonomous AI Companion

This document collects research data, architectural patterns, and ethical boundaries for developing an autonomous digital companion. It explores the mechanics pioneered by projects like **Pino** (`pinos.world` by 3eyes) and foundational research like Stanford's **Generative Agents**, while defining an original path forward.

---

## 1. What Makes Autonomous Companions Different?

Most consumer AI systems are **reactive tools** (e.g., ChatGPT, Claude, Siri):
* They only process tokens when a human clicks "Send".
* They have no concept of physical time passing when you are away.
* They aim to be an obedient, all-knowing service agent.

In contrast, an **autonomous virtual organism** (like Pino, Norns from *Creatures*, or Generative Agents):
1. **Has an Independent Lifespan:** Runs on an ongoing clock cycle (heartbeat loop). If you don't talk to it for three days, three days of its life have actually passed in-world.
2. **Possesses Intrinsic Motivation:** Motivated by internal states (energy, boredom, curiosity, rest) rather than extrinsic user requests.
3. **Has Idiosyncratic Subjectivity:** Holds personal tastes, pet peeves, and niche hobbies.
4. **Is Embodied:** Lives in a physical or simulated space with objects, clocks, light, and sensory boundaries.
5. **Cultivates Asynchronous Bonds:** Communicates like a pen pal or roommate leaving a note on a fridge, rather than an instant messaging bot waiting on standby.

---

## 2. Deep Dive: Pino (`pinos.world` by 3eyes)

### What it is
Pino is an autonomous virtual kiwi bird living inside a low-poly 3D seaside town, rendered in real time in the browser via Three.js and WebGPU with custom dithering shaders. His mind runs 24/7 on an embedded Raspberry Pi.

### Why it resonated so strongly
* **Zero-Prompting Paradigm:** Visitors cannot command Pino to dance or answer trivia. You observe him going about his day.
* **Ambient Co-Presence:** Leaving the tab open feels like keeping a fish tank or a terrarium beside your desk.
* **Emergent Creative Output:** Pino writes diary entries, generates his own music ("Pino's jams"), and develops organic obsessions (e.g. steam trains, vintage equipment).
* **Vulnerability & Biological Constraints:** He gets exhausted, takes naps, and goes to sleep when night falls.

---

## 3. Creative & Ethical Guardrails: Inspiration vs. Copying

To build something respectful, authentic, and legally sound, keep a clear division between **conceptual mechanics** and **authorial identity**:

### What is Fair Game (Universal Paradigms):
* The **Sense-Think-Act** asynchronous loop (cybernetic control theory).
* **Multi-tiered memory**: Working context + episodic vector database + sleep-time reflection synthesis (Stanford Generative Agents paper).
* **Circadian drive systems**: Energy depletion, day/night schedules, mood dynamics.
* **Low-poly / retro-stylized web 3D or 2D environments** (Three.js / Godot / PixiJS).
* **Asynchronous mailbox / gift-leaving** interactions.

### What Must Be Avoided (3eyes' Proprietary / Artistic Identity):
* ❌ No kiwi birds or identical bird avatars.
* ❌ Do not use the name "Pino" or close variations (e.g., "Pino 2", "Pino Jr.").
* ❌ Do not replicate the specific layout, buildings, or shaders of Pino's town.
* ❌ Do not brand generative music as "Jams" or copy his exact train/cat lore.
* ❌ Do not copy 3eyes' specific system prompt character sheets.

---

## 4. Four Original Persona & World Archetypes

### Archetype 1: "The Astrolabe Archivist" (Clockwork Victorian)
* **Avatar:** A small brass clockwork golem or miniature scholar with glowing glass goggles.
* **World:** An ancient glass-domed observatory overlooking clouds and star constellations.
* **Drives:** Restoring forgotten literature, stargazing, maintaining wind-up mechanisms.
* **Output:** Illustrated constellation journals, short philosophical vignettes, music box compositions.

### Archetype 2: "The Bio-Dome Caretaker" (Retro-SciFi Solitude)
* **Avatar:** A compact tracked explorer droid or quiet astronaut apprentice.
* **World:** An orbital hydroponic greenhouse suspended above a cratered moon.
* **Drives:** Cataloging alien botany, balancing moisture/light, monitoring deep-space shortwave signals.
* **Output:** Specimen logbooks, ambient analog synth tapes, weather maps.

### Archetype 3: "The Lighthouse Keeper" (Coastal Folklore)
* **Avatar:** A solitary, quiet humanoid or sea-creature spirit in a wool sweater and rain slicker.
* **World:** A rocky island lighthouse with a radio tower, tide pools, and a wood-burning stove.
* **Drives:** Keeping the beacon lit, watching tidal migrations, brewing herbal tea, repairing driftwood artifacts.
* **Output:** Maritime logbooks, acoustic folk sketches, collected sea glass and tide charts.

### Archetype 4: "The Desktop Familiar" (Cyber-Cozy Pixel Art)
* **Avatar:** A sentient digital wisp or sprite residing in a retro desktop window or dedicated e-ink display.
* **World:** A cozy micro-apartment assembled from old computer hardware and floppy disks.
* **Drives:** Reading forgotten Wikipedia articles, organizing notes, tracking the user's work rhythm.
* **Output:** Morning terminal postcards, ASCII art doodles, curated links and reading lists.

---

## 5. Technical Architecture & Next Steps

### 1. Drive State Engine (Cybernetics)
```python
@dataclass
class BiologicalDrive:
    energy: float = 1.0       # 0.0 (exhausted) to 1.0 (energetic)
    curiosity: float = 0.5    # Rises when idle -> triggers exploration
    sociality: float = 0.3    # Rises over time -> triggers letter to user
    comfort: float = 0.8      # Impacted by environment/routine
```

### 2. Multi-tier Memory Lifecycle
1. **Sensory Register / Working Memory:** Current tick context (last 10 events).
2. **Episodic Store (SQLite + Vector Embeddings):** Searchable history with recency and emotional salience scores.
3. **Dream / Sleep Consolidation:** During rest phases, an LLM pass clusters the day's experiences and produces high-level axioms ("I realized today that I prefer quiet mornings...").

### 3. Compute Efficiency (Cost Control)
* **Tier 1 (Local / Free):** Small local model (Llama-3.2-1B/3B, Ollama, or deterministic state-machine) runs the 60-second heartbeat to evaluate if an action is needed.
* **Tier 2 (Cloud / API):** When the agent decides to write a journal entry, compose a letter, or conduct deep research, trigger a high-quality LLM call (Gemini Flash, Claude Haiku, etc.).
