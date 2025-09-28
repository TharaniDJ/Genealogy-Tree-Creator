"""Service functions for fetching language genealogical relationships.

The implementation adapts the exploration logic prototyped in `info.ipynb` into
an async, streaming form suitable for WebSocket incremental updates.

Strategy:
1. Resolve input language name -> Wikidata QID (using Wikipedia API lookups).
2. Recursively traverse parent (P279) and child (P527 + reverse P279) relations
   up to the requested depth while de‑duplicating and preventing runaway growth.
3. For every relationship discovered, immediately stream a JSON message over the
   provided WebSocket connection so the frontend can progressively render.
4. Perform light validation (ensuring candidate QIDs map to language / dialect /
   family classes) to reduce noise. (Kept minimal to avoid excess SPARQL load.)

NOTE: Network calls use `requests` (blocking). For production scalability you
may wish to migrate to `httpx.AsyncClient`. Given the relatively small request
volume per tree and FastAPI's default threadpool offload for sync I/O, this is
acceptable for now.
"""

from __future__ import annotations

import time
import asyncio
import requests
from typing import Dict, List, Optional, Set, Tuple

from app.core.websocket_manager import WebSocketManager
from app.core.config import settings

HEADERS = {"User-Agent": "LanguageFamilyTreeService/1.0 (https://dasun.codes)", "Accept": "application/json"}

WIKIPEDIA_API = settings.WIKIPEDIA_API
WIKIDATA_QUERY_API = settings.WIKIDATA_QUERY_API
SPARQL_ENDPOINT = settings.SPARQL_API

MAX_QIDS_PER_CALL = 50
MAX_RETRIES = 4
BACKOFF_BASE = 0.8
MAX_NODES = 1500

LABEL_CACHE: Dict[str, str] = {}
VALID_QIDS: Set[str] = set()
INVALID_QIDS: Set[str] = set()
CLASSIFICATION_CACHE: Dict[str, Optional[str]] = {}

# Accepted Wikidata type QIDs (instance/subclass) considered valid language entities
VALID_TYPE_QIDS: Dict[str, str] = {
	"language": "Q34770",
	
	"dialect": "Q33384",
	
	"language_family": "Q25295",
	
	"proto_language": "Q206577",
	"extinct_language": "Q38058796",
	"dead_language": "Q45762",
}


from SPARQLWrapper import SPARQLWrapper, JSON

async def fetch_language_info(qid: str, lang_code: str = "en"):
	"""
	Fetch important information about a language, language family, or dialect by its Wikidata QID.
	Uses Wikidata SPARQL to retrieve speakers, ISO code, and distribution map URL when available.

	Args:
		qid (str): Wikidata QID like 'Q12345'
		lang_code (str): Language code for labels/descriptions (default 'en')

	Returns:
		dict: Extracted information matching LanguageInfo model structure
	"""
	info: Dict[str, Optional[str]] = {
		"speakers": None,
		"iso_code": None,
		"distribution_map_url": None
	}
	sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

	try:
		# SPARQL query to get language information (without Wikipedia infobox fallback)
		sparql.setQuery(f"""
		SELECT ?itemLabel ?itemDescription ?speakersValue ?isoCode WHERE {{
		  VALUES ?item {{ wd:{qid} }}
		  OPTIONAL {{ ?item wdt:P1098 ?speakersValue. }}
		  OPTIONAL {{ ?item wdt:P219 ?isoCode. }}
		  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "{lang_code},en". }}
		}}
		""")
		sparql.setReturnFormat(JSON)
		results = sparql.query().convert()

		# Handle different return types from SPARQLWrapper
		if isinstance(results, dict):
			bindings = results.get("results", {}).get("bindings", [])
		else:
			bindings = []

		if bindings:
			b = bindings[0]
			info["speakers"] = b.get("speakersValue", {}).get("value")
			info["iso_code"] = b.get("isoCode", {}).get("value")
	except Exception:
		# Silently ignore SPARQL errors and return whatever info we have
		pass

	# Get distribution map image URL
	info["distribution_map_url"] = get_distribution_map_image(qid)

	return info

