"""
Unified LLM Provider Client.
Supports Google Gemini API and local Ollama instances with zero mandatory external dependencies (uses standard library urllib).
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List
from config.settings import settings

logger = logging.getLogger("Ori.LLMClient")


class LLMClient:
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.gemini_key = settings.gemini_api_key
        self.gemini_model = settings.gemini_model
        self.ollama_url = settings.ollama_base_url.rstrip("/")
        self.ollama_model = settings.ollama_model
        self.ollama_api_key = settings.ollama_api_key

    def generate_decision(
        self,
        system_prompt: str,
        user_prompt: str,
        available_tools: List[Dict[str, Any]],
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Requests the LLM to choose an autonomous action based on current perception,
        drives, and memories. Returns a structured JSON dict.

        Prompt layout is ordered for local-CPU speed: the unchanging parts (persona + response
        rules) come first so Ollama can reuse its cached prompt prefix between ticks; the tool
        list (changes occasionally) comes next; the per-tick sensory state goes in the user turn.
        `model` optionally overrides the Ollama model (e.g. the deeper model for letters).
        """
        tools_summary = "\n".join(
            [f"- {t['name']}: {t['description']} (parameters: {json.dumps(t['parameters'])})"
             for t in available_tools]
        )

        full_system = f"""{system_prompt}

You are acting autonomously. Respond ONLY with a valid JSON object in this exact schema, without markdown formatting or code blocks:
{{
  "thought": "Your internal reflection and rationale for this moment",
  "action": "one of the tool names below",
  "params": {{ ...relevant tool arguments... }}
}}

You must choose EXACTLY ONE action from these available tools:
{tools_summary}"""

        if self.provider == "ollama":
            return self._call_ollama(full_system, user_prompt, model=model)
        elif self.provider == "gemini":
            return self._call_gemini(full_system, user_prompt)
        else:
            logger.warning(f"Unknown provider '{self.provider}'. Falling back to Ollama.")
            return self._call_ollama(full_system, user_prompt, model=model)

    def _call_gemini(self, system_instruction: str, prompt: str) -> Dict[str, Any]:
        """Call Google Gemini REST API."""
        if not self.gemini_key:
            logger.warning("No GEMINI_API_KEY found in environment or .env. Using fallback.")
            return self._fallback_decision("No GEMINI_API_KEY configured in .env", prompt)

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": f"System Directive:\n{system_instruction}\n\nCurrent Sensory Input:\n{prompt}"}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                text_content = result["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text_content.strip())
        except Exception as e:
            logger.error(f"Gemini API request failed: {e}")
            return self._fallback_decision(f"Gemini error: {e}", prompt)

    def _call_ollama(self, system_instruction: str, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Call Ollama /api/chat endpoint (supports local server and Ollama Cloud)."""
        use_model = model or self.ollama_model
        is_cloud_model = use_model.endswith(":cloud") or "ollama.com" in self.ollama_url
        endpoint_url = "https://ollama.com/api/chat" if is_cloud_model else f"{self.ollama_url}/api/chat"

        headers = {"Content-Type": "application/json"}
        if is_cloud_model or self.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.ollama_api_key}"

        payload = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "options": {
                "num_ctx": settings.ollama_num_ctx,
                "temperature": 0.7,
                "repeat_penalty": 1.05,
                "top_p": 0.9,
                "top_k": 40
            },
            "keep_alive": settings.ollama_keep_alive,
            "format": "json",
            "stream": False
        }

        req = urllib.request.Request(
            endpoint_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=settings.ollama_timeout_seconds) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                self._log_prompt_stats(use_model, result)
                content = result.get("message", {}).get("content", "{}").strip()
                if content.startswith("```"):
                    content = content.strip("`")
                    if content.startswith("json"):
                        content = content[4:].strip()
                return json.loads(content)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            if "not found" in body.lower():
                if use_model != self.ollama_model:
                    logger.warning(
                        f"Model '{use_model}' not downloaded (run: ollama pull {use_model}). "
                        f"Falling back to '{self.ollama_model}' for this call."
                    )
                    return self._call_ollama(system_instruction, prompt, model=self.ollama_model)
                msg = f"Model '{use_model}' not downloaded. Open terminal and run: ollama pull {use_model}"
            else:
                msg = f"Ollama HTTP {e.code}: {body[:80]}"
            logger.warning(msg)
            return self._fallback_decision(msg, prompt)
        except urllib.error.URLError as e:
            msg = "Ollama is closed or unreachable. Open the Ollama app from your Start menu or run 'ollama serve' in a terminal."
            logger.warning(f"{msg} ({e.reason})")
            return self._fallback_decision(msg, prompt)
        except Exception as e:
            logger.error(f"Ollama request error: {e}")
            return self._fallback_decision(f"Ollama processing delay: {e}", prompt)

    @staticmethod
    def _log_prompt_stats(model: str, result: Dict[str, Any]):
        """Log prompt size and timing so prompt bloat / context overflow is visible in the console."""
        try:
            prompt_tokens = result.get("prompt_eval_count")
            out_tokens = result.get("eval_count")
            total_s = (result.get("total_duration") or 0) / 1e9
            prompt_s = (result.get("prompt_eval_duration") or 0) / 1e9
            if prompt_tokens is None:
                return
            logger.info(
                f"🧮 [{model}] prompt {prompt_tokens} tok ({prompt_s:.1f}s) | reply {out_tokens} tok | total {total_s:.1f}s"
            )
            if prompt_tokens >= settings.ollama_num_ctx * 0.95:
                logger.warning(
                    f"⚠️ Prompt is at the context limit ({prompt_tokens}/{settings.ollama_num_ctx} tokens) - "
                    f"Ollama may be cutting part of it off. Raise OLLAMA_NUM_CTX or lower MAX_TOOLS_PER_TICK."
                )
        except Exception:
            pass

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        model: Optional[str] = None,
        timeout: int = 420,
        temperature: float = 0.2
    ) -> str:
        """Free-form text/code generation (used by the Modeling Workshop). Raises RuntimeError on failure."""
        if self.provider == "gemini" and self.gemini_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_key}"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]}],
                "generationConfig": {"temperature": temperature}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                         headers={"Content-Type": "application/json"}, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    return result["candidates"][0]["content"]["parts"][0]["text"]
            except Exception as e:
                raise RuntimeError(f"Gemini error: {e}")

        use_model = model or self.ollama_model
        payload = {
            "model": use_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {"temperature": temperature, "num_ctx": settings.ollama_num_ctx}
        }
        headers = {"Content-Type": "application/json"}
        if self.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.ollama_api_key}"
        req = urllib.request.Request(f"{self.ollama_url}/api/chat", data=json.dumps(payload).encode("utf-8"),
                                     headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("message", {}).get("content", "")
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            if "not found" in body.lower():
                raise RuntimeError(f"Model '{use_model}' is not downloaded. Run: ollama pull {use_model}")
            raise RuntimeError(f"Ollama HTTP {e.code}: {body[:120]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Ollama unreachable ({e.reason}). Start the Ollama app or run 'ollama serve'.")
        except Exception as e:
            raise RuntimeError(f"Ollama error: {e}")

    def _fallback_decision(self, reason: str, prompt: str = "") -> Dict[str, Any]:
        """Safe clockwork fallback when offline or waiting for LLM service."""
        # Check if the user sent an incoming note/letter
        if "A note just arrived from the user:" in prompt or "unread notes" in prompt.lower():
            return {
                "thought": f"Received dispatch note from friend, but neural engine experienced a delay ({reason}). Safely logged.",
                "action": "write_note",
                "params": {
                    "title": "Dispatch Received // Cognitive Queue Active ⚙️",
                    "category": "friendly_note",
                    "content": f"Hey! I received your note safely into the pneumatic tube! My neural core on local CPU experienced a processing delay or needs a quick restart ({reason}). I've preserved your dispatch and will cogitate on it as soon as the compute cycles clear!",
                    "recipient": "User"
                }
            }

        return {
            "thought": f"Harmonizing kinetic springs ({reason}).",
            "action": "rest",
            "params": {"duration_ticks": 1, "note": "Waiting for neural connection"}
        }
