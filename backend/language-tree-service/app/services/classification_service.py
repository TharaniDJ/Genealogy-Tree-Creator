"""
language_resolver.py

Given a list of language names, resolves them to Wikidata QIDs (when possible),
validates that the entity is language-related (P31 / P279 checks against a
language type whitelist), and fetches the P1846 distribution map file URL
(if available). Uses batch Wikipedia title lookups and a batched SPARQL query
(with VALUES) to minimize HTTP requests.

Persistent cache (SQLite) stores normalized_name -> JSON result to avoid repeated queries.
"""

from __future__ import annotations
import time
import json
import sqlite3
import requests
from typing import List, Dict, Optional, Tuple, Any, Iterator
from itertools import islice

# -----------------------------
# Configuration
# -----------------------------
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

# polite headers (include contact URL/email)
HEADERS = {
    "User-Agent": "LanguageFamilyTreeService/1.0 (https://example.org; contact@example.org)",
    "Accept": "application/json",
}

MAX_RETRIES = 4
BACKOFF_BASE = 0.8

# Batch sizes chosen conservatively to be accepted by MediaWiki and WDQS:
WIKIPEDIA_BATCH_TITLES = 50
SPARQL_BATCH_QIDS = 50

# SQLite cache file
CACHE_DB = "language_resolver_cache.sqlite"

# Language type hierarchy mapping names -> QIDs used for validation
LANGUAGE_TYPE_HIERARCHY = [
    ("language", "Q34770"),
    ("modern_language", "Q1288568"),
    ("historical language", "Q2315359"),
    ("ancient_language", "Q436240"),
    ("dead_language", "Q45762"),
    ("extinct_language", "Q38058796"),
    ("dialect", "Q33384"),
    ("sign_language", "Q34228"),
    ("creole_language", "Q33289"),
    ("pidgin_language", "Q33831"),
    ("language_family", "Q25295"),
    ("proto_language", "Q206577"),
]

# -----------------------------
# Utilities
# -----------------------------
def chunked(iterable: Iterator[Any], n: int) -> Iterator[List[Any]]:
    it = iter(iterable)
    while True:
        chunk = list(islice(it, n))
        if not chunk:
            break
        yield chunk

def normalize_name(name: str) -> str:
    return " ".join(name.strip().split()).lower()

# -----------------------------
# Simple SQLite cache
# -----------------------------
class SimpleCache:
    def __init__(self, db_path: str = CACHE_DB):
        self.db_path = db_path
        self._ensure_table()

    def _ensure_table(self):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value TEXT, ts INTEGER)"
            )
            conn.commit()
        finally:
            conn.close()

    def get(self, key: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("SELECT value FROM cache WHERE key = ?", (key,)).fetchone()
            if row:
                return json.loads(row[0])
            return None
        finally:
            conn.close()

    def set(self, key: str, value: Optional[dict]):
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, ts) VALUES (?, ?, strftime('%s','now'))",
                (key, json.dumps(value)),
            )
            conn.commit()
        finally:
            conn.close()

# -----------------------------
# HTTP helpers with retry/backoff
# -----------------------------
def _safe_get_json(session: requests.Session, url: str, *, params: dict, headers: dict | None = None, timeout: int = 20) -> Optional[dict]:
    merged = {**HEADERS, **(headers or {})}
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = session.get(url, params=params, headers=merged, timeout=timeout)
            status = resp.status_code
            if status == 429:
                # Too many requests: back off more aggressively
                wait = BACKOFF_BASE * (2 ** (attempt - 1))  # exponential
                time.sleep(wait)
                continue
            if status >= 500:
                time.sleep(BACKOFF_BASE * attempt)
                continue
            if status != 200:
                # treat non-200 as transient for a few attempts (but don't spam)
                time.sleep(BACKOFF_BASE * attempt)
                try:
                    # sometimes APIs return JSON error details we may want to see
                    return resp.json()
                except Exception:
                    return None
            txt = resp.text.strip()
            if not txt:
                time.sleep(BACKOFF_BASE * attempt)
                continue
            return resp.json()
        except requests.RequestException:
            time.sleep(BACKOFF_BASE * attempt)
    return None

