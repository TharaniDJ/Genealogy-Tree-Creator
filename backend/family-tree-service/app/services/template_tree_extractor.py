# import requests
# import re
# from typing import List, Optional

# WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

# def get_family_tree_template(page_title: str) -> Optional[str]:
#     """Fetch wikitext and extract the first ahnentafel template."""
#     params = {
#         "action": "parse",
#         "page": page_title,
#         "prop": "wikitext",
#         "format": "json",
#     }
#     response = requests.get(WIKIPEDIA_API_URL, params=params).json()

#     if "parse" not in response or "wikitext" not in response["parse"]:
#         return None

#     wikitext = response["parse"]["wikitext"]["*"]
#     matches = re.findall(r"\{\{ahnentafel[\s\S]+?\n\}\}", wikitext, re.IGNORECASE)
#     return matches[0] if matches else None

# def extract_ahnentafel_relationships(template_text: str) -> List[List[str]]:
#     """Extract [child, 'child of', parent] triples from ahnentafel template."""
#     raw_entries = re.findall(r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", template_text)
#     entries = {num: re.sub(r"^\s*\d+\.\s*", "", name.strip()) for num, name in raw_entries}

#     relationships = []
#     for num_str, child_name in entries.items():
#         num = int(num_str)
#         father_num = 2 * num
#         mother_num = 2 * num + 1

#         if str(father_num) in entries:
#             relationships.append([child_name, "child of", entries[str(father_num)]])
#         if str(mother_num) in entries:
#             relationships.append([child_name, "child of", entries[str(mother_num)]])

#     return relationships

# def extract_spouse_relationships(template_text: str) -> List[List[str]]:
#     """Extract spouse entries from template."""
#     spouses = re.findall(r"\|\s*spouse\d*\s*=\s*\[{2}([^\|\]]+)", template_text)
#     main = re.search(r'\|\s*1\s*=\s*\[{2}([^\|\]]+)', template_text)
#     if main:
#         main_person = main.group(1)
#         return [[main_person.strip(), "spouse of", spouse.strip()] for spouse in spouses]
#     return []

# def extract_relationships_from_page(title: str) -> List[List[str]]:
#     """Main API function: given a title, return genealogical relationships."""
#     raw_template = get_family_tree_template(title)
#     if not raw_template:
#         return []

#     child_relationships = extract_ahnentafel_relationships(raw_template)
#     spouse_relationships = extract_spouse_relationships(raw_template)
#     return child_relationships + spouse_relationships 

# template_tree_extractor.py

# app/services/template_tree_extractor.py

# import requests
# import re
# from typing import List, Optional

# WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

# def get_family_tree_template(page_title: str) -> Optional[str]:
#     """Fetch wikitext and extract the first ahnentafel template."""
#     params = {
#         "action": "parse",
#         "page": page_title,
#         "prop": "wikitext",
#         "format": "json",
#     }
#     response = requests.get(WIKIPEDIA_API_URL, params=params).json()

#     if "parse" not in response or "wikitext" not in response["parse"]:
#         return None

#     wikitext = response["parse"]["wikitext"]["*"]
#     matches = re.findall(r"\{\{ahnentafel[\s\S]+?\n\}\}", wikitext, re.IGNORECASE)
#     return matches[0] if matches else None


# def extract_ahnentafel_relationships(template_text: str) -> List[List[str]]:
#     """Extract [child, 'child of', parent] triples from ahnentafel template."""
#     raw_entries = re.findall(
#         r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", 
#         template_text
#     )
#     entries = {num: re.sub(r"^\s*\d+\.\s*", "", name.strip()) for num, name in raw_entries}

#     relationships = []
#     for num_str, child_name in entries.items():
#         num = int(num_str)
#         father_num = 2 * num
#         mother_num = 2 * num + 1

#         if str(father_num) in entries:
#             relationships.append([child_name, "child of", entries[str(father_num)]])
#         if str(mother_num) in entries:
#             relationships.append([child_name, "child of", entries[str(mother_num)]])

