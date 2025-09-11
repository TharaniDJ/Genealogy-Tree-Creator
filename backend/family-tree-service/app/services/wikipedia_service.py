
from typing import List, Dict, Optional
import requests
import asyncio
import aiohttp
import json
from app.core.websocket_manager import WebSocketManager

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
SPARQL_API='https://query.wikidata.org/sparql'

async def getPersonalDetails(page_title:str):
    qid = get_qid(page_title)
    if not qid:
        return None
    return await getPersonalDetailsByQid(qid)

async def getPersonalDetailsByQid(qid: str):
    """Get personal details directly using Wikidata QID."""
    query = f"""
    SELECT ?birthDate ?deathDate ?image WHERE {{
      wd:{qid} wdt:P569 ?birthDate.
      OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate. }}
      OPTIONAL {{ wd:{qid} wdt:P18 ?image. }}
    }}
    """

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise RuntimeError(f"SPARQL query failed ({resp.status}): {text}")

            # Allow aiohttp to parse JSON even if content-type is not strictly application/json
            data = await resp.json(content_type=None)
            results = data.get("results", {}).get("bindings", [])

            if not results:
                return None

            result = results[0]
            birth_date = result.get("birthDate", {}).get("value")
            death_date = result.get("deathDate", {}).get("value")
            image = result.get("image", {}).get("value")

            return {
                "birth_year": birth_date[:4] if birth_date else None,
                "death_year": death_date[:4] if death_date else None,
                "image_url": image
            }

async def fetch_relationships(page_title: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """
    Fetch genealogical relationships for a given Wikipedia page title and depth.
    Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
    """
    try:
        qid = get_qid(page_title)
        print(f"Fetched QID for '{page_title}': {qid}")  # Debug print
        
        if not qid:
            # Send error message via WebSocket if available
            if websocket_manager:
                await websocket_manager.send_message(json.dumps({
                    "type": "status",
                    "data": {
                        "message": f"No Wikipedia/Wikidata entry found for '{page_title}'. This person may not have sufficient notable information.",
                        "progress": 100
                    }
                }))
            print(f"No QID found for '{page_title}', returning empty relationships")
            return []
            
        return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
    except Exception as e:
        error_msg = f"Error fetching relationships for '{page_title}': {str(e)}"
        print(error_msg)
        
        # Send error message via WebSocket if available
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "status",
                "data": {
                    "message": error_msg,
                    "progress": 100
                }
            }))
        
        return []

def get_qid(page_title: str) -> Optional[str]:
    """Return the Wikidata Q-identifier for a Wikipedia page title, or None if not found."""
    params = {
        "action": "query",
        "titles": page_title,
        "prop": "pageprops",
        "ppprop": "wikibase_item",
        "format": "json",
    }

    headers = {
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }

    try:
        response = requests.get(WIKIPEDIA_API, params=params, headers=headers)

        print(f"Status code: {response.status_code}")
        if response.status_code != 200:
            print(f"Failed to fetch data for {page_title}: {response.status_code}")
            return None

        data = response.json()
        print(f"Wikipedia API response for '{page_title}': {data}")  # Debug print

        # Navigate through the JSON structure safely
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            # Check if page exists (not missing)
            if "missing" in page:
                print(f"Page '{page_title}' does not exist on Wikipedia")
                return None
                
            qid = page.get("pageprops", {}).get("wikibase_item")
            if qid:
                return qid

        print(f"Q-id not found for page: {page_title}")
        return None

    except Exception as e:
        print(f"Error fetching QID for {page_title}: {e}")
        return None

WIKIDATA_API = "https://www.wikidata.org/w/api.php"

