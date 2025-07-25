from typing import List, Dict
import requests

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

def fetch_relationships(page_title: str, depth: int) -> List[Dict[str, str]]:
    """
    Fetch relationships for a given Wikipedia page title and depth.
    """
    qid = get_qid(page_title)
    return collect_relationships(qid, depth)


def get_qid(page_title: str) -> str:
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
    url = WIKIDATA_API.format(qid)
    return requests.get(url).json()["entities"][qid]

def collect_relationships(qid: str, depth: int) -> List[Dict[str, str]]:
    relationships = []
    visited = set()

    def recursive_collect(qid: str, depth: int):
        if depth == 0 or qid in visited:
            return
        visited.add(qid)

        entity = fetch_entity(qid)
        claims = entity.get("claims", {})

        for snak in claims.get("P22", []):  # Father relationships
            father_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append({"entity1": qid, "relationship": "child of", "entity2": father_qid})
            recursive_collect(father_qid, depth - 1)

        for snak in claims.get("P25", []):  # Mother relationships
            mother_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append({"entity1": qid, "relationship": "child of", "entity2": mother_qid})
            recursive_collect(mother_qid, depth - 1)

        for snak in claims.get("P40", []):  # Child relationships
            child_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append({"entity1": child_qid, "relationship": "child of", "entity2": qid})
            recursive_collect(child_qid, depth - 1)

    recursive_collect(qid, depth)
    return relationships