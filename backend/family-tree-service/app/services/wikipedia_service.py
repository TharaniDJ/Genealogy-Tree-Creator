# from typing import List, Dict, Optional
# import requests
# import asyncio
# import aiohttp
# import json
# from app.core.websocket_manager import WebSocketManager

# WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
# SPARQL_API='https://query.wikidata.org/sparql'

# async def getPersonalDetails(page_title:str):
#     qid = get_qid(page_title)
#     if not qid:
#         return None
#     return await getPersonalDetailsByQid(qid)

# async def getPersonalDetailsByQid(qid: str):
#     """Get personal details directly using Wikidata QID."""
#     query = f"""
#     SELECT ?birthDate ?deathDate ?image WHERE {{
#       wd:{qid} wdt:P569 ?birthDate.
#       OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate. }}
#       OPTIONAL {{ wd:{qid} wdt:P18 ?image. }}
#     }}
#     """

#     headers = {
#         "Accept": "application/sparql-results+json",
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#             if resp.status != 200:
#                 text = await resp.text()
#                 raise RuntimeError(f"SPARQL query failed ({resp.status}): {text}")

#             # Allow aiohttp to parse JSON even if content-type is not strictly application/json
#             data = await resp.json(content_type=None)
#             results = data.get("results", {}).get("bindings", [])

#             if not results:
#                 return None

#             result = results[0]
#             birth_date = result.get("birthDate", {}).get("value")
#             death_date = result.get("deathDate", {}).get("value")
#             image = result.get("image", {}).get("value")

#             return {
#                 "birth_year": birth_date[:4] if birth_date else None,
#                 "death_year": death_date[:4] if death_date else None,
#                 "image_url": image
#             }

# async def fetch_relationships(page_title: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """
#     Fetch genealogical relationships for a given Wikipedia page title and depth.
#     Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
#     """
#     try:
#         qid = get_qid(page_title)
#         print(f"Fetched QID for '{page_title}': {qid}")  # Debug print
        
#         if not qid:
#             # Send error message via WebSocket if available
#             if websocket_manager:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "status",
#                     "data": {
#                         "message": f"No Wikipedia/Wikidata entry found for '{page_title}'. This person may not have sufficient notable information.",
#                         "progress": 100
#                     }
#                 }))
#             print(f"No QID found for '{page_title}', returning empty relationships")
#             return []
            
#         return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
#     except Exception as e:
#         error_msg = f"Error fetching relationships for '{page_title}': {str(e)}"
#         print(error_msg)
        
#         # Send error message via WebSocket if available
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": error_msg,
#                     "progress": 100
#                 }
#             }))
        
#         return []

# def get_qid(page_title: str) -> Optional[str]:
#     """Return the Wikidata Q-identifier for a Wikipedia page title, or None if not found."""
#     params = {
#         "action": "query",
#         "titles": page_title,
#         "prop": "pageprops",
#         "ppprop": "wikibase_item",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     try:
#         response = requests.get(WIKIPEDIA_API, params=params, headers=headers)

#         print(f"Status code: {response.status_code}")
#         if response.status_code != 200:
#             print(f"Failed to fetch data for {page_title}: {response.status_code}")
#             return None

#         data = response.json()
#         print(f"Wikipedia API response for '{page_title}': {data}")  # Debug print

#         # Navigate through the JSON structure safely
#         pages = data.get("query", {}).get("pages", {})
#         for page in pages.values():
#             # Check if page exists (not missing)
#             if "missing" in page:
#                 print(f"Page '{page_title}' does not exist on Wikipedia")
#                 return None
                
#             qid = page.get("pageprops", {}).get("wikibase_item")
#             if qid:
#                 return qid

#         print(f"Q-id not found for page: {page_title}")
#         return None

#     except Exception as e:
#         print(f"Error fetching QID for {page_title}: {e}")
#         return None

# WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# def fetch_entity(qid: str) -> dict:
#     """Return the full JSON entity document for a given Wikidata QID."""
#     params = {
#         "action": "wbgetentities",
#         "ids": qid,
#         "format": "json"
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         raise RuntimeError(f"Failed to fetch entity {qid}: {response.status_code}")

#     data = response.json()
#     entities = data.get("entities", {})
#     if qid not in entities:
#         raise ValueError(f"Entity {qid} not found in response")

#     return entities[qid]

# def get_labels(qids: set) -> Dict[str, str]:
#     """Batch-fetch English labels for a set of Q-ids (returns dict)."""
#     if not qids:
#         return {}

#     params = {
#         "action": "wbgetentities",
#         "ids": "|".join(qids),  # pipe-separated list (not comma)
#         "props": "labels",
#         "languages": "en",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         print(f"Failed to fetch labels: {response.status_code}")
#         print(f"Response text: {response.text}")
#         return {}  # Return empty dict instead of raising error

#     data = response.json()
    
#     # Check for errors in response
#     if "error" in data:
#         print(f"Wikidata API error: {data['error']}")
#         return {}
        
#     entities = data.get("entities", {})

#     # Build dict of qid -> label
#     labels = {}
#     for qid, entity in entities.items():
#         # Check if entity exists (not missing)
#         if entity.get("missing"):
#             print(f"Entity {qid} is missing from Wikidata")
#             continue
            
#         label_info = entity.get("labels", {}).get("en")
#         if label_info and "value" in label_info:
#             labels[qid] = label_info["value"]
#         else:
#             print(f"No English label found for {qid}")

#     return labels

# def get_parents(qid: str) -> List[str]:
#     """Return a list of parent QIDs for a given QID."""
#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})
#     parents = []
#     for snak in claims.get("P22", []):  # Father
#         parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
#     for snak in claims.get("P25", []):  # Mother
#         parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
#     return parents

# async def get_adoptive_children_sparql(qid: str) -> List[str]:
#     """Get adoptive children using SPARQL query."""
#     query = f"""
#     SELECT ?child WHERE {{
#       ?child wdt:P1441 wd:{qid} .
#     }}
#     """

#     headers = {
#         "Accept": "application/sparql-results+json",
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#                 if resp.status != 200:
#                     print(f"SPARQL query failed for adoptive children of {qid}: {resp.status}")
#                     return []

#                 data = await resp.json(content_type=None)
#                 results = data.get("results", {}).get("bindings", [])
                
#                 children = []
#                 for result in results:
#                     child_uri = result.get("child", {}).get("value", "")
#                     if child_uri.startswith("http://www.wikidata.org/entity/"):
#                         child_qid = child_uri.split("/")[-1]
#                         children.append(child_qid)
                
#                 return children
#     except Exception as e:
#         print(f"Error fetching adoptive children for {qid}: {e}")
#         return []

# async def get_all_children_sparql(qid: str) -> Dict[str, List[str]]:
#     """Get all types of children using SPARQL query."""
#     query = f"""
#     SELECT ?child ?relationship WHERE {{
#       {{
#         ?child wdt:P22 wd:{qid} .
#         BIND("biological_father" AS ?relationship)
#       }} UNION {{
#         ?child wdt:P25 wd:{qid} .
#         BIND("biological_mother" AS ?relationship)
#       }} UNION {{
#         ?child wdt:P1441 wd:{qid} .
#         BIND("adoptive_parent" AS ?relationship)
#       }} UNION {{
#         ?child wdt:P8810 wd:{qid} .
#         BIND("parent" AS ?relationship)
#       }}
#     }}
#     """

#     headers = {
#         "Accept": "application/sparql-results+json",
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     try:
#         async with aiohttp.ClientSession() as session:
#             async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#                 if resp.status != 200:
#                     print(f"SPARQL query failed for children of {qid}: {resp.status}")
#                     return {}

#                 data = await resp.json(content_type=None)
#                 results = data.get("results", {}).get("bindings", [])
                
#                 children_by_type = {
#                     "biological_father": [],
#                     "biological_mother": [],
#                     "adoptive_parent": [],
#                     "parent": []
#                 }
                
#                 for result in results:
#                     child_uri = result.get("child", {}).get("value", "")
#                     relationship = result.get("relationship", {}).get("value", "")
                    
#                     if child_uri.startswith("http://www.wikidata.org/entity/"):
#                         child_qid = child_uri.split("/")[-1]
#                         if relationship in children_by_type:
#                             children_by_type[relationship].append(child_qid)
                
#                 return children_by_type
#     except Exception as e:
#         print(f"Error fetching children for {qid}: {e}")
#         return {}

# def extract_qid(snak: dict) -> Optional[str]:
#     """Safely extract QID from a snak, return None if unavailable."""
#     try:
#         if snak.get("mainsnak", {}).get("snaktype") != "value":
#             return None
#         return snak["mainsnak"]["datavalue"]["value"]["id"]
#     except Exception:
#         return None

# async def collect_relationships(
#     qid: str,
#     depth: int,
#     direction: str,
#     relationships: List[Dict[str, str]],
#     visited: set,
#     all_qids: set,
#     websocket_manager: Optional[WebSocketManager] = None,
#     sent_entities: Optional[set] = None
# ):
#     """
#     Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
#     Supports only 3 types: child of, spouse of, adopted by.
#     """
#     if depth == 0 or qid in visited:
#         return
#     visited.add(qid)

#     if sent_entities is None:
#         sent_entities = set()

#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})

#     # ----------------------
#     # Biological & adoptive parents (UP)
#     # ----------------------
#     if direction == "up":
#         for prop, rel_name in {
#             "P22": "child of",     # father
#             "P25": "child of",     # mother
#             "P3373": "adopted by", # adoptive parent
#             "P3448": "adopted by"  # stepparent
#         }.items():
#             for snak in claims.get(prop, []):
#                 parent_qid = extract_qid(snak)
#                 if not parent_qid:
#                     continue
#                 relationships.append({"entity1": qid, "relationship": rel_name, "entity2": parent_qid})
#                 all_qids.update([qid, parent_qid])

#                 if websocket_manager:
#                     labels = get_labels({qid, parent_qid})
#                     named_rel = {
#                         "entity1": labels.get(qid, qid),
#                         "relationship": rel_name,
#                         "entity2": labels.get(parent_qid, parent_qid)
#                     }
#                     await websocket_manager.send_message(json.dumps({"type": "relationship", "data": named_rel}))

#                     if parent_qid not in sent_entities:
#                         parent_details = await getPersonalDetailsByQid(parent_qid)
#                         if parent_details:
#                             await websocket_manager.send_message(json.dumps({
#                                 "type": "personal_details",
#                                 "data": {
#                                     "entity": labels.get(parent_qid, parent_qid),
#                                     "qid": parent_qid,
#                                     **parent_details
#                                 }
#                             }))
#                             sent_entities.add(parent_qid)

#                 # recurse upward
#                 await collect_relationships(
#                     parent_qid, depth - 1, direction,
#                     relationships, visited, all_qids,
#                     websocket_manager, sent_entities
#                 )

#     # ----------------------
#     # Spouses & children (DOWN)
#     # ----------------------
#     elif direction == "down":
#         # spouses
#         for prop, rel_name in {"P26": "spouse of", "P451": "spouse of"}.items():
#             for snak in claims.get(prop, []):
#                 spouse_qid = extract_qid(snak)
#                 if not spouse_qid:
#                     continue
#                 relationships.append({"entity1": qid, "relationship": rel_name, "entity2": spouse_qid})
#                 all_qids.update([qid, spouse_qid])

#                 if websocket_manager:
#                     labels = get_labels({qid, spouse_qid})
#                     named_rel = {
#                         "entity1": labels.get(qid, qid),
#                         "relationship": rel_name,
#                         "entity2": labels.get(spouse_qid, spouse_qid)
#                     }
#                     await websocket_manager.send_message(json.dumps({"type": "relationship", "data": named_rel}))

#                     if spouse_qid not in sent_entities:
#                         spouse_details = await getPersonalDetailsByQid(spouse_qid)
#                         if spouse_details:
#                             await websocket_manager.send_message(json.dumps({
#                                 "type": "personal_details",
#                                 "data": {
#                                     "entity": labels.get(spouse_qid, spouse_qid),
#                                     "qid": spouse_qid,
#                                     **spouse_details
#                                 }
#                             }))
#                             sent_entities.add(spouse_qid)

#         # children
#         for snak in claims.get("P40", []):
#             child_qid = extract_qid(snak)
#             if not child_qid:
#                 continue
#             relationships.append({"entity1": child_qid, "relationship": "child of", "entity2": qid})
#             all_qids.update([child_qid, qid])

#             if websocket_manager:
#                 labels = get_labels({child_qid, qid})
#                 named_rel = {
#                     "entity1": labels.get(child_qid, child_qid),
#                     "relationship": "child of",
#                     "entity2": labels.get(qid, qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({"type": "relationship", "data": named_rel}))