# -----------------------------
# Core resolver
# -----------------------------
class LanguageResolver:
    def __init__(self, cache: Optional[SimpleCache] = None):
        self.session = requests.Session()
        self.cache = cache or SimpleCache()
        # Precompute set of valid QIDs for faster checking
        self._valid_qid_set = {qid for _, qid in LANGUAGE_TYPE_HIERARCHY}

    def batch_lookup_titles(self, titles: List[str]) -> Dict[str, Optional[str]]:
        """
        Query Wikipedia in batches for pageprops.wikibase_item for many titles at once.
        Returns mapping title -> wikibase_item QID or None.
        """
        results: Dict[str, Optional[str]] = {}
        for chunk in chunked(iter(titles), WIKIPEDIA_BATCH_TITLES):
            params = {
                "action": "query",
                "titles": "|".join(chunk),
                "prop": "pageprops",
                "ppprop": "wikibase_item",
                "format": "json",
            }
            data = _safe_get_json(self.session, WIKIPEDIA_API, params=params) or {}
            pages = data.get("query", {}).get("pages", {})
            # pages returned keyed by pageid; some may be missing wikibase_item
            for page in pages.values():
                title = page.get("title")
                qid = None
                if "pageprops" in page and "wikibase_item" in page["pageprops"]:
                    qid = page["pageprops"]["wikibase_item"]
                if title:
                    results[title] = qid
            # Some titles in request might not appear in pages? but usually they do.
            # politeness sleep small (batch-level)
            time.sleep(0.15)
        return results

    def batch_sparql_validate_and_fetch(self, qids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch SPARQL to get types (P31/P279) for multiple QIDs.
        Returns mapping qid -> {"types": [qid,..]}.
        """
        if not qids:
            return {}
        out: Dict[str, Dict[str, Any]] = {qid: {"types": []} for qid in qids}

        # process in batches to keep queries reasonable
        for chunk in chunked(iter(qids), SPARQL_BATCH_QIDS):
            values = " ".join(f"wd:{qid}" for qid in chunk)
            query = (
                "SELECT ?item ?type WHERE { "
                f"VALUES ?item {{ {values} }} "
                "OPTIONAL { ?item wdt:P31 ?type. } "
                "OPTIONAL { ?item wdt:P279 ?type. } "
                "}"
            )
            params = {"query": query, "format": "json"}
            data = _safe_get_json(self.session, SPARQL_ENDPOINT, params=params) or {}
            bindings = data.get("results", {}).get("bindings", [])
            for b in bindings:
                item_uri = b.get("item", {}).get("value", "")
                item_qid = item_uri.split("/")[-1] if item_uri else None
                if not item_qid:
                    continue
                # type may be missing
                if "type" in b:
                    t_uri = b["type"]["value"]
                    t_qid = t_uri.split("/")[-1]
                    out.setdefault(item_qid, {"types": []})
                    out[item_qid]["types"].append(t_qid)
            # politeness: small pause between heavy SPARQL calls
            time.sleep(0.25)
        return out

    def _validate_types(self, qid_types: List[str]) -> Tuple[bool, List[str]]:
        """
        Given a list of type QIDs (P31/P279 results), return (is_valid, matched_type_names).
        """
        if not qid_types:
            return False, []
        found = set(qid_types) & self._valid_qid_set
        matching_names = [name for name, t_qid in LANGUAGE_TYPE_HIERARCHY if t_qid in found]
        return len(matching_names) > 0, matching_names

    # Distribution map lookup removed; only type classification is required

    def _search_wikipedia_for_title(self, search_term: str, limit: int = 8) -> List[str]:
        """
        Use MediaWiki search API to return list of candidate titles (strings).
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_term,
            "srlimit": limit,
            "format": "json",
        }
        data = _safe_get_json(self.session, WIKIPEDIA_API, params=params) or {}
        results = data.get("query", {}).get("search", [])
        titles = [r["title"] for r in results]
        # small delay to avoid heavy search rates
        time.sleep(0.12)
        return titles

    def resolve_languages(self, names: List[str]) -> Dict[str, Optional[dict]]:
        """
        Main entrypoint.

        Input: list of language names (strings).
                Returns a mapping original_name -> result dict or None. Result dict:
                    {
                        "qid": "Qxxxx",
                        "types": ["language", ...],           # human-friendly matched type names
                    }
        """
        results: Dict[str, Optional[dict]] = {}
        # Normalize names and check cache first
        normalized_map = {orig: normalize_name(orig) for orig in names}
        to_resolve = []
        for orig, norm in normalized_map.items():
            cached = self.cache.get(norm)
            if cached is not None:
                results[orig] = cached
            else:
                # mark for resolution
                results[orig] = None
                to_resolve.append((orig, norm))

        if not to_resolve:
            return results

        # Stage A: try direct page lookups in batches using the input names and "<name> language" variations
        # Build a list of title candidates to query in batch (we'll map matches back)
        # We'll query both the exact name and "<name> language" for all unresolved items
        title_to_orig: Dict[str, str] = {}
        titles_to_query: List[str] = []
        for orig, norm in to_resolve:
            exact = orig.strip()
            alt = f"{exact} language"
            # avoid duplicates in batch list
            for t in (exact, alt):
                if t not in title_to_orig:
                    title_to_orig[t] = orig
                    titles_to_query.append(t)

        # Batch lookup titles
        title_qid_map = self.batch_lookup_titles(titles_to_query)

        # Map back qids to original names (a title might map to a QID)
        orig_qids: Dict[str, str] = {}
        for title, qid in title_qid_map.items():
            if title in title_to_orig and qid:
                orig = title_to_orig[title]
                # prefer exact match over alt; if multiple titles map to different qids for same orig,
                # keep first found (fallbacks later will help)
                if orig not in orig_qids:
                    orig_qids[orig] = qid

        # Stage B: For any found QIDs, batch validate and fetch files
        found_qids = list(set(orig_qids.values()))
        qid_info_map = self.batch_sparql_validate_and_fetch(found_qids)

        # Assemble results for those with qids
        for orig, norm in to_resolve:
            if orig in orig_qids:
                qid = orig_qids[orig]
                info = qid_info_map.get(qid, {"types": []})
                is_valid, matched_types = self._validate_types(info.get("types", []))
                if is_valid:
                    out = {
                        "qid": qid,
                        "types": matched_types,
                    }
                    results[orig] = out
                    # cache by normalized input
                    self.cache.set(normalized_map[orig], out)

        # Stage C: For unresolved names, run a per-name search fallback (limited, sequential, polite)
        unresolved = [orig for orig, _ in to_resolve if results[orig] is None]
        for orig in unresolved:
            # search candidate titles
            candidates = []
            # try several smart variants
            for variant in [orig, f"{orig} language", f"Ancient {orig}", f"Old {orig}", f"{orig}ese"]:
                candidates.extend(self._search_wikipedia_for_title(variant, limit=6))
                # small pause between variant searches
                time.sleep(0.08)

            # de-dup; prioritize titles that look close to the original
            seen = set()
            prioritized = []
            lower_orig = normalize_name(orig)
            for t in candidates:
                if t in seen:
                    continue
                seen.add(t)
                tl = t.lower()
                score = 10
                if tl == lower_orig:
                    score = 0
                elif tl == f"{lower_orig} language":
                    score = 1
                elif tl.startswith(f"{lower_orig} "):
                    score = 2
                elif lower_orig in tl:
                    score = 3
                prioritized.append((score, t))
            prioritized.sort(key=lambda x: x[0])

            # Try each candidate title sequentially until a valid language entity is found
            found_good = False
            for _, title in prioritized[:8]:
                # lookup pageprops for this single title
                page_props = self.batch_lookup_titles([title])
                qid = page_props.get(title)
                if not qid:
                    continue
                # run a small SPARQL validate for this qid
                qinfo = self.batch_sparql_validate_and_fetch([qid]).get(qid, {"types": []})
                is_valid, matched_types = self._validate_types(qinfo.get("types", []))
                if is_valid:
                    out = {
                        "qid": qid,
                        "types": matched_types,
                    }
                    results[orig] = out
                    self.cache.set(normalize_name(orig), out)
                    found_good = True
                    break
                # brief pause to be polite
                time.sleep(0.12)

            if not found_good:
                # store None in cache to avoid repeated heavy retries in short time
                self.cache.set(normalize_name(orig), None)
                results[orig] = None

        return results

