#!/usr/bin/env python3
"""
Language family graph extractor
- Entry: language name (English wikipedia title) and depth (int)
- Output: NetworkX graph object + JSON export (nodes/edges)
"""

import asyncio
import json
import os
import re
import time
from collections import deque, defaultdict
from typing import Dict, List, Optional, Set, Tuple

import httpx
import networkx as nx
from bs4 import BeautifulSoup

# Optional: spaCy coref (will try to import but fallback if not present)
try:
    import spacy

    HAS_SPACY = True
    # do not load model by default; user can enable later
except Exception:
    HAS_SPACY = False

# ---- Simple file cache to avoid repeated network calls ----
import shelve

CACHE_PATH = "wf_cache.db"


def cache_get(key: str):
    with shelve.open(CACHE_PATH) as db:
        return db.get(key)


def cache_set(key: str, value):
    with shelve.open(CACHE_PATH) as db:
        db[key] = value


# ---- Wikidata / Wikipedia helpers (async) ----
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
WIKIDATA_ENTITY_JSON = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

HEADERS = {"User-Agent": "LangFamilyBot/1.0 (data-science project; contact: none)"}  # be polite


async def fetch_wikipedia_page_html(title: str, client: httpx.AsyncClient) -> Optional[str]:
    """Get Wikipedia page HTML for optional infobox parsing."""
    key = f"wiki_html::{title}"
    cached = cache_get(key)
    if cached:
        return cached
    params = {
        "action": "parse",
        "page": title,
        "prop": "text",
        "format": "json",
        "formatversion": 2,
    }
    try:
        r = await client.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=30.0)
        r.raise_for_status()
        j = r.json()
        html = j.get("parse", {}).get("text")
        cache_set(key, html)
        return html
    except Exception:
        return None


async def get_wikibase_qid_from_wikipedia(title: str, client: httpx.AsyncClient) -> Optional[str]:
    """Use Wikipedia API to get pageprops.wikibase_item (the Wikidata QID)."""
    key = f"wiki_qid::{title}"
    cached = cache_get(key)
    if cached:
        return cached
    params = {
        "action": "query",
        "titles": title,
        "prop": "pageprops",
        "format": "json",
        "formatversion": 2,
    }
    r = await client.get(WIKIPEDIA_API, params=params, headers=HEADERS, timeout=20.0)
    r.raise_for_status()
    j = r.json()
    pages = j.get("query", {}).get("pages", [])
    if not pages:
        return None
    page = pages[0]
    q = page.get("pageprops", {}).get("wikibase_item")
    if q:
        cache_set(key, q)
    return q


async def get_wikidata_entity_labels(qids: List[str], client: httpx.AsyncClient) -> Dict[str, str]:
    """Fetch labels for QIDs in English via wbgetentities. Returns mapping qid->label."""
    # batch them
    out = {}
    to_fetch = []
    for q in qids:
        key = f"wd_label::{q}"
        cached = cache_get(key)
        if cached:
            out[q] = cached
        else:
            to_fetch.append(q)
    if not to_fetch:
        return out
    ids = "|".join(to_fetch)
    params = {"action": "wbgetentities", "ids": ids, "props": "labels", "languages": "en", "format": "json"}
    r = await client.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=30.0)
    r.raise_for_status()
    j = r.json()
    entities = j.get("entities", {})
    for q, ent in entities.items():
        label = ent.get("labels", {}).get("en", {}).get("value") or ent.get("labels", {}).get("") or q
        out[q] = label
        cache_set(f"wd_label::{q}", label)
    return out


async def get_wikidata_parents(qid: str, client: httpx.AsyncClient) -> List[str]:
    """Get P279 (subclass of) targets for the entity (list of QIDs)."""
    key = f"wd_parents::{qid}"
    cached = cache_get(key)
    if cached:
        return cached
    params = {"action": "wbgetentities", "ids": qid, "props": "claims", "format": "json"}
    r = await client.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=30.0)
    r.raise_for_status()
    j = r.json()
    parents = []
    entities = j.get("entities", {})
    ent = entities.get(qid, {})
    claims = ent.get("claims", {})
    if "P279" in claims:
        for claim in claims["P279"]:
            mainsnak = claim.get("mainsnak", {})
            datavalue = mainsnak.get("datavalue", {})
            value = datavalue.get("value", {})
            target = value.get("id")
            if target:
                parents.append(target)
    cache_set(key, parents)
    return parents