#                 if child_qid not in sent_entities:
#                     child_details = await getPersonalDetailsByQid(child_qid)
#                     if child_details:
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "personal_details",
#                             "data": {
#                                 "entity": labels.get(child_qid, child_qid),
#                                 "qid": child_qid,
#                                 **child_details
#                             }
#                         }))
#                         sent_entities.add(child_qid)

#             # recurse downward
#             await collect_relationships(
#                 child_qid, depth - 1, direction,
#                 relationships, visited, all_qids,
#                 websocket_manager, sent_entities
#             )

# async def send_relationship_and_details(websocket_manager: Optional[WebSocketManager], relationship: Dict[str, str], qids: set, sent_entities: set):
#     """Helper function to send relationship and personal details via WebSocket."""
#     if not websocket_manager:
#         return
        
#     # Get labels for this specific relationship
#     labels = get_labels(qids)
    
#     # Send relationship with proper labels
#     entity1_name = labels.get(relationship["entity1"], relationship["entity1"])
#     entity2_name = labels.get(relationship["entity2"], relationship["entity2"])
    
#     named_relationship = {
#         "entity1": entity1_name,
#         "relationship": relationship["relationship"],
#         "entity2": entity2_name
#     }
    
#     await websocket_manager.send_message(json.dumps({
#         "type": "relationship",
#         "data": named_relationship
#     }))
    
#     # Send personal details for entities not already sent
#     for qid in qids:
#         if qid not in sent_entities:
#             details = await getPersonalDetailsByQid(qid)
#             if details:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "personal_details",
#                     "data": {
#                         "entity": labels.get(qid, qid),
#                         "qid": qid,
#                         **details
#                     }
#                 }))
#                 sent_entities.add(qid)

# async def handle_child_spouse_relationships(child_qid: str, spouse_qids: set, relationships: List[Dict[str, str]], all_qids: set, websocket_manager: Optional[WebSocketManager], sent_entities: set):
#     """Helper function to handle child-spouse relationships."""
#     # Check if any of the known spouses is also a parent of this child
#     child_entity = fetch_entity(child_qid)
#     child_claims = child_entity.get("claims", {})
#     child_parents = set()
    
#     # Check all parent types
#     for parent_prop in ["P22", "P25", "P1441", "P8810"]:  # Father, mother, adoptive parent, generic parent
#         for parent_snak in child_claims.get(parent_prop, []):
#             parent_qid = parent_snak["mainsnak"]["datavalue"]["value"]["id"]
#             child_parents.add(parent_qid)

#     # For each spouse that is also a parent of this child, send the child-spouse relationship
#     for spouse_qid in spouse_qids:
#         if spouse_qid in child_parents:
#             spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
#             relationships.append(spouse_relationship)
#             all_qids.add(spouse_qid)
            
#             await send_relationship_and_details(websocket_manager, spouse_relationship, {child_qid, spouse_qid}, sent_entities)

# async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """Collect relationships in both directions and return formatted list."""
#     relationships = []
#     all_qids = set([qid])
#     sent_entities = set()  # Track entities whose personal details have been sent
    
#     # Send initial status via WebSocket
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Starting relationship collection (including adoptions)...", "progress": 0}
#         }))
        
#         # Get initial entity details and send them
#         initial_labels = get_labels({qid})
#         print(f"Fetched labels for '{qid}': {initial_labels}")  # Debug print
#         initial_entity_name = initial_labels.get(qid, qid)
#         print(f"Initial entity name for '{qid}': {initial_entity_name}")  # Debug print
#         initial_details = await getPersonalDetailsByQid(qid)
#         print(f"Initial personal details for '{qid}': {initial_details}")  # Debug print
#         if initial_details:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "personal_details",
#                 "data": {
#                     "entity": initial_entity_name,
#                     "qid": qid,
#                     **initial_details
#                 }
#             }))
#             sent_entities.add(qid)  # Mark initial entity as sent

#     # Collect ancestors (upward) - includes biological parents, adoptive parents, and spouses
#     await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

#     # Send progress update
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
#         }))

#     # Collect descendants (downward) - includes biological children, adopted children, and spouses
#     await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

#     # Send completion status
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Collection complete! (Including adoption relationships)", "progress": 100}
#         }))

#     # Fetch labels for all entities
#     labels = get_labels(all_qids)

#     # Replace QIDs with names in relationships
#     named_relationships = []
#     for rel in relationships:
#         entity1_name = labels.get(rel["entity1"], rel["entity1"])
#         entity2_name = labels.get(rel["entity2"], rel["entity2"])
#         named_relationships.append({
#             "entity1": entity1_name,
#             "relationship": rel["relationship"],
#             "entity2": entity2_name
#         })

#     return named_relationships

# async def check_wikipedia_tree(page_title: str) -> bool:
#     """Check if Wikipedia page contains family tree templates."""
#     try:
#         params = {
#             "action": "parse",
#             "page": page_title,
#             "prop": "wikitext",
#             "format": "json",
#         }
#         response = requests.get(WIKIPEDIA_API, params=params).json()
#         if "parse" in response and "wikitext" in response["parse"]:
#             text = response["parse"]["wikitext"]["*"]
#             needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
#             return any(n.lower() in text.lower() for n in needles)
#     except:
#         pass
#     return False


#second code
# from typing import List, Dict, Optional
# import requests
# import asyncio
# import aiohttp
# import json
# from app.core.websocket_manager import WebSocketManager

# WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
# SPARQL_API='https://query.wikidata.org/sparql'

# async def getPersonalDetails(page_title:str):
#     qid = get_qid(page_title)
#     if not qid:
#         return None
#     return await getPersonalDetailsByQid(qid)

# async def getPersonalDetailsByQid(qid: str):
#     """Get personal details directly using Wikidata QID."""
#     query = f"""
#     SELECT ?birthDate ?deathDate ?image WHERE {{
#       wd:{qid} wdt:P569 ?birthDate.
#       OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate. }}
#       OPTIONAL {{ wd:{qid} wdt:P18 ?image. }}
#     }}
#     """

#     headers = {
#         "Accept": "application/sparql-results+json",
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#             if resp.status != 200:
#                 text = await resp.text()
#                 raise RuntimeError(f"SPARQL query failed ({resp.status}): {text}")

#             # Allow aiohttp to parse JSON even if content-type is not strictly application/json
#             data = await resp.json(content_type=None)
#             results = data.get("results", {}).get("bindings", [])

#             if not results:
#                 return None

#             result = results[0]
#             birth_date = result.get("birthDate", {}).get("value")
#             death_date = result.get("deathDate", {}).get("value")
#             image = result.get("image", {}).get("value")

#             return {
#                 "birth_year": birth_date[:4] if birth_date else None,
#                 "death_year": death_date[:4] if death_date else None,
#                 "image_url": image
#             }

# async def fetch_relationships(page_title: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """
#     Fetch genealogical relationships for a given Wikipedia page title and depth.
#     Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
#     """
#     try:
#         qid = get_qid(page_title)
#         print(f"Fetched QID for '{page_title}': {qid}")  # Debug print
        
#         if not qid:
#             # Send error message via WebSocket if available
#             if websocket_manager:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "status",
#                     "data": {
#                         "message": f"No Wikipedia/Wikidata entry found for '{page_title}'. This person may not have sufficient notable information.",
#                         "progress": 100
#                     }
#                 }))
#             print(f"No QID found for '{page_title}', returning empty relationships")
#             return []
            
#         return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
#     except Exception as e:
#         error_msg = f"Error fetching relationships for '{page_title}': {str(e)}"
#         print(error_msg)
        
#         # Send error message via WebSocket if available
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": error_msg,
#                     "progress": 100
#                 }
#             }))
        
#         return []

# def get_qid(page_title: str) -> Optional[str]:
#     """Return the Wikidata Q-identifier for a Wikipedia page title, or None if not found."""
#     params = {
#         "action": "query",
#         "titles": page_title,
#         "prop": "pageprops",
#         "ppprop": "wikibase_item",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     try:
#         response = requests.get(WIKIPEDIA_API, params=params, headers=headers)

#         print(f"Status code: {response.status_code}")
#         if response.status_code != 200:
#             print(f"Failed to fetch data for {page_title}: {response.status_code}")
#             return None

#         data = response.json()
#         print(f"Wikipedia API response for '{page_title}': {data}")  # Debug print

#         # Navigate through the JSON structure safely
#         pages = data.get("query", {}).get("pages", {})
#         for page in pages.values():
#             # Check if page exists (not missing)
#             if "missing" in page:
#                 print(f"Page '{page_title}' does not exist on Wikipedia")
#                 return None
                
#             qid = page.get("pageprops", {}).get("wikibase_item")
#             if qid:
#                 return qid

#         print(f"Q-id not found for page: {page_title}")
#         return None

#     except Exception as e:
#         print(f"Error fetching QID for {page_title}: {e}")
#         return None

# WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# def fetch_entity(qid: str) -> dict:
#     """Return the full JSON entity document for a given Wikidata QID."""
#     params = {
#         "action": "wbgetentities",
#         "ids": qid,
#         "format": "json"
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         raise RuntimeError(f"Failed to fetch entity {qid}: {response.status_code}")

#     data = response.json()
#     entities = data.get("entities", {})
#     if qid not in entities:
#         raise ValueError(f"Entity {qid} not found in response")

#     return entities[qid]

# def get_labels(qids: set) -> Dict[str, str]:
#     """Batch-fetch English labels for a set of Q-ids (returns dict)."""
#     if not qids:
#         return {}

#     params = {
#         "action": "wbgetentities",
#         "ids": "|".join(qids),  # pipe-separated list (not comma)
#         "props": "labels",
#         "languages": "en",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         print(f"Failed to fetch labels: {response.status_code}")
#         print(f"Response text: {response.text}")
#         return {}  # Return empty dict instead of raising error

#     data = response.json()
    
#     # Check for errors in response
#     if "error" in data:
#         print(f"Wikidata API error: {data['error']}")
#         return {}
        
#     entities = data.get("entities", {})

#     # Build dict of qid -> label
#     labels = {}
#     for qid, entity in entities.items():
#         # Check if entity exists (not missing)
#         if entity.get("missing"):
#             print(f"Entity {qid} is missing from Wikidata")
#             continue
            
#         label_info = entity.get("labels", {}).get("en")
#         if label_info and "value" in label_info:
#             labels[qid] = label_info["value"]
#         else:
#             print(f"No English label found for {qid}")

#     return labels

# def get_parents(qid: str) -> List[str]:
#     """Return a list of parent QIDs for a given QID."""
#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})
#     parents = []
#     for snak in claims.get("P22", []):  # Father
#         if extract_qid(snak):
#             parents.append(extract_qid(snak))
#     for snak in claims.get("P25", []):  # Mother
#         if extract_qid(snak):
#             parents.append(extract_qid(snak))
#     return parents

# def extract_qid(snak: dict) -> Optional[str]:
#     """Safely extract QID from a snak, return None if unavailable."""
#     try:
#         if snak.get("mainsnak", {}).get("snaktype") != "value":
#             return None
#         return snak["mainsnak"]["datavalue"]["value"]["id"]
#     except Exception:
#         return None

# async def send_relationship_and_details(
#     websocket_manager: Optional[WebSocketManager], 
#     entity1_qid: str, 
#     relationship: str, 
#     entity2_qid: str, 
#     all_qids: set, 
#     sent_entities: set
# ):
#     """Helper function to send relationship and personal details via WebSocket."""
#     if not websocket_manager:
#         return
        
#     # Get labels for the entities
#     labels = get_labels({entity1_qid, entity2_qid})
    
#     # Send relationship with proper labels
#     entity1_name = labels.get(entity1_qid, entity1_qid)
#     entity2_name = labels.get(entity2_qid, entity2_qid)
    
#     named_relationship = {
#         "entity1": entity1_name,
#         "relationship": relationship,
#         "entity2": entity2_name
#     }
    
#     await websocket_manager.send_message(json.dumps({
#         "type": "relationship",
#         "data": named_relationship
#     }))
    
#     # Send personal details for entities not already sent
#     for qid in [entity1_qid, entity2_qid]:
#         if qid not in sent_entities:
#             details = await getPersonalDetailsByQid(qid)
#             if details:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "personal_details",
#                     "data": {
#                         "entity": labels.get(qid, qid),
#                         "qid": qid,
#                         **details
#                     }
#                 }))
#                 sent_entities.add(qid)

# async def collect_relationships(
#     qid: str, 
#     depth: int, 
#     direction: str, 
#     relationships: List[Dict[str, str]], 
#     visited: set, 
#     all_qids: set, 
#     websocket_manager: Optional[WebSocketManager] = None, 
#     sent_entities: Optional[set] = None
# ):
#     """
#     Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
#     direction: 'up' (ancestors) or 'down' (descendants)
#     """
#     if depth == 0 or qid in visited:
#         return
#     visited.add(qid)
    
