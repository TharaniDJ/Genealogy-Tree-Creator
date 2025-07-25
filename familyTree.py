#!/usr/bin/env python3
"""
family_tree_relations.py
Generate genealogical relationships in [entity1, relationship, entity2] format using Wikidata.
Modified to output relationships as "father of", "mother of", "child of" format.
"""

import requests
import sys
from collections import defaultdict

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API   = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"

# ---------- Utility helpers ----------

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

def get_labels(qids):
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
    return {qid: data["entities"][qid]["labels"]["en"]["value"]
            for qid in data["entities"]
            if "labels" in data["entities"][qid] and "en" in data["entities"][qid]["labels"]}

# ---------- Relationship collection ----------

def collect_relationships(qid: str, depth: int, direction: str, relationships, visited):
    """
    Recursively collect family relationships in [entity1, relationship, entity2] format.
    direction: 'up' (ancestors) or 'down' (descendants)
    relationships: list to store [entity1, relationship, entity2] tuples
    visited: set of already processed Q-ids to avoid cycles
    """
    if depth == 0 or qid in visited:
        return
    visited.add(qid)

    entity = fetch_entity(qid)
    claims = entity.get("claims", {})

    if direction == "up":        # ancestors via P22+P25
        # Father relationships (P22)
        for snak in claims.get("P22", []):
            father_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append([father_qid, "father of", qid])
            collect_relationships(father_qid, depth - 1, direction, relationships, visited)
        
        # Mother relationships (P25)
        for snak in claims.get("P25", []):
            mother_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append([mother_qid, "mother of", qid])
            collect_relationships(mother_qid, depth - 1, direction, relationships, visited)

    elif direction == "down":    # descendants via P40
        # Child relationships (P40)
        for snak in claims.get("P40", []):
            child_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationships.append([qid, "parent of", child_qid])
            collect_relationships(child_qid, depth - 1, direction, relationships, visited)

def collect_bidirectional_relationships(qid: str, depth: int):
    """Collect relationships in both directions and return formatted list."""
    relationships = []
    
    # Collect ancestors (upward)
    collect_relationships(qid, depth, "up", relationships, set())
    
    # Collect descendants (downward) 
    collect_relationships(qid, depth, "down", relationships, set())
    
    # Get all unique QIDs for labeling
    all_qids = set()
    for rel in relationships:
        all_qids.add(rel[0])  # entity1
        all_qids.add(rel[2])  # entity2
    all_qids.add(qid)  # include the root person
    
    # Fetch labels for all entities
    labels = get_labels(all_qids)
    
    # Convert QIDs to human-readable names
    formatted_relationships = []
    for entity1_qid, relationship, entity2_qid in relationships:
        entity1_name = labels.get(entity1_qid, entity1_qid)
        entity2_name = labels.get(entity2_qid, entity2_qid)
        formatted_relationships.append([entity1_name, relationship, entity2_name])
    
    return formatted_relationships

# ---------- Optional: detect existing family-tree template ----------

def wikipedia_has_tree(page_title: str) -> bool:
    """Check if Wikipedia page contains family tree templates."""
    try:
        params = {
            "action": "parse",
            "page":   page_title,
            "prop":   "wikitext",
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

# ---------- Main entry point ----------

def build_family_relationships(page_title: str, depth: int):
    """Main function to build and display family relationships."""
    try:
        qid = get_qid(page_title)
        relationships = collect_bidirectional_relationships(qid, depth)
        
        print(f"\nGenealogical relationships for {page_title} (depth {depth}):")
        print("Format: [entity1, relationship, entity2]\n")
        
        # Sort relationships for better readability
        relationships.sort(key=lambda x: (x[1], x[0], x[2]))
        
        for entity1, relationship, entity2 in relationships:
            print(f"[{entity1}, {relationship}, {entity2}]")
        
        print(f"\nTotal relationships found: {len(relationships)}")
        
        # Report existing on-wiki trees
        if wikipedia_has_tree(page_title):
            print("\nNote: The Wikipedia article already contains a family-tree template.")
            
    except Exception as e:
        print(f"Error: {e}")
        return []

# ---------- CLI ----------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python family_tree_relations.py 'Page Title' depth")
        print("Example: python family_tree_relations.py 'Albert Einstein' 2")
        sys.exit(1)
    
    title = sys.argv[1]
    try:
        depth = int(sys.argv[2])
        if depth < 1:
            print("Depth must be a positive integer")
            sys.exit(1)
    except ValueError:
        print("Depth must be a valid integer")
        sys.exit(1)
    
    build_family_relationships(title, depth)