async def get_wikidata_children(qid: str, client: httpx.AsyncClient) -> List[str]:
    """
    Reverse lookup via SPARQL: find entities where wdt:P279 = wd:QID
    Returns list of QIDs (may be large)
    """
    key = f"wd_children::{qid}"
    cached = cache_get(key)
    if cached:
        return cached
    # SPARQL
    query = f"""
    SELECT ?child WHERE {{
      ?child wdt:P279 wd:{qid} .
    }}
    LIMIT 500
    """
    headers = {"User-Agent": "LangFamilyBot/1.0 (sparql)", "Accept": "application/sparql-results+json"}
    params = {"query": query}
    r = await client.get(WIKIDATA_SPARQL, params=params, headers=headers, timeout=60.0)
    r.raise_for_status()
    j = r.json()
    results = j.get("results", {}).get("bindings", [])
    children = []
    for b in results:
        uri = b["child"]["value"]  # e.g. https://www.wikidata.org/entity/Qxxxx
        m = re.search(r"/(Q\d+)$", uri)
        if m:
            children.append(m.group(1))
    cache_set(key, children)
    return children


def parse_infobox_relations(html: str) -> Dict[str, List[str]]:
    """Minimal infobox parser: grabs rows and looks for family/dialects keys (heuristic)."""
    if not html:
        return {}
    soup = BeautifulSoup(html, "lxml")
    infobox = soup.find("table", class_=re.compile(r"infobox"))
    if not infobox:
        return {}
    rows = infobox.find_all("tr")
    relations = defaultdict(list)
    for r in rows:
        th = r.find("th")
        td = r.find("td")
        if not th or not td:
            continue
        key = th.get_text(strip=True).lower()
        val = td.get_text(" ", strip=True)
        if not val:
            continue
        # heuristics
        if "family" in key or "language family" in key:
            relations["family"].append(val)
        if "dialect" in key or "variety" in key:
            relations["dialects"].append(val)
        if "iso" in key:
            relations["iso"].append(val)
    return dict(relations)


# ---- Optional LLM helper (Groq / Llama3-8B) ----
# This is a small wrapper illustrating how you'd call Groq. It is disabled by default.
# You MUST set GROQ_API_KEY environment variable and configure endpoint per your plan.
# The code below avoids calling the LLM unless `use_llm=True` in pipeline.

async def llm_extract_relations_from_text(text: str, client: httpx.AsyncClient, api_key: str, max_calls=1) -> List[Tuple[str, str]]:
    """
    Minimal example: send a short prompt asking for 'parent/child' relations found in text.
    Returns list of tuples (relation_type, mention_text). This is optional and minimal.
    """
    if not api_key:
        return []
    # Example Groq endpoint placeholder (user must fill with actual)
    GROQ_ENDPOINT = os.environ.get("GROQ_ENDPOINT", "https://api.groq.com/v1/llama3-8b-instruct")
    # Keep prompt small since you have a free plan — use sparingly
    prompt = (
        "Extract language relationships from the following text. "
        "Return JSON array of objects with fields `type` (one of parent, child, dialect, family) and `mention`.\n\n"
        f"Text:\n{text[:12000]}\n\nReturn only JSON."
    )
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "User-Agent": "LangFamilyBot/1.0"}
    payload = {"prompt": prompt, "max_tokens": 400}
    try:
        r = await client.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=60.0)
        r.raise_for_status()
        j = r.json()
        # This will depend on the API shape; here's an illustrative parse:
        out_text = j.get("text") or json.dumps(j)
        # try load json from out_text
        try:
            parsed = json.loads(out_text)
            results = [(o.get("type"), o.get("mention")) for o in parsed]
            return results
        except Exception:
            return []
    except Exception:
        return []


# ---- Main graph builder ----

