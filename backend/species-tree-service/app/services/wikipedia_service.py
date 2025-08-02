from typing import List, Dict, Optional
import requests
import asyncio
import aiohttp
import json
from app.core.websocket_manager import WebSocketManager
from app.core.config import settings

async def get_species_details(species_name: str) -> Optional[Dict]:
    """Get detailed information about a species"""
    qid = get_species_qid(species_name)
    if not qid:
        return None
    return await get_species_details_by_qid(qid)

async def get_species_details_by_qid(qid: str) -> Optional[Dict]:
    """Get species details directly using QID"""
    query = f"""
    SELECT ?name ?scientificName ?conservationStatusLabel ?habitatLabel ?image 
           ?kingdomLabel ?phylumLabel ?classLabel ?orderLabel ?familyLabel ?genusLabel
           ?length ?mass ?lifespan WHERE {{
      wd:{qid} rdfs:label ?name .
      FILTER(LANG(?name) = "en")
      
      OPTIONAL {{ wd:{qid} wdt:P225 ?scientificName . }}
      OPTIONAL {{ wd:{qid} wdt:P141 ?conservationStatus . }}
      OPTIONAL {{ wd:{qid} wdt:P2295 ?habitat . }}
      OPTIONAL {{ wd:{qid} wdt:P18 ?image . }}
      OPTIONAL {{ wd:{qid} wdt:P2043 ?length . }}
      OPTIONAL {{ wd:{qid} wdt:P2067 ?mass . }}
      OPTIONAL {{ wd:{qid} wdt:P2250 ?lifespan . }}
      
      # Get taxonomic hierarchy
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?kingdom .
        ?kingdom wdt:P105 wd:Q36732 .
        ?kingdom rdfs:label ?kingdomLabel .
        FILTER(LANG(?kingdomLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?phylum .
        ?phylum wdt:P105 wd:Q38348 .
        ?phylum rdfs:label ?phylumLabel .
        FILTER(LANG(?phylumLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?class .
        ?class wdt:P105 wd:Q5284 .
        ?class rdfs:label ?classLabel .
        FILTER(LANG(?classLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?order .
        ?order wdt:P105 wd:Q36602 .
        ?order rdfs:label ?orderLabel .
        FILTER(LANG(?orderLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?family .
        ?family wdt:P105 wd:Q35409 .
        ?family rdfs:label ?familyLabel .
        FILTER(LANG(?familyLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?genus .
        ?genus wdt:P105 wd:Q34740 .
        ?genus rdfs:label ?genusLabel .
        FILTER(LANG(?genusLabel) = "en")
      }}
      
      OPTIONAL {{ ?conservationStatus rdfs:label ?conservationStatusLabel . FILTER(LANG(?conservationStatusLabel) = "en") }}
      OPTIONAL {{ ?habitat rdfs:label ?habitatLabel . FILTER(LANG(?habitatLabel) = "en") }}
    }}
    LIMIT 1
    """
    headers = {
        "Accept": "application/sparql-results+json",
        "User-Agent": "SpeciesTreeService/1.0"
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
                    "scientific_name": result.get("scientificName", {}).get("value"),
                    "kingdom": result.get("kingdomLabel", {}).get("value"),
                    "phylum": result.get("phylumLabel", {}).get("value"),
                    "class_name": result.get("classLabel", {}).get("value"),
                    "order": result.get("orderLabel", {}).get("value"),
                    "family": result.get("familyLabel", {}).get("value"),
                    "genus": result.get("genusLabel", {}).get("value"),
                    "conservation_status": result.get("conservationStatusLabel", {}).get("value"),
                    "habitat": result.get("habitatLabel", {}).get("value"),
                    "size": result.get("length", {}).get("value"),
                    "lifespan": result.get("lifespan", {}).get("value"),
                    "image_url": result.get("image", {}).get("value")
                }
    except Exception as e:
        print(f"Error fetching species details: {e}")
        return None