#     if sent_entities is None:
#         sent_entities = set()

#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})

#     if direction == "up":  # Ancestors - parents and spouses
#         # Biological and adoptive parents
#         parent_properties = {
#             "P22": "child of",    # father
#             "P25": "child of",    # mother
#             "P1441": "adopted by", # adoptive parent
#             "P3373": "adopted by", # adoptive parent (alternative)
#             "P8810": "child of"   # generic parent
#         }
        
#         for prop, rel_name in parent_properties.items():
#             for snak in claims.get(prop, []):
#                 parent_qid = extract_qid(snak)
#                 if not parent_qid:
#                     continue
                    
#                 relationship = {"entity1": qid, "relationship": rel_name, "entity2": parent_qid}
#                 relationships.append(relationship)
#                 all_qids.update([qid, parent_qid])
                
#                 # Send relationship immediately via WebSocket
#                 await send_relationship_and_details(
#                     websocket_manager, qid, rel_name, parent_qid, all_qids, sent_entities
#                 )
                
#                 # Recurse upward
#                 await collect_relationships(
#                     parent_qid, depth - 1, direction, relationships, 
#                     visited, all_qids, websocket_manager, sent_entities
#                 )

#         # Spouses (only in up direction to avoid duplication)
#         spouse_properties = ["P26", "P451"]  # spouse, unmarried partner
#         for prop in spouse_properties:
#             for snak in claims.get(prop, []):
#                 spouse_qid = extract_qid(snak)
#                 if not spouse_qid:
#                     continue
                    
#                 relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
#                 relationships.append(relationship)
#                 all_qids.update([qid, spouse_qid])
                
#                 # Send relationship immediately via WebSocket
#                 await send_relationship_and_details(
#                     websocket_manager, qid, "spouse of", spouse_qid, all_qids, sent_entities
#                 )

#     elif direction == "down":  # Descendants - children and their relationships
#         # Collect all spouses first
#         spouse_qids = set()
#         spouse_properties = ["P26", "P451"]  # spouse, unmarried partner
        
#         for prop in spouse_properties:
#             for snak in claims.get(prop, []):
#                 spouse_qid = extract_qid(snak)
#                 if spouse_qid:
#                     spouse_qids.add(spouse_qid)
#                     # Note: spouse relationships are handled in "up" direction to avoid duplication

#         # Children (biological, adopted, etc.)
#         for snak in claims.get("P40", []):  # child
#             child_qid = extract_qid(snak)
#             if not child_qid:
#                 continue
                
#             relationship = {"entity1": child_qid, "relationship": "child of", "entity2": qid}
#             relationships.append(relationship)
#             all_qids.update([child_qid, qid])

#             # Send relationship immediately via WebSocket
#             await send_relationship_and_details(
#                 websocket_manager, child_qid, "child of", qid, all_qids, sent_entities
#             )

#             # Check if any of the known spouses is also a parent of this child
#             child_entity = fetch_entity(child_qid)
#             child_claims = child_entity.get("claims", {})
#             child_parents = set()
            
#             # Check all parent types for this child
#             for parent_prop in ["P22", "P25", "P1441", "P3373", "P8810"]:
#                 for parent_snak in child_claims.get(parent_prop, []):
#                     parent_qid = extract_qid(parent_snak)
#                     if parent_qid:
#                         child_parents.add(parent_qid)

#             # For each spouse that is also a parent of this child, add that relationship
#             for spouse_qid in spouse_qids:
#                 if spouse_qid in child_parents:
#                     spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
#                     relationships.append(spouse_relationship)
#                     all_qids.add(spouse_qid)
                    
#                     # Send spouse-child relationship immediately via WebSocket
#                     await send_relationship_and_details(
#                         websocket_manager, child_qid, "child of", spouse_qid, all_qids, sent_entities
#                     )

#             # Recurse downward
#             await collect_relationships(
#                 child_qid, depth - 1, direction, relationships, 
#                 visited, all_qids, websocket_manager, sent_entities
#             )

# async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """Collect relationships in both directions and return formatted list."""
#     relationships = []
#     all_qids = set([qid])
#     sent_entities = set()  # Track entities whose personal details have been sent
    
#     # Send initial status via WebSocket
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Starting relationship collection (including adoptions)...", "progress": 0}
#         }))
        
#         # Get initial entity details and send them
#         initial_labels = get_labels({qid})
#         print(f"Fetched labels for '{qid}': {initial_labels}")  # Debug print
#         initial_entity_name = initial_labels.get(qid, qid)
#         print(f"Initial entity name for '{qid}': {initial_entity_name}")  # Debug print
#         initial_details = await getPersonalDetailsByQid(qid)
#         print(f"Initial personal details for '{qid}': {initial_details}")  # Debug print
#         if initial_details:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "personal_details",
#                 "data": {
#                     "entity": initial_entity_name,
#                     "qid": qid,
#                     **initial_details
#                 }
#             }))
#             sent_entities.add(qid)  # Mark initial entity as sent

#     # Collect ancestors (upward) - includes biological parents, adoptive parents, and spouses
#     await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

#     # Send progress update
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
#         }))

#     # Collect descendants (downward) - includes biological children, adopted children
#     await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

#     # Send progress update for sibling discovery
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status", 
#             "data": {"message": "Finding additional siblings...", "progress": 75}
#         }))

#     # Find indirect siblings for all discovered people
#     discovered_qids = list(all_qids)  # Copy to avoid modification during iteration
#     for person_qid in discovered_qids:
#         await find_indirect_siblings(person_qid, all_qids, relationships, websocket_manager, sent_entities)

#     # Send completion status
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Collection complete! (Including adoption relationships)", "progress": 100}
#         }))

#     # DEBUG: Print debugging information
#     print(f"DEBUG: Total QIDs found: {len(all_qids)}")
#     print(f"DEBUG: QIDs: {all_qids}")
#     print(f"DEBUG: Total relationships: {len(relationships)}")
    
#     # Check for disconnected nodes
#     qids_in_relationships = set()
#     for rel in relationships:
#         qids_in_relationships.add(rel["entity1"])
#         qids_in_relationships.add(rel["entity2"])
    
#     disconnected_qids = all_qids - qids_in_relationships
#     if disconnected_qids:
#         print(f"DEBUG: DISCONNECTED QIDs FOUND: {disconnected_qids}")
    
#     # Fetch labels for all entities
#     labels = get_labels(all_qids)

#     # Replace QIDs with names in relationships
#     named_relationships = []
#     for rel in relationships:
#         entity1_name = labels.get(rel["entity1"], rel["entity1"])
#         entity2_name = labels.get(rel["entity2"], rel["entity2"])
#         named_relationships.append({
#             "entity1": entity1_name,
#             "relationship": rel["relationship"],
#             "entity2": entity2_name
#         })

#     return named_relationships

# async def check_wikipedia_tree(page_title: str) -> bool:
#     """Check if Wikipedia page contains family tree templates."""
#     try:
#         params = {
#             "action": "parse",
#             "page": page_title,
#             "prop": "wikitext",
#             "format": "json",
#         }
#         response = requests.get(WIKIPEDIA_API, params=params).json()
#         if "parse" in response and "wikitext" in response["parse"]:
#             text = response["parse"]["wikitext"]["*"]
#             needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
#             return any(n.lower() in text.lower() for n in needles)
#     except:
#         pass
#     return False
#third code
# from typing import List, Dict, Optional
# import requests
# import asyncio
# import aiohttp
# import json
# from app.core.websocket_manager import WebSocketManager

# WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
# SPARQL_API='https://query.wikidata.org/sparql'

# async def getPersonalDetails(page_title:str):
#     qid = get_qid(page_title)
#     if not qid:
#         return None
#     return await getPersonalDetailsByQid(qid)

# async def getPersonalDetailsByQid(qid: str):
#     """Get personal details directly using Wikidata QID."""
#     query = f"""
#     SELECT ?birthDate ?deathDate ?image WHERE {{
#       wd:{qid} wdt:P569 ?birthDate.
#       OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate. }}
#       OPTIONAL {{ wd:{qid} wdt:P18 ?image. }}
#     }}
#     """

#     headers = {
#         "Accept": "application/sparql-results+json",
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#             if resp.status != 200:
#                 text = await resp.text()
#                 raise RuntimeError(f"SPARQL query failed ({resp.status}): {text}")

#             # Allow aiohttp to parse JSON even if content-type is not strictly application/json
#             data = await resp.json(content_type=None)
#             results = data.get("results", {}).get("bindings", [])

#             if not results:
#                 return None

#             result = results[0]
#             birth_date = result.get("birthDate", {}).get("value")
#             death_date = result.get("deathDate", {}).get("value")
#             image = result.get("image", {}).get("value")

#             return {
#                 "birth_year": birth_date[:4] if birth_date else None,
#                 "death_year": death_date[:4] if death_date else None,
#                 "image_url": image
#             }

# async def fetch_relationships(page_title: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """
#     Fetch genealogical relationships for a given Wikipedia page title and depth.
#     Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
#     """
#     try:
#         qid = get_qid(page_title)
#         print(f"Fetched QID for '{page_title}': {qid}")  # Debug print
        
#         if not qid:
#             # Send error message via WebSocket if available
#             if websocket_manager:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "status",
#                     "data": {
#                         "message": f"No Wikipedia/Wikidata entry found for '{page_title}'. This person may not have sufficient notable information.",
#                         "progress": 100
#                     }
#                 }))
#             print(f"No QID found for '{page_title}', returning empty relationships")
#             return []
            
#         return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
#     except Exception as e:
#         error_msg = f"Error fetching relationships for '{page_title}': {str(e)}"
#         print(error_msg)
        
#         # Send error message via WebSocket if available
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": error_msg,
#                     "progress": 100
#                 }
#             }))
        
#         return []

# def get_qid(page_title: str) -> Optional[str]:
#     """Return the Wikidata Q-identifier for a Wikipedia page title, or None if not found."""
#     params = {
#         "action": "query",
#         "titles": page_title,
#         "prop": "pageprops",
#         "ppprop": "wikibase_item",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     try:
#         response = requests.get(WIKIPEDIA_API, params=params, headers=headers)

#         print(f"Status code: {response.status_code}")
#         if response.status_code != 200:
#             print(f"Failed to fetch data for {page_title}: {response.status_code}")
#             return None

#         data = response.json()
#         print(f"Wikipedia API response for '{page_title}': {data}")  # Debug print

#         # Navigate through the JSON structure safely
#         pages = data.get("query", {}).get("pages", {})
#         for page in pages.values():
#             # Check if page exists (not missing)
#             if "missing" in page:
#                 print(f"Page '{page_title}' does not exist on Wikipedia")
#                 return None
                
#             qid = page.get("pageprops", {}).get("wikibase_item")
#             if qid:
#                 return qid

#         print(f"Q-id not found for page: {page_title}")
#         return None

#     except Exception as e:
#         print(f"Error fetching QID for {page_title}: {e}")
#         return None

# WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# def fetch_entity(qid: str) -> dict:
#     """Return the full JSON entity document for a given Wikidata QID."""
#     params = {
#         "action": "wbgetentities",
#         "ids": qid,
#         "format": "json"
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         raise RuntimeError(f"Failed to fetch entity {qid}: {response.status_code}")

#     data = response.json()
#     entities = data.get("entities", {})
#     if qid not in entities:
#         raise ValueError(f"Entity {qid} not found in response")

#     return entities[qid]

# def get_labels(qids: set) -> Dict[str, str]:
#     """Batch-fetch English labels for a set of Q-ids (returns dict)."""
#     if not qids:
#         return {}

#     params = {
#         "action": "wbgetentities",
#         "ids": "|".join(qids),  # pipe-separated list (not comma)
#         "props": "labels",
#         "languages": "en",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         print(f"Failed to fetch labels: {response.status_code}")
#         print(f"Response text: {response.text}")
#         return {}  # Return empty dict instead of raising error

#     data = response.json()
    
#     # Check for errors in response
#     if "error" in data:
#         print(f"Wikidata API error: {data['error']}")
#         return {}
        
#     entities = data.get("entities", {})

#     # Build dict of qid -> label
#     labels = {}
#     for qid, entity in entities.items():
#         # Check if entity exists (not missing)
#         if entity.get("missing"):
#             print(f"Entity {qid} is missing from Wikidata")
#             continue
            
#         label_info = entity.get("labels", {}).get("en")
#         if label_info and "value" in label_info:
#             labels[qid] = label_info["value"]
#         else:
#             print(f"No English label found for {qid}")

#     return labels

