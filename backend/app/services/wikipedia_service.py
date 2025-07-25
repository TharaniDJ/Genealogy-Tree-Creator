from typing import List, Dict
import requests
import asyncio

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

async def fetch_relationships(page_title: str, depth: int) -> List[Dict[str, str]]:
    """
    Fetch genealogical relationships for a given Wikipedia page title and depth.
    Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
    """
    qid = get_qid(page_title)
    return collect_bidirectional_relationships(qid, depth)

def get_qid(page_title: str) -> str:
    """Return the Wikidata Q-identifier for a Wikipedia page title."""
    params = {
        "action": "query",
        "titles": page_title,
        "prop": "pageprops",
        "ppprop": "wikibase_item",
        "format": "json",
    }
    data = requests.get(WIKIPEDIA_API, params=params).json()
    for page in data["query"]["pages"].values():
        if "pageprops" in page and "wikibase_item" in page["pageprops"]:
            return page["pageprops"]["wikibase_item"]
    raise ValueError(f"Q-id not found for page: {page_title}")

def fetch_entity(qid: str) -> dict:
    """Return the full JSON entity document for a given QID."""
    url = WIKIDATA_API.format(qid)
    return requests.get(url).json()["entities"][qid]

def get_labels(qids: set) -> Dict[str, str]:
    """Batch-fetch labels for a set of Q-ids (returns dict)."""
    if not qids:
        return {}
    params = {
        "action": "wbgetentities",
        "ids": "|".join(qids),
        "props": "labels",
        "languages": "en",
        "format": "json",
    }
    data = requests.get("https://www.wikidata.org/w/api.php", params=params).json()
    return {
        qid: data["entities"][qid]["labels"]["en"]["value"]
        for qid in data["entities"]
        if "labels" in data["entities"][qid] and "en" in data["entities"][qid]["labels"]
    }

def collect_relationships(qid: str, depth: int, direction: str, relationships: List[Dict[str, str]], visited: set, all_qids: set):
    """
    Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
    direction: 'up' (ancestors) or 'down' (descendants)
    """
    if depth == 0 or qid in visited:
        return
    visited.add(qid)

    entity = fetch_entity(qid)
    claims = entity.get("claims", {})

    if direction == "up":  # Ancestors via P22 (father) and P25 (mother)
        for snak in claims.get("P22", []):  # Father relationships
            father_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append({"entity1": qid, "relationship": "child of", "entity2": father_qid})
            all_qids.update([qid, father_qid])
            collect_relationships(father_qid, depth - 1, direction, relationships, visited, all_qids)

        for snak in claims.get("P25", []):  # Mother relationships
            mother_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append({"entity1": qid, "relationship": "child of", "entity2": mother_qid})
            all_qids.update([qid, mother_qid])
            collect_relationships(mother_qid, depth - 1, direction, relationships, visited, all_qids)

    elif direction == "down":  # Descendants via P40 (child)
        for snak in claims.get("P40", []):  # Child relationships
            child_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append({"entity1": child_qid, "relationship": "child of", "entity2": qid})
            all_qids.update([child_qid, qid])

            # Check if spouse is also a parent of this child
            child_entity = fetch_entity(child_qid)
            child_claims = child_entity.get("claims", {})
            child_parents = set()
            for parent_prop in ["P22", "P25"]:  # Father and mother
                for parent_snak in child_claims.get(parent_prop, []):
                    parent_qid = parent_snak["mainsnak"]["datavalue"]["value"]["id"]
                    child_parents.add(parent_qid)

            for spouse_snak in claims.get("P26", []):  # Spouse relationships
                spouse_qid = spouse_snak["mainsnak"]["datavalue"]["value"]["id"]
                if spouse_qid in child_parents:
                    relationships.append({"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid})
                    all_qids.add(spouse_qid)

            collect_relationships(child_qid, depth - 1, direction, relationships, visited, all_qids)

    # Collect spouse relationships (P26) regardless of direction
    for snak in claims.get("P26", []):
        spouse_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
        relationships.append({"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid})
        all_qids.update([qid, spouse_qid])

def collect_bidirectional_relationships(qid: str, depth: int) -> List[Dict[str, str]]:
    """Collect relationships in both directions and return formatted list."""
    relationships = []
    all_qids = set([qid])

    # Collect ancestors (upward)
    collect_relationships(qid, depth, "up", relationships, set(), all_qids)

    # Collect descendants (downward)
    collect_relationships(qid, depth, "down", relationships, set(), all_qids)

    # Fetch labels for all entities
    labels = get_labels(all_qids)

    # Replace QIDs with names in relationships
    named_relationships = []
    for rel in relationships:
        entity1_name = labels.get(rel["entity1"], rel["entity1"])
        entity2_name = labels.get(rel["entity2"], rel["entity2"])
        named_relationships.append({
            "entity1": entity1_name,
            "relationship": rel["relationship"],
            "entity2": entity2_name
        })

    return named_relationships

async def check_wikipedia_tree(page_title: str) -> bool:
    """Check if Wikipedia page contains family tree templates."""
    try:
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json",
        }
        response = requests.get(WIKIPEDIA_API, params=params).json()
        if "parse" in response and "wikitext" in response["parse"]:
            text = response["parse"]["wikitext"]["*"]
            needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
            return any(n.lower() in text.lower() for n in needles)
    except:
        pass
    return False