async def fetch_species_relationships(species_name: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """
    Fetch taxonomic relationships for a given species and depth.
    Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
    """
    qid = get_species_qid(species_name)
    if not qid:
        return []
    return await collect_taxonomic_relationships(qid, depth, websocket_manager)

def get_species_qid(species_name: str) -> Optional[str]:
    """Return the Wikidata Q-identifier for a species name."""
    try:
        # First try direct page lookup
        params = {
            "action": "query",
            "titles": species_name,
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
            "srsearch": species_name,
            "srlimit": 5,
            "format": "json",
        }
        data = requests.get(settings.WIKIPEDIA_API, params=params).json()
        
        if data["query"]["search"]:
            # Try each search result
            for result in data["query"]["search"]:
                page_title = result["title"]
                params = {
                    "action": "query",
                    "titles": page_title,
                    "prop": "pageprops",
                    "ppprop": "wikibase_item",
                    "format": "json",
                }
                page_data = requests.get(settings.WIKIPEDIA_API, params=params).json()
                
                for page in page_data["query"]["pages"].values():
                    if "pageprops" in page and "wikibase_item" in page["pageprops"]:
                        qid = page["pageprops"]["wikibase_item"]
                        # Verify this is actually a biological entity
                        if verify_biological_entity(qid):
                            return qid
                    
    except Exception as e:
        print(f"Error getting QID for {species_name}: {e}")
    
    return None

def verify_biological_entity(qid: str) -> bool:
    """Verify that the QID represents a biological entity"""
    try:
        query = f"""
        ASK {{
          wd:{qid} wdt:P31/wdt:P279* wd:Q16521 .  # Instance of taxon
        }}
        """
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "SpeciesTreeService/1.0"
        }
        params = {"query": query}
        response = requests.get(settings.SPARQL_API, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("boolean", False)
    except Exception as e:
        print(f"Error verifying biological entity {qid}: {e}")
    
    return False

def fetch_species_entity(qid: str) -> dict:
    """Return the full JSON entity document for a given QID."""
    try:
        url = settings.WIKIDATA_API.format(qid)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()["entities"][qid]
    except Exception as e:
        print(f"Error fetching entity {qid}: {e}")
    return {}

def get_species_labels(qids: set) -> Dict[str, str]:
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

def get_parent_taxa(qid: str) -> List[str]:
    """Return a list of parent taxon QIDs for a given QID."""
    entity = fetch_species_entity(qid)
    claims = entity.get("claims", {})
    parents = []
    
    # P171: parent taxon
    for snak in claims.get("P171", []):
        if "datavalue" in snak["mainsnak"] and "value" in snak["mainsnak"]["datavalue"]:
            parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
            
    return parents

def get_child_taxa(qid: str) -> List[str]:
    """Return a list of child taxon QIDs for a given QID."""
    # This requires a SPARQL query since we need to find taxa that have this one as parent
    query = f"""
    SELECT DISTINCT ?child WHERE {{
      ?child wdt:P171 wd:{qid} .
      ?child wdt:P31/wdt:P279* wd:Q16521 .  # Instance of taxon
    }}
    LIMIT 50
    """
    
    try:
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "SpeciesTreeService/1.0"
        }
        params = {"query": query}
        response = requests.get(settings.SPARQL_API, params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            results = data["results"]["bindings"]
            return [result["child"]["value"].split("/")[-1] for result in results]
    except Exception as e:
        print(f"Error getting children for {qid}: {e}")
    
    return []

async def get_taxonomic_classification(qid: str) -> Dict[str, str]:
    """Get complete taxonomic classification for a species"""
    query = f"""
    SELECT ?kingdomLabel ?phylumLabel ?classLabel ?orderLabel ?familyLabel ?genusLabel ?speciesLabel WHERE {{
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?kingdom .
        ?kingdom wdt:P105 wd:Q36732 .
        ?kingdom rdfs:label ?kingdomLabel .
        FILTER(LANG(?kingdomLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?phylum .
        ?phylum wdt:P105 wd:Q38348 .
        ?phylum rdfs:label ?phylumLabel .
        FILTER(LANG(?phylumLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?class .
        ?class wdt:P105 wd:Q5284 .
        ?class rdfs:label ?classLabel .
        FILTER(LANG(?classLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?order .
        ?order wdt:P105 wd:Q36602 .
        ?order rdfs:label ?orderLabel .
        FILTER(LANG(?orderLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?family .
        ?family wdt:P105 wd:Q35409 .
        ?family rdfs:label ?familyLabel .
        FILTER(LANG(?familyLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P171* ?genus .
        ?genus wdt:P105 wd:Q34740 .
        ?genus rdfs:label ?genusLabel .
        FILTER(LANG(?genusLabel) = "en")
      }}
      OPTIONAL {{ 
        wd:{qid} wdt:P105 wd:Q7432 .
        wd:{qid} rdfs:label ?speciesLabel .
        FILTER(LANG(?speciesLabel) = "en")
      }}
    }}
    LIMIT 1
    """
    
    try:
        headers = {
            "Accept": "application/sparql-results+json",
            "User-Agent": "SpeciesTreeService/1.0"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(settings.SPARQL_API, params={"query": query}, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data["results"]["bindings"]
                    if results:
                        result = results[0]
                        return {
                            "kingdom": result.get("kingdomLabel", {}).get("value"),
                            "phylum": result.get("phylumLabel", {}).get("value"),
                            "class_name": result.get("classLabel", {}).get("value"),
                            "order": result.get("orderLabel", {}).get("value"),
                            "family": result.get("familyLabel", {}).get("value"),
                            "genus": result.get("genusLabel", {}).get("value"),
                            "species": result.get("speciesLabel", {}).get("value")
                        }
    except Exception as e:
        print(f"Error getting taxonomic classification: {e}")
    
    return {}

async def collect_taxonomic_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """Collect taxonomic relationships in both directions and return formatted list."""
    relationships = []
    all_qids = set([qid])
    sent_entities = set()

    # Send initial status via WebSocket
    if websocket_manager:
        await websocket_manager.send_status("Starting taxonomic relationship collection...", 0)
        
        # Get initial entity details and send them
        initial_labels = get_species_labels({qid})
        initial_species_name = initial_labels.get(qid, qid)
        initial_details = await get_species_details_by_qid(qid)
        if initial_details:
            await websocket_manager.send_json({
                "type": "species_details",
                "data": {
                    "entity": initial_species_name,
                    "qid": qid,
                    **initial_details
                }
            })
            sent_entities.add(qid)

    # Collect parent taxa (upward)
    await collect_relationships_recursive(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send progress update
    if websocket_manager:
        await websocket_manager.send_status("Parent taxa collected, now collecting child taxa...", 50)

    # Collect child taxa (downward)
    await collect_relationships_recursive(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

    # Send completion status
    if websocket_manager:
        await websocket_manager.send_status("Collection complete!", 100)

    # Fetch labels for all entities
    labels = get_species_labels(all_qids)

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
    Recursively collect taxonomic relationships in {"entity1": str, "relationship": str, "entity2": str} format.
    direction: 'up' (parent taxa) or 'down' (child taxa)
    """
    if depth == 0 or qid in visited:
        return
    visited.add(qid)
    
    if sent_entities is None:
        sent_entities = set()

    if direction == "up":  # Parent taxa
        parents = get_parent_taxa(qid)
        for parent_qid in parents:
            relationship = {"entity1": qid, "relationship": "child of", "entity2": parent_qid}
            relationships.append(relationship)
            all_qids.update([qid, parent_qid])
            
            # Send relationship immediately via WebSocket
            if websocket_manager:
                labels = get_species_labels({qid, parent_qid})
                named_relationship = {
                    "entity1": labels.get(qid, qid),
                    "relationship": "child of",
                    "entity2": labels.get(parent_qid, parent_qid)
                }
                await websocket_manager.send_json({
                    "type": "relationship",
                    "data": named_relationship
                })
                
                # Send species details if not already sent
                if parent_qid not in sent_entities:
                    parent_details = await get_species_details_by_qid(parent_qid)
                    if parent_details:
                        await websocket_manager.send_json({
                            "type": "species_details",
                            "data": {
                                "entity": labels.get(parent_qid, parent_qid),
                                "qid": parent_qid,
                                **parent_details
                            }
                        })
                        sent_entities.add(parent_qid)
            
            await collect_relationships_recursive(parent_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

    elif direction == "down":  # Child taxa
        children = get_child_taxa(qid)
        for child_qid in children[:20]:  # Limit to avoid too many results
            relationship = {"entity1": child_qid, "relationship": "child of", "entity2": qid}
            relationships.append(relationship)
            all_qids.update([child_qid, qid])

            # Send relationship immediately via WebSocket
            if websocket_manager:
                labels = get_species_labels({child_qid, qid})
                named_relationship = {
                    "entity1": labels.get(child_qid, child_qid),
                    "relationship": "child of",
                    "entity2": labels.get(qid, qid)
                }
                await websocket_manager.send_json({
                    "type": "relationship",
                    "data": named_relationship
                })
                
                # Send species details if not already sent
                if child_qid not in sent_entities:
                    child_details = await get_species_details_by_qid(child_qid)
                    if child_details:
                        await websocket_manager.send_json({
                            "type": "species_details",
                            "data": {
                                "entity": labels.get(child_qid, child_qid),
                                "qid": child_qid,
                                **child_details
                            }
                        })
                        sent_entities.add(child_qid)

            await collect_relationships_recursive(child_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

async def check_species_validity(species_name: str) -> bool:
    """Check if the species name corresponds to a valid biological entity in Wikidata."""
    qid = get_species_qid(species_name)
    return qid is not None and verify_biological_entity(qid)
