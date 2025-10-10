"""Wikipedia relationship extraction service using infobox + LLM pipeline."""

from __future__ import annotations

import asyncio
import ast
import os
import re
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Sequence, Tuple

import mwparserfromhell
import numpy as np
import requests
from google import genai  # type: ignore
from mwparserfromhell.nodes import Heading
from mwparserfromhell.wikicode import Wikicode
from sentence_transformers import SentenceTransformer

from app.models.language import LanguageInfo, LanguageRelationship

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
DEFAULT_HEADERS = {
    "User-Agent": "GenealogyTreeLanguageService/1.0 (language-tree-service)"
}

DEFAULT_GENAI_MODELS = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-preview-09-2025",
    "models/gemini-2.5-flash-preview-05-20",
    "models/gemini-2.5-pro-preview-06-05",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite-001",
]


FIELD_TO_RELATION: Dict[str, Tuple[str, str]] = {
    "language family": ("belongs to family", "up"),
    "family": ("belongs to family", "up"),
    "familycolor": ("belongs to family", "up"),
    **{f"fam{i}": ("belongs to family", "up") for i in range(1, 21)},
    "dialects": ("is a dialect of", "down"),
    "varieties": ("is a dialect of", "down"),
    "dialect": ("is a dialect of", "down"),
    **{f"dia{i}": ("is a dialect of", "down") for i in range(1, 41)},
    "child": ("is a child of", "down"),
    "children": ("is a child of", "down"),
    **{f"child{i}": ("is a child of", "down") for i in range(1, 21)},
    "descendants": ("descends from", "down"),
    "posterior forms": ("descends from", "down"),
}

INFOTO_TEMPLATE_NAME_PATTERNS: Sequence[re.Pattern[str]] = (
    re.compile(r".*infobox.*", re.IGNORECASE),
    re.compile(r".*language.*", re.IGNORECASE),
    re.compile(r".*proto.*", re.IGNORECASE),
    re.compile(r".*langbox.*", re.IGNORECASE),
)

GENETIC_RELATIONS = [
    "belongs to family",
    "proto language is",
    "descends from",
    "is a child of",
    "is a dialect of",
    "early form of",
    "influenced by",
]

try:
    embed_model: Optional[SentenceTransformer] = SentenceTransformer("all-MiniLM-L6-v2")
    print("[wikipedia_service] Loaded sentence-transformer model 'all-MiniLM-L6-v2'.")
except Exception as exc:  # pragma: no cover - depends on environment
    embed_model = None
    print(f"[wikipedia_service] Failed to load sentence-transformer model: {exc}")

_genai_client: Optional[genai.Client] = None


def _get_genai_client() -> genai.Client:
    global _genai_client
    if _genai_client is None:
        api_key = "AIzaSyCjm3E6c33P7DfORc7lwggHstlughbgY5o"
        print("[wikipedia_service] Initialising Google Generative AI client.")
        _genai_client = genai.Client(api_key=api_key)
    return _genai_client


def fetch_wikitext(title: str, headers: Optional[dict] = None, max_retries: int = 3, backoff: float = 1.0) -> str:
    headers = headers or DEFAULT_HEADERS
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvprop": "content",
        "titles": title,
        "formatversion": "2",
    }
    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(WIKIPEDIA_API, params=params, headers=headers, timeout=20)
            resp.raise_for_status()
            payload = resp.json()
            pages = payload.get("query", {}).get("pages", [])
            if not pages:
                return ""
            page = pages[0]
            if "missing" in page:
                return ""
            return page.get("revisions", [{}])[0].get("content", "") or ""
        except requests.HTTPError as exc:
            status = getattr(exc.response, "status_code", None)
            if status == 403 and attempt < max_retries:
                time.sleep(backoff * attempt)
                continue
            raise
        except Exception as exc:
            if attempt < max_retries:
                time.sleep(backoff * attempt)
            else:
                print(f"[wikipedia_service] Unexpected error fetching wikitext for {title}: {exc}")
    return ""