# def get_parents(qid: str) -> List[str]:
#     """Return a list of parent QIDs for a given QID."""
#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})
#     parents = []
#     for snak in claims.get("P22", []):  # Father
#         if extract_qid(snak):
#             parents.append(extract_qid(snak))
#     for snak in claims.get("P25", []):  # Mother
#         if extract_qid(snak):
#             parents.append(extract_qid(snak))
#     return parents

# def extract_qid(snak: dict) -> Optional[str]:
#     """Safely extract QID from a snak, return None if unavailable."""
#     try:
#         if snak.get("mainsnak", {}).get("snaktype") != "value":
#             return None
#         return snak["mainsnak"]["datavalue"]["value"]["id"]
#     except Exception:
#         return None

# async def send_relationship_and_details(
#     websocket_manager: Optional[WebSocketManager], 
#     entity1_qid: str, 
#     relationship: str, 
#     entity2_qid: str, 
#     all_qids: set, 
#     sent_entities: set
# ):
#     """Helper function to send relationship and personal details via WebSocket."""
#     if not websocket_manager:
#         return
        
#     # Get labels for the entities
#     labels = get_labels({entity1_qid, entity2_qid})
    
#     # Send relationship with proper labels
#     entity1_name = labels.get(entity1_qid, entity1_qid)
#     entity2_name = labels.get(entity2_qid, entity2_qid)
    
#     named_relationship = {
#         "entity1": entity1_name,
#         "relationship": relationship,
#         "entity2": entity2_name
#     }
    
#     await websocket_manager.send_message(json.dumps({
#         "type": "relationship",
#         "data": named_relationship
#     }))
    
#     # Send personal details for entities not already sent
#     for qid in [entity1_qid, entity2_qid]:
#         if qid not in sent_entities:
#             details = await getPersonalDetailsByQid(qid)
#             if details:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "personal_details",
#                     "data": {
#                         "entity": labels.get(qid, qid),
#                         "qid": qid,
#                         **details
#                     }
#                 }))
#                 sent_entities.add(qid)

# async def collect_relationships(
#     qid: str, 
#     depth: int, 
#     direction: str, 
#     relationships: List[Dict[str, str]], 
#     visited: set, 
#     all_qids: set, 
#     websocket_manager: Optional[WebSocketManager] = None, 
#     sent_entities: Optional[set] = None
# ):
#     """
#     Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
#     direction: 'up' (ancestors) or 'down' (descendants)
#     """
#     if depth == 0 or qid in visited:
#         return
#     visited.add(qid)
    
#     if sent_entities is None:
#         sent_entities = set()

#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})

#     if direction == "up":  # Ancestors - parents and spouses
#         # Biological and adoptive parents
#         parent_properties = {
#             "P22": "child of",    # father
#             "P25": "child of",    # mother
#             "P1441": "adopted by", # adoptive parent
#             "P3373": "adopted by", # adoptive parent (alternative)
#             "P8810": "child of"   # generic parent
#         }
        
#         for prop, rel_name in parent_properties.items():
#             for snak in claims.get(prop, []):
#                 parent_qid = extract_qid(snak)
#                 if not parent_qid:
#                     continue
                    
#                 relationship = {"entity1": qid, "relationship": rel_name, "entity2": parent_qid}
#                 relationships.append(relationship)
#                 all_qids.update([qid, parent_qid])
                
#                 # Send relationship immediately via WebSocket
#                 await send_relationship_and_details(
#                     websocket_manager, qid, rel_name, parent_qid, all_qids, sent_entities
#                 )
                
#                 # Recurse upward
#                 await collect_relationships(
#                     parent_qid, depth - 1, direction, relationships, 
#                     visited, all_qids, websocket_manager, sent_entities
#                 )

#         # Spouses (only in up direction to avoid duplication)
#         spouse_properties = ["P26", "P451"]  # spouse, unmarried partner
#         for prop in spouse_properties:
#             for snak in claims.get(prop, []):
#                 spouse_qid = extract_qid(snak)
#                 if not spouse_qid:
#                     continue
                    
#                 relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
#                 relationships.append(relationship)
#                 all_qids.update([qid, spouse_qid])
                
#                 # Send relationship immediately via WebSocket
#                 await send_relationship_and_details(
#                     websocket_manager, qid, "spouse of", spouse_qid, all_qids, sent_entities
#                 )

#     elif direction == "down":  # Descendants - children and their relationships
#         # Collect all spouses first
#         spouse_qids = set()
#         spouse_properties = ["P26", "P451"]  # spouse, unmarried partner
        
#         for prop in spouse_properties:
#             for snak in claims.get(prop, []):
#                 spouse_qid = extract_qid(snak)
#                 if spouse_qid:
#                     spouse_qids.add(spouse_qid)
#                     # Note: spouse relationships are handled in "up" direction to avoid duplication

#         # Children (biological, adopted, etc.)
#         for snak in claims.get("P40", []):  # child
#             child_qid = extract_qid(snak)
#             if not child_qid:
#                 continue
                
#             relationship = {"entity1": child_qid, "relationship": "child of", "entity2": qid}
#             relationships.append(relationship)
#             all_qids.update([child_qid, qid])

#             # Send relationship immediately via WebSocket
#             await send_relationship_and_details(
#                 websocket_manager, child_qid, "child of", qid, all_qids, sent_entities
#             )

#             # Check if any of the known spouses is also a parent of this child
#             child_entity = fetch_entity(child_qid)
#             child_claims = child_entity.get("claims", {})
#             child_parents = set()
            
#             # Check all parent types for this child
#             for parent_prop in ["P22", "P25", "P1441", "P3373", "P8810"]:
#                 for parent_snak in child_claims.get(parent_prop, []):
#                     parent_qid = extract_qid(parent_snak)
#                     if parent_qid:
#                         child_parents.add(parent_qid)

#             # For each spouse that is also a parent of this child, add that relationship
#             for spouse_qid in spouse_qids:
#                 if spouse_qid in child_parents:
#                     spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
#                     relationships.append(spouse_relationship)
#                     all_qids.add(spouse_qid)
                    
#                     # Send spouse-child relationship immediately via WebSocket
#                     await send_relationship_and_details(
#                         websocket_manager, child_qid, "child of", spouse_qid, all_qids, sent_entities
#                     )

#             # Recurse downward
#             await collect_relationships(
#                 child_qid, depth - 1, direction, relationships, 
#                 visited, all_qids, websocket_manager, sent_entities
#             )

# async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """Collect relationships in both directions and return formatted list."""
#     relationships = []
#     all_qids = set([qid])
#     sent_entities = set()  # Track entities whose personal details have been sent
    
#     # Send initial status via WebSocket
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Starting relationship collection (including adoptions)...", "progress": 0}
#         }))
        
#         # Get initial entity details and send them
#         initial_labels = get_labels({qid})
#         print(f"Fetched labels for '{qid}': {initial_labels}")  # Debug print
#         initial_entity_name = initial_labels.get(qid, qid)
#         print(f"Initial entity name for '{qid}': {initial_entity_name}")  # Debug print
#         initial_details = await getPersonalDetailsByQid(qid)
#         print(f"Initial personal details for '{qid}': {initial_details}")  # Debug print
#         if initial_details:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "personal_details",
#                 "data": {
#                     "entity": initial_entity_name,
#                     "qid": qid,
#                     **initial_details
#                 }
#             }))
#             sent_entities.add(qid)  # Mark initial entity as sent

#     # Collect ancestors (upward) - includes biological parents, adoptive parents, and spouses
#     await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

#     # Send progress update
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
#         }))

#     # Collect descendants (downward) - includes biological children, adopted children
#     await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

#     # Send completion status
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Collection complete! (Including adoption relationships)", "progress": 100}
#         }))

#     # Fetch labels for all entities
#     labels = get_labels(all_qids)

#     # Replace QIDs with names in relationships
#     named_relationships = []
#     for rel in relationships:
#         entity1_name = labels.get(rel["entity1"], rel["entity1"])
#         entity2_name = labels.get(rel["entity2"], rel["entity2"])
#         named_relationships.append({
#             "entity1": entity1_name,
#             "relationship": rel["relationship"],
#             "entity2": entity2_name
#         })

#     return named_relationships

# async def check_wikipedia_tree(page_title: str) -> bool:
#     """Check if Wikipedia page contains family tree templates."""
#     try:
#         params = {
#             "action": "parse",
#             "page": page_title,
#             "prop": "wikitext",
#             "format": "json",
#         }
#         response = requests.get(WIKIPEDIA_API, params=params).json()
#         if "parse" in response and "wikitext" in response["parse"]:
#             text = response["parse"]["wikitext"]["*"]
#             needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
#             return any(n.lower() in text.lower() for n in needles)
#     except:
#         pass
#     return False
# #fourth code
# from typing import List, Dict, Optional
# import requests
# import asyncio
# import aiohttp
# import json
# from app.core.websocket_manager import WebSocketManager

# WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
# SPARQL_API='https://query.wikidata.org/sparql'

# async def fetch_relationships_by_qid(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None, entity_name: Optional[str] = None) -> List[Dict[str, str]]:
#     """
#     Fetch genealogical relationships using QID directly (no name lookup needed).
#     This is more reliable and faster than name-based lookup.
#     """
#     try:
#         # Validate QID format
#         if not qid or not qid.startswith('Q') or not qid[1:].isdigit():
#             error_msg = f"Invalid QID format: {qid}"
#             print(error_msg)
            
#             if websocket_manager:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "status",
#                     "data": {
#                         "message": error_msg,
#                         "progress": 100
#                     }
#                 }))
#             return []
        
#         # Send initial status
#         display_name = entity_name or qid
#         print(f"Starting QID-based expansion for '{qid}' (entity: {display_name})")
        
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": f"Expanding family tree for {display_name} using QID {qid}...",
#                     "progress": 0
#                 }
#             }))
        
#         # Use existing function with QID directly - no name lookup needed
#         return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
#     except Exception as e:
#         error_msg = f"Error fetching relationships for QID '{qid}': {str(e)}"
#         print(error_msg)
        
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": error_msg,
#                     "progress": 100
#                 }
#             }))
        
#         return []
# async def getPersonalDetails(page_title:str):
#     qid = get_qid(page_title)
#     if not qid:
#         return None
#     return await getPersonalDetailsByQid(qid)

# async def getPersonalDetailsByQid(qid: str):
#     """Get personal details directly using Wikidata QID."""
#     query = f"""
#     SELECT ?birthDate ?deathDate ?image WHERE {{
#       wd:{qid} wdt:P569 ?birthDate.
#       OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate. }}
#       OPTIONAL {{ wd:{qid} wdt:P18 ?image. }}
#     }}
#     """

#     headers = {
#         "Accept": "application/sparql-results+json",
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#             if resp.status != 200:
#                 text = await resp.text()
#                 raise RuntimeError(f"SPARQL query failed ({resp.status}): {text}")

#             data = await resp.json(content_type=None)
#             results = data.get("results", {}).get("bindings", [])

#             if not results:
#                 return None

#             result = results[0]
#             birth_date = result.get("birthDate", {}).get("value")
#             death_date = result.get("deathDate", {}).get("value")
#             image = result.get("image", {}).get("value")

#             return {
#                 "birth_year": birth_date[:4] if birth_date else None,
#                 "death_year": death_date[:4] if death_date else None,
#                 "image_url": image
#             }

# async def fetch_relationships(page_title: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """
#     Fetch genealogical relationships for a given Wikipedia page title and depth.
#     Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
#     """
#     try:
#         qid = get_qid(page_title)
#         print(f"Fetched QID for '{page_title}': {qid}")
        
#         if not qid:
#             if websocket_manager:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "status",
#                     "data": {
#                         "message": f"No Wikipedia/Wikidata entry found for '{page_title}'. This person may not have sufficient notable information.",
#                         "progress": 100
#                     }
#                 }))
#             print(f"No QID found for '{page_title}', returning empty relationships")
#             return []
            
#         return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
#     except Exception as e:
#         error_msg = f"Error fetching relationships for '{page_title}': {str(e)}"
#         print(error_msg)
        
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": error_msg,
#                     "progress": 100
#                 }
#             }))
        
#         return []

# def get_qid(page_title: str) -> Optional[str]:
#     """Return the Wikidata Q-identifier for a Wikipedia page title, or None if not found."""
#     params = {
#         "action": "query",
#         "titles": page_title,
#         "prop": "pageprops",
#         "ppprop": "wikibase_item",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     try:
#         response = requests.get(WIKIPEDIA_API, params=params, headers=headers)

#         print(f"Status code: {response.status_code}")
#         if response.status_code != 200:
#             print(f"Failed to fetch data for {page_title}: {response.status_code}")
#             return None

