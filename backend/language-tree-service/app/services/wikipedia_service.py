from typing import List, Dict, Optional
import requests
import asyncio
import aiohttp
import json
from app.core.websocket_manager import WebSocketManager
from app.core.config import settings

async def get_language_details(language_name: str) -> Optional[Dict]:
    """Get detailed information about a language"""
    qid = get_language_qid(language_name)
    if not qid:
        return None
    return await get_language_details_by_qid(qid)

async def get_language_details_by_qid(qid: str) -> Optional[Dict]:
    """Get language details directly using QID"""
    query = f"""
    SELECT ?name ?familyLabel ?speakerCount ?writingSystemLabel ?isoCode ?regionLabel ?statusLabel ?image WHERE {{
      wd:{qid} rdfs:label ?name .
      FILTER(LANG(?name) = "en")
      
      OPTIONAL {{ wd:{qid} wdt:P31 ?status . }}
      OPTIONAL {{ wd:{qid} wdt:P220 ?isoCode . }}
      OPTIONAL {{ wd:{qid} wdt:P1098 ?speakerCount . }}
      OPTIONAL {{ wd:{qid} wdt:P282 ?writingSystem . }}
      OPTIONAL {{ wd:{qid} wdt:P17 ?region . }}
      OPTIONAL {{ wd:{qid} wdt:P279 ?family . }}
      OPTIONAL {{ wd:{qid} wdt:P18 ?image . }}
      
      OPTIONAL {{ ?status rdfs:label ?statusLabel . FILTER(LANG(?statusLabel) = "en") }}
      OPTIONAL {{ ?writingSystem rdfs:label ?writingSystemLabel . FILTER(LANG(?writingSystemLabel) = "en") }}
      OPTIONAL {{ ?region rdfs:label ?regionLabel . FILTER(LANG(?regionLabel) = "en") }}
      OPTIONAL {{ ?family rdfs:label ?familyLabel . FILTER(LANG(?familyLabel) = "en") }}
    }}
    LIMIT 1
    """
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "LanguageTreeService/1.0"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(settings.SPARQL_API, params={"query": query}, headers=headers) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                results = data["results"]["bindings"]

                if not results:
                    return None

                result = results[0]
                return {
                    "name": result.get("name", {}).get("value"),
                    "language_family": result.get("familyLabel", {}).get("value"),
                    "speakers": result.get("speakerCount", {}).get("value"),
                    "writing_system": result.get("writingSystemLabel", {}).get("value"),
                    "iso_code": result.get("isoCode", {}).get("value"),
                    "region": result.get("regionLabel", {}).get("value"),
                    "status": result.get("statusLabel", {}).get("value"),
                    "image_url": result.get("image", {}).get("value")
                }
    except Exception as e:
        print(f"Error fetching language details: {e}")
        return None

async def fetch_language_relationships(language_name: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """
    Fetch language family relationships for a given language and depth.
    Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
    """
    qid = get_language_qid(language_name)
    if not qid:
        return []
    return await collect_language_relationships(qid, depth, websocket_manager)

def get_language_qid(language_name: str) -> Optional[str]:
    """Return the Wikidata Q-identifier for a language name."""
    try:
        # First try direct page lookup
        params = {
            "action": "query",
            "titles": f"{language_name} language",
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "format": "json",
        }
        data = requests.get(settings.WIKIPEDIA_API, params=params).json()
        
        for page in data["query"]["pages"].values():
            if "pageprops" in page and "wikibase_item" in page["pageprops"]:
                return page["pageprops"]["wikibase_item"]
        
        # If direct lookup fails, try search
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{language_name} language",
            "srlimit": 1,
            "format": "json",
        }
        data = requests.get(settings.WIKIPEDIA_API, params=params).json()
        
        if data["query"]["search"]:
            page_title = data["query"]["search"][0]["title"]
            params = {
                "action": "query",
                "titles": page_title,
                "prop": "pageprops",
                "ppprop": "wikibase_item",
                "format": "json",
            }
            data = requests.get(settings.WIKIPEDIA_API, params=params).json()
            
            for page in data["query"]["pages"].values():
                if "pageprops" in page and "wikibase_item" in page["pageprops"]:
                    return page["pageprops"]["wikibase_item"]
                    
    except Exception as e:
        print(f"Error getting QID for {language_name}: {e}")
    
    return None

def fetch_language_entity(qid: str) -> dict:
    """Return the full JSON entity document for a given QID."""
    try:
        url = settings.WIKIDATA_API.format(qid)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["entities"][qid]
    except Exception as e:
        print(f"Error fetching entity {qid}: {e}")
    return {}

def get_language_labels(qids: set) -> Dict[str, str]:
    """Batch-fetch labels for a set of Q-ids (returns dict)."""
    if not qids:
        return {}
    
    try:
        params = {
            "action": "wbgetentities",
            "ids": "|".join(qids),
            "props": "labels",
            "languages": "en",
            "format": "json",
        }
        data = requests.get(settings.WIKIDATA_QUERY_API, params=params).json()
        return {
            qid: data["entities"][qid]["labels"]["en"]["value"]
            for qid in data["entities"]
            if "labels" in data["entities"][qid] and "en" in data["entities"][qid]["labels"]
        }
    except Exception as e:
        print(f"Error getting labels: {e}")
        return {}