def _template_name_matches(name: str) -> bool:
    if not name:
        return False
    name = name.strip()
    for pattern in INFOTO_TEMPLATE_NAME_PATTERNS:
        if pattern.search(name):
            return True
    return False


def _extract_links_and_text(value_wikitext: str) -> List[str]:
    if not value_wikitext:
        return []

    node = mwparserfromhell.parse(value_wikitext)
    note_templates = {"efn", "refn", "notelist", "note", "sfn", "harv", "harvnb", "harvcol", "harvcolnb", "harvcoltxt"}
    for template in list(node.filter_templates()):
        if str(template.name).strip().lower() in note_templates:
            node.remove(template)
    for tag in list(node.filter_tags()):
        if tag.tag.lower() == "ref":
            node.remove(tag)

    results: List[str] = []
    for link in node.filter_wikilinks():
        target = str(link.title).strip()
        if "#" in target:
            target = target.split("#", 1)[0].strip()
        if target:
            results.append(target)

    if not results:
        text = node.strip_code().strip()
        if text:
            parts = re.split(r"\s*(?:,|/|;|\band\b|\bor\b)\s*", text)
            results.extend([p.strip() for p in parts if p.strip()])

    deduped: List[str] = []
    seen = set()
    for item in results:
        if item and item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def parse_infobox_from_wikitext(wikitext: str) -> List[Tuple[str, str, str]]:
    triples: List[Tuple[str, str, str]] = []
    if not wikitext:
        return triples

    parsed = mwparserfromhell.parse(wikitext)
    templates = parsed.filter_templates()
    infobox_templates = [t for t in templates if _template_name_matches(str(t.name).strip())]

    if not infobox_templates:
        return triples

    for template in infobox_templates:
        subject = None
        if template.has("name"):
            subject = template.get("name").value.strip_code().strip()
        if not subject:
            subject = "__PAGE__"

        fam_chain: List[List[str]] = []
        base_fam_keys = ["language family", "family", "familycolor"]
        for key in base_fam_keys:
            if template.has(key):
                fam_chain.append(_extract_links_and_text(str(template.get(key).value)))
        for i in range(1, 20):
            key = f"fam{i}"
            if template.has(key):
                fam_chain.append(_extract_links_and_text(str(template.get(key).value)))
        fam_chain_flat = [item for sublist in fam_chain for item in sublist]
        if fam_chain_flat:
            fam_chain_flat.append(subject)
            for idx in range(len(fam_chain_flat) - 1):
                triples.append((fam_chain_flat[idx + 1], "belongs to family", fam_chain_flat[idx]))

        for param in template.params:
            key = str(param.name).strip().lower()
            if key not in FIELD_TO_RELATION:
                continue
            rel, direction = FIELD_TO_RELATION[key]
            if direction != "down":
                if rel != "Proto language is":
                    continue
            val = str(param.value).strip()
            if not val:
                continue
            objs = _extract_links_and_text(val)
            for obj in objs:
                triples.append((obj, rel, subject))

    seen = set()
    unique: List[Tuple[str, str, str]] = []
    for a, b, c in triples:
        trip = (a.strip(), b.strip(), c.strip())
        if trip[0] and trip[2] and trip not in seen:
            unique.append(trip)
            seen.add(trip)
    return unique


def extract_clean_sections(wikitext: str) -> Dict[str, str]:
    if not wikitext:
        return {}
    parsed = mwparserfromhell.parse(wikitext)
    sections: Dict[str, str] = {}
    current_section = "Introduction"
    content: List[str] = []
    for node in parsed.nodes:
        if isinstance(node, Heading):
            if content:
                sections[current_section] = " ".join(content).strip()
            current_section = str(node.title).strip() or "Untitled"
            content = []
        else:
            clean = Wikicode([node]).strip_code().strip()
            if clean:
                content.append(clean)
    if content:
        sections[current_section] = " ".join(content).strip()
    return sections