#         data = response.json()
#         print(f"Wikipedia API response for '{page_title}': {data}")

#         pages = data.get("query", {}).get("pages", {})
#         for page in pages.values():
#             if "missing" in page:
#                 print(f"Page '{page_title}' does not exist on Wikipedia")
#                 return None
                
#             qid = page.get("pageprops", {}).get("wikibase_item")
#             if qid:
#                 return qid

#         print(f"Q-id not found for page: {page_title}")
#         return None

#     except Exception as e:
#         print(f"Error fetching QID for {page_title}: {e}")
#         return None

# WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# def fetch_entity(qid: str) -> dict:
#     """Return the full JSON entity document for a given Wikidata QID."""
#     params = {
#         "action": "wbgetentities",
#         "ids": qid,
#         "format": "json"
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         raise RuntimeError(f"Failed to fetch entity {qid}: {response.status_code}")

#     data = response.json()
#     entities = data.get("entities", {})
#     if qid not in entities:
#         raise ValueError(f"Entity {qid} not found in response")

#     return entities[qid]

# def get_labels(qids: set) -> Dict[str, str]:
#     """Batch-fetch English labels for a set of Q-ids (returns dict)."""
#     if not qids:
#         return {}

#     params = {
#         "action": "wbgetentities",
#         "ids": "|".join(qids),
#         "props": "labels",
#         "languages": "en",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         print(f"Failed to fetch labels: {response.status_code}")
#         print(f"Response text: {response.text}")
#         return {}

#     data = response.json()
    
#     if "error" in data:
#         print(f"Wikidata API error: {data['error']}")
#         return {}
        
#     entities = data.get("entities", {})

#     labels = {}
#     for qid, entity in entities.items():
#         if entity.get("missing"):
#             print(f"Entity {qid} is missing from Wikidata")
#             continue
            
#         label_info = entity.get("labels", {}).get("en")
#         if label_info and "value" in label_info:
#             labels[qid] = label_info["value"]
#         else:
#             print(f"No English label found for {qid}")

#     return labels

# def get_parents(qid: str) -> List[str]:
#     """Return a list of parent QIDs for a given QID."""
#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})
#     parents = []
#     for snak in claims.get("P22", []):  # Father
#         parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
#     for snak in claims.get("P25", []):  # Mother
#         parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
#     return parents

# def safe_extract_qid(snak: dict) -> Optional[str]:
#     """Safely extract QID from a snak, return None if unavailable."""
#     try:
#         if snak.get("mainsnak", {}).get("snaktype") != "value":
#             return None
#         return snak["mainsnak"]["datavalue"]["value"]["id"]
#     except Exception:
#         return None

# async def collect_relationships(qid: str, depth: int, direction: str, relationships: List[Dict[str, str]], visited: set, all_qids: set, websocket_manager: Optional[WebSocketManager] = None, sent_entities: Optional[set] = None):
#     """
#     Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
#     direction: 'up' (ancestors) or 'down' (descendants)
#     """
#     if depth == 0 or qid in visited:
#         return
#     visited.add(qid)
    
#     if sent_entities is None:
#         sent_entities = set()

#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})

#     if direction == "up":  # Ancestors via P22 (father), P25 (mother), and adoptive parents
#         # BIOLOGICAL PARENTS
#         for snak in claims.get("P22", []):  # Father relationships
#             father_qid = safe_extract_qid(snak)
#             if not father_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "child of", "entity2": father_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, father_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, father_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "child of",
#                     "entity2": labels.get(father_qid, father_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 if father_qid not in sent_entities:
#                     father_details = await getPersonalDetailsByQid(father_qid)
#                     if father_details:
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "personal_details",
#                             "data": {
#                                 "entity": labels.get(father_qid, father_qid),
#                                 "qid": father_qid,
#                                 **father_details
#                             }
#                         }))
#                         sent_entities.add(father_qid)
            
#             await collect_relationships(father_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#         for snak in claims.get("P25", []):  # Mother relationships
#             mother_qid = safe_extract_qid(snak)
#             if not mother_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "child of", "entity2": mother_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, mother_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, mother_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "child of",
#                     "entity2": labels.get(mother_qid, mother_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 if mother_qid not in sent_entities:
#                     mother_details = await getPersonalDetailsByQid(mother_qid)
#                     if mother_details:
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "personal_details",
#                             "data": {
#                                 "entity": labels.get(mother_qid, mother_qid),
#                                 "qid": mother_qid,
#                                 **mother_details
#                             }
#                         }))
#                         sent_entities.add(mother_qid)
            
#             await collect_relationships(mother_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#         # ADOPTIVE PARENTS (NEW ADDITION)
#         for snak in claims.get("P1441", []):  # Adoptive father/mother
#             adoptive_parent_qid = safe_extract_qid(snak)
#             if not adoptive_parent_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "adopted by", "entity2": adoptive_parent_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, adoptive_parent_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, adoptive_parent_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "adopted by",
#                     "entity2": labels.get(adoptive_parent_qid, adoptive_parent_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 if adoptive_parent_qid not in sent_entities:
#                     adoptive_parent_details = await getPersonalDetailsByQid(adoptive_parent_qid)
#                     if adoptive_parent_details:
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "personal_details",
#                             "data": {
#                                 "entity": labels.get(adoptive_parent_qid, adoptive_parent_qid),
#                                 "qid": adoptive_parent_qid,
#                                 **adoptive_parent_details
#                             }
#                         }))
#                         sent_entities.add(adoptive_parent_qid)
            
#             await collect_relationships(adoptive_parent_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#     elif direction == "down":  # Descendants via P40 (child) and adoptive children
#         # First, collect all spouses and send spouse relationships
#         spouse_qids = set()
#         for spouse_snak in claims.get("P26", []):  # Spouse relationships
#             spouse_qid = safe_extract_qid(spouse_snak)
#             if not spouse_qid:
#                 continue
                
#             spouse_qids.add(spouse_qid)
#             relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, spouse_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, spouse_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "spouse of",
#                     "entity2": labels.get(spouse_qid, spouse_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 if spouse_qid not in sent_entities:
#                     spouse_details = await getPersonalDetailsByQid(spouse_qid)
#                     if spouse_details:
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "personal_details",
#                             "data": {
#                                 "entity": labels.get(spouse_qid, spouse_qid),
#                                 "qid": spouse_qid,
#                                 **spouse_details
#                             }
#                         }))
#                         sent_entities.add(spouse_qid)

#         # BIOLOGICAL CHILDREN
#         for snak in claims.get("P40", []):  # Child relationships
#             child_qid = safe_extract_qid(snak)
#             if not child_qid:
#                 continue
                
#             relationship = {"entity1": child_qid, "relationship": "child of", "entity2": qid}
#             relationships.append(relationship)
#             all_qids.update([child_qid, qid])

#             if websocket_manager:
#                 labels = get_labels({child_qid, qid})
#                 named_relationship = {
#                     "entity1": labels.get(child_qid, child_qid),
#                     "relationship": "child of",
#                     "entity2": labels.get(qid, qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 if child_qid not in sent_entities:
#                     child_details = await getPersonalDetailsByQid(child_qid)
#                     if child_details:
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "personal_details",
#                             "data": {
#                                 "entity": labels.get(child_qid, child_qid),
#                                 "qid": child_qid,
#                                 **child_details
#                             }
#                         }))
#                         sent_entities.add(child_qid)

#             # Check if any of the known spouses is also a parent of this child
#             child_entity = fetch_entity(child_qid)
#             child_claims = child_entity.get("claims", {})
#             child_parents = set()
#             for parent_prop in ["P22", "P25", "P1441"]:  # Father, mother, and adoptive parent
#                 for parent_snak in child_claims.get(parent_prop, []):
#                     parent_qid = safe_extract_qid(parent_snak)
#                     if parent_qid:
#                         child_parents.add(parent_qid)

#             # For each spouse that is also a parent of this child, send the child-spouse relationship
#             for spouse_qid in spouse_qids:
#                 if spouse_qid in child_parents:
#                     spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
#                     relationships.append(spouse_relationship)
#                     all_qids.add(spouse_qid)
                    
#                     if websocket_manager:
#                         labels = get_labels({child_qid, spouse_qid})
#                         named_relationship = {
#                             "entity1": labels.get(child_qid, child_qid),
#                             "relationship": "child of",
#                             "entity2": labels.get(spouse_qid, spouse_qid)
#                         }
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "relationship",
#                             "data": named_relationship
#                         }))

#             await collect_relationships(child_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#         # ADOPTIVE CHILDREN (NEW ADDITION)
#         # Find children who have this person as adoptive parent
#         entity_data = fetch_entity(qid)
#         # We need to find entities that point to this QID via P1441
#         # Since we can't easily reverse-query, we'll use a different approach
        
#         # Use SPARQL to find adoptive children
#         try:
#             async with aiohttp.ClientSession() as session:
#                 query = f"""
#                 SELECT ?child WHERE {{
#                     ?child wdt:P1441 wd:{qid} .
#                 }}
#                 """
                
#                 headers = {
#                     "Accept": "application/sparql-results+json",
#                     "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#                 }
                
#                 async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#                     if resp.status == 200:
#                         data = await resp.json(content_type=None)
#                         results = data.get("results", {}).get("bindings", [])
                        
#                         for result in results:
#                             child_uri = result.get("child", {}).get("value", "")
#                             if child_uri.startswith("http://www.wikidata.org/entity/"):
#                                 adoptive_child_qid = child_uri.split("/")[-1]
                                
#                                 relationship = {"entity1": adoptive_child_qid, "relationship": "adopted by", "entity2": qid}
#                                 relationships.append(relationship)
#                                 all_qids.update([adoptive_child_qid, qid])

#                                 if websocket_manager:
#                                     labels = get_labels({adoptive_child_qid, qid})
#                                     named_relationship = {
#                                         "entity1": labels.get(adoptive_child_qid, adoptive_child_qid),
#                                         "relationship": "adopted by",
#                                         "entity2": labels.get(qid, qid)
#                                     }
#                                     await websocket_manager.send_message(json.dumps({
#                                         "type": "relationship",
#                                         "data": named_relationship
#                                     }))
                                    
#                                     if adoptive_child_qid not in sent_entities:
#                                         adoptive_child_details = await getPersonalDetailsByQid(adoptive_child_qid)
#                                         if adoptive_child_details:
#                                             await websocket_manager.send_message(json.dumps({
#                                                 "type": "personal_details",
#                                                 "data": {
#                                                     "entity": labels.get(adoptive_child_qid, adoptive_child_qid),
#                                                     "qid": adoptive_child_qid,
#                                                     **adoptive_child_details
#                                                 }
#                                             }))
#                                             sent_entities.add(adoptive_child_qid)

#                                 await collect_relationships(adoptive_child_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)
#         except Exception as e:
#             print(f"Error fetching adoptive children for {qid}: {e}")

#     # Collect spouse relationships (P26) only for "up" direction to avoid duplication
#     if direction == "up":
#         for snak in claims.get("P26", []):
#             spouse_qid = safe_extract_qid(snak)
#             if not spouse_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, spouse_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, spouse_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "spouse of",
#                     "entity2": labels.get(spouse_qid, spouse_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 if spouse_qid not in sent_entities:
#                     spouse_details = await getPersonalDetailsByQid(spouse_qid)
#                     if spouse_details:
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "personal_details",
#                             "data": {
#                                 "entity": labels.get(spouse_qid, spouse_qid),
#                                 "qid": spouse_qid,
#                                 **spouse_details
#                             }
#                         }))
#                         sent_entities.add(spouse_qid)

# async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """Collect relationships in both directions and return formatted list."""
#     relationships = []
#     all_qids = set([qid])
#     sent_entities = set()
    
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Starting relationship collection (including adoptions)...", "progress": 0}
#         }))
        
#         initial_labels = get_labels({qid})
#         print(f"Fetched labels for '{qid}': {initial_labels}")
#         initial_entity_name = initial_labels.get(qid, qid)
#         print(f"Initial entity name for '{qid}': {initial_entity_name}")
#         initial_details = await getPersonalDetailsByQid(qid)
#         print(f"Initial personal details for '{qid}': {initial_details}")
#         if initial_details:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "personal_details",
#                 "data": {
#                     "entity": initial_entity_name,
#                     "qid": qid,
#                     **initial_details
#                 }
#             }))
#             sent_entities.add(qid)

#     # Collect ancestors (upward) - includes biological parents, adoptive parents, and spouses
#     await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
#         }))

#     # Collect descendants (downward) - includes biological children, adoptive children, and spouses
#     await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Collection complete! (Including adoption relationships)", "progress": 100}
#         }))

#     # Fetch labels for all entities
#     labels = get_labels(all_qids)