def get_language_family(qid: str) -> List[str]:
    """Return a list of parent language family QIDs for a given QID."""
    entity = fetch_language_entity(qid)
    claims = entity.get("claims", {})
    families = []
    
    # P279: subclass of (language family relationships)
    for snak in claims.get("P279", []):
        if "datavalue" in snak["mainsnak"] and "value" in snak["mainsnak"]["datavalue"]:
            families.append(snak["mainsnak"]["datavalue"]["value"]["id"])
    
    # P361: part of (language group membership)
    for snak in claims.get("P361", []):
        if "datavalue" in snak["mainsnak"] and "value" in snak["mainsnak"]["datavalue"]:
            families.append(snak["mainsnak"]["datavalue"]["value"]["id"])
            
    return families

def get_language_descendants(qid: str) -> List[str]:
    """Return a list of descendant language QIDs for a given QID."""
    # This requires a SPARQL query since we need to find languages that have this one as ancestor
    query = f"""
    SELECT DISTINCT ?descendant WHERE {{
      ?descendant wdt:P279+ wd:{qid} .
      ?descendant wdt:P31/wdt:P279* wd:Q34770 .  # Instance of language
    }}
    LIMIT 100
    """
    
    try:
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "LanguageTreeService/1.0"
        }
        params = {"query": query}
        response = requests.get(settings.SPARQL_API, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            results = data["results"]["bindings"]
            return [result["descendant"]["value"].split("/")[-1] for result in results]
    except Exception as e:
        print(f"Error getting descendants for {qid}: {e}")
    
    return []

async def collect_language_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """Collect language family relationships in both directions and return formatted list."""
    relationships = []
    all_qids = set([qid])
    sent_entities = set()

    # Send initial status via WebSocket
    if websocket_manager:
        await websocket_manager.send_status("Starting language relationship collection...", 0)
        
        # Get initial entity details and send them
        initial_labels = get_language_labels({qid})
        initial_language_name = initial_labels.get(qid, qid)
        initial_details = await get_language_details_by_qid(qid)
        if initial_details:
            await websocket_manager.send_json({
                "type": "language_details",
                "data": {
                    "entity": initial_language_name,
                    "qid": qid,
                    **initial_details
                }
            })
            sent_entities.add(qid)

    # Collect language family relationships (upward)
    await collect_relationships_recursive(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send progress update
    if websocket_manager:
        await websocket_manager.send_status("Language families collected, now collecting descendants...", 50)

    # Collect language descendants (downward)
    await collect_relationships_recursive(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send completion status
    if websocket_manager:
        await websocket_manager.send_status("Collection complete!", 100)

    # Fetch labels for all entities
    labels = get_language_labels(all_qids)

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

async def collect_relationships_recursive(qid: str, depth: int, direction: str, relationships: List[Dict[str, str]], 
                                        visited: set, all_qids: set, websocket_manager: Optional[WebSocketManager] = None, 
                                        sent_entities: Optional[set] = None):
    """
    Recursively collect language relationships in {"entity1": str, "relationship": str, "entity2": str} format.
    direction: 'up' (language families) or 'down' (descendant languages)
    """
    if depth == 0 or qid in visited:
        return
    visited.add(qid)
    
    if sent_entities is None:
        sent_entities = set()

    if direction == "up":  # Language families
        families = get_language_family(qid)
        for family_qid in families:
            relationship = {"entity1": qid, "relationship": "member of", "entity2": family_qid}
            relationships.append(relationship)
            all_qids.update([qid, family_qid])
            
            # Send relationship immediately via WebSocket
            if websocket_manager:
                labels = get_language_labels({qid, family_qid})
                named_relationship = {
                    "entity1": labels.get(qid, qid),
                    "relationship": "member of",
                    "entity2": labels.get(family_qid, family_qid)
                }
                await websocket_manager.send_json({
                    "type": "relationship",
                    "data": named_relationship
                })
                
                # Send language details if not already sent
                if family_qid not in sent_entities:
                    family_details = await get_language_details_by_qid(family_qid)
                    if family_details:
                        await websocket_manager.send_json({
                            "type": "language_details",
                            "data": {
                                "entity": labels.get(family_qid, family_qid),
                                "qid": family_qid,
                                **family_details
                            }
                        })
                        sent_entities.add(family_qid)
            
            await collect_relationships_recursive(family_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

    elif direction == "down":  # Descendant languages
        descendants = get_language_descendants(qid)
        for descendant_qid in descendants[:20]:  # Limit to avoid too many results
            relationship = {"entity1": descendant_qid, "relationship": "member of", "entity2": qid}
            relationships.append(relationship)
            all_qids.update([descendant_qid, qid])

            # Send relationship immediately via WebSocket
            if websocket_manager:
                labels = get_language_labels({descendant_qid, qid})
                named_relationship = {
                    "entity1": labels.get(descendant_qid, descendant_qid),
                    "relationship": "member of",
                    "entity2": labels.get(qid, qid)
                }
                await websocket_manager.send_json({
                    "type": "relationship",
                    "data": named_relationship
                })
                
                # Send language details if not already sent
                if descendant_qid not in sent_entities:
                    descendant_details = await get_language_details_by_qid(descendant_qid)
                    if descendant_details:
                        await websocket_manager.send_json({
                            "type": "language_details",
                            "data": {
                                "entity": labels.get(descendant_qid, descendant_qid),
                                "qid": descendant_qid,
                                **descendant_details
                            }
                        })
                        sent_entities.add(descendant_qid)

            await collect_relationships_recursive(descendant_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

async def check_language_validity(language_name: str) -> bool:
    """Check if the language name corresponds to a valid language in Wikidata."""
    qid = get_language_qid(language_name)
    return qid is not None