def select_relevant_chunks(sections: Dict[str, str], top_k: int = 20) -> str:
    if not sections or embed_model is None:
        print("[wikipedia_service] Embedding model unavailable or no sections to select from.")
        return ""
    query = "Genetic language relationships, family trees,belongs to family,descends from,is a child of,part of, ancestry, dialects,early form of,influenced and historical linguistic evolution."
    query_emb = embed_model.encode(query, normalize_embeddings=True)
    chunks = [
        f"Section: {title}\n{paragraph.strip()}"
        for title, text in sections.items()
        for paragraph in text.split("\n")
        if paragraph.strip()
    ]
    if not chunks:
        return ""
    chunk_embs = embed_model.encode(chunks, normalize_embeddings=True)
    similarities = np.dot(chunk_embs, query_emb)
    top_indices = np.argsort(similarities)[-top_k:]
    return "\n\n".join(chunks[i] for i in top_indices if 0 <= i < len(chunks))


def parse_list_like_from_text(raw: str):
    if not raw:
        return None
    cleaned = re.sub(r"```(?:python)?", "", raw, flags=re.I).strip()
    cleaned = cleaned.replace("```", "").strip()
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if not match:
        print("[wikipedia_service] Parser warning: could not find list-like structure [] in LLM response.")
        return None
    list_str = match.group(0)
    try:
        return ast.literal_eval(list_str)
    except (ValueError, SyntaxError) as exc:
        print(f"[wikipedia_service] Parser error: could not parse extracted list string. Error: {exc}")
        return None


def get_normalized_hierarchical_graph(
    infobox_triples: List[Tuple[str, str, str]],
    relevant_text: str,
    language: str,
) -> List[Tuple[str, str, str]]:
    if not infobox_triples and not relevant_text:
        print(f"[wikipedia_service] No infobox triples or relevant text for {language}.")
        return []

    client = _get_genai_client()
    models_to_try = _get_model_candidates()
    infobox_triples_str = "\n".join([str(t) for t in infobox_triples])
    prompt = f"""
You are an expert in historical linguistics. Your task is to create a single, unified, and strictly hierarchical graph of genetic language relationships for "{language}".

You are given infobox triples and relevant text.

**CRITICAL INSTRUCTIONS:**
1.  **Normalize ALL relationships** to the single format: `('Child Language', 'is child of', 'Parent Language')`.
2.  **Create a Strict Hierarchy**: Each language or dialect must have **only ONE direct parent**. If Spanish evolved from Old Spanish, which evolved from Latin, the output must be `('Spanish', 'is child of', 'Old Spanish')` and `('Old Spanish', 'is child of', 'Latin')`.
3.  **DO NOT include redundant "grandfather" links**. For the example above, you must NOT output `('Spanish', 'is child of', 'Latin')`. Only include the link to the immediate parent.
4.  **Merge and Deduplicate**: Combine information from both the infobox and the text, then remove any exact duplicate triples.
5.  **Be Accurate**: Only include relationships explicitly stated in the provided context.

**Final Output Format**: A single Python list of (`subject`, `relation`, `object`) tuples.

---
**INPUT DATA for "{language}"**
**1. Infobox Triples:**
{infobox_triples_str}

**2. Relevant Text:**
{relevant_text}
Produce the final, normalized, and strictly hierarchical list of triples now."""
    last_error: Optional[Exception] = None
    for model in models_to_try:
        try:
            print(f"[wikipedia_service] Calling Generative AI model '{model}' for {language}.")
            response = client.models.generate_content(model=model, contents=prompt)
            response_text = getattr(response, "text", "")
            print(f"[wikipedia_service] LLM raw response for {language}: {response_text}")
            if not response_text:
                print(f"[wikipedia_service] LLM returned an empty response for {language}.")
                last_error = RuntimeError("LLM returned empty response")
                continue
            parsed = parse_list_like_from_text(response_text)
            if not parsed:
                print(f"[wikipedia_service] LLM response for {language} could not be parsed into a list.")
                last_error = RuntimeError("LLM response parsing failed")
                continue
            final_triples: List[Tuple[str, str, str]] = []
            seen = set()
            for item in parsed:
                if isinstance(item, (list, tuple)) and len(item) == 3:
                    subj, rel, obj = str(item[0]).strip(), str(item[1]).strip(), str(item[2]).strip()
                    if rel == "is child of" and subj and obj:
                        triple = (subj, rel, obj)
                        if triple not in seen:
                            final_triples.append(triple)
                            seen.add(triple)
            if final_triples:
                print(
                    f"[wikipedia_service] Successfully obtained hierarchical graph for {language} using model '{model}'."
                )
                return final_triples
            last_error = RuntimeError("LLM produced no valid triples")
        except Exception as exc:
            print(f"[wikipedia_service] Error during LLM processing with model '{model}' for {language}: {exc}")
            last_error = exc

    print(f"[wikipedia_service] All LLM attempts failed for {language}. Returning empty list.")
    if last_error:
        print(f"[wikipedia_service] Last LLM error: {last_error}")
    return []