#     # Replace QIDs with names in relationships
#     named_relationships = []
#     for rel in relationships:
#         entity1_name = labels.get(rel["entity1"], rel["entity1"])
#         entity2_name = labels.get(rel["entity2"], rel["entity2"])
#         named_relationships.append({
#             "entity1": entity1_name,
#             "relationship": rel["relationship"],
#             "entity2": entity2_name
#         })

#     return named_relationships

# async def check_wikipedia_tree(page_title: str) -> bool:
#     """Check if Wikipedia page contains family tree templates."""
#     try:
#         params = {
#             "action": "parse",
#             "page": page_title,
#             "prop": "wikitext",
#             "format": "json",
#         }
#         response = requests.get(WIKIPEDIA_API, params=params).json()
#         if "parse" in response and "wikitext" in response["parse"]:
#             text = response["parse"]["wikitext"]["*"]
#             needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
#             return any(n.lower() in text.lower() for n in needles)
#     except:
#         pass
#     return False
# #fifth code
# from typing import List, Dict, Optional
# import requests
# import asyncio
# import aiohttp
# import json
# from app.core.websocket_manager import WebSocketManager

# WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
# WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
# SPARQL_API='https://query.wikidata.org/sparql'

# async def fetch_relationships_by_qid(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None, entity_name: Optional[str] = None) -> List[Dict[str, str]]:
#     """
#     Fetch genealogical relationships using QID directly (no name lookup needed).
#     This is more reliable and faster than name-based lookup.
#     """
#     try:
#         # Validate QID format
#         if not qid or not qid.startswith('Q') or not qid[1:].isdigit():
#             error_msg = f"Invalid QID format: {qid}"
#             print(error_msg)
            
#             if websocket_manager:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "status",
#                     "data": {
#                         "message": error_msg,
#                         "progress": 100
#                     }
#                 }))
#             return []
        
#         # Send initial status
#         display_name = entity_name or qid
#         print(f"Starting QID-based expansion for '{qid}' (entity: {display_name})")
        
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": f"Expanding family tree for {display_name} using QID {qid}...",
#                     "progress": 0
#                 }
#             }))
        
#         # Use existing function with QID directly - no name lookup needed
#         return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
#     except Exception as e:
#         error_msg = f"Error fetching relationships for QID '{qid}': {str(e)}"
#         print(error_msg)
        
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": error_msg,
#                     "progress": 100
#                 }
#             }))
        
#         return []
# async def getPersonalDetails(page_title:str):
#     qid = get_qid(page_title)
#     if not qid:
#         return None
#     return await getPersonalDetailsByQid(qid)

# async def getPersonalDetailsByQid(qid: str):
#     """Get personal details directly using Wikidata QID."""
#     query = f"""
#     SELECT ?birthDate ?deathDate ?image WHERE {{
#       wd:{qid} wdt:P569 ?birthDate.
#       OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate. }}
#       OPTIONAL {{ wd:{qid} wdt:P18 ?image. }}
#     }}
#     """

#     headers = {
#         "Accept": "application/sparql-results+json",
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#             if resp.status != 200:
#                 text = await resp.text()
#                 raise RuntimeError(f"SPARQL query failed ({resp.status}): {text}")

#             data = await resp.json(content_type=None)
#             results = data.get("results", {}).get("bindings", [])

#             if not results:
#                 return None

#             result = results[0]
#             birth_date = result.get("birthDate", {}).get("value")
#             death_date = result.get("deathDate", {}).get("value")
#             image = result.get("image", {}).get("value")

#             return {
#                 "birth_year": birth_date[:4] if birth_date else None,
#                 "death_year": death_date[:4] if death_date else None,
#                 "image_url": image
#             }

# async def fetch_relationships(page_title: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """
#     Fetch genealogical relationships for a given Wikipedia page title and depth.
#     Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
#     """
#     try:
#         qid = get_qid(page_title)
#         print(f"Fetched QID for '{page_title}': {qid}")
        
#         if not qid:
#             if websocket_manager:
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "status",
#                     "data": {
#                         "message": f"No Wikipedia/Wikidata entry found for '{page_title}'. This person may not have sufficient notable information.",
#                         "progress": 100
#                     }
#                 }))
#             print(f"No QID found for '{page_title}', returning empty relationships")
#             return []
            
#         return await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
#     except Exception as e:
#         error_msg = f"Error fetching relationships for '{page_title}': {str(e)}"
#         print(error_msg)
        
#         if websocket_manager:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "status",
#                 "data": {
#                     "message": error_msg,
#                     "progress": 100
#                 }
#             }))
        
#         return []

# def get_qid(page_title: str) -> Optional[str]:
#     """Return the Wikidata Q-identifier for a Wikipedia page title, or None if not found."""
#     params = {
#         "action": "query",
#         "titles": page_title,
#         "prop": "pageprops",
#         "ppprop": "wikibase_item",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     try:
#         response = requests.get(WIKIPEDIA_API, params=params, headers=headers)

#         print(f"Status code: {response.status_code}")
#         if response.status_code != 200:
#             print(f"Failed to fetch data for {page_title}: {response.status_code}")
#             return None

#         data = response.json()
#         print(f"Wikipedia API response for '{page_title}': {data}")

#         pages = data.get("query", {}).get("pages", {})
#         for page in pages.values():
#             if "missing" in page:
#                 print(f"Page '{page_title}' does not exist on Wikipedia")
#                 return None
                
#             qid = page.get("pageprops", {}).get("wikibase_item")
#             if qid:
#                 return qid

#         print(f"Q-id not found for page: {page_title}")
#         return None

#     except Exception as e:
#         print(f"Error fetching QID for {page_title}: {e}")
#         return None

# WIKIDATA_API = "https://www.wikidata.org/w/api.php"

# def fetch_entity(qid: str) -> dict:
#     """Return the full JSON entity document for a given Wikidata QID."""
#     params = {
#         "action": "wbgetentities",
#         "ids": qid,
#         "format": "json"
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         raise RuntimeError(f"Failed to fetch entity {qid}: {response.status_code}")

#     data = response.json()
#     entities = data.get("entities", {})
#     if qid not in entities:
#         raise ValueError(f"Entity {qid} not found in response")

#     return entities[qid]

# def get_labels(qids: set) -> Dict[str, str]:
#     """Batch-fetch English labels for a set of Q-ids (returns dict)."""
#     if not qids:
#         return {}

#     params = {
#         "action": "wbgetentities",
#         "ids": "|".join(qids),
#         "props": "labels",
#         "languages": "en",
#         "format": "json",
#     }

#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }

#     response = requests.get(WIKIDATA_API, params=params, headers=headers)
#     if response.status_code != 200:
#         print(f"Failed to fetch labels: {response.status_code}")
#         print(f"Response text: {response.text}")
#         return {}

#     data = response.json()
    
#     if "error" in data:
#         print(f"Wikidata API error: {data['error']}")
#         return {}
        
#     entities = data.get("entities", {})

#     labels = {}
#     for qid, entity in entities.items():
#         if entity.get("missing"):
#             print(f"Entity {qid} is missing from Wikidata")
#             continue
            
#         label_info = entity.get("labels", {}).get("en")
#         if label_info and "value" in label_info:
#             labels[qid] = label_info["value"]
#         else:
#             print(f"No English label found for {qid}")

#     return labels

# def get_parents(qid: str) -> List[str]:
#     """Return a list of parent QIDs for a given QID."""
#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})
#     parents = []
#     for snak in claims.get("P22", []):  # Father
#         parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
#     for snak in claims.get("P25", []):  # Mother
#         parents.append(snak["mainsnak"]["datavalue"]["value"]["id"])
#     return parents

# def safe_extract_qid(snak: dict) -> Optional[str]:
#     """Safely extract QID from a snak, return None if unavailable."""
#     try:
#         if snak.get("mainsnak", {}).get("snaktype") != "value":
#             return None
#         return snak["mainsnak"]["datavalue"]["value"]["id"]
#     except Exception:
#         return None

# async def collect_relationships(qid: str, depth: int, direction: str, relationships: List[Dict[str, str]], visited: set, all_qids: set, websocket_manager: Optional[WebSocketManager] = None, sent_entities: Optional[set] = None):
#     """
#     Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
#     direction: 'up' (ancestors) or 'down' (descendants)
#     """
#     if depth == 0 or qid in visited:
#         return
#     visited.add(qid)
    
#     if sent_entities is None:
#         sent_entities = set()

#     entity = fetch_entity(qid)
#     claims = entity.get("claims", {})

#     if direction == "up":  # Ancestors via P22 (father), P25 (mother), and adoptive parents
#         # BIOLOGICAL PARENTS - FATHER
#         for snak in claims.get("P22", []):
#             father_qid = safe_extract_qid(snak)
#             if not father_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "child of", "entity2": father_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, father_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, father_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "child of",
#                     "entity2": labels.get(father_qid, father_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 # CRITICAL FIX: Always send personal details, even if empty
#                 if father_qid not in sent_entities:
#                     father_details = await getPersonalDetailsByQid(father_qid)
#                     await websocket_manager.send_message(json.dumps({
#                         "type": "personal_details",
#                         "data": {
#                             "entity": labels.get(father_qid, father_qid),
#                             "qid": father_qid,
#                             "birth_year": father_details.get("birth_year") if father_details else None,
#                             "death_year": father_details.get("death_year") if father_details else None,
#                             "image_url": father_details.get("image_url") if father_details else None
#                         }
#                     }))
#                     sent_entities.add(father_qid)
            
#             await collect_relationships(father_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#         # BIOLOGICAL PARENTS - MOTHER
#         for snak in claims.get("P25", []):
#             mother_qid = safe_extract_qid(snak)
#             if not mother_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "child of", "entity2": mother_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, mother_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, mother_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "child of",
#                     "entity2": labels.get(mother_qid, mother_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 # CRITICAL FIX: Always send personal details, even if empty
#                 if mother_qid not in sent_entities:
#                     mother_details = await getPersonalDetailsByQid(mother_qid)
#                     await websocket_manager.send_message(json.dumps({
#                         "type": "personal_details",
#                         "data": {
#                             "entity": labels.get(mother_qid, mother_qid),
#                             "qid": mother_qid,
#                             "birth_year": mother_details.get("birth_year") if mother_details else None,
#                             "death_year": mother_details.get("death_year") if mother_details else None,
#                             "image_url": mother_details.get("image_url") if mother_details else None
#                         }
#                     }))
#                     sent_entities.add(mother_qid)
            
#             await collect_relationships(mother_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#         # ADOPTIVE PARENTS
#         for snak in claims.get("P1441", []):
#             adoptive_parent_qid = safe_extract_qid(snak)
#             if not adoptive_parent_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "adopted by", "entity2": adoptive_parent_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, adoptive_parent_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, adoptive_parent_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "adopted by",
#                     "entity2": labels.get(adoptive_parent_qid, adoptive_parent_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 # CRITICAL FIX: Always send personal details, even if empty
#                 if adoptive_parent_qid not in sent_entities:
#                     adoptive_parent_details = await getPersonalDetailsByQid(adoptive_parent_qid)
#                     await websocket_manager.send_message(json.dumps({
#                         "type": "personal_details",
#                         "data": {
#                             "entity": labels.get(adoptive_parent_qid, adoptive_parent_qid),
#                             "qid": adoptive_parent_qid,
#                             "birth_year": adoptive_parent_details.get("birth_year") if adoptive_parent_details else None,
#                             "death_year": adoptive_parent_details.get("death_year") if adoptive_parent_details else None,
#                             "image_url": adoptive_parent_details.get("image_url") if adoptive_parent_details else None
#                         }
#                     }))
#                     sent_entities.add(adoptive_parent_qid)
            
#             await collect_relationships(adoptive_parent_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#     elif direction == "down":  # Descendants via P40 (child) and adoptive children
#         # SPOUSES
#         spouse_qids = set()
#         for spouse_snak in claims.get("P26", []):
#             spouse_qid = safe_extract_qid(spouse_snak)
#             if not spouse_qid:
#                 continue
                
#             spouse_qids.add(spouse_qid)
#             relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, spouse_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, spouse_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "spouse of",
#                     "entity2": labels.get(spouse_qid, spouse_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 # CRITICAL FIX: Always send personal details, even if empty
#                 if spouse_qid not in sent_entities:
#                     spouse_details = await getPersonalDetailsByQid(spouse_qid)
#                     await websocket_manager.send_message(json.dumps({
#                         "type": "personal_details",
#                         "data": {
#                             "entity": labels.get(spouse_qid, spouse_qid),
#                             "qid": spouse_qid,
#                             "birth_year": spouse_details.get("birth_year") if spouse_details else None,
#                             "death_year": spouse_details.get("death_year") if spouse_details else None,
#                             "image_url": spouse_details.get("image_url") if spouse_details else None
#                         }
#                     }))
#                     sent_entities.add(spouse_qid)

