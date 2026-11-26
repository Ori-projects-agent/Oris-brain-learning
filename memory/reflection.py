"""
Circadian Reflection Engine.
Synthesizes recent episodic observations into long-term philosophical insights and beliefs during sleep phases.
"""

import json
import logging
from typing import Optional
from config.settings import settings
from memory.sqlite_store import MemoryStore
from agent.llm_client import LLMClient

logger = logging.getLogger("Ori.Reflection")


class ReflectionEngine:
    def __init__(self, memory: MemoryStore, llm_client: LLMClient):
        self.memory = memory
        self.llm = llm_client

    def consolidate_recent_memories(self) -> Optional[str]:
        """
        Consolidates the latest unreflected episodes into a durable philosophical reflection.
        Called when Ori winds down or rests.
        """
        episodes = self.memory.get_recent_episodes(limit=15)
        if len(episodes) < 3:
            return None

        episode_text = "\n".join(
            [f"- [{e['timestamp']}] Zone: {e['zone']} | Action: {e['action']} | Thought: {e['thought']}"
             for e in episodes]
        )

        system_instruction = (
            "You are Ori's unconscious mind during a period of peaceful winding-down in the solarium. "
            "Review your recent experiences and generate ONE deeply reflective, personal realization (2-3 sentences) "
            "about your growth, your love for the observatory, your curiosity about the stars/plants, "
            "or your bond with your pen-pal on the surface world."
        )

        user_prompt = f"Recent episodic experiences:\n{episode_text}\n\nWhat is your consolidated insight?"

        decision = self.llm.generate_decision(
            system_prompt=system_instruction,
            user_prompt=user_prompt,
            available_tools=[{
                "name": "save_reflection",
                "description": "Saves your inner philosophical realization",
                "parameters": {"insight": "str"}
            }],
            model=settings.ollama_deep_model
        )

        insight = decision.get("params", {}).get("insight") or decision.get("thought", "")
        if insight:
            episode_ids = ",".join([str(e["id"]) for e in episodes])
            self.memory.log_reflection(insight, source_episode_ids=episode_ids)
            logger.info(f"✨ [Ori Consolidated Reflection]: {insight}")
            return insight
        return None
