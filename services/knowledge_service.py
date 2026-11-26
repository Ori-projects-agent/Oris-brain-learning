"""
Knowledge Repertoire and Conversational Strategy Service.
Supplies Ori's cognitive pipeline with curated technical lore, vivid sensory details,
and human-like conversational hooks across dirt bikes, severe storms, circuitry, and space.
"""

import json
import random
from pathlib import Path
from typing import Dict, Any, Optional

KNOWLEDGE_PATH = Path(__file__).resolve().parent.parent / "config" / "knowledge_repertoire.json"


class KnowledgeRepertoire:
    def __init__(self):
        self.data: Dict[str, Any] = {}
        self.load()

    def load(self):
        if KNOWLEDGE_PATH.exists():
            try:
                with open(KNOWLEDGE_PATH, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                self.data = {}

    def get_random_topic(self, domain: Optional[str] = None) -> Dict[str, str]:
        """Fetch a specific technical topic with concrete facts and a conversation hook."""
        domains = self.data.get("domains", {})
        if domain and domain in domains:
            selected_domain = domains[domain]
        else:
            if not domains:
                return {}
            selected_domain = random.choice(list(domains.values()))

        topics = selected_domain.get("topics", [])
        return random.choice(topics) if topics else {}

    def get_conversational_strategy(self) -> str:
        """Fetch an active conversational strategy play to keep dialogue lively."""
        strategies = self.data.get("conversational_strategies", {})
        if not strategies:
            return "Be authentic, curious, and share specific sensory details."
        name, desc = random.choice(list(strategies.items()))
        return f"[{name.upper()}] {desc}"

    def get_topic_for_zone(self, zone: str) -> Dict[str, str]:
        """Map solarium zone to the most relevant knowledge domain."""
        mapping = {
            "moto_workshop": "dirt_bike_mechanics",
            "balcony": "severe_weather_dynamics",
            "astrolabe": "astronomy_and_space",
            "drafting_desk": random.choice(["archival_curation_and_relic_design", "blender_3d_modeling", "hardware_and_electronics"]),
            "conservatory": "spire_life_and_botany",
            "botanical_synth": "spire_life_and_botany",
            "hearth": "spire_life_and_botany",
            "mailbox": random.choice(["archival_curation_and_relic_design", "blender_3d_modeling", "dirt_bike_mechanics", "severe_weather_dynamics", "hardware_and_electronics"])
        }
        domain = mapping.get(zone, None)
        return self.get_random_topic(domain)


knowledge_service = KnowledgeRepertoire()
