"""
Live Fact-Checking & Knowledge Grounding Service for Ori's Archival Curator Pipeline.
Queries free, zero-API-key public endpoints (Wikipedia REST Summary & Search API,
plus user-supplied URLs) to extract verified real-world dates, materials, origins,
and exact source URLs for custom museum relics.
"""

import json
import logging
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from services.web_service import web_service

logger = logging.getLogger("Ori.FactCheck")


class FactCheckService:
    """Zero-key live fact-checker using Wikipedia REST APIs and WebService."""

    def __init__(self):
        self.headers = {
            "User-Agent": "OriArchivalCurator/1.0 (https://github.com/ori-solarium; educational-museum-project)",
            "Accept": "application/json",
        }
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_json(self, url: str, timeout: int = 6) -> Optional[Dict[str, Any]]:
        req = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8", errors="ignore"))
        except urllib.error.HTTPError as e:
            if e.code != 404:
                logger.warning(f"FactCheck HTTP {e.code} for {url}")
            return None
        except Exception as e:
            logger.warning(f"FactCheck request failed for {url}: {e}")
            return None

    def _search_wikipedia_title(self, query: str) -> Optional[str]:
        encoded = urllib.parse.quote_plus(query.strip())
        search_url = (
            f"https://en.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={encoded}&srlimit=3&format=json"
        )
        data = self._get_json(search_url)
        if not data:
            return None
        results = data.get("query", {}).get("search", [])
        if not results:
            return None
        return results[0].get("title")

    def verify_topic(self, topic: str) -> Dict[str, Any]:
        """
        Look up a real-world concept on Wikipedia REST Summary API (with search fallback).
        Returns verified title, summary extract, source URL, and extracted year/material clues.
        """
        clean_topic = topic.strip()
        if not clean_topic:
            return {"topic": topic, "status": "empty"}

        cache_key = clean_topic.lower()
        now = time.time()
        if cache_key in self._cache and (now - self._cache[cache_key].get("ts", 0) < 1800):
            return self._cache[cache_key]

        slug = urllib.parse.quote(clean_topic.replace(" ", "_"), safe="")
        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
        data = self._get_json(summary_url)

        # Fallback to Wikipedia search if direct title 404s or is a disambiguation page
        if not data or data.get("type") == "disambiguation" or not data.get("extract"):
            matched_title = self._search_wikipedia_title(clean_topic)
            if matched_title:
                slug2 = urllib.parse.quote(matched_title.replace(" ", "_"), safe="")
                data = self._get_json(f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug2}")

        if not data or not data.get("extract"):
            res = {
                "topic": clean_topic,
                "title": clean_topic,
                "extract": "",
                "url": "",
                "status": "not_found",
                "ts": now,
            }
            self._cache[cache_key] = res
            return res

        extract = re.sub(r"\s+", " ", data.get("extract", "")).strip()
        if len(extract) > 650:
            extract = extract[:647].rsplit(" ", 1)[0] + "..."

        page_url = (
            data.get("content_urls", {}).get("desktop", {}).get("page")
            or f"https://en.wikipedia.org/wiki/{urllib.parse.quote(data.get('title', clean_topic).replace(' ', '_'))}"
        )

        res = {
            "topic": clean_topic,
            "title": data.get("title", clean_topic),
            "description": data.get("description", ""),
            "extract": extract,
            "url": page_url,
            "wikibase_item": data.get("wikibase_item", ""),
            "status": "verified",
            "ts": now,
        }
        self._cache[cache_key] = res
        logger.info(f"📚 Fact-checked '{clean_topic}' -> '{res['title']}' ({page_url})")
        return res

    def fact_check_bundle(
        self,
        topics: List[str],
        urls: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Verify a list of real-world topics and optional URLs, returning structured
        `verified_facts` text and `fact_sources` citations.
        """
        fact_lines: List[str] = []
        sources: List[Dict[str, str]] = []
        seen_urls = set()

        for raw_topic in topics:
            t = str(raw_topic).strip()
            if not t:
                continue
            info = self.verify_topic(t)
            if info.get("status") == "verified" and info.get("extract"):
                desc_tag = f" ({info['description']})" if info.get("description") else ""
                fact_lines.append(f"• {info['title']}{desc_tag}: {info['extract']}")
                u = info.get("url", "")
                if u and u not in seen_urls:
                    seen_urls.add(u)
                    sources.append({
                        "title": f"Wikipedia — {info['title']}",
                        "url": u,
                        "source_type": "wikipedia",
                    })

        for raw_url in (urls or []):
            u = str(raw_url).strip()
            if not u or u in seen_urls:
                continue
            web_res = web_service.fetch_webpage(u, max_chars=700)
            if web_res.get("status") == "success" and web_res.get("text"):
                seen_urls.add(web_res["url"])
                fact_lines.append(f"• {web_res['title']}: {web_res['text']}")
                sources.append({
                    "title": web_res.get("title", web_res["url"]),
                    "url": web_res["url"],
                    "source_type": "web",
                })

        return {
            "verified_facts": "\n".join(fact_lines),
            "fact_sources": sources,
            "verified_count": len(sources),
        }


fact_check_service = FactCheckService()
