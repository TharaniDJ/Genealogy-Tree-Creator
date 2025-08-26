
# --- Enhanced Wikipedia Infobox-based Language Family Extractor ---
import requests
import re
from collections import deque
from typing import List, Dict, Optional, Tuple, Set
from app.core.websocket_manager import WebSocketManager

class LanguageFamilyTreeExtractor:
    def __init__(self, user_agent: str = "LanguageTreeBot/1.0 (research purposes)"):
        self.base_url = "https://en.wikipedia.org/w/api.php"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.page_cache = {}

    def get_page_content(self, title: str) -> str:
        if title in self.page_cache:
            return self.page_cache[title]
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'revisions',
            'rvprop': 'content',
            'rvslots': 'main'
        }
        try:
            response = self.session.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            page_data = next(iter(pages.values()))
            if 'revisions' in page_data:
                content = page_data['revisions'][0]['slots']['main']['*']
                self.page_cache[title] = content
                return content
            else:
                return ""
        except Exception as e:
            print(f"Error fetching page {title}: {e}")
            return ""

    def clean_wiki_value(self, value: str) -> str:
        if not value:
            return ""
        value = re.sub(r'\[\[([^|\]]*)\|([^\]]*)\]\]', r'\2', value)
        value = re.sub(r'\[\[([^\]]*)\]\]', r'\1', value)
        while True:
            old_value = value
            value = re.sub(r'\{\{[^{}]*\}\}', '', value)
            if value == old_value:
                break
        value = re.sub(r'<ref[^>]*>.*?</ref>', '', value, flags=re.DOTALL)
        value = re.sub(r'<ref[^>]*/?>', '', value)
        value = re.sub(r'<[^>]*>', '', value)
        value = re.sub(r'\s+', ' ', value).strip()
        return value

    def find_wiki_links(self, text: str) -> List[str]:
        links = []
        for match in re.finditer(r'\[\[([^|]+)(?:\|[^]]*)?\]\]', text):
            link = match.group(1).strip()
            if link:
                links.append(link)
        return links

    def extract_infobox(self, wikitext: str) -> Tuple[Dict[str, str], Dict[str, str]]:
        infobox_clean = {}
        infobox_raw = {}
        infobox_start = wikitext.find("{{Infobox language")
        if infobox_start == -1:
            infobox_start = wikitext.find("{{Infobox language family")
        if infobox_start == -1:
            match = re.search(r'\{\{infobox\s+(language|language family)', wikitext, re.IGNORECASE)
            if match:
                infobox_start = match.start()
            else:
                return infobox_clean, infobox_raw
        brace_count = 1
        pos = infobox_start + 2
        infobox_end = -1
        while pos < len(wikitext):
            if wikitext[pos:pos+2] == '{{':
                brace_count += 1
                pos += 2
            elif wikitext[pos:pos+2] == '}}':
                brace_count -= 1
                pos += 2
                if brace_count == 0:
                    infobox_end = pos
                    break
            else:
                pos += 1
        if infobox_end == -1:
            return infobox_clean, infobox_raw
        infobox_content = wikitext[infobox_start:infobox_end]
        lines = infobox_content.split('\n')
        current_key = None
        current_value = []
        for line in lines:
            line = line.strip()
            if line.startswith('{{Infobox language') or line.startswith('{{infobox language'):
                continue
            if line.startswith('|') and '=' in line:
                if current_key and current_value:
                    raw_text = '\n'.join(current_value)
                    cleaned_value = self.clean_wiki_value(raw_text)
                    infobox_raw[current_key] = raw_text
                    if cleaned_value:
                        infobox_clean[current_key] = cleaned_value
                parts = line[1:].split('=', 1)
                if len(parts) == 2:
                    current_key = parts[0].strip()
                    current_value = [parts[1].strip()]
            elif line.startswith('|') and current_key:
                current_value.append(line[1:].strip())
            elif current_key and not line.startswith('|'):
                current_value.append(line)
        if current_key and current_value:
            raw_text = '\n'.join(current_value)
            cleaned_value = self.clean_wiki_value(raw_text)
            infobox_raw[current_key] = raw_text
            if cleaned_value:
                infobox_clean[current_key] = cleaned_value
        return infobox_clean, infobox_raw

    def get_language_family_hierarchy(self, language_name: str) -> List[Tuple[str, str, str]]:
        relationships = []
        page_variations = [
            f"{language_name} language",
            language_name,
            f"{language_name} Language",
            f"{language_name} languages",
            f"{language_name} language family"
        ]
        content = ""
        for page_title in page_variations:
            content = self.get_page_content(page_title)
            if content and ("{{Infobox language" in content or "{{Infobox language family" in content):
                break
        if not content:
            return relationships
        infobox_clean, infobox_raw = self.extract_infobox(content)
        if not infobox_clean:
            return relationships
        family_chain = []
        if 'familycolor' in infobox_clean:
            family_chain.append(infobox_clean['familycolor'])
        for i in range(1, 16):
            fam_key = f'fam{i}'
            if fam_key in infobox_clean:
                family_chain.append(infobox_clean[fam_key])
        if family_chain:
            if len(family_chain) > 0:
                relationships.append((language_name, "belongs_to", family_chain[-1]))
            for i in range(len(family_chain) - 1, 0, -1):
                relationships.append((family_chain[i], "belongs_to", family_chain[i-1]))
        ancestors = []
        for i in range(1, 9):
            ancestor_key = f'ancestor{i}' if i > 1 else 'ancestor'
            if ancestor_key in infobox_clean:
                ancestors.append(infobox_clean[ancestor_key])
        if 'protoname' in infobox_clean:
            ancestors.append(infobox_clean['protoname'])
        if 'earlyforms' in infobox_raw:
            early_links = self.find_wiki_links(infobox_raw['earlyforms'])
            early_links.reverse()
            ancestors.extend(early_links)
        current_descendant = language_name
        for ancestor in ancestors:
            relationships.append((current_descendant, "descended_from", ancestor))
            current_descendant = ancestor
        for i in range(1, 41):
            dialect_key = f'dia{i}'
            if dialect_key in infobox_raw:
                dialects = self.find_wiki_links(infobox_raw[dialect_key])
                for dialect in dialects:
                    relationships.append((dialect, "dialect_of", language_name))
        if 'dialects' in infobox_clean:
            cleaned = infobox_clean['dialects']
            if 'list' not in cleaned.lower() and 'see' not in cleaned.lower():
                dialects = self.find_wiki_links(infobox_raw['dialects'])
                for dialect in dialects:
                    relationships.append((dialect, "dialect_of", language_name))
        for i in range(1, 51):
            child_key = f'child{i}'
            if child_key in infobox_raw:
                children = self.find_wiki_links(infobox_raw[child_key])
                for child in children:
                    relationships.append((child, "belongs_to", language_name))
        return relationships

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
        if current_depth > depth or current_lang in processed_languages:
            continue
        processed_languages.add(current_lang)
        lang_relationships = extractor.get_language_family_hierarchy(current_lang)
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
