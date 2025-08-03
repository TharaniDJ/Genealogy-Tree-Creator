from typing import List, Dict
from app.services.wikipedia_service import fetch_relationships
import requests
import re

def fetch_family_tree_templates(page_title: str) -> list:
    """
    Fetches family tree templates (e.g., ahnentafel) from the page wikitext.
    Returns a list of template strings (can be empty if none found).
    """
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json",
    }
    response = requests.get("https://en.wikipedia.org/w/api.php", params=params).json()

    if "parse" not in response or "wikitext" not in response["parse"]:
        return []

    wikitext = response["parse"]["wikitext"]["*"]

    matches = re.findall(r"\{\{ahnentafel[\s\S]+?\n\}\}", wikitext, re.IGNORECASE)

    return matches  # a list of template strings
import re

def parse_family_tree_template(template: str) -> list:
    """
    Parse an ahnentafel-style family tree template into structured relationships.
    Supports child-parent and spouse relations.
    """
    relationships = []

    # Extract entries with numbering
    raw_entries = re.findall(r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", template)
    entries = {num: re.sub(r"^\s*\d+\.\s*", "", name.strip()) for num, name in raw_entries}

    # Build child-parent relationships
    for num_str, child_name in entries.items():
        num = int(num_str)
        father_num = 2 * num
        mother_num = 2 * num + 1

        if str(father_num) in entries:
            relationships.append({
                "from": child_name,
                "to": entries[str(father_num)],
                "relation": "child of"
            })

        if str(mother_num) in entries:
            relationships.append({
                "from": child_name,
                "to": entries[str(mother_num)],
                "relation": "child of"
            })

    # Extract spouse relationships
    spouses = re.findall(r"\|\s*spouse\d*\s*=\s*\[{2}([^\|\]]+)", template)
    main = re.search(r"\|\s*1\s*=\s*\[{2}([^\|\]]+)", template)
    if main:
        main_person = main.group(1).strip()
        for spouse in spouses:
            relationships.append({
                "from": main_person,
                "to": spouse.strip(),
                "relation": "spouse of"
            })

    return relationships

class GenealogyService:
    def __init__(self):
        pass

    def get_relationships(self, page_title: str, depth: int) -> List[Dict[str, str]]:
        relationships = fetch_relationships(page_title, depth)
        formatted_relationships = self.format_relationships(relationships)
        return formatted_relationships

    def format_relationships(self, relationships: List[List[str]]) -> List[Dict[str, str]]:
        formatted = []
        for entity1, relationship, entity2 in relationships:
            formatted.append({
                "entity1": entity1,
                "relationship": relationship,
                "entity2": entity2
            })
        return formatted