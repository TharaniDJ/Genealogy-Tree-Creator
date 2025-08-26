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
    
    headers = {
        "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
    }
    
    try:
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch wikitext: {response.status_code}")
            print(f"Response text: {response.text}")
            return None

        # Allow parsing even if content-type is not strictly application/json
        try:
            data = response.json()
        except ValueError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Response text: {response.text}")
            return None

        # Check for API errors in response
        if "error" in data:
            print(f"Wikipedia API error: {data['error']}")
            return None

        if "parse" not in data or "wikitext" not in data["parse"]:
            print(f"No parse data found for page: {page_title}")
            return None

        wikitext = data["parse"]["wikitext"]["*"]
        matches = re.findall(r"\{\{ahnentafel[\s\S]+?\n\}\}", wikitext, re.IGNORECASE)
        return matches[0] if matches else None
        
    except requests.RequestException as e:
        print(f"Request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in get_family_tree_template: {e}")
        return None

def extract_ahnentafel_relationships(template_text: str) -> List[List[str]]:
    """Extract [child, 'child of', parent] triples from ahnentafel template."""
    try:
        raw_entries = re.findall(
            r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", 
            template_text
        )
        entries = {num: re.sub(r"^\s*\d+\.\s*", "", name.strip()) for num, name in raw_entries}

        relationships = []
        for num_str, child_name in entries.items():
            try:
                num = int(num_str)
                father_num = 2 * num
                mother_num = 2 * num + 1

                if str(father_num) in entries:
                    relationships.append([child_name, "child of", entries[str(father_num)]])
                if str(mother_num) in entries:
                    relationships.append([child_name, "child of", entries[str(mother_num)]])
            except (ValueError, KeyError) as e:
                print(f"Error processing entry {num_str}: {e}")
                continue

        return relationships
    except Exception as e:
        print(f"Error extracting ahnentafel relationships: {e}")
        return []

def extract_spouse_relationships(template_text: str) -> List[List[str]]:
    """Extract spouse entries from template."""
    try:
        spouses = re.findall(r"\|\s*spouse\d*\s*=\s*\[{2}([^\|\]]+)", template_text)
        main = re.search(r'\|\s*1\s*=\s*\[{2}([^\|\]]+)', template_text)
        if main:
            main_person = main.group(1)
            return [[main_person.strip(), "spouse of", spouse.strip()] for spouse in spouses]
        return []
    except Exception as e:
        print(f"Error extracting spouse relationships: {e}")
        return []

def extract_relationships_from_page(title: str) -> List[List[str]]:
    """Main API function: given a title, return genealogical relationships."""
    try:
        raw_template = get_family_tree_template(title)
        if not raw_template:
            print(f"No family tree template found for: {title}")
            return []

        child_relationships = extract_ahnentafel_relationships(raw_template)
        spouse_relationships = extract_spouse_relationships(raw_template)
        
        all_relationships = child_relationships + spouse_relationships
        print(f"Found {len(all_relationships)} relationships for {title}")
        return all_relationships
        
    except Exception as e:
        print(f"Error extracting relationships from page {title}: {e}")
        return []

def build_tree_from_template(title: str):
    """Debug function to display relationships and raw template."""
    try:
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
        
    except Exception as e:
        print(f"Error in build_tree_from_template: {e}")

def check_wikipedia_tree(page_title: str) -> bool:
    """Check if Wikipedia page contains family tree templates."""
    try:
        params = {
            "action": "parse",
            "page": page_title,
            "prop": "wikitext",
            "format": "json",
        }
        
        headers = {
            "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
        }
        
        response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers)
        if response.status_code != 200:
            return False
            
        try:
            data = response.json()
        except ValueError:
            return False
            
        if "error" in data:
            return False
            
        if "parse" in data and "wikitext" in data["parse"]:
            text = data["parse"]["wikitext"]["*"]
            needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
            return any(n.lower() in text.lower() for n in needles)
    except Exception as e:
        print(f"Error checking Wikipedia tree for {page_title}: {e}")
        
    return False

# Test the function
if __name__ == "__main__":
    build_tree_from_template("Charles III")