def get_wikipedia_language_page_title(input_name: str) -> Optional[str]:
    headers = DEFAULT_HEADERS
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": input_name,
        "srlimit": 10,
    }
    try:
        resp = requests.get(WIKIPEDIA_API, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
    except Exception as exc:
        print(f"[wikipedia_service] Failed to resolve page title for '{input_name}': {exc}")
        return None

    if not results:
        return None

    input_words = set(input_name.lower().split())
    best_match = None
    best_match_score = -1
    for entry in results:
        title = entry.get("title")
        if not title:
            continue
        title_words = set(title.lower().replace("-", " ").split())
        score = len(input_words.intersection(title_words))
        has_language_suffix = title.lower().endswith("language") or title.lower().endswith("languages")
        if score > best_match_score and has_language_suffix:
            best_match = title
            best_match_score = score
    if best_match:
        return best_match
    return results[0].get("title") if results else None


def _normalise_infobox_triples(
    infobox_triples: List[Tuple[str, str, str]],
    page_title: str,
) -> List[Tuple[str, str, str]]:
    processed: List[Tuple[str, str, str]] = []
    for subject, relation, obj in infobox_triples:
        subject_resolved = page_title if subject == "__PAGE__" else subject
        object_resolved = page_title if obj == "__PAGE__" else obj
        processed.append((subject_resolved, relation, object_resolved))
    return processed


def _build_relationship_graph(
    triples: List[Tuple[str, str, str]]
) -> Tuple[Dict[str, str], Dict[str, set[str]]]:
    parent_map: Dict[str, str] = {}
    children_map: Dict[str, set[str]] = defaultdict(set)
    for child, relation, parent in triples:
        if relation != "is child of":
            continue
        parent_map[child] = parent
        children_map[parent].add(child)
    return parent_map, children_map


def _normalise_label_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]", "", label.lower())


def _strip_language_tokens(label: str) -> str:
    return re.sub(r"\blanguages?\b", "", label, flags=re.I).strip()


def _get_model_candidates() -> List[str]:
    raw_list = os.getenv("GOOGLE_GENAI_MODEL_LIST")
    if raw_list:
        candidates = [model.strip() for model in raw_list.split(",") if model.strip()]
        if candidates:
            return candidates

    primary = os.getenv("GOOGLE_GENAI_MODEL")
    if primary:
        ordered = [primary]
        ordered.extend(model for model in DEFAULT_GENAI_MODELS if model != primary)
        return ordered

    return DEFAULT_GENAI_MODELS


