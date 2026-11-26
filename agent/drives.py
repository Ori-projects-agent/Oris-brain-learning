"""
Cybernetic Drive Engine.
Manages Ori's internal biological and clockwork needs (Energy, Curiosity, Botanical Care, Sociality).
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class Drives:
    energy: float = 1.0              # 0.0 (exhausted, springs unwound) to 1.0 (fully wound)
    curiosity: float = 0.6           # 0.0 to 1.0 (prompts research & stargazing when high)
    botanical_care: float = 0.5      # 0.0 to 1.0 (prompts misting & plant care when high)
    sociality: float = 0.3           # 0.0 to 1.0 (prompts sending letters to user when high)
    creative_urge: float = 0.5       # 0.0 to 1.0 (prompts inventing & drawing field sketches when high)
    storm_fascination: float = 0.5   # 0.0 to 1.0 (prompts storm tracking & probe launches when high)
    last_actions: List[str] = field(default_factory=list)

    def tick(self, active_action: str, has_active_storm: bool = False):
        """Update drives after each heartbeat tick."""
        self.last_actions.append(active_action)
        if len(self.last_actions) > 5:
            self.last_actions.pop(0)

        if active_action == "rest":
            self.energy = min(1.0, self.energy + 0.35)
            self.curiosity = min(1.0, self.curiosity + 0.03)
            self.botanical_care = min(1.0, self.botanical_care + 0.02)
            self.sociality = min(1.0, self.sociality + 0.02)
            self.creative_urge = min(1.0, self.creative_urge + 0.02)
            self.storm_fascination = min(1.0, self.storm_fascination + (0.05 if has_active_storm else 0.02))
        elif active_action == "brew_tea":
            # Brewing tea restores thermal kinetic spring energy while reducing botanical urge
            self.energy = min(1.0, self.energy + 0.20)
            self.botanical_care = max(0.1, self.botanical_care - 0.40)
            self.curiosity = min(1.0, self.curiosity + 0.02)
        else:
            # Active work drains energy
            self.energy = max(0.0, self.energy - 0.05)

            # Reduce the drive satisfied by the action
            if active_action in ("stargaze", "study_dirt_bikes", "research_topic", "curate_and_study_relic", "inspect_reference_archive"):
                self.curiosity = max(0.1, self.curiosity - 0.45)
            elif active_action in ("invent_device", "draw_field_sketch", "expand_workspace", "create_custom_relic", "design_model", "revise_model"):
                self.creative_urge = max(0.1, self.creative_urge - 0.45)
                self.curiosity = max(0.1, self.curiosity - 0.25)
            elif active_action in ("study_storm", "launch_weather_probe", "launch_atmospheric_probe", "tune_solarium_climate"):
                self.storm_fascination = max(0.1, self.storm_fascination - 0.50)
            elif active_action in ("tend_flora", "synthesize_botanical", "design_greenhouse_plant", "organize_greenhouse"):
                self.botanical_care = max(0.1, self.botanical_care - 0.50)
                if active_action == "design_greenhouse_plant":
                    self.creative_urge = max(0.1, self.creative_urge - 0.35)
            elif active_action in ("send_letter", "reply_letter", "write_note", "develop_note"):
                self.sociality = max(0.1, self.sociality - 0.45)
                # Sharing ideas relieves built-up creative urge and storm fascination
                self.creative_urge = max(0.2, self.creative_urge - 0.25)
                self.storm_fascination = max(0.2, self.storm_fascination - 0.20)

            # Other drives slowly accumulate
            self.curiosity = min(1.0, self.curiosity + 0.04)
            self.botanical_care = min(1.0, self.botanical_care + 0.03)
            self.sociality = min(1.0, self.sociality + 0.03)
            self.creative_urge = min(1.0, self.creative_urge + 0.04)
            self.storm_fascination = min(1.0, self.storm_fascination + (0.08 if has_active_storm else 0.03))

        # Anti-repetition hysteresis: If same action ran 2+ times in a row, depress its drive to encourage rotation
        if len(self.last_actions) >= 2 and self.last_actions[-1] == self.last_actions[-2]:
            repeated = self.last_actions[-1]
            if repeated in ("tend_flora", "synthesize_botanical"):
                self.botanical_care = 0.1
            elif repeated in ("stargaze", "study_dirt_bikes", "research_topic", "curate_and_study_relic", "inspect_reference_archive"):
                self.curiosity = 0.1
            elif repeated in ("invent_device", "draw_field_sketch", "create_custom_relic", "design_model", "revise_model"):
                self.creative_urge = 0.1
            elif repeated in ("study_storm", "launch_weather_probe"):
                self.storm_fascination = 0.1
            elif repeated in ("write_note", "develop_note", "send_letter"):
                self.sociality = 0.1

    def to_dict(self) -> Dict[str, float]:
        return {
            "energy": round(self.energy, 2),
            "curiosity": round(self.curiosity, 2),
            "botanical_care": round(self.botanical_care, 2),
            "sociality": round(self.sociality, 2),
            "creative_urge": round(self.creative_urge, 2),
            "storm_fascination": round(self.storm_fascination, 2),
        }
