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

async def collect_relationships(qid: str, depth: int, direction: str, relationships: List[Dict[str, str]], visited: set, all_qids: set, websocket_manager: Optional[WebSocketManager] = None, sent_entities: Optional[set] = None):
    """
    Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
    direction: 'up' (ancestors) or 'down' (descendants)
    """
    if depth == 0 or qid in visited:
        return
    visited.add(qid)
    
    # Initialize sent_entities if not provided
    if sent_entities is None:
        sent_entities = set()

    entity = fetch_entity(qid)
    claims = entity.get("claims", {})

    if direction == "up":  # Ancestors via P22 (father) and P25 (mother)
        for snak in claims.get("P22", []):  # Father relationships
            father_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationship = {"entity1": qid, "relationship": "child of", "entity2": father_qid}
            relationships.append(relationship)
            all_qids.update([qid, father_qid])
            
            # Send relationship immediately via WebSocket
            if websocket_manager:
                # Get labels for this specific relationship
                labels = get_labels({qid, father_qid})

                print(f"labels for {qid} and {father_qid}: {labels}")

                named_relationship = {
                    "entity1": labels.get(qid, qid),
                    "relationship": "child of",
                    "entity2": labels.get(father_qid, father_qid)
                }
                await websocket_manager.send_message(json.dumps({
                    "type": "relationship",
                    "data": named_relationship
                }))
                
                # Send personal details for father if not already sent
                if father_qid not in sent_entities:
                    father_details = await getPersonalDetailsByQid(father_qid)
                    if father_details:
                        await websocket_manager.send_message(json.dumps({
                            "type": "personal_details",
                            "data": {
                                "entity": labels.get(father_qid, father_qid),
                                "qid": father_qid,
                                **father_details
                            }
                        }))
                        sent_entities.add(father_qid)
            
            await collect_relationships(father_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

        for snak in claims.get("P25", []):  # Mother relationships
            mother_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationship = {"entity1": qid, "relationship": "child of", "entity2": mother_qid}
            relationships.append(relationship)
            all_qids.update([qid, mother_qid])
            
            # Send relationship immediately via WebSocket
            if websocket_manager:
                # Get labels for this specific relationship
                labels = get_labels({qid, mother_qid})
                named_relationship = {
                    "entity1": labels.get(qid, qid),
                    "relationship": "child of",
                    "entity2": labels.get(mother_qid, mother_qid)
                }
                await websocket_manager.send_message(json.dumps({
                    "type": "relationship",
                    "data": named_relationship
                }))
                
                # Send personal details for mother if not already sent
                if mother_qid not in sent_entities:
                    mother_details = await getPersonalDetailsByQid(mother_qid)
                    if mother_details:
                        await websocket_manager.send_message(json.dumps({
                            "type": "personal_details",
                            "data": {
                                "entity": labels.get(mother_qid, mother_qid),
                                "qid": mother_qid,
                                **mother_details
                            }
                        }))
                        sent_entities.add(mother_qid)
            
            await collect_relationships(mother_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

    elif direction == "down":  # Descendants via P40 (child)
        # First, collect all spouses and send spouse relationships
        spouse_qids = set()
        for spouse_snak in claims.get("P26", []):  # Spouse relationships
            spouse_qid = spouse_snak["mainsnak"]["datavalue"]["value"]["id"]
            spouse_qids.add(spouse_qid)
            relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
            relationships.append(relationship)
            all_qids.update([qid, spouse_qid])
            
            # Send spouse relationship immediately via WebSocket
            if websocket_manager:
                # Get labels for this specific relationship
                labels = get_labels({qid, spouse_qid})
                named_relationship = {
                    "entity1": labels.get(qid, qid),
                    "relationship": "spouse of",
                    "entity2": labels.get(spouse_qid, spouse_qid)
                }
                await websocket_manager.send_message(json.dumps({
                    "type": "relationship",
                    "data": named_relationship
                }))
                
                # Send personal details for spouse if not already sent
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

        # Then, process child relationships
        for snak in claims.get("P40", []):  # Child relationships
            child_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationship = {"entity1": child_qid, "relationship": "child of", "entity2": qid}
            relationships.append(relationship)
            all_qids.update([child_qid, qid])

            # Send relationship immediately via WebSocket
            if websocket_manager:
                # Get labels for this specific relationship
                labels = get_labels({child_qid, qid})
                named_relationship = {
                    "entity1": labels.get(child_qid, child_qid),
                    "relationship": "child of",
                    "entity2": labels.get(qid, qid)
                }
                await websocket_manager.send_message(json.dumps({
                    "type": "relationship",
                    "data": named_relationship
                }))
                
                # Send personal details for child if not already sent
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

            # Check if any of the known spouses is also a parent of this child
            child_entity = fetch_entity(child_qid)
            child_claims = child_entity.get("claims", {})
            child_parents = set()
            for parent_prop in ["P22", "P25"]:  # Father and mother
                for parent_snak in child_claims.get(parent_prop, []):
                    parent_qid = parent_snak["mainsnak"]["datavalue"]["value"]["id"]
                    child_parents.add(parent_qid)

            # For each spouse that is also a parent of this child, send the child-spouse relationship
            for spouse_qid in spouse_qids:
                if spouse_qid in child_parents:
                    spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
                    relationships.append(spouse_relationship)
                    all_qids.add(spouse_qid)
                    
                    # Send spouse-child relationship immediately via WebSocket
                    if websocket_manager:
                        # Get labels for this specific relationship
                        labels = get_labels({child_qid, spouse_qid})
                        named_relationship = {
                            "entity1": labels.get(child_qid, child_qid),
                            "relationship": "child of",
                            "entity2": labels.get(spouse_qid, spouse_qid)
                        }
                        await websocket_manager.send_message(json.dumps({
                            "type": "relationship",
                            "data": named_relationship
                        }))

            await collect_relationships(child_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

    # Collect spouse relationships (P26) only for "up" direction to avoid duplication
    # For "down" direction, spouse relationships are already handled before child relationships
    if direction == "up":
        for snak in claims.get("P26", []):
            spouse_qid = snak["mainsnak"]["datavalue"]["value"]["id"]
            relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
            relationships.append(relationship)
            all_qids.update([qid, spouse_qid])
            
            # Send spouse relationship immediately via WebSocket
            if websocket_manager:
                # Get labels for this specific relationship
                labels = get_labels({qid, spouse_qid})
                named_relationship = {
                    "entity1": labels.get(qid, qid),
                    "relationship": "spouse of",
                    "entity2": labels.get(spouse_qid, spouse_qid)
                }
                await websocket_manager.send_message(json.dumps({
                    "type": "relationship",
                    "data": named_relationship
                }))
                
                # Send personal details for spouse if not already sent
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

async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """Collect relationships in both directions and return formatted list."""
    relationships = []
    all_qids = set([qid])
    sent_entities = set()  # Track entities whose personal details have been sent
    # Send initial status via WebSocket
    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Starting relationship collection...", "progress": 0}
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

    # Collect ancestors (upward)
    await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send progress update
    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
        }))

    # Collect descendants (downward)
    await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send completion status
    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Collection complete!", "progress": 100}
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