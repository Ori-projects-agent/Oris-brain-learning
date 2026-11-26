"""
Situational Tool Selector.

Instead of sending all ~29 tool descriptions to the model every tick (≈5k tokens — more than a
small local model's context window can hold alongside the persona), pick only the handful that
make sense right now: replying to a letter, resting when tired, or the tool groups behind
Ori's strongest drives. Fewer, more relevant choices also make small models pick better.
"""

from typing import Dict, Any, List, Optional
from agent.tools import AVAILABLE_TOOLS

TOOLS_BY_NAME: Dict[str, Dict[str, Any]] = {t["name"]: t for t in AVAILABLE_TOOLS}

# Tools that answer a letter from the user (mirrors the allowed set in heartbeat.tick_once)
LETTER_TOOLS = [
    "write_note", "develop_note", "send_letter", "research_topic", "browse_website",
    "create_custom_relic", "curate_and_study_relic", "publish_github_gist", "create_github_repo",
]

REST_TOOLS = ["rest", "brew_tea", "write_journal"]

# Drive -> tools that satisfy it (ordered by preference)
DRIVE_TOOL_GROUPS: Dict[str, List[str]] = {
    "curiosity": [
        "research_topic", "stargaze", "search_current_events", "inspect_reference_archive",
        "curate_and_study_relic", "study_dirt_bikes", "browse_website",
    ],
    "creative_urge": [
        "revise_model", "design_model", "create_custom_relic", "invent_device",
        "draw_field_sketch", "expand_workspace",
    ],
    "storm_fascination": ["study_storm", "launch_atmospheric_probe", "tune_solarium_climate"],
    "botanical_care": ["tend_flora", "design_greenhouse_plant", "synthesize_botanical", "organize_greenhouse", "brew_tea"],
    "sociality": ["write_note", "develop_note", "send_letter"],
}

MODELER_TOOLS = {"design_model", "revise_model"}
ALWAYS_INCLUDE = ["write_note", "rest"]


def select_tools(
    drives: Dict[str, float],
    has_unread_letter: bool,
    modeler_busy: bool = False,
    suggested_action: Optional[str] = None,
    max_tools: int = 8,
) -> List[Dict[str, Any]]:
    """Return the subset of AVAILABLE_TOOLS relevant to the current situation."""
    chosen: List[str] = []

    def add(names: List[str], limit: Optional[int] = None):
        added = 0
        for n in names:
            if limit is not None and added >= limit:
                break
            if n in TOOLS_BY_NAME and n not in chosen and not (modeler_busy and n in MODELER_TOOLS):
                chosen.append(n)
                added += 1

    # A cue in the prompt names a specific tool -> it must be offered
    if suggested_action:
        add([suggested_action])

    if has_unread_letter:
        add(LETTER_TOOLS)
    elif drives.get("energy", 1.0) < 0.28:
        add(REST_TOOLS)
    else:
        # Top two drives (energy excluded) decide which tool groups are offered
        ranked = sorted(
            (k for k in DRIVE_TOOL_GROUPS if k in drives),
            key=lambda k: drives.get(k, 0.0),
            reverse=True,
        )
        for i, drive in enumerate(ranked[:2]):
            add(DRIVE_TOOL_GROUPS[drive], limit=4 if i == 0 else 3)

    add(ALWAYS_INCLUDE)
    return [TOOLS_BY_NAME[n] for n in chosen[:max(max_tools, len(ALWAYS_INCLUDE))]]