def fetch_entity(qid: str) -> dict:
    """Return the full JSON entity document for a given Wikidata QID."""
    params = {
        "action": "wbgetentities",
        "ids": qid,
        "format": "json"
    }

    headers = {
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }

    response = requests.get(WIKIDATA_API, params=params, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch entity {qid}: {response.status_code}")

    data = response.json()
    entities = data.get("entities", {})
    if qid not in entities:
        raise ValueError(f"Entity {qid} not found in response")

    return entities[qid]

def get_labels(qids: set) -> Dict[str, str]:
    """Batch-fetch English labels for a set of Q-ids (returns dict)."""
    if not qids:
        return {}

    params = {
        "action": "wbgetentities",
        "ids": "|".join(qids),  # pipe-separated list (not comma)
        "props": "labels",
        "languages": "en",
        "format": "json",
    }

    headers = {
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }

    response = requests.get(WIKIDATA_API, params=params, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch labels: {response.status_code}")
        print(f"Response text: {response.text}")
        return {}  # Return empty dict instead of raising error

    data = response.json()
    
    # Check for errors in response
    if "error" in data:
        print(f"Wikidata API error: {data['error']}")
        return {}
        
    entities = data.get("entities", {})

    # Build dict of qid -> label
    labels = {}
    for qid, entity in entities.items():
        # Check if entity exists (not missing)
        if entity.get("missing"):
            print(f"Entity {qid} is missing from Wikidata")
            continue
            
        label_info = entity.get("labels", {}).get("en")
        if label_info and "value" in label_info:
            labels[qid] = label_info["value"]
        else:
            print(f"No English label found for {qid}")

    return labels

def get_parents(qid: str) -> List[str]:
    """Return a list of parent QIDs for a given QID."""
    entity = fetch_entity(qid)
    claims = entity.get("claims", {})
    parents = []
    for snak in claims.get("P22", []):  # Father
        parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
    for snak in claims.get("P25", []):  # Mother
        parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
    return parents

async def get_adoptive_children_sparql(qid: str) -> List[str]:
    """Get adoptive children using SPARQL query."""
    query = f"""
    SELECT ?child WHERE {{
      ?child wdt:P1441 wd:{qid} .
    }}
    """

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
                if resp.status != 200:
                    print(f"SPARQL query failed for adoptive children of {qid}: {resp.status}")
                    return []

                data = await resp.json(content_type=None)
                results = data.get("results", {}).get("bindings", [])
                
                children = []
                for result in results:
                    child_uri = result.get("child", {}).get("value", "")
                    if child_uri.startswith("http://www.wikidata.org/entity/"):
                        child_qid = child_uri.split("/")[-1]
                        children.append(child_qid)
                
                return children
    except Exception as e:
        print(f"Error fetching adoptive children for {qid}: {e}")
        return []

async def get_all_children_sparql(qid: str) -> Dict[str, List[str]]:
    """Get all types of children using SPARQL query."""
    query = f"""
    SELECT ?child ?relationship WHERE {{
      {{
        ?child wdt:P22 wd:{qid} .
        BIND("biological_father" AS ?relationship)
      }} UNION {{
        ?child wdt:P25 wd:{qid} .
        BIND("biological_mother" AS ?relationship)
      }} UNION {{
        ?child wdt:P1441 wd:{qid} .
        BIND("adoptive_parent" AS ?relationship)
      }} UNION {{
        ?child wdt:P8810 wd:{qid} .
        BIND("parent" AS ?relationship)
      }}
    }}
    """

    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
                if resp.status != 200:
                    print(f"SPARQL query failed for children of {qid}: {resp.status}")
                    return {}

                data = await resp.json(content_type=None)
                results = data.get("results", {}).get("bindings", [])
                
                children_by_type = {
                    "biological_father": [],
                    "biological_mother": [],
                    "adoptive_parent": [],
                    "parent": []
                }
                
                for result in results:
                    child_uri = result.get("child", {}).get("value", "")
                    relationship = result.get("relationship", {}).get("value", "")
                    
                    if child_uri.startswith("http://www.wikidata.org/entity/"):
                        child_qid = child_uri.split("/")[-1]
                        if relationship in children_by_type:
                            children_by_type[relationship].append(child_qid)
                
                return children_by_type
    except Exception as e:
        print(f"Error fetching children for {qid}: {e}")
        return {}

def extract_qid(snak: dict) -> Optional[str]:
    """Safely extract QID from a snak, return None if unavailable."""
    try:
        if snak.get("mainsnak", {}).get("snaktype") != "value":
            return None
        return snak["mainsnak"]["datavalue"]["value"]["id"]
    except Exception:
        return None


async def collect_relationships(
    qid: str,
    depth: int,
    direction: str,
    relationships: List[Dict[str, str]],
    visited: set,
    all_qids: set,
    websocket_manager: Optional[WebSocketManager] = None,
    sent_entities: Optional[set] = None
):
    """
    Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
    Supports only 3 types: child of, spouse of, adopted by.
    """
    if depth == 0 or qid in visited:
        return
    visited.add(qid)

    if sent_entities is None:
        sent_entities = set()

    entity = fetch_entity(qid)
    claims = entity.get("claims", {})

    # ----------------------
    # Biological & adoptive parents (UP)
    # ----------------------
    if direction == "up":
        for prop, rel_name in {
            "P22": "child of",     # father
            "P25": "child of",     # mother
            "P3373": "adopted by", # adoptive parent
            "P3448": "adopted by"  # stepparent
        }.items():
            for snak in claims.get(prop, []):
                parent_qid = extract_qid(snak)
                if not parent_qid:
                    continue
                relationships.append({"entity1": qid, "relationship": rel_name, "entity2": parent_qid})
                all_qids.update([qid, parent_qid])

                if websocket_manager:
                    labels = get_labels({qid, parent_qid})
                    named_rel = {
                        "entity1": labels.get(qid, qid),
                        "relationship": rel_name,
                        "entity2": labels.get(parent_qid, parent_qid)
                    }
                    await websocket_manager.send_message(json.dumps({"type": "relationship", "data": named_rel}))

                    if parent_qid not in sent_entities:
                        parent_details = await getPersonalDetailsByQid(parent_qid)
                        if parent_details:
                            await websocket_manager.send_message(json.dumps({
                                "type": "personal_details",
                                "data": {
                                    "entity": labels.get(parent_qid, parent_qid),
                                    "qid": parent_qid,
                                    **parent_details
                                }
                            }))
                            sent_entities.add(parent_qid)

                # recurse upward
                await collect_relationships(
                    parent_qid, depth - 1, direction,
                    relationships, visited, all_qids,
                    websocket_manager, sent_entities
                )

    # ----------------------
    # Spouses & children (DOWN)
    # ----------------------
    elif direction == "down":
        # spouses
        for prop, rel_name in {"P26": "spouse of", "P451": "spouse of"}.items():
            for snak in claims.get(prop, []):
                spouse_qid = extract_qid(snak)
                if not spouse_qid:
                    continue
                relationships.append({"entity1": qid, "relationship": rel_name, "entity2": spouse_qid})
                all_qids.update([qid, spouse_qid])

                if websocket_manager:
                    labels = get_labels({qid, spouse_qid})
                    named_rel = {
                        "entity1": labels.get(qid, qid),
                        "relationship": rel_name,
                        "entity2": labels.get(spouse_qid, spouse_qid)
                    }
                    await websocket_manager.send_message(json.dumps({"type": "relationship", "data": named_rel}))

                    if spouse_qid not in sent_entities:
                        spouse_details = await getPersonalDetailsByQid(spouse_qid)
                        if spouse_details:
                            await websocket_manager.send_message(json.dumps({
                                "type": "personal_details",
                                "data": {
                                    "entity": labels.get(spouse_qid, spouse_qid),
                                    "qid": spouse_qid,
                                    **spouse_details
                                }
                            }))
                            sent_entities.add(spouse_qid)

        # children
        for snak in claims.get("P40", []):
            child_qid = extract_qid(snak)
            if not child_qid:
                continue
            relationships.append({"entity1": child_qid, "relationship": "child of", "entity2": qid})
            all_qids.update([child_qid, qid])

            if websocket_manager:
                labels = get_labels({child_qid, qid})
                named_rel = {
                    "entity1": labels.get(child_qid, child_qid),
                    "relationship": "child of",
                    "entity2": labels.get(qid, qid)
                }
                await websocket_manager.send_message(json.dumps({"type": "relationship", "data": named_rel}))

                if child_qid not in sent_entities:
                    child_details = await getPersonalDetailsByQid(child_qid)
                    if child_details:
                        await websocket_manager.send_message(json.dumps({
                            "type": "personal_details",
                            "data": {
                                "entity": labels.get(child_qid, child_qid),
                                "qid": child_qid,
                                **child_details
                            }
                        }))
                        sent_entities.add(child_qid)

            # recurse downward
            await collect_relationships(
                child_qid, depth - 1, direction,
                relationships, visited, all_qids,
                websocket_manager, sent_entities
            )

async def send_relationship_and_details(websocket_manager: Optional[WebSocketManager], relationship: Dict[str, str], qids: set, sent_entities: set):
    """Helper function to send relationship and personal details via WebSocket."""
    if not websocket_manager:
        return
        
    # Get labels for this specific relationship
    labels = get_labels(qids)
    
    # Send relationship with proper labels
    entity1_name = labels.get(relationship["entity1"], relationship["entity1"])
    entity2_name = labels.get(relationship["entity2"], relationship["entity2"])
    
    named_relationship = {
        "entity1": entity1_name,
        "relationship": relationship["relationship"],
        "entity2": entity2_name
    }
    
    await websocket_manager.send_message(json.dumps({
        "type": "relationship",
        "data": named_relationship
    }))
    
    # Send personal details for entities not already sent
    for qid in qids:
        if qid not in sent_entities:
            details = await getPersonalDetailsByQid(qid)
            if details:
                await websocket_manager.send_message(json.dumps({
                    "type": "personal_details",
                    "data": {
                        "entity": labels.get(qid, qid),
                        "qid": qid,
                        **details
                    }
                }))
                sent_entities.add(qid)

async def handle_child_spouse_relationships(child_qid: str, spouse_qids: set, relationships: List[Dict[str, str]], all_qids: set, websocket_manager: Optional[WebSocketManager], sent_entities: set):
    """Helper function to handle child-spouse relationships."""
    # Check if any of the known spouses is also a parent of this child
    child_entity = fetch_entity(child_qid)
    child_claims = child_entity.get("claims", {})
    child_parents = set()
    
    # Check all parent types
    for parent_prop in ["P22", "P25", "P1441", "P8810"]:  # Father, mother, adoptive parent, generic parent
        for parent_snak in child_claims.get(parent_prop, []):
            parent_qid = parent_snak["mainsnak"]["datavalue"]["value"]["id"]
            child_parents.add(parent_qid)

    # For each spouse that is also a parent of this child, send the child-spouse relationship
    for spouse_qid in spouse_qids:
        if spouse_qid in child_parents:
            spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
            relationships.append(spouse_relationship)
            all_qids.add(spouse_qid)
            
            await send_relationship_and_details(websocket_manager, spouse_relationship, {child_qid, spouse_qid}, sent_entities)

async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """Collect relationships in both directions and return formatted list."""
    relationships = []
    all_qids = set([qid])
    sent_entities = set()  # Track entities whose personal details have been sent
    
    # Send initial status via WebSocket
    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Starting relationship collection (including adoptions)...", "progress": 0}
        }))
        
        # Get initial entity details and send them
        initial_labels = get_labels({qid})
        print(f"Fetched labels for '{qid}': {initial_labels}")  # Debug print
        initial_entity_name = initial_labels.get(qid, qid)
        print(f"Initial entity name for '{qid}': {initial_entity_name}")  # Debug print
        initial_details = await getPersonalDetailsByQid(qid)
        print(f"Initial personal details for '{qid}': {initial_details}")  # Debug print
        if initial_details:
            await websocket_manager.send_message(json.dumps({
                "type": "personal_details",
                "data": {
                    "entity": initial_entity_name,
                    "qid": qid,
                    **initial_details
                }
            }))
            sent_entities.add(qid)  # Mark initial entity as sent

    # Collect ancestors (upward) - includes biological parents, adoptive parents, and spouses
    await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send progress update
    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
        }))

    # Collect descendants (downward) - includes biological children, adopted children, and spouses
    await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send completion status
    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Collection complete! (Including adoption relationships)", "progress": 100}
        }))

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