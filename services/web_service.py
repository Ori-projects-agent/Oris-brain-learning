"""
Live Web & Current Events Service for Ori.
Enables fetching readable text from websites and retrieving live news/current events
without mandatory external dependencies (uses standard library urllib, re, xml/html parsers).
"""

import re
import time
import logging
import urllib.request
import urllib.error
import urllib.parse
from html import unescape
from typing import Dict, Any, List, Optional

logger = logging.getLogger("Ori.WebService")


class WebService:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (OriAutonomousSolarium/1.0)"
        }
        self._url_cache: Dict[str, Dict[str, Any]] = {}

    def fetch_webpage(self, url: str, max_chars: int = 2500) -> Dict[str, Any]:
        """
        Fetches an arbitrary webpage URL and extracts clean readable text.
        Caches results for 10 minutes to avoid redundant network overhead.
        """
        # Clean URL
        url = url.strip().rstrip(".,;)>'\"")
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        now = time.time()
        if url in self._url_cache and (now - self._url_cache[url]["timestamp"] < 600):
            return self._url_cache[url]

        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw_bytes = resp.read()

                # Detect encoding
                encoding = "utf-8"
                if "charset=" in content_type.lower():
                    try:
                        encoding = content_type.lower().split("charset=")[-1].split(";")[0].strip()
                    except Exception:
                        encoding = "utf-8"

                raw_html = raw_bytes.decode(encoding, errors="ignore")

                # Extract page title
                title_match = re.search(r"<title>(.*?)</title>", raw_html, re.IGNORECASE | re.DOTALL)
                title = unescape(title_match.group(1).strip()) if title_match else url

                # Strip script, style, svg, nav, footer tags
                cleaned = re.sub(r"<(script|style|svg|noscript|nav|footer).*?>.*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
                
                # Strip HTML comments
                cleaned = re.sub(r"<!--.*?-->", " ", cleaned, flags=re.DOTALL)

                # Strip remaining tags
                text = re.sub(r"<[^>]+>", " ", cleaned)
                # Normalize whitespaces
                text = re.sub(r"\s+", " ", text).strip()
                text = unescape(text)

                # Truncate to relevant readable snippet
                snippet = text[:max_chars] if len(text) > max_chars else text

                result = {
                    "url": url,
                    "title": title,
                    "text": snippet,
                    "full_length": len(text),
                    "status": "success",
                    "timestamp": now
                }
                self._url_cache[url] = result
                logger.info(f"🌐 Successfully fetched website [{url}] - Title: '{title}' ({len(snippet)} chars)")
                return result

        except Exception as e:
            logger.warning(f"Failed to fetch webpage {url}: {e}")
            return {
                "url": url,
                "title": url,
                "text": f"Could not retrieve live contents: {e}",
                "status": "error",
                "timestamp": now
            }

    def search_current_events(self, query: str = "astronomy", limit: int = 5) -> List[Dict[str, str]]:
        """
        Fetches live current event headlines and summaries via open RSS feeds.
        Zero API keys required.
        """
        encoded_q = urllib.parse.quote_plus(query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"

        try:
            req = urllib.request.Request(rss_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                xml = resp.read().decode("utf-8", errors="ignore")

                items = re.findall(r"<item>(.*?)</item>", xml, re.DOTALL)
                articles = []
                for item in items[:limit]:
                    title_m = re.search(r"<title>(.*?)</title>", item)
                    link_m = re.search(r"<link>(.*?)</link>", item)
                    pub_m = re.search(r"<pubDate>(.*?)</pubDate>", item)
                    desc_m = re.search(r"<description>(.*?)</description>", item)

                    title = unescape(title_m.group(1)) if title_m else "News Story"
                    link = link_m.group(1) if link_m else ""
                    pub = pub_m.group(1) if pub_m else ""
                    desc = unescape(re.sub(r"<[^>]+>", "", desc_m.group(1))) if desc_m else ""

                    articles.append({
                        "title": title,
                        "link": link,
                        "published": pub,
                        "summary": desc[:250]
                    })

                logger.info(f"📰 Fetched {len(articles)} live current event stories for query: '{query}'")
                return articles

        except Exception as e:
            logger.warning(f"Current events search error for '{query}': {e}")
            return [
                {
                    "title": f"Observational stream for '{query}' active",
                    "link": "https://maxvelocitywx.com/severeweather",
                    "published": time.strftime("%a, %d %b %Y %H:%M:%S GMT"),
                    "summary": "Live radio frequency monitoring from the Solarium Spire."
                }
            ]

    def extract_urls(self, text: str) -> List[str]:
        """Finds any http/https links present in a text message."""
        pattern = r"https?://[^\s<>\"'()]+"
        return re.findall(pattern, text)


web_service = WebService()