def _validate_qid(qid: str) -> Tuple[bool, Optional[str]]:
	"""Return (is_valid, classification_key) for a Wikidata QID.

	Caches results to avoid repeated SPARQL calls. Classification key is one
	of the keys in VALID_TYPE_QIDS or None if not matched.
	"""
	if not qid:
		return False, None
	if qid in VALID_QIDS:
		# We may or may not have stored classification separately
		return True, CLASSIFICATION_CACHE.get(qid)
	if qid in INVALID_QIDS:
		return False, None
	# Build VALUES clause of acceptable types
	values_clause = " ".join(f"wd:{t}" for t in VALID_TYPE_QIDS.values())
	query = f"""
	SELECT ?type WHERE {{
	  VALUES ?item {{ wd:{qid} }}
	  {{ ?item wdt:P31 ?type. }} UNION {{ ?item wdt:P279 ?type. }}
	  VALUES ?validType {{ {values_clause} }}
	  FILTER(?type IN (?validType))
	}}
	LIMIT 1
	"""
	data = _safe_get_json(SPARQL_ENDPOINT, params={"query": query, "format": "json"}) or {}
	bindings = data.get("results", {}).get("bindings", [])
	if not bindings:
		INVALID_QIDS.add(qid)
		CLASSIFICATION_CACHE[qid] = None
		return False, None
	type_uri = bindings[0]["type"]["value"]
	type_qid = type_uri.split("/")[-1]
	# Reverse lookup classification key
	for key, tqid in VALID_TYPE_QIDS.items():
		if tqid == type_qid:
			VALID_QIDS.add(qid)
			CLASSIFICATION_CACHE[qid] = key
			return True, key
	# Fallback (should not happen if VALUES clause matches)
	VALID_QIDS.add(qid)
	CLASSIFICATION_CACHE[qid] = None
	return True, None


def _validate_root_language(qid: str) -> Tuple[bool, List[str]]:
	"""Comprehensive validation for root language QID with detailed type information.
	
	Returns (is_valid, list_of_matching_types) where matching_types are ordered by priority.
	Priority order: language -> modern/ancient/dead/extinct -> dialect -> sign -> creole/pidgin -> family -> proto
	"""
	if not qid:
		return False, []
		
	# Comprehensive language type QIDs in priority order
	LANGUAGE_TYPE_HIERARCHY = [
		("language", "Q34770"),
		("modern_language", "Q1288568"),
		("ancient_language", "Q436240"), 
		("dead_language", "Q45762"),
		("extinct_language", "Q38058796"),
		("dialect", "Q33384"),
		("sign_language", "Q34228"),
		("creole_language", "Q33289"),
		("pidgin_language", "Q33831"),
		("language_family", "Q25295"),
		("proto_language", "Q206577"),
	]
	
	# Build VALUES clause for all language types
	values_clause = " ".join(f"wd:{qid_val}" for _, qid_val in LANGUAGE_TYPE_HIERARCHY)
	
	query = f"""
	SELECT ?type WHERE {{
	  VALUES ?item {{ wd:{qid} }}
	  {{ ?item wdt:P31 ?type. }} UNION {{ ?item wdt:P279 ?type. }}
	  VALUES ?validType {{ {values_clause} }}
	  FILTER(?type IN (?validType))
	}}
	"""
	
	data = _safe_get_json(SPARQL_ENDPOINT, params={"query": query, "format": "json"}) or {}
	bindings = data.get("results", {}).get("bindings", [])
	
	if not bindings:
		return False, []
	
	# Extract all matching type QIDs
	found_type_qids = set()
	for binding in bindings:
		type_uri = binding["type"]["value"]
		type_qid = type_uri.split("/")[-1]
		found_type_qids.add(type_qid)
	
	# Map back to type names in priority order
	matching_types = []
	for type_name, type_qid in LANGUAGE_TYPE_HIERARCHY:
		if type_qid in found_type_qids:
			matching_types.append(type_name)
	
	# Valid if we found at least one matching type
	is_valid = len(matching_types) > 0
	return is_valid, matching_types


def _safe_get_json(url: str, *, params: dict, headers: dict | None = None):
	merged = {**HEADERS, **(headers or {})}
	for attempt in range(1, MAX_RETRIES + 1):
		try:
			resp = requests.get(url, params=params, headers=merged, timeout=20)
			status = resp.status_code
			if status == 429:
				wait = BACKOFF_BASE * attempt * 2
				time.sleep(wait)
				continue
			if status >= 500:
				wait = BACKOFF_BASE * attempt
				time.sleep(wait)
				continue
			if status != 200:
				return None
			txt = resp.text.strip()
			if not txt:
				wait = BACKOFF_BASE * attempt
				time.sleep(wait)
				continue
			return resp.json()
		except Exception:
			wait = BACKOFF_BASE * attempt
			time.sleep(wait)
	return None