#         # BIOLOGICAL CHILDREN
#         for snak in claims.get("P40", []):
#             child_qid = safe_extract_qid(snak)
#             if not child_qid:
#                 continue
                
#             relationship = {"entity1": child_qid, "relationship": "child of", "entity2": qid}
#             relationships.append(relationship)
#             all_qids.update([child_qid, qid])

#             if websocket_manager:
#                 labels = get_labels({child_qid, qid})
#                 named_relationship = {
#                     "entity1": labels.get(child_qid, child_qid),
#                     "relationship": "child of",
#                     "entity2": labels.get(qid, qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 # CRITICAL FIX: Always send personal details, even if empty
#                 if child_qid not in sent_entities:
#                     child_details = await getPersonalDetailsByQid(child_qid)
#                     await websocket_manager.send_message(json.dumps({
#                         "type": "personal_details",
#                         "data": {
#                             "entity": labels.get(child_qid, child_qid),
#                             "qid": child_qid,
#                             "birth_year": child_details.get("birth_year") if child_details else None,
#                             "death_year": child_details.get("death_year") if child_details else None,
#                             "image_url": child_details.get("image_url") if child_details else None
#                         }
#                     }))
#                     sent_entities.add(child_qid)

#             # Check if any of the known spouses is also a parent of this child
#             child_entity = fetch_entity(child_qid)
#             child_claims = child_entity.get("claims", {})
#             child_parents = set()
#             for parent_prop in ["P22", "P25", "P1441"]:
#                 for parent_snak in child_claims.get(parent_prop, []):
#                     parent_qid = safe_extract_qid(parent_snak)
#                     if parent_qid:
#                         child_parents.add(parent_qid)

#             # For each spouse that is also a parent of this child, send the child-spouse relationship
#             for spouse_qid in spouse_qids:
#                 if spouse_qid in child_parents:
#                     spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
#                     relationships.append(spouse_relationship)
#                     all_qids.add(spouse_qid)
                    
#                     if websocket_manager:
#                         labels = get_labels({child_qid, spouse_qid})
#                         named_relationship = {
#                             "entity1": labels.get(child_qid, child_qid),
#                             "relationship": "child of",
#                             "entity2": labels.get(spouse_qid, spouse_qid)
#                         }
#                         await websocket_manager.send_message(json.dumps({
#                             "type": "relationship",
#                             "data": named_relationship
#                         }))

#             await collect_relationships(child_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

#         # ADOPTIVE CHILDREN
#         try:
#             async with aiohttp.ClientSession() as session:
#                 query = f"""
#                 SELECT ?child WHERE {{
#                     ?child wdt:P1441 wd:{qid} .
#                 }}
#                 """
                
#                 headers = {
#                     "Accept": "application/sparql-results+json",
#                     "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#                 }
                
#                 async with session.get(SPARQL_API, params={"query": query}, headers=headers) as resp:
#                     if resp.status == 200:
#                         data = await resp.json(content_type=None)
#                         results = data.get("results", {}).get("bindings", [])
                        
#                         for result in results:
#                             child_uri = result.get("child", {}).get("value", "")
#                             if child_uri.startswith("http://www.wikidata.org/entity/"):
#                                 adoptive_child_qid = child_uri.split("/")[-1]
                                
#                                 relationship = {"entity1": adoptive_child_qid, "relationship": "adopted by", "entity2": qid}
#                                 relationships.append(relationship)
#                                 all_qids.update([adoptive_child_qid, qid])

#                                 if websocket_manager:
#                                     labels = get_labels({adoptive_child_qid, qid})
#                                     named_relationship = {
#                                         "entity1": labels.get(adoptive_child_qid, adoptive_child_qid),
#                                         "relationship": "adopted by",
#                                         "entity2": labels.get(qid, qid)
#                                     }
#                                     await websocket_manager.send_message(json.dumps({
#                                         "type": "relationship",
#                                         "data": named_relationship
#                                     }))
                                    
#                                     # CRITICAL FIX: Always send personal details, even if empty
#                                     if adoptive_child_qid not in sent_entities:
#                                         adoptive_child_details = await getPersonalDetailsByQid(adoptive_child_qid)
#                                         await websocket_manager.send_message(json.dumps({
#                                             "type": "personal_details",
#                                             "data": {
#                                                 "entity": labels.get(adoptive_child_qid, adoptive_child_qid),
#                                                 "qid": adoptive_child_qid,
#                                                 "birth_year": adoptive_child_details.get("birth_year") if adoptive_child_details else None,
#                                                 "death_year": adoptive_child_details.get("death_year") if adoptive_child_details else None,
#                                                 "image_url": adoptive_child_details.get("image_url") if adoptive_child_details else None
#                                             }
#                                         }))
#                                         sent_entities.add(adoptive_child_qid)

#                                 await collect_relationships(adoptive_child_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)
#         except Exception as e:
#             print(f"Error fetching adoptive children for {qid}: {e}")

#     # Collect spouse relationships (P26) only for "up" direction to avoid duplication
#     if direction == "up":
#         for snak in claims.get("P26", []):
#             spouse_qid = safe_extract_qid(snak)
#             if not spouse_qid:
#                 continue
                
#             relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
#             relationships.append(relationship)
#             all_qids.update([qid, spouse_qid])
            
#             if websocket_manager:
#                 labels = get_labels({qid, spouse_qid})
#                 named_relationship = {
#                     "entity1": labels.get(qid, qid),
#                     "relationship": "spouse of",
#                     "entity2": labels.get(spouse_qid, spouse_qid)
#                 }
#                 await websocket_manager.send_message(json.dumps({
#                     "type": "relationship",
#                     "data": named_relationship
#                 }))
                
#                 # CRITICAL FIX: Always send personal details, even if empty
#                 if spouse_qid not in sent_entities:
#                     spouse_details = await getPersonalDetailsByQid(spouse_qid)
#                     await websocket_manager.send_message(json.dumps({
#                         "type": "personal_details",
#                         "data": {
#                             "entity": labels.get(spouse_qid, spouse_qid),
#                             "qid": spouse_qid,
#                             "birth_year": spouse_details.get("birth_year") if spouse_details else None,
#                             "death_year": spouse_details.get("death_year") if spouse_details else None,
#                             "image_url": spouse_details.get("image_url") if spouse_details else None
#                         }
#                     }))
#                     sent_entities.add(spouse_qid)

# async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
#     """Collect relationships in both directions and return formatted list."""
#     relationships = []
#     all_qids = set([qid])
#     sent_entities = set()
    
#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Starting relationship collection (including adoptions)...", "progress": 0}
#         }))
        
#         initial_labels = get_labels({qid})
#         print(f"Fetched labels for '{qid}': {initial_labels}")
#         initial_entity_name = initial_labels.get(qid, qid)
#         print(f"Initial entity name for '{qid}': {initial_entity_name}")
#         initial_details = await getPersonalDetailsByQid(qid)
#         print(f"Initial personal details for '{qid}': {initial_details}")
#         if initial_details:
#             await websocket_manager.send_message(json.dumps({
#                 "type": "personal_details",
#                 "data": {
#                     "entity": initial_entity_name,
#                     "qid": qid,
#                     **initial_details
#                 }
#             }))
#             sent_entities.add(qid)

#     # Collect ancestors (upward) - includes biological parents, adoptive parents, and spouses
#     await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
#         }))

#     # Collect descendants (downward) - includes biological children, adoptive children, and spouses
#     await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

#     if websocket_manager:
#         await websocket_manager.send_message(json.dumps({
#             "type": "status",
#             "data": {"message": "Collection complete! (Including adoption relationships)", "progress": 100}
#         }))

#     # Fetch labels for all entities
#     labels = get_labels(all_qids)

#     # Replace QIDs with names in relationships
#     named_relationships = []
#     for rel in relationships:
#         entity1_name = labels.get(rel["entity1"], rel["entity1"])
#         entity2_name = labels.get(rel["entity2"], rel["entity2"])
#         named_relationships.append({
#             "entity1": entity1_name,
#             "relationship": rel["relationship"],
#             "entity2": entity2_name
#         })

#     return named_relationships

# async def check_wikipedia_tree(page_title: str) -> bool:
#     """Check if Wikipedia page contains family tree templates."""
#     try:
#         params = {
#             "action": "parse",
#             "page": page_title,
#             "prop": "wikitext",
#             "format": "json",
#         }
#         response = requests.get(WIKIPEDIA_API, params=params).json()
#         if "parse" in response and "wikitext" in response["parse"]:
#             text = response["parse"]["wikitext"]["*"]
#             needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
#             return any(n.lower() in text.lower() for n in needles)
#     except:
#         pass
#     return False

from typing import List, Dict, Optional
import requests
import asyncio
import aiohttp
import json
from app.core.websocket_manager import WebSocketManager
from app.services.llm_relationship_extractor import LLMRelationshipExtractor


WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/wiki/Special:EntityData/{}.json"
SPARQL_API='https://query.wikidata.org/sparql'

# Add a new parameter to control LLM usage
async def fetch_relationships_by_qid(
    qid: str, 
    depth: int, 
    websocket_manager: Optional[WebSocketManager] = None, 
    entity_name: Optional[str] = None,
    use_llm_enrichment: bool = False  # NEW PARAMETER
) -> List[Dict[str, str]]:
    """
    Fetch genealogical relationships using QID directly.
    
    Args:
        qid: Wikidata QID
        depth: How many generations to traverse
        websocket_manager: WebSocket for real-time updates
        entity_name: Display name for the entity
        use_llm_enrichment: If True, supplement Wikidata with LLM extraction
    """
    try:
        # Validate QID format
        if not qid or not qid.startswith('Q') or not qid[1:].isdigit():
            error_msg = f"Invalid QID format: {qid}"
            print(error_msg)
            
            if websocket_manager:
                await websocket_manager.send_message(json.dumps({
                    "type": "status",
                    "data": {
                        "message": error_msg,
                        "progress": 100
                    }
                }))
            return []
        
        display_name = entity_name or qid
        print(f"Starting expansion for '{qid}' (entity: {display_name}), use_llm={use_llm_enrichment}")
        
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "status",
                "data": {
                    "message": f"Fetching family tree for {display_name} from Wikidata...",
                    "progress": 10
                }
            }))
        
        # Phase 1: ALWAYS get Wikidata relationships
        wikidata_relationships = await collect_bidirectional_relationships(qid, depth, websocket_manager)
        
        # Phase 2: ONLY use LLM if explicitly requested (expand node case)
        if use_llm_enrichment:
            if websocket_manager:
                await websocket_manager.send_message(json.dumps({
                    "type": "status",
                    "data": {
                        "message": f"Wikidata complete ({len(wikidata_relationships)} relationships). Now enriching with AI analysis of Wikipedia text...",
                        "progress": 50
                    }
                }))
            
            # Get Wikipedia page title from entity name
            # Get Wikipedia page title from entity name
            page_title = entity_name or get_label_from_qid(qid)

            if page_title:
                try:
                    # CRITICAL: Collect all existing entity names from Wikidata relationships
                    existing_entities = set()
                    for rel in wikidata_relationships:
                        existing_entities.add(rel['entity1'])
                        existing_entities.add(rel['entity2'])
        
                    print(f"📋 Passing {len(existing_entities)} existing entities to LLM for deduplication")
        
                    extractor = LLMRelationshipExtractor()
                    llm_rels = await extractor.extract_relationships_for_person(
                        page_title, 
                        qid,
                        existing_entities=existing_entities  # Pass existing entities
                    )
                    
                    # Convert LLM format to standard format
                    # Convert LLM format to standard format
                    llm_relationships = []

                    # Handle child_of relationships - allow BOTH directions now
                    for child, parent in llm_rels.get('child_of', []):
                        # Add if subject is the child
                        if child == page_title:
                            llm_relationships.append({
                                "entity1": child,
                                "relationship": "child of",
                                "entity2": parent
                            })
                        # ALSO add if child exists and parent is new (connecting children to new spouse)
                        else:
                            llm_relationships.append({
                                "entity1": child,
                                "relationship": "child of",
                                "entity2": parent
                            })

                    for spouse in llm_rels.get('spouse_of', []):
                        if spouse[0] == page_title:
                            llm_relationships.append({
                                "entity1": spouse[0],
                                "relationship": "spouse of",
                                "entity2": spouse[1]
                            })

                    for adopter in llm_rels.get('adopted_by', []):
                        if adopter[0] == page_title:
                            llm_relationships.append({
                                "entity1": adopter[0],
                                "relationship": "adopted by",
                                "entity2": adopter[1]
                            })
                    
                    # Deduplicate: only add LLM relationships not in Wikidata
                    # Deduplicate: only add LLM relationships not in Wikidata
                    existing_pairs = set()
                    for rel in wikidata_relationships:
                        # Create normalized key for comparison (consider both directions for child_of)
                        pair = f"{rel['entity1'].lower()}-{rel['relationship']}-{rel['entity2'].lower()}"
                        existing_pairs.add(pair)

                    new_llm_count = 0
                    for llm_rel in llm_relationships:
                        pair = f"{llm_rel['entity1'].lower()}-{llm_rel['relationship']}-{llm_rel['entity2'].lower()}"
    
                        # SPECIAL: For child_of, don't skip if we're adding a new parent to existing child
                        if pair not in existing_pairs:
                            wikidata_relationships.append(llm_rel)
                            new_llm_count += 1
        
                            # Send LLM-extracted relationships via websocket
                            if websocket_manager:
                                await websocket_manager.send_message(json.dumps({
                                    "type": "relationship",
                                        "data": {
                                        **llm_rel,
                                        "source": "llm"
                                    }
                                }))
            
                                # Send personal details for NEW entities only (not for existing children)
                                for entity in [llm_rel['entity1'], llm_rel['entity2']]:
                                    if entity != page_title:
                                        # Check if entity is truly new (not in existing_entities)
                                        entity_is_new = entity not in existing_entities
                    
                                        if entity_is_new:
                                            await websocket_manager.send_message(json.dumps({
                                                "type": "personal_details",
                                                    "data": {
                                                    "entity": entity,
                                                    "qid": "temp",
                                                    "birth_year": None,
                                                    "death_year": None,
                                                    "image_url": None
                                                }
                                            }))
                    
                    if websocket_manager:
                        await websocket_manager.send_message(json.dumps({
                            "type": "status",
                            "data": {
                                "message": f"✓ Complete! {len(wikidata_relationships)} total relationships ({new_llm_count} enriched from Wikipedia text)",
                                "progress": 100
                            }
                        }))
                    
                    print(f"LLM enrichment added {new_llm_count} new relationships")
                    
                except Exception as llm_error:
                    print(f"LLM enrichment failed: {llm_error}")
                    if websocket_manager:
                        await websocket_manager.send_message(json.dumps({
                            "type": "status",
                            "data": {
                                "message": f"Complete! Found {len(wikidata_relationships)} relationships (LLM enrichment unavailable)",
                                "progress": 100
                            }
                        }))
        else:
            # Wikidata-only mode (initial tree)
            if websocket_manager:
                await websocket_manager.send_message(json.dumps({
                    "type": "status",
                    "data": {
                        "message": f"Complete! Found {len(wikidata_relationships)} relationships from Wikidata",
                        "progress": 100
                    }
                }))
        
        return wikidata_relationships
        
    except Exception as e:
        error_msg = f"Error fetching relationships for QID '{qid}': {str(e)}"
        print(error_msg)
        
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "status",
                "data": {
                    "message": error_msg,
                    "progress": 100
                }
            }))
        
        return []