#     return relationships


# def extract_spouse_relationships(template_text: str) -> List[List[str]]:
#     """Extract spouse entries from template."""
#     spouses = re.findall(r"\|\s*spouse\d*\s*=\s*\[{2}([^\|\]]+)", template_text)
#     main = re.search(r'\|\s*1\s*=\s*\[{2}([^\|\]]+)', template_text)
#     if main:
#         main_person = main.group(1)
#         return [[main_person.strip(), "spouse of", spouse.strip()] for spouse in spouses]
#     return []


# def extract_relationships_from_page(title: str) -> List[List[str]]:
#     """Main API function: given a title, return genealogical relationships."""
#     raw_template = get_family_tree_template(title)
#     if not raw_template:
#         return []

#     child_relationships = extract_ahnentafel_relationships(raw_template)
#     spouse_relationships = extract_spouse_relationships(raw_template)
#     return child_relationships + spouse_relationships

import requests
import re
from typing import List, Optional

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

def get_family_tree_template(page_title: str) -> Optional[str]:
    """Fetch wikitext and extract the first ahnentafel template."""
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json",
    }
    response = requests.get(WIKIPEDIA_API_URL, params=params).json()

    if "parse" not in response or "wikitext" not in response["parse"]:
        return None

    wikitext = response["parse"]["wikitext"]["*"]
    matches = re.findall(r"\{\{ahnentafel[\s\S]+?\n\}\}", wikitext, re.IGNORECASE)
    return matches[0] if matches else None


def extract_ahnentafel_relationships(template_text: str) -> List[List[str]]:
    """Extract [child, 'child of', parent] triples from ahnentafel template."""
    raw_entries = re.findall(
        r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", 
        template_text
    )
    entries = {num: re.sub(r"^\s*\d+\.\s*", "", name.strip()) for num, name in raw_entries}

    relationships = []
    for num_str, child_name in entries.items():
        num = int(num_str)
        father_num = 2 * num
        mother_num = 2 * num + 1

        if str(father_num) in entries:
            relationships.append([child_name, "child of", entries[str(father_num)]])
        if str(mother_num) in entries:
            relationships.append([child_name, "child of", entries[str(mother_num)]])

    return relationships


def extract_spouse_relationships(template_text: str) -> List[List[str]]:
    """Extract spouse entries from template."""
    spouses = re.findall(r"\|\s*spouse\d*\s*=\s*\[{2}([^\|\]]+)", template_text)
    main = re.search(r'\|\s*1\s*=\s*\[{2}([^\|\]]+)', template_text)
    if main:
        main_person = main.group(1)
        return [[main_person.strip(), "spouse of", spouse.strip()] for spouse in spouses]
    return []


def extract_relationships_from_page(title: str) -> List[List[str]]:
    """Main API function: given a title, return genealogical relationships."""
    raw_template = get_family_tree_template(title)
    if not raw_template:
        return []

    child_relationships = extract_ahnentafel_relationships(raw_template)
    spouse_relationships = extract_spouse_relationships(raw_template)
    return child_relationships + spouse_relationships


def build_tree_from_template(title: str):
    """Debug function to display relationships and raw template."""
    raw_template = get_family_tree_template(title)
    if not raw_template:
        print("No family tree found.")
        return

    # Debug: show raw template preview
    print("\n=== Raw Template Preview ===\n")
    print(raw_template[:1000])

    child_relationships = extract_ahnentafel_relationships(raw_template)
    spouse_relationships = extract_spouse_relationships(raw_template)
    all_rels = child_relationships + spouse_relationships

    print(f"\nGenealogical relationships for {title}:")
    print("Format: [entity1, relationship, entity2]\n")
    for rel in all_rels:
        print(f"[{rel[0]}, {rel[1]}, {rel[2]}]")

    print(f"\nTotal relationships found: {len(all_rels)}")


# Test the function
if __name__ == "__main__":
    build_tree_from_template("Charles III")