def _get_language_labels(qids: List[str]) -> Dict[str, str]:
	qids = list({q for q in qids if q})
	if not qids:
		return {}
	results: Dict[str, str] = {}
	for i in range(0, len(qids), MAX_QIDS_PER_CALL):
		group = qids[i : i + MAX_QIDS_PER_CALL]
		params = {
			"action": "wbgetentities",
			"ids": "|".join(group),
			"props": "labels",
			"languages": "en",
			"format": "json",
			"origin": "*",
		}
		data = _safe_get_json(WIKIDATA_QUERY_API, params=params) or {}
		entities = data.get("entities", {})
		for qid, ent in entities.items():
			label = ent.get("labels", {}).get("en", {}).get("value")
			if label and label.strip():
				results[qid] = label.strip()
			# Don't set a fallback - let _get_label handle missing labels
		time.sleep(0.05)
	return results


def _get_label(qid: str) -> str:
	if not qid:
		return qid
	if qid in LABEL_CACHE:
		return LABEL_CACHE[qid]
	labels = _get_language_labels([qid])
	label = labels.get(qid, qid)
	
	# If label is the same as QID, it means lookup failed
	# Don't cache failed lookups and return empty string to signal failure
	if label == qid:
		return ""
	
	LABEL_CACHE[qid] = label
	return label


