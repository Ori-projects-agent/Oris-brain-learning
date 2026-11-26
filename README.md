# Ori's Brain & Learning (`Oris-brain-learning`)

Core cognitive engine, personality, autonomous self-functions, memory, and personalized learning curator architecture for **Ori Solarium** (`Ori-projects-agent`).

---

## Repository Organization (by Role)

Python package folders (`agent/`, `config/`, `memory/`, `services/`) are kept at the root so all imports work out of the box.

### 1. Brain & Reasoning (`agent/`)
| File | Role |
|---|---|
| [`agent/heartbeat.py`](agent/heartbeat.py) | Sense → Retrieve → Reason → Act → Reflect continuous loop (with deep-sleep skip & cache-friendly prompt ordering) |
| [`agent/llm_client.py`](agent/llm_client.py) | Local Ollama & Gemini client with two-brain model routing, shared `num_ctx`, and token/timing stats |
| [`agent/tool_selector.py`](agent/tool_selector.py) | Situational tool subset selector (keeps prompts compact for local CPU inference) |
| [`agent/drives.py`](agent/drives.py) | Cybernetic drive engine (`energy`, `curiosity`, `botanical_care`, `sociality`, `creative_urge`, `storm_fascination`) |

### 2. Personality & Knowledge (`config/`)
| File | Role |
|---|---|
| [`config/persona.json`](config/persona.json) | Ori's character sheet, voice, passions, Solarium zones, and drive thresholds |
| [`config/knowledge_repertoire.json`](config/knowledge_repertoire.json) | Curated technical topics & conversational hooks across Ori's domains |
| [`config/settings.py`](config/settings.py) | `.env` loader and runtime settings (`OLLAMA_MODEL`, `OLLAMA_DEEP_MODEL`, `ASTRAL_ARCHIVE_URL`, etc.) |

### 3. Self-Functions & Workshop (`agent/`, `services/`)
| File | Role |
|---|---|
| [`agent/tools.py`](agent/tools.py) | 29 in-world affordances (stargazing, storm study, probes, relic curation, letters, research, GitHub, Blender) |
| [`agent/modeler.py`](agent/modeler.py) | Autonomous Blender 3D modeling workshop (script generation, scoring, self-critique, and `model_lessons`) |
| [`services/blender_runner.py`](services/blender_runner.py) | Sandboxed headless Blender execution & mesh inspection |
| [`services/relic_archive.py`](services/relic_archive.py) | Reference 3D `.glb`/`.gltf` archive scanner & geometry analyzer |

### 4. Memory & Reflection (`memory/`)
| File | Role |
|---|---|
| [`memory/sqlite_store.py`](memory/sqlite_store.py) | Persistent multi-tier SQLite store (episodes, reflections, correspondence, relics, models, lessons) |
| [`memory/reflection.py`](memory/reflection.py) | Circadian sleep-state memory consolidation using `ollama_deep_model` |

### 5. External & Support Services (`services/`)
| File | Role |
|---|---|
| [`services/knowledge_service.py`](services/knowledge_service.py) | Zone-to-domain topic & conversational strategy selector |
| [`services/fact_check_service.py`](services/fact_check_service.py) | Wikipedia API fact-checking for relics and research |
| [`services/web_service.py`](services/web_service.py) | Webpage fetcher & Google News RSS current-events scanner |
| [`services/telemetry.py`](services/telemetry.py) | Live NWS severe weather & NOAA space-weather feeds |
| [`services/github_service.py`](services/github_service.py) | GitHub repo, Gist, and `astral-archive` relic library sync |
| [`services/ollama_service.py`](services/ollama_service.py) | Local Ollama server auto-detection & startup helper |

### 6. Architecture & Learning Curator Docs (`docs/`)
See [`docs/README.md`](docs/README.md) for the full documentation index, including [`docs/LEARNING_CURATOR_PLAN.md`](docs/LEARNING_CURATOR_PLAN.md).

---

## Setup Notes
- Copy `.env.example` to `.env` and set your local Ollama models and `ASTRAL_ARCHIVE_URL`.
- Secrets (`.env`) and local runtime databases (`*.db`) are excluded via `.gitignore`.
