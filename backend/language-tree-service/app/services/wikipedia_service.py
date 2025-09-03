
# --- Enhanced Wikipedia Infobox-based Language Family Extractor ---
import requests
import re
import mwparserfromhell
import wikipediaapi
import json
from collections import deque
from typing import List, Dict, Optional, Tuple, Set
from app.core.websocket_manager import WebSocketManager

class LanguageFamilyTreeExtractor:
    def __init__(self, user_agent: str = "LanguageTreeBot/1.0 (research purposes)"):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.page_cache = {}

    ########################
    ## Wikidata + Wikipedia helpers
    ########################

    def get_language_relationships_wikidata(self, language_name):
        """
        Fetch language relationships from Wikidata using a SPARQL query.
        """
        sparql_query = f"""
        SELECT ?parentLabel ?childLabel ?dialectLabel ?siblingLabel
        WHERE {{
          ?language rdfs:label "{language_name}"@en .
          ?language wdt:P31/wdt:P279* wd:Q34770 .  # instance/subclass of language

          # Optional: parent/child relationships
          OPTIONAL {{ ?language wdt:P279 ?parent . }}  # subclass of
          OPTIONAL {{ ?child wdt:P279 ?language . }}  # children as subclasses

          # Dialects: items that are 'dialect of' this language
          OPTIONAL {{ ?dialect wdt:P5019 ?language . }}

          # Siblings: other dialects of the same parent
          OPTIONAL {{
            ?sibling wdt:P5019 ?commonParent .
            ?language wdt:P5019 ?commonParent .
            FILTER(?sibling != ?language)
          }}

          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
        }}
        """
        url = 'https://query.wikidata.org/sparql'
        try:
            headers = {
                'User-Agent': 'LanguageRelationshipFetcher/1.1 (educational@example.com)'
            }
            response = requests.get(url, params={'query': sparql_query, 'format': 'json'}, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error querying Wikidata: {e}")
            return {}

        results = {
            "parents": [],
            "children": [],
            "dialects": [],
            "siblings": [],
        }

        parent_set = set()
        children_set = set()
        dialects_set = set()
        siblings_set = set()

        for item in data.get('results', {}).get('bindings', []):
            if 'parentLabel' in item:
                parent_set.add(item['parentLabel']['value'])
            if 'childLabel' in item:
                children_set.add(item['childLabel']['value'])
            if 'dialectLabel' in item:
                dialects_set.add(item['dialectLabel']['value'])
            if 'siblingLabel' in item:
                siblings_set.add(item['siblingLabel']['value'])

        results["parents"] = sorted(list(parent_set))
        results["children"] = sorted(list(children_set))
        results["dialects"] = sorted(list(dialects_set))
        results["siblings"] = sorted(list(siblings_set))
        return results

    def get_language_relationships_infobox(self, language_name):
        """
        Fetches language relationships from the Wikipedia infobox.
        """
        wiki_wiki = wikipediaapi.Wikipedia('LanguageTreeBuilder/1.0 (educational@example.com)', 'en')
        page = wiki_wiki.page(language_name)

        if not page.exists():
            print(f"Page for '{language_name}' not found on Wikipedia.")
            return {}

        wikicode = mwparserfromhell.parse(page.text)

        infoboxes = wikicode.filter_templates(matches=lambda t: t.name.strip().lower().startswith('infobox language'))

        if not infoboxes:
            return {}
        infobox = infoboxes[0]

        results = {"parents": [], "dialects": []}
        parent_set = set()
        dialect_set = set()
        parent_params = ['family', 'fam', 'family1', 'fam1', 'ancestor', 'ancestors']
        dialect_params = ['dialects', 'varieties']

        for param in infobox.params:
            param_name = param.name.strip().lower()
            param_value = param.value.strip_code().strip()

            if any(p in param_name for p in parent_params):
                parents = [p.strip() for p in param_value.replace('\n', ',').split(',') if p.strip()]
                parent_set.update(parents)

            if any(d in param_name for d in dialect_params):
                dialects = [d.strip() for d in param_value.replace('\n', ',').split(',') if d.strip()]
                dialect_set.update(dialects)

        results["parents"] = sorted(list(parent_set))
        results["dialects"] = sorted(list(dialect_set))
        return results

    ########################
    ## Raw wikitext dialect extractor (dia1..dia40)
    ########################

    def _get_page_content(self, title: str) -> str:
        """Fetch raw wikitext content of the given page title."""
        if title in self.page_cache:
            return self.page_cache[title]
        
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "revisions",
            "rvprop": "content",
            "rvslots": "main",
        }
        try:
            r = requests.get(self.base_url, params=params, headers={'User-Agent': 'LanguageTreeNotebook/1.0 (educational)'}, timeout=15)
            r.raise_for_status()
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return ""
            page = next(iter(pages.values()))
            revs = page.get("revisions")
            if not revs:
                return ""
            content = revs[0].get("slots", {}).get("main", {}).get("*", "")
            self.page_cache[title] = content
            return content
        except Exception:
            return ""

    def _find_wiki_links(self, text: str) -> List[str]:
        """Return list of linked page titles from wiki link markup [[Title|...]]."""
        if not text:
            return []
        links = []
        for m in re.finditer(r"\[\[([^|#\]]+)(?:\|[^\]]*)?\]\]", text):
            t = m.group(1).strip()
            if t:
                links.append(t)
        return links

    def _extract_infobox(self, wikitext: str) -> Dict[str, str]:
        """Extract raw key->value pairs from the Infobox (language or language family)."""
        if not wikitext:
            return {}

        start = wikitext.find("{{Infobox language")
        if start == -1:
            start = wikitext.find("{{Infobox language family")
        if start == -1:
            m = re.search(r"\{\{infobox\s+(language|language family)", wikitext, re.IGNORECASE)
            if m:
                start = m.start()
            else:
                return {}

        # Find the matching closing braces for the infobox
        pos = start + 2
        depth = 1
        end = -1
        while pos < len(wikitext):
            if wikitext[pos:pos+2] == "{{":
                depth += 1
                pos += 2
            elif wikitext[pos:pos+2] == "}}":
                depth -= 1
                pos += 2
                if depth == 0:
                    end = pos
                    break
            else:
                pos += 1
        if end == -1:
            return {}

        content = wikitext[start:end]
        raw: Dict[str, str] = {}
        current_key = None
        current_val_lines: List[str] = []

        for line in content.split("\n"):
            s = line.strip()
            if s.lower().startswith("{{infobox language"):
                continue
            if s.startswith("|") and "=" in s:
                if current_key is not None and current_val_lines:
                    raw[current_key] = "\n".join(current_val_lines).strip()
                key, val = s[1:].split("=", 1)
                current_key = key.strip()
                current_val_lines = [val.strip()]
            elif s.startswith("|") and current_key is not None:
                current_val_lines.append(s[1:].strip())
            elif current_key is not None and not s.startswith("|"):
                current_val_lines.append(s)

        if current_key is not None and current_val_lines:
            raw[current_key] = "\n".join(current_val_lines).strip()

        return raw

    def _get_page_categories(self, title: str) -> List[str]:
        """Fetch non-hidden categories for a Wikipedia page title."""
        params = {
            "action": "query",
            "format": "json",
            "prop": "categories",
            "titles": title,
            "clshow": "!hidden",
            "cllimit": "50",
        }
        try:
            r = requests.get(self.base_url, params=params, headers={'User-Agent': 'LanguageTreeNotebook/1.0 (educational)'}, timeout=15)
            r.raise_for_status()
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return []
            page = next(iter(pages.values()))
            cats = page.get("categories", []) or []
            return [c.get("title", "") for c in cats if c.get("title")]
        except Exception:
            return []

    def _is_probable_geopage(self, title: str) -> bool:
        """
        Heuristic: exclude pages that are likely countries/regions/geography.
        Uses categories to spot geographic topics.
        """
        cats = self._get_page_categories(title)
        if not cats:
            return False
        joined = " ".join(cats).lower()
        geo_keywords = [
            "country","countries","sovereign state","sovereign states","empire","empires",
            "kingdom","kingdoms","roman","province","provinces","city","cities",
            "populated places","regions of","counties of","states of","geography of",
        ]
        return any(k in joined for k in geo_keywords)

    def _filter_dialect_titles(self, titles: List[str], language_name: str) -> List[str]:
        """
        Remove obvious non-dialect entries such as list pages, media namespaces,
        the language itself, and geographic pages (countries/regions).
        """
        out: List[str] = []
        seen = set()
        for t in titles:
            tt = (t or "").strip()
            if not tt:
                continue
            low = tt.lower()
            # Exclude list/maintenance and non-article namespaces
            if low.startswith("list of") or low.startswith("outline of") or low.startswith("history of"):
                continue
            if any(tt.startswith(ns) for ns in ("Category:", "File:", "Image:", "Template:")):
                continue
            # Exclude the language's main page variants
            if tt in {language_name, f"{language_name} language", f"{language_name} Language"}:
                continue
            # Exclude likely geo pages (countries/regions)
            if self._is_probable_geopage(tt):
                continue
            if tt not in seen:
                seen.add(tt)
                out.append(tt)
        return out

    def get_dialect_relationships(self, language_name: str) -> List[Tuple[str, str, str]]:
        """
        Return only (dialect, 'dialect_of', language_name) tuples extracted from the
        language's Wikipedia infobox. Looks at 'dialects' and 'dia1'..'dia40' fields,
        and filters out non-dialect pages (e.g., countries, lists).
        """
        if not language_name or not isinstance(language_name, str):
            return []

        # Try a few common page title variations
        candidates = [
            f"{language_name} language",
            language_name,
            f"{language_name} Language",
            f"{language_name} languages",
            f"{language_name} language family",
        ]

        wikitext = ""
        for t in candidates:
            wikitext = self._get_page_content(t)
            if wikitext and ("{{Infobox language" in wikitext or "{{Infobox language family" in wikitext):
                break
        if not wikitext:
            return []

        infobox_raw = self._extract_infobox(wikitext)
        if not infobox_raw:
            return []

        found: List[str] = []

        # Collect from explicit 'dialects' field if it contains links
        if "dialects" in infobox_raw:
            found.extend(self._find_wiki_links(infobox_raw["dialects"]))

        # Collect from dia1..dia40 fields
        for i in range(1, 41):
            k = f"dia{i}"
            if k in infobox_raw:
                found.extend(self._find_wiki_links(infobox_raw[k]))

        # Deduplicate while preserving order
        seen = set()
        ordered: List[str] = []
        for d in found:
            if d not in seen:
                seen.add(d)
                ordered.append(d)

        # Filter out non-dialect pages
        dialects = self._filter_dialect_titles(ordered, language_name)

        return [(d, "dialect_of", language_name) for d in dialects]

    ########################
    ## Main Pipeline
    ########################
    
    def get_language_relationships(self, language_name):
        """
        Main pipeline function to get language relationships.
        Combines Wikidata, Wikipedia infobox parsing, and raw wikitext parsing.
        """
        print(f"--- Fetching relationships for: {language_name} ---\n")

        print("1. Querying Wikidata...")
        wikidata_results = self.get_language_relationships_wikidata(language_name)
        print("Done.\n")

        print("2. Parsing Wikipedia Infobox (mwparserfromhell)...")
        infobox_results = self.get_language_relationships_infobox(language_name)
        print("Done.\n")

        print("3. Extracting dialects from raw Infobox wikitext (dia1..dia40)...")
        dialect_tuples = self.get_dialect_relationships(language_name)
        wikitext_dialects = [d for (d, _rel, _lang) in dialect_tuples]
        print(f"   Found {len(wikitext_dialects)} dialects via wikitext parser.\n")

        combined_parents = set(wikidata_results.get("parents", []))
        if "parents" in infobox_results:
            combined_parents.update(infobox_results["parents"])

        # Filter infobox-derived dialects as well
        infobox_dialects = infobox_results.get("dialects", [])
        infobox_dialects_filtered = self._filter_dialect_titles(list(infobox_dialects), language_name)

        combined_dialects = set(wikidata_results.get("dialects", []))
        combined_dialects.update(infobox_dialects_filtered)
        combined_dialects.update(wikitext_dialects)

        return {
            "language": language_name,
            "parents": sorted(list(combined_parents)),
            "children": wikidata_results.get("children", []),
            "siblings": wikidata_results.get("siblings", []),
            "dialects": sorted(list(combined_dialects)),
        }

    def get_direct_relationships(self, language_name: str) -> List[Tuple[str, str, str]]:
        """
        Get direct language relationships using the enhanced pipeline.
        Returns list of tuples: (entity1, relationship, entity2)
        """
        relationships = []
        data = self.get_language_relationships(language_name)
        
        # Convert the structured data to relationship tuples
        for parent in data.get("parents", []):
            relationships.append((language_name, "descended_from", parent))
        
        for child in data.get("children", []):
            relationships.append((child, "descended_from", language_name))
        
        for dialect in data.get("dialects", []):
            relationships.append((dialect, "dialect_of", language_name))
        
        for sibling in data.get("siblings", []):
            relationships.append((sibling, "sibling_of", language_name))
        
        return relationships

    def get_language_family_hierarchy(self, language_name: str) -> List[Tuple[str, str, str]]:
        """
        Get comprehensive language family hierarchy.
        This method provides backward compatibility for the check_language_validity function.
        """
        return self.get_direct_relationships(language_name)