def get_wikidata_entity_id(language_name):
    """
    
    Tries multiple search strategies and validates each QID to ensure it's 
    actually a language-related entity.
    """
    def _try_page_lookup(title):
       
        params = {
            "action": "query",
            "titles": title,
            "prop": "pageprops",
            "ppprop": "wikibase_item",
            "format": "json",
        }
        data = _safe_get_json(WIKIPEDIA_API, params=params) or {}
        pages = data.get("query", {}).get("pages", {})
        for page in pages.values():
            if "pageprops" in page and "wikibase_item" in page["pageprops"]:
                return page["pageprops"]["wikibase_item"]
        return None
    
    def _try_page_lookup_with_validation(title, check_title_match=False):
        """Helper to try page lookup and validate the QID is language-related."""
        qid = _try_page_lookup(title)
        if qid:
            is_valid, _ = _validate_root_language(qid)
            if is_valid:
                
                if check_title_match:
                    # Check if the page title is relevant to the language name
                    title_lower = title.lower()
                    language_lower = language_name.lower()
                    
                    
                    if (title_lower == language_lower or 
                        title_lower == f"{language_lower} language" or
                        title_lower.startswith(f"{language_lower} ") or
                        title_lower.endswith(f" {language_lower}")):
                        return qid
                    return None
                return qid
        return None
    
    def _search_and_validate_with_priority(search_term, check_title_match=True):
        """Search and validate results with priority for exact or close matches."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": search_term,
            "srlimit": 10,  # Check more results for better coverage
            "format": "json",
        }
        data = _safe_get_json(WIKIPEDIA_API, params=params) or {}
        search_results = data.get("query", {}).get("search", [])
        
        if not search_results:
            return None
            
        # Sort results by relevance - prioritize exact matches and close matches
        language_lower = language_name.lower()
        
        def get_priority(result):
            title = result["title"].lower()
            # Highest priority: exact match
            if title == language_lower:
                return 0
            # High priority: exact match with "language"
            if title == f"{language_lower} language":
                return 1
            # Medium priority: starts with language name
            if title.startswith(f"{language_lower} "):
                return 2
            # Lower priority: contains language name
            if language_lower in title:
                return 3
            # Lowest priority: other matches
            return 4
        
        sorted_results = sorted(search_results, key=get_priority)
        
        for result in sorted_results:
            page_title = result["title"]
            qid = _try_page_lookup_with_validation(page_title, check_title_match)
            if qid:
                return qid
        return None
    
    try:
        # Strategy 1: Try direct name lookup first (e.g., "Sanskrit")
        qid = _try_page_lookup_with_validation(language_name)
        if qid:
            return qid
        
        # Strategy 2: Try with " language" suffix
        qid = _try_page_lookup_with_validation(f"{language_name} language")
        if qid:
            return qid
            
        # Strategy 3: Search with direct name, prioritizing exact matches
        qid = _search_and_validate_with_priority(language_name, check_title_match=True)
        if qid:
            return qid
            
        # Strategy 4: Search with " language" suffix, prioritizing exact matches
        qid = _search_and_validate_with_priority(f"{language_name} language", check_title_match=True)
        if qid:
            return qid
        
        # Strategy 5: Broader search without strict title matching as fallback
        qid = _search_and_validate_with_priority(language_name, check_title_match=False)
        if qid:
            return qid
                
        # Strategy 6: Try common language name variations
        variations = [
            f"{language_name}ese",
            f"{language_name}ese language", 
            f"Ancient {language_name}",
            f"Old {language_name}",
            f"Modern {language_name}",
            f"{language_name} language family"
        ]
        
        for variation in variations:
            qid = _try_page_lookup_with_validation(variation)
            if qid:
                return qid
                
    except Exception as e:
        print(f"Error getting QID for {language_name}: {e}")
    return None



def _sparql_pairs(entity_id: str, query_body: str, parent_var: str, label_var: str) -> List[Tuple[str, str]]:
	query = f"""
	SELECT ?{parent_var} ?{label_var} WHERE {{
	  {query_body}
	  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
	}}
	"""
	data = _safe_get_json(SPARQL_ENDPOINT, params={"query": query, "format": "json"}) or {}
	results = data.get("results", {}).get("bindings", [])
	out: List[Tuple[str, str]] = []
	for r in results:
		try:
			qid = r[parent_var]["value"].split("/")[-1]
			label = r[label_var]["value"]
			out.append((qid, label))
		except Exception:
			continue
	return out


def _get_parents(entity_id: str) -> List[Tuple[str, str]]:
	return _sparql_pairs(entity_id, f"wd:{entity_id} wdt:P279 ?parent.", "parent", "parentLabel")


def _get_children_by_p527(entity_id: str) -> List[Tuple[str, str]]:
	return _sparql_pairs(entity_id, f"wd:{entity_id} wdt:P527 ?child.", "child", "childLabel")


def _get_children(entity_id: str) -> List[Tuple[str, str]]:
	return _sparql_pairs(entity_id, f"?child wdt:P279 wd:{entity_id}.", "child", "childLabel")


def get_distribution_map_image(qid: str) -> Optional[str]:
	"""Get distribution map image URL for a given language QID.
	
	Args:
		qid: Wikidata QID (e.g., 'Q1860' for English)
		
	Returns:
		Image URL if found, None otherwise
	"""
	if not qid:
		return None
		
	query = f"""
	SELECT ?image WHERE {{
	  wd:{qid} wdt:P1846 ?image.
	}}
	"""
	print(qid)
	data = _safe_get_json(SPARQL_ENDPOINT, params={"query": query, "format": "json"}) or {}
	results = data.get("results", {}).get("bindings", [])
	
	if results:
		image_url = results[0]["image"]["value"]
		return image_url
	return None


def relationships_depth1_by_qid(qid: str) -> List[Dict[str, str]]:
	"""Return immediate parent/child relationships for a given QID (depth=1).

	Does not perform WebSocket streaming. Intended for on-demand node expansion
	when the frontend already knows the QID of the node to expand.
	"""
	if not qid:
		return []

	# Ensure classification cache is populated for the root qid
	_validate_qid(qid)
	root_label = _get_label(qid)

	rels_set: Set[Tuple[str, str]] = set()  # (child_id, parent_id)
	out: List[Dict[str, str]] = []

	def _emit(child_id: str, parent_id: str, child_label: str, parent_label: str):
		# Skip if labels are missing
		if not child_label or not child_label.strip() or not parent_label or not parent_label.strip():
			return
		key = (child_id, parent_id)
		if key in rels_set:
			return
		rels_set.add(key)

		# Validate and capture categories
		_validate_qid(child_id)
		_validate_qid(parent_id)
		child_cat = CLASSIFICATION_CACHE.get(child_id) or ""
		parent_cat = CLASSIFICATION_CACHE.get(parent_id) or ""

		out.append({
			"language1": child_label,
			"relationship": "Child of",
			"language2": parent_label,
			"language1_qid": child_id,
			"language2_qid": parent_id,
			"language1_category": child_cat,
			"language2_category": parent_cat,
		})

	# Parents of root (root is child of parent)
	for parent_id, _ in _get_parents(qid):
		proper_parent_label = _get_label(parent_id)
		# Resolve root label if not available yet
		proper_child_label = root_label or _get_label(qid)
		_emit(qid, parent_id, proper_child_label, proper_parent_label)

	# Children of root by P527
	for child_id, _ in _get_children_by_p527(qid):
		proper_child_label = _get_label(child_id)
		proper_parent_label = root_label or _get_label(qid)
		_emit(child_id, qid, proper_child_label, proper_parent_label)

	# Children of root by reverse P279
	for child_id, _ in _get_children(qid):
		proper_child_label = _get_label(child_id)
		proper_parent_label = root_label or _get_label(qid)
		_emit(child_id, qid, proper_child_label, proper_parent_label)

	return out


async def fetch_language_relationships(language_name: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
	"""Fetch genealogical relationships for a language up to `depth`.

	Streams each discovered relationship via websocket (type=relationship) with
	a running count so the frontend can progressively display nodes.
	Returns the full de‑duplicated list at the end.
	"""

	if depth < 1:
		raise ValueError("Depth must be >= 1")
	if depth > settings.MAX_DEPTH:
		raise ValueError(f"Depth exceeds allowed maximum ({settings.MAX_DEPTH})")

	root_qid = get_wikidata_entity_id(language_name)
    
	if not root_qid:
		raise ValueError(f"Language '{language_name}' not found in Wikidata")
	print(root_qid)
	
	
	root_label = _get_label(root_qid)
	
	
	root_valid, root_types = _validate_root_language(root_qid)
	if not root_valid:
		raise ValueError(f"Root entity for '{language_name}' (QID {root_qid}) is not a recognized language/dialect/family")
	
	# Emit root language information with detailed type classification
	if websocket_manager:
		await websocket_manager.send_json({
			"type": "root_language",
			"data": {
				"language_name": language_name,
				"qid": root_qid,
				"label": root_label,
				"types": root_types,
				"primary_type": root_types[0] if root_types else None,
				"is_language_family": "language_family" in root_types,
				"is_extinct": any(t in root_types for t in ["dead_language", "extinct_language", "ancient_language"]),
				"is_constructed": "constructed_language" in root_types,
				"is_sign_language": "sign_language" in root_types
			}
		})
	
	VALID_QIDS.add(root_qid)

	visited: Set[str] = set()
	relations: List[Tuple[str, str, str, str, str]] = []  # (lang1, relationship, lang2, qid1, qid2) full history
	emitted: Set[Tuple[str, str, str, str, str]] = set()
	total = 0

	async def emit(rel: Tuple[str, str, str, str, str]):
		nonlocal total
		if rel in emitted:
			return
		
		# Validate that both languages have proper names (not just QIDs)
		lang1_name, relationship, lang2_name, qid1, qid2 = rel
		
		# Skip if either language name is actually a QID (starts with Q followed by digits)
		if (lang1_name.startswith('Q') and lang1_name[1:].isdigit()) or \
		   (lang2_name.startswith('Q') and lang2_name[1:].isdigit()):
			return
		
		# Skip if either language name is empty or None
		if not lang1_name or not lang2_name or lang1_name.strip() == '' or lang2_name.strip() == '':
			return
			
		emitted.add(rel)
		total += 1
		if websocket_manager:
			# Derive categories (classification) from cached QIDs if available
			cat1 = CLASSIFICATION_CACHE.get(qid1) if qid1 else None
			cat2 = CLASSIFICATION_CACHE.get(qid2) if qid2 else None
			await websocket_manager.send_json(
				{
					"type": "relationship",
					"data": {
						"language1": lang1_name,
						"relationship": relationship,
						"language2": lang2_name,
						"language1_qid": qid1,
						"language2_qid": qid2,
						"count": total,
						"language1_category": cat1,
						"language2_category": cat2,
					},
				}
			)

	async def recurse(entity_id: str, current_depth: int, direction: str = "both"):
		"""
		Recursively traverse language relationships with direction awareness.
		
		Args:
			entity_id: Wikidata QID to process
			current_depth: Current traversal depth
			direction: "up" (parents only), "down" (children only), "both" (both directions)
		"""
		if entity_id in visited or len(visited) >= MAX_NODES:
			return
		
		# For depth control with direction awareness
		if direction == "up" and current_depth > depth:
			# If we've reached max depth going up, explore children with remaining depth and return
			current_label = _get_label(entity_id)
			if current_label and current_label.strip():
				visited.add(entity_id)
				_validate_qid(entity_id)
				# Use depth-respecting downward traversal for the root level
				await explore_children_with_depth(entity_id, current_label, depth)
			return
		elif direction == "down" and current_depth > depth:
			return
		elif direction == "both" and current_depth > depth:
			return
			
		visited.add(entity_id)
		current_label = _get_label(entity_id)
		
		# Skip if we couldn't get a proper label for this entity
		if not current_label or current_label.strip() == "":
			return

		# Validate current entity (may already be validated)
		_validate_qid(entity_id)

		# Parents (only if direction allows upward traversal)
		if direction in ["up", "both"]:
			for parent_id, parent_label in _get_parents(entity_id):
				if parent_id in visited:
					continue
				valid_parent, parent_class = _validate_qid(parent_id)
				if not valid_parent:
					continue
				# Get proper label, skip if empty
				proper_parent_label = _get_label(parent_id)
				if not proper_parent_label or proper_parent_label.strip() == "":
					continue
				rel = (current_label, "Child of", proper_parent_label, entity_id, parent_id)
				relations.append(rel)
				await emit(rel)
				if current_depth < depth:
					await recurse(parent_id, current_depth + 1, "both")
				else:
					await recurse(parent_id, current_depth + 1, "up")

		# Children (only if direction allows downward traversal)
		if direction in ["down", "both"]:
			await explore_children_with_depth(entity_id, current_label, depth - current_depth + 1)
	
	async def explore_children_one_level(entity_id: str, current_label: str):
		"""Helper function to explore only immediate children (one level) of a given entity.
		Used for breadth-first search operations where you need precise level control."""
		# Children by P527
		for child_id, child_label in _get_children_by_p527(entity_id):
			if child_id != entity_id and child_id not in visited and len(visited) < MAX_NODES:
				valid_child, child_class = _validate_qid(child_id)
				if not valid_child:
					continue
				# Get proper label, skip if empty
				proper_child_label = _get_label(child_id)
				if not proper_child_label or proper_child_label.strip() == "":
					continue
				rel = (proper_child_label, "Child of", current_label, child_id, entity_id)
				relations.append(rel)
				await emit(rel)

		# Children by reverse P279
		for child_id, child_label in _get_children(entity_id):
			if child_id != entity_id and child_id not in visited and len(visited) < MAX_NODES:
				valid_child, child_class = _validate_qid(child_id)
				if not valid_child:
					continue
				# Get proper label, skip if empty
				proper_child_label = _get_label(child_id)
				if not proper_child_label or proper_child_label.strip() == "":
					continue
				rel = (proper_child_label, "Child of", current_label, child_id, entity_id)
				relations.append(rel)
				await emit(rel)

	async def explore_children_with_depth(entity_id: str, current_label: str, remaining_depth: int):
		"""Helper function to explore children of a given entity up to a specified depth.
		Performs depth-respecting downward traversal for breadth-first search."""
		if remaining_depth <= 0 or len(visited) >= MAX_NODES:
			return
			
		children_to_explore = []
		
		# Collect children by P527
		for child_id, child_label in _get_children_by_p527(entity_id):
			if child_id != entity_id and child_id not in visited:
				valid_child, child_class = _validate_qid(child_id)
				if not valid_child:
					continue
				# Get proper label, skip if empty
				proper_child_label = _get_label(child_id)
				if not proper_child_label or proper_child_label.strip() == "":
					continue
				
				visited.add(child_id)
				rel = (proper_child_label, "Child of", current_label, child_id, entity_id)
				relations.append(rel)
				await emit(rel)
				
				if remaining_depth > 1:
					children_to_explore.append((child_id, proper_child_label))

		# Collect children by reverse P279
		for child_id, child_label in _get_children(entity_id):
			if child_id != entity_id and child_id not in visited:
				valid_child, child_class = _validate_qid(child_id)
				if not valid_child:
					continue
				# Get proper label, skip if empty
				proper_child_label = _get_label(child_id)
				if not proper_child_label or proper_child_label.strip() == "":
					continue
				
				visited.add(child_id)
				rel = (proper_child_label, "Child of", current_label, child_id, entity_id)
				relations.append(rel)
				await emit(rel)
				
				if remaining_depth > 1:
					children_to_explore.append((child_id, proper_child_label))

		# Recursively explore children at the next depth level
		for child_id, child_label in children_to_explore:
			if len(visited) < MAX_NODES:
				await explore_children_with_depth(child_id, child_label, remaining_depth - 1)

	# Perform traversal with immediate emission - start with both directions
	await recurse(root_qid, 1, "both")

	# Final unique list
	unique_relations = list({(r[0], r[1], r[2], r[3], r[4]) for r in relations})
	return [
		{
			"language1": r[0], 
			"relationship": r[1], 
			"language2": r[2],
			"language1_qid": r[3],
			"language2_qid": r[4]
		} for r in unique_relations
	]