def _find_graph_root_label(
    root_label: str,
    parent_map: Dict[str, str],
    children_map: Dict[str, set[str]],
) -> Optional[str]:
    graph_nodes = (
        set(parent_map.keys())
        | set(parent_map.values())
        | set(children_map.keys())
    )
    if not graph_nodes:
        return None

    normalised_lookup: Dict[str, str] = {}
    for node in graph_nodes:
        key = _normalise_label_key(node)
        if key and key not in normalised_lookup:
            normalised_lookup[key] = node

    def _candidates(name: str) -> List[str]:
        variants = {name}
        stripped = _strip_language_tokens(name)
        if stripped:
            variants.add(stripped)
        if "(" in name:
            variants.add(name.split("(", 1)[0].strip())
        if name.lower().endswith(" language"):
            variants.add(name[: -len(" language")].strip())
        if name.lower().endswith(" languages"):
            variants.add(name[: -len(" languages")].strip())
        return [variant for variant in variants if variant]

    for candidate in _candidates(root_label):
        for node in graph_nodes:
            if node.lower() == candidate.lower():
                return node
        normalised_candidate = _normalise_label_key(candidate)
        if normalised_candidate in normalised_lookup:
            return normalised_lookup[normalised_candidate]
        stripped_normalised = _normalise_label_key(_strip_language_tokens(candidate))
        if stripped_normalised in normalised_lookup:
            return normalised_lookup[stripped_normalised]

    return None


def _relationships_within_depth(
    root: str,
    depth: Optional[int],
    parent_map: Dict[str, str],
    children_map: Dict[str, set[str]],
) -> List[Tuple[LanguageRelationship, str, int]]:
    if depth is not None and depth <= 0:
        return []

    bounded: List[Tuple[LanguageRelationship, str, int]] = []
    seen_edges: set[Tuple[str, str, str]] = set()

    if (
        root not in parent_map
        and root not in children_map
        and root not in parent_map.values()
    ):
        print(
            f"[wikipedia_service] Warning: root '{root}' not present in relationship graph."
        )
        return []

    current = root
    current_level = 1
    while True:
        parent = parent_map.get(current)
        if not parent:
            break
        edge_key = (current, "is child of", parent)
        if edge_key not in seen_edges:
            bounded.append(
                (
                    LanguageRelationship(
                        language1=current,
                        relationship="is child of",
                        language2=parent,
                    ),
                    "ancestor",
                    current_level,
                )
            )
            seen_edges.add(edge_key)
        current = parent
        current_level += 1
        if depth is not None and current_level > depth:
            break

    queue = deque([(root, 0)])
    seen_nodes = {root}
    while queue:
        node, level = queue.popleft()
        if depth is not None and level >= depth:
            continue
        for child in children_map.get(node, set()):
            edge_key = (child, "is child of", node)
            if edge_key not in seen_edges:
                bounded.append(
                    (
                        LanguageRelationship(
                            language1=child,
                            relationship="is child of",
                            language2=node,
                        ),
                        "descendant",
                        level + 1,
                    )
                )
                seen_edges.add(edge_key)
            if child not in seen_nodes:
                queue.append((child, level + 1))
                seen_nodes.add(child)

    return bounded


async def _send_status(message: str, progress: Optional[int], websocket_manager, connection_id) -> None:
    if websocket_manager and connection_id:
        await websocket_manager.send_status(message, progress, connection_id)


async def _send_root_language(label: str, websocket_manager, connection_id) -> None:
    if websocket_manager and connection_id:
        await websocket_manager.send_json({"type": "root_language", "data": {"label": label}}, connection_id)