# --- Async wrapper for extractor with websocket updates ---
async def fetch_language_relationships(language_name: str, depth: int, websocket_manager: Optional[WebSocketManager] = None) -> List[Dict[str, str]]:
    """
    Fetch language family relationships for a given language and depth using Wikipedia infoboxes.
    Returns relationships in the format [{"entity1": str, "relationship": str, "entity2": str}].
    Sends websocket updates after each relationship is found.
    """
    extractor = LanguageFamilyTreeExtractor()
    all_relationships = []
    processed_languages: Set[str] = set()
    languages_to_process = deque([(language_name, 0)])
    total_found = 0
    if websocket_manager:
        await websocket_manager.send_status(f"Starting language relationship collection for '{language_name}'...", 0)
    while languages_to_process:
        current_lang, current_depth = languages_to_process.popleft()
        print(current_lang)
        if current_depth > depth or current_lang in processed_languages:
            continue
        processed_languages.add(current_lang)
        lang_relationships = extractor.get_direct_relationships(current_lang)
        
        if lang_relationships:
            for lang1, rel, lang2 in lang_relationships:
                rel_dict = {"entity1": lang1, "relationship": rel, "entity2": lang2}
                all_relationships.append(rel_dict)
                total_found += 1
                # Send websocket update after each relationship
                if websocket_manager:
                    await websocket_manager.send_json({
                        "type": "relationship",
                        "data": rel_dict
                    })
            # Add related languages for further exploration
            if current_depth < depth:
                for lang1, rel, lang2 in lang_relationships:
                    if rel == "dialect_of":
                        continue
                    if lang1 not in processed_languages:
                        languages_to_process.append((lang1, current_depth + 1))
                    if lang2 not in processed_languages:
                        languages_to_process.append((lang2, current_depth + 1))
        # Optionally send progress update every 10 relationships
        if websocket_manager and total_found % 10 == 0:
            percent = min(100, int(100 * len(processed_languages) / (depth * 10 + 1)))
            await websocket_manager.send_status(f"Processed {len(processed_languages)} languages, {total_found} relationships found...", percent)
    if websocket_manager:
        await websocket_manager.send_status(f"Collection complete! {total_found} relationships found.", 100)
    return all_relationships

async def check_language_validity(language_name: str) -> bool:
    """Check if the language name corresponds to a valid Wikipedia page with an infobox."""
    extractor = LanguageFamilyTreeExtractor()
    rels = extractor.get_language_family_hierarchy(language_name)
    return bool(rels)