class LangFamilyGraphBuilder:
    def __init__(self, client: httpx.AsyncClient, use_infobox: bool = True, use_llm: bool = False, llm_api_key: Optional[str] = None, spacy_model: Optional[str] = None):
        self.client = client
        self.graph = nx.DiGraph()
        self.use_infobox = use_infobox
        self.use_llm = use_llm
        self.llm_api_key = llm_api_key
        self.spacy_model = spacy_model
        self.visited: Set[str] = set()

    async def add_node(self, qid: str, label: str, source: str):
        if not self.graph.has_node(qid):
            self.graph.add_node(qid, label=label, source=source)
        else:
            # update sources
            srcs = set(self.graph.nodes[qid].get("source", "").split("|"))
            srcs.add(source)
            self.graph.nodes[qid]["source"] = "|".join(sorted(srcs))

    async def add_edge(self, a: str, b: str, relation: str):
        # edges are directed a -> b
        self.graph.add_edge(a, b, relation=relation)

    async def expand_node(self, qid: str):
        """Fetch parents/children and infobox; return dict of lists."""
        parents = await get_wikidata_parents(qid, self.client)
        children = await get_wikidata_children(qid, self.client)
        info = {"parents": parents, "children": children}
        if self.use_infobox:
            # try to find a wikipedia title for this QID and fetch page for infobox parsing
            # wbgetentities can contain sitelinks, but simpler: query wikidata to get wikipedia sitelink
            key = f"wd_sitelink::{qid}"
            sitelink = cache_get(key)
            if sitelink is None:
                params = {"action": "wbgetentities", "ids": qid, "props": "sitelinks", "format": "json"}
                r = await self.client.get(WIKIDATA_API, params=params, headers=HEADERS, timeout=30.0)
                r.raise_for_status()
                j = r.json()
                ent = j.get("entities", {}).get(qid, {})
                sl = ent.get("sitelinks", {}).get("enwiki", {})
                sitelink = sl.get("title") if sl else None
                cache_set(key, sitelink)
            if sitelink:
                html = await fetch_wikipedia_page_html(sitelink, self.client)
                parsed = parse_infobox_relations(html or "")
                info["infobox"] = parsed
        return info

    async def build(self, start_title: str, depth: int = 2):
        # Resolve start title -> QID
        start_qid = await get_wikibase_qid_from_wikipedia(start_title, self.client)
        print(start_qid)
        if not start_qid:
            raise ValueError(f"Could not resolve '{start_title}' to a Wikidata QID.")
        start_label = (await get_wikidata_entity_labels([start_qid], self.client)).get(start_qid, start_qid)
        await self.add_node(start_qid, start_label, source="start")
        # BFS queue: (qid, remaining_depth)
        q = deque()
        q.append((start_qid, depth))
        self.visited.add(start_qid)
        # But we want to still re-visit nodes at different depths if needed for sibling expansions; so visited controls infinite loops
        while q:
            qid, rem = q.popleft()
            if rem <= 0:
                continue
            # fetch relations
            try:
                info = await self.expand_node(qid)
            except Exception as e:
                # if one node fails, continue
                print(f"Warning: failed expand {qid}: {e}")
                continue
            # get labels for newly discovered qids
            all_qs = set(info.get("parents", []) + info.get("children", []))
            print(all_qs)
            labels = {}
            if all_qs:
                labels = await get_wikidata_entity_labels(list(all_qs), self.client)
            # Add parent edges (child -> parent with relation 'subclass_of')
            for p in info.get("parents", []):
                lbl = labels.get(p, p)
                await self.add_node(p, lbl, source="P279_parent")
                await self.add_edge(qid, p, relation="subclass_of")
                # siblings will be discovered when fetching parent's children
                if p not in self.visited:
                    q.append((p, rem - 1))
                    self.visited.add(p)
            # Add children edges (parent -> child with relation 'has_subclass')
            for c in info.get("children", []):
                lbl = labels.get(c, c)
                await self.add_node(c, lbl, source="P279_child")
                await self.add_edge(qid, c, relation="has_subclass")
                if c not in self.visited:
                    q.append((c, rem - 1))
                    self.visited.add(c)
            # Siblings: for each parent, find its children and add sibling_of edges among them
            for p in info.get("parents", []):
                siblings = await get_wikidata_children(p, self.client)
                # ensure labels for siblings
                sib_labels = {}
                if siblings:
                    sib_labels = await get_wikidata_entity_labels(siblings, self.client)
                for s in siblings:
                    if s == qid:
                        continue
                    s_lbl = sib_labels.get(s, s)
                    await self.add_node(s, s_lbl, source="sibling")
                    await self.add_edge(qid, s, relation="sibling_of")
                    # optionally add bidirectional sibling edge
                    await self.add_edge(s, qid, relation="sibling_of")
                    if s not in self.visited:
                        q.append((s, rem - 1))
                        self.visited.add(s)
            # Infobox-derived relations (heuristic) - we only attach textual mentions as properties
            inf = info.get("infobox", {})
            if inf:
                # store as node attributes (text mentions); not converting to QIDs automatically
                curr_lbl = self.graph.nodes[qid].get("label", qid)
                self.graph.nodes[qid].setdefault("infobox", {})
                for k, vals in inf.items():
                    self.graph.nodes[qid]["infobox"].setdefault(k, []).extend(vals)
            # Optional LLM extraction (disabled by default; will be used only if configured)
            if self.use_llm and self.llm_api_key:
                # fetch the Wikipedia page text and pass to llm_extract_relations_from_text
                # caution: limited LLM calls for free plan, so this should be used sparingly
                sitelink = cache_get(f"wd_sitelink::{qid}")
                if sitelink:
                    html = await fetch_wikipedia_page_html(sitelink, self.client)
                    # strip tags to plain text
                    if html:
                        soup = BeautifulSoup(html, "lxml")
                        text = soup.get_text("\n", strip=True)
                        llm_rels = await llm_extract_relations_from_text(text, self.client, api_key=self.llm_api_key)
                        # attach results as node property
                        if llm_rels:
                            self.graph.nodes[qid].setdefault("llm_rels", []).extend(llm_rels)
        return self.graph