async def fetch_language_relationships(
    language_name: str,
    depth: Optional[int],
    websocket_manager=None,
    connection_id: Optional[str] = None,
) -> List[Dict[str, object]]:
    depth_desc = f"depth={depth}" if depth is not None else "full-tree"
    print(f"[wikipedia_service] Starting extraction for '{language_name}' ({depth_desc}).")

    await _send_status("Resolving Wikipedia page title...", 5, websocket_manager, connection_id)
    resolved_title = await asyncio.to_thread(get_wikipedia_language_page_title, language_name)
    if not resolved_title:
        raise ValueError(f"Unable to find a Wikipedia page for '{language_name}'")
    print(f"[wikipedia_service] Resolved '{language_name}' to '{resolved_title}'.")
    await _send_root_language(resolved_title, websocket_manager, connection_id)

    await _send_status(f"Fetching Wikipedia content for '{resolved_title}'...", 15, websocket_manager, connection_id)
    wikitext = await asyncio.to_thread(fetch_wikitext, resolved_title)
    if not wikitext:
        raise ValueError(f"No Wikipedia content found for '{resolved_title}'")
    print(f"[wikipedia_service] Fetched wikitext for '{resolved_title}' ({len(wikitext)} characters).")

    await _send_status("Parsing infobox data...", 30, websocket_manager, connection_id)
    raw_infobox_triples = await asyncio.to_thread(parse_infobox_from_wikitext, wikitext)
    infobox_processed = _normalise_infobox_triples(raw_infobox_triples, resolved_title)
    print(f"[wikipedia_service] Extracted {len(infobox_processed)} infobox triples for '{resolved_title}'.")

    await _send_status("Extracting relevant sections...", 45, websocket_manager, connection_id)
    sections = await asyncio.to_thread(extract_clean_sections, wikitext)
    relevant_text = ""
    if sections:
        relevant_text = await asyncio.to_thread(select_relevant_chunks, sections)
    print(f"[wikipedia_service] Selected {len(relevant_text)} characters of relevant text for '{resolved_title}'.")

    await _send_status("Synthesising hierarchical relationships with LLM...", 70, websocket_manager, connection_id)
    final_triples = await asyncio.to_thread(
        get_normalized_hierarchical_graph,
        infobox_processed,
        relevant_text,
        resolved_title,
    )
    print(f"[wikipedia_service] LLM produced {len(final_triples)} hierarchical triples for '{resolved_title}'.")

    parent_map, children_map = _build_relationship_graph(final_triples)
    graph_root = _find_graph_root_label(resolved_title, parent_map, children_map)
    if graph_root and graph_root != resolved_title:
        print(
            f"[wikipedia_service] Using graph node '{graph_root}' as root for depth traversal."
        )
    elif not graph_root:
        print(
            f"[wikipedia_service] Unable to directly match '{resolved_title}' in graph; using page title as fallback."
        )
    traversal_root = graph_root or resolved_title

    bounded_relationships = _relationships_within_depth(
        traversal_root,
        depth,
        parent_map,
        children_map,
    )

    relationships_payload: List[Dict[str, object]] = []
    for rel_model, relation_type, level in bounded_relationships:
        payload = rel_model.model_dump()
        payload.update({"direction": relation_type, "level": level})
        relationships_payload.append(payload)

    if websocket_manager and connection_id:
        await websocket_manager.send_json({"type": "relationships", "data": relationships_payload}, connection_id)

    if depth is None:
        summary = f"Generated {len(relationships_payload)} relationships (full hierarchy)."
    else:
        summary = f"Generated {len(relationships_payload)} relationships within depth {depth}."

    await _send_status(
        summary,
        95,
        websocket_manager,
        connection_id,
    )
    print(
        f"[wikipedia_service] Completed extraction for '{resolved_title}' with "
        f"{len(relationships_payload)} relationships ({depth_desc})."
    )

    return relationships_payload


async def fetch_language_info(qid: str) -> Optional[LanguageInfo]:
    print(f"[wikipedia_service] fetch_language_info called for {qid} but not implemented.")
    return None


def get_distribution_map_image(qid: str) -> Optional[str]:
    print(f"[wikipedia_service] get_distribution_map_image called for {qid} but not implemented.")
    return None