def get_label_from_qid(qid: str) -> Optional[str]:
    """Get the English label for a QID."""
    labels = get_labels({qid})
    return labels.get(qid)

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
    Fetch genealogical relationships for initial tree creation.
    Uses ONLY Wikidata (no LLM enrichment).
    """
    try:
        qid = get_qid(page_title)
        print(f"Fetched QID for '{page_title}': {qid}")
        
        if not qid:
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
        
        # Call with use_llm_enrichment=False for initial tree
        return await fetch_relationships_by_qid(
            qid, 
            depth, 
            websocket_manager, 
            page_title,
            use_llm_enrichment=False  # NO LLM for initial tree
        )
        
    except Exception as e:
        error_msg = f"Error fetching relationships for '{page_title}': {str(e)}"
        print(error_msg)
        
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
        print(f"Wikipedia API response for '{page_title}': {data}")

        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
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
        "ids": "|".join(qids),
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
        return {}

    data = response.json()
    
    if "error" in data:
        print(f"Wikidata API error: {data['error']}")
        return {}
        
    entities = data.get("entities", {})

    labels = {}
    for qid, entity in entities.items():
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

def safe_extract_qid(snak: dict) -> Optional[str]:
    """Safely extract QID from a snak, return None if unavailable."""
    try:
        if snak.get("mainsnak", {}).get("snaktype") != "value":
            return None
        return snak["mainsnak"]["datavalue"]["value"]["id"]
    except Exception:
        return None

async def collect_relationships(qid: str, depth: int, direction: str, relationships: List[Dict[str, str]], visited: set, all_qids: set, websocket_manager: Optional[WebSocketManager] = None, sent_entities: Optional[set] = None):
    """
    Recursively collect family relationships in {"entity1": str, "relationship": str, "entity2": str} format.
    direction: 'up' (ancestors) or 'down' (descendants)
    """
    if depth == 0 or qid in visited:
        return
    visited.add(qid)
    
    if sent_entities is None:
        sent_entities = set()

    entity = fetch_entity(qid)
    claims = entity.get("claims", {})

    if direction == "up":  # Ancestors via P22 (father), P25 (mother)
        # BIOLOGICAL PARENTS - FATHER
        for snak in claims.get("P22", []):
            father_qid = safe_extract_qid(snak)
            if not father_qid:
                continue
                
            relationship = {"entity1": qid, "relationship": "child of", "entity2": father_qid}
            relationships.append(relationship)
            all_qids.update([qid, father_qid])
            
            if websocket_manager:
                labels = get_labels({qid, father_qid})
                named_relationship = {
                    "entity1": labels.get(qid, qid),
                    "relationship": "child of",
                    "entity2": labels.get(father_qid, father_qid)
                }
                await websocket_manager.send_message(json.dumps({
                    "type": "relationship",
                    "data": named_relationship
                }))
                
                # CRITICAL FIX: Always send personal details, even if empty
                if father_qid not in sent_entities:
                    father_details = await getPersonalDetailsByQid(father_qid)
                    await websocket_manager.send_message(json.dumps({
                        "type": "personal_details",
                        "data": {
                            "entity": labels.get(father_qid, father_qid),
                            "qid": father_qid,
                            "birth_year": father_details.get("birth_year") if father_details else None,
                            "death_year": father_details.get("death_year") if father_details else None,
                            "image_url": father_details.get("image_url") if father_details else None
                        }
                    }))
                    sent_entities.add(father_qid)
            
            await collect_relationships(father_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

        # BIOLOGICAL PARENTS - MOTHER
        for snak in claims.get("P25", []):
            mother_qid = safe_extract_qid(snak)
            if not mother_qid:
                continue
                
            relationship = {"entity1": qid, "relationship": "child of", "entity2": mother_qid}
            relationships.append(relationship)
            all_qids.update([qid, mother_qid])
            
            if websocket_manager:
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
                
                # CRITICAL FIX: Always send personal details, even if empty
                if mother_qid not in sent_entities:
                    mother_details = await getPersonalDetailsByQid(mother_qid)
                    await websocket_manager.send_message(json.dumps({
                        "type": "personal_details",
                        "data": {
                            "entity": labels.get(mother_qid, mother_qid),
                            "qid": mother_qid,
                            "birth_year": mother_details.get("birth_year") if mother_details else None,
                            "death_year": mother_details.get("death_year") if mother_details else None,
                            "image_url": mother_details.get("image_url") if mother_details else None
                        }
                    }))
                    sent_entities.add(mother_qid)
            
            await collect_relationships(mother_qid, depth - 1, direction, relationships, visited, all_qids, websocket_manager, sent_entities)

    elif direction == "down":  # Descendants via P40 (child)
        # SPOUSES
        spouse_qids = set()
        for spouse_snak in claims.get("P26", []):
            spouse_qid = safe_extract_qid(spouse_snak)
            if not spouse_qid:
                continue
                
            spouse_qids.add(spouse_qid)
            relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
            relationships.append(relationship)
            all_qids.update([qid, spouse_qid])
            
            if websocket_manager:
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
                
                # CRITICAL FIX: Always send personal details, even if empty
                if spouse_qid not in sent_entities:
                    spouse_details = await getPersonalDetailsByQid(spouse_qid)
                    await websocket_manager.send_message(json.dumps({
                        "type": "personal_details",
                        "data": {
                            "entity": labels.get(spouse_qid, spouse_qid),
                            "qid": spouse_qid,
                            "birth_year": spouse_details.get("birth_year") if spouse_details else None,
                            "death_year": spouse_details.get("death_year") if spouse_details else None,
                            "image_url": spouse_details.get("image_url") if spouse_details else None
                        }
                    }))
                    sent_entities.add(spouse_qid)

        # BIOLOGICAL CHILDREN
        for snak in claims.get("P40", []):
            child_qid = safe_extract_qid(snak)
            if not child_qid:
                continue
                
            relationship = {"entity1": child_qid, "relationship": "child of", "entity2": qid}
            relationships.append(relationship)
            all_qids.update([child_qid, qid])

            if websocket_manager:
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
                
                # CRITICAL FIX: Always send personal details, even if empty
                if child_qid not in sent_entities:
                    child_details = await getPersonalDetailsByQid(child_qid)
                    await websocket_manager.send_message(json.dumps({
                        "type": "personal_details",
                        "data": {
                            "entity": labels.get(child_qid, child_qid),
                            "qid": child_qid,
                            "birth_year": child_details.get("birth_year") if child_details else None,
                            "death_year": child_details.get("death_year") if child_details else None,
                            "image_url": child_details.get("image_url") if child_details else None
                        }
                    }))
                    sent_entities.add(child_qid)

            # Check if any of the known spouses is also a parent of this child
            child_entity = fetch_entity(child_qid)
            child_claims = child_entity.get("claims", {})
            child_parents = set()
            for parent_prop in ["P22", "P25"]:
                for parent_snak in child_claims.get(parent_prop, []):
                    parent_qid = safe_extract_qid(parent_snak)
                    if parent_qid:
                        child_parents.add(parent_qid)

            # For each spouse that is also a parent of this child, send the child-spouse relationship
            for spouse_qid in spouse_qids:
                if spouse_qid in child_parents:
                    spouse_relationship = {"entity1": child_qid, "relationship": "child of", "entity2": spouse_qid}
                    relationships.append(spouse_relationship)
                    all_qids.add(spouse_qid)
                    
                    if websocket_manager:
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
    if direction == "up":
        for snak in claims.get("P26", []):
            spouse_qid = safe_extract_qid(snak)
            if not spouse_qid:
                continue
                
            relationship = {"entity1": qid, "relationship": "spouse of", "entity2": spouse_qid}
            relationships.append(relationship)
            all_qids.update([qid, spouse_qid])
            
            if websocket_manager:
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
                
                # CRITICAL FIX: Always send personal details, even if empty
                if spouse_qid not in sent_entities:
                    spouse_details = await getPersonalDetailsByQid(spouse_qid)
                    await websocket_manager.send_message(json.dumps({
                        "type": "personal_details",
                        "data": {
                            "entity": labels.get(spouse_qid, spouse_qid),
                            "qid": spouse_qid,
                            "birth_year": spouse_details.get("birth_year") if spouse_details else None,
                            "death_year": spouse_details.get("death_year") if spouse_details else None,
                            "image_url": spouse_details.get("image_url") if spouse_details else None
                        }
                    }))
                    sent_entities.add(spouse_qid)

async def collect_bidirectional_relationships(qid: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """Collect relationships in both directions and return formatted list."""
    relationships = []
    all_qids = set([qid])
    sent_entities = set()
    
    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Starting relationship collection...", "progress": 0}
        }))
        
        initial_labels = get_labels({qid})
        print(f"Fetched labels for '{qid}': {initial_labels}")
        initial_entity_name = initial_labels.get(qid, qid)
        print(f"Initial entity name for '{qid}': {initial_entity_name}")
        initial_details = await getPersonalDetailsByQid(qid)
        print(f"Initial personal details for '{qid}': {initial_details}")
        if initial_details:
            await websocket_manager.send_message(json.dumps({
                "type": "personal_details",
                "data": {
                    "entity": initial_entity_name,
                    "qid": qid,
                    **initial_details
                }
            }))
            sent_entities.add(qid)

    # Collect ancestors (upward) - includes biological parents and spouses
    await collect_relationships(qid, depth, "up", relationships, set(), all_qids, websocket_manager, sent_entities)

    if websocket_manager:
        await websocket_manager.send_message(json.dumps({
            "type": "status",
            "data": {"message": "Ancestors collected, now collecting descendants...", "progress": 50}
        }))

    # Collect descendants (downward) - includes biological children and spouses
    await collect_relationships(qid, depth, "down", relationships, set(), all_qids, websocket_manager, sent_entities)

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