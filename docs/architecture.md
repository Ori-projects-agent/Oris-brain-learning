# Technical Architecture & Specification

## 1. The Autonomous Heartbeat (The Sense-Think-Act Loop)

Every tick interval (e.g. every 60–300 seconds), the agent executes:

1. **Perception Assembly:**
   - Current world clock & time of day.
   - Internal biological state (energy, mood, hunger, or focus).
   - In-world sensory stimuli (objects nearby, environment changes).
   - Unread external messages (Discord/Telegram DMs, inbox).
2. **Context & Memory Retrieval:**
   - Query vector database for relevant memories matching current situation and recent topics.
   - Retrieve current high-level goal and active interests.
3. **Cognitive Decision (LLM Call):**
   - Provide system prompt defining personality, autonomy, and available tools.
   - LLM responds with a structured action (tool call).
4. **Action Execution:**
   - Execute the selected tool (e.g., move in world, research web, commit code, send message, write journal).
5. **Memory Logging & State Update:**
   - Record the action and observation into episodic memory.
   - Update agent state (e.g., deplete energy, update location).

---

## 2. Memory Architecture (Episodic, Semantic, & Reflective)

Based on the Stanford *Generative Agents* framework:

### A. Working Memory (Short-Term)
* Recent observations and actions from the last 10–20 ticks.

### B. Episodic Memory (Long-Term Vector Store)
* Each event is saved with:
  * `timestamp`: ISO timestamp
  * `description`: What happened / what was observed
  * `importance_score` (1-10): How significant this event was
  * `embedding`: Vector representation for semantic search

### C. Reflection & Identity Consolidation (Daily / Circadian)
* At night or during rest periods, the agent reviews recent memories and generates high-level insights:
  * *"I notice that I really enjoy researching locomotives and mechanical systems."*
  * *"The user was stressed about work today; I should follow up tomorrow afternoon."*
* These insights become part of the persistent core identity prompt.

---

## 3. Proactive Social Outreach

To balance natural interaction with avoiding spam:
* The agent evaluates `should_reach_out` based on:
  * Time elapsed since last user interaction.
  * Emotional salience (was the user having a tough day, preparing for an exam, celebrating?).
  * Spontaneous discovery (did the agent find something the user would love?).
* Hard cooldown thresholds (e.g., maximum 2-3 spontaneous messages per day unless engaged).