# ---- Exports ----
def graph_to_json(graph: nx.DiGraph) -> Dict:
    nodes = []
    for n, data in graph.nodes(data=True):
        nodes.append({"id": n, "label": data.get("label"), **{k: v for k, v in data.items() if k != "label"}})
    edges = []
    for a, b, data in graph.edges(data=True):
        edges.append({"source": a, "target": b, "relation": data.get("relation")})
    return {"nodes": nodes, "edges": edges}


# ---- CLI usage ----
async def main_async(title: str, depth: int = 2, out_json: str = "lang_graph.json", use_infobox: bool = True, use_llm: bool = False):
    async with httpx.AsyncClient(timeout=60.0) as client:
        builder = LangFamilyGraphBuilder(client, use_infobox=use_infobox, use_llm=use_llm, llm_api_key="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")
        graph = await builder.build(title, depth=depth)
        data = graph_to_json(graph)
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Also save a pickled NetworkX graph
        nx.write_gexf(graph, out_json.replace(".json", ".gexf"))
        print(f"Saved JSON -> {out_json} and Graph (GEXF) -> {out_json.replace('.json', '.gexf')}")
        # Very small summary
        print(f"Nodes: {graph.number_of_nodes()}, Edges: {graph.number_of_edges()}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build language family graph from English Wikipedia + Wikidata")
    parser.add_argument("title", help="English Wikipedia page title for the language (e.g. 'English')")
    parser.add_argument("--depth", type=int, default=2, help="Depth to explore (both up & down)")
    parser.add_argument("--out", default="lang_graph.json", help="Output JSON path")
    parser.add_argument("--no-infobox", dest="infobox", action="store_false", help="Disable infobox scraping")
    parser.add_argument("--use-llm", dest="llm", action="store_true", help="Enable optional LLM extractions (requires GROQ_API_KEY env var)")
    args = parser.parse_args()
    asyncio.run(main_async(args.title, depth=args.depth, out_json=args.out, use_infobox=args.infobox, use_llm=args.llm))


if __name__ == "__main__":
    main()
