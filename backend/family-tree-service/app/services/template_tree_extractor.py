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
    
#     headers = {
#         "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#     }
    
#     try:
#         response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers)
#         if response.status_code != 200:
#             print(f"Failed to fetch wikitext: {response.status_code}")
#             print(f"Response text: {response.text}")
#             return None

#         # Allow parsing even if content-type is not strictly application/json
#         try:
#             data = response.json()
#         except ValueError as e:
#             print(f"Failed to parse JSON response: {e}")
#             print(f"Response text: {response.text}")
#             return None

#         # Check for API errors in response
#         if "error" in data:
#             print(f"Wikipedia API error: {data['error']}")
#             return None

#         if "parse" not in data or "wikitext" not in data["parse"]:
#             print(f"No parse data found for page: {page_title}")
#             return None

#         wikitext = data["parse"]["wikitext"]["*"]
#         matches = re.findall(r"\{\{ahnentafel[\s\S]+?\n\}\}", wikitext, re.IGNORECASE)
#         return matches[0] if matches else None
        
#     except requests.RequestException as e:
#         print(f"Request failed: {e}")
#         return None
#     except Exception as e:
#         print(f"Unexpected error in get_family_tree_template: {e}")
#         return None

# def extract_ahnentafel_relationships(template_text: str) -> List[List[str]]:
#     """Extract [child, 'child of', parent] triples from ahnentafel template."""
#     try:
#         raw_entries = re.findall(
#             r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", 
#             template_text
#         )
#         entries = {num: re.sub(r"^\s*\d+\.\s*", "", name.strip()) for num, name in raw_entries}

#         relationships = []
#         for num_str, child_name in entries.items():
#             try:
#                 num = int(num_str)
#                 father_num = 2 * num
#                 mother_num = 2 * num + 1

#                 if str(father_num) in entries:
#                     relationships.append([child_name, "child of", entries[str(father_num)]])
#                 if str(mother_num) in entries:
#                     relationships.append([child_name, "child of", entries[str(mother_num)]])
#             except (ValueError, KeyError) as e:
#                 print(f"Error processing entry {num_str}: {e}")
#                 continue

#         return relationships
#     except Exception as e:
#         print(f"Error extracting ahnentafel relationships: {e}")
#         return []

# def extract_spouse_relationships(template_text: str) -> List[List[str]]:
#     """Extract spouse entries from template."""
#     try:
#         spouses = re.findall(r"\|\s*spouse\d*\s*=\s*\[{2}([^\|\]]+)", template_text)
#         main = re.search(r'\|\s*1\s*=\s*\[{2}([^\|\]]+)', template_text)
#         if main:
#             main_person = main.group(1)
#             return [[main_person.strip(), "spouse of", spouse.strip()] for spouse in spouses]
#         return []
#     except Exception as e:
#         print(f"Error extracting spouse relationships: {e}")
#         return []

# def extract_relationships_from_page(title: str) -> List[List[str]]:
#     """Main API function: given a title, return genealogical relationships."""
#     try:
#         raw_template = get_family_tree_template(title)
#         if not raw_template:
#             print(f"No family tree template found for: {title}")
#             return []

#         child_relationships = extract_ahnentafel_relationships(raw_template)
#         spouse_relationships = extract_spouse_relationships(raw_template)
        
#         all_relationships = child_relationships + spouse_relationships
#         print(f"Found {len(all_relationships)} relationships for {title}")
#         return all_relationships
        
#     except Exception as e:
#         print(f"Error extracting relationships from page {title}: {e}")
#         return []

# def build_tree_from_template(title: str):
#     """Debug function to display relationships and raw template."""
#     try:
#         raw_template = get_family_tree_template(title)
#         if not raw_template:
#             print("No family tree found.")
#             return

#         # Debug: show raw template preview
#         print("\n=== Raw Template Preview ===\n")
#         print(raw_template[:1000])

#         child_relationships = extract_ahnentafel_relationships(raw_template)
#         spouse_relationships = extract_spouse_relationships(raw_template)
#         all_rels = child_relationships + spouse_relationships

#         print(f"\nGenealogical relationships for {title}:")
#         print("Format: [entity1, relationship, entity2]\n")
#         for rel in all_rels:
#             print(f"[{rel[0]}, {rel[1]}, {rel[2]}]")

#         print(f"\nTotal relationships found: {len(all_rels)}")
        
#     except Exception as e:
#         print(f"Error in build_tree_from_template: {e}")

# def check_wikipedia_tree(page_title: str) -> bool:
#     """Check if Wikipedia page contains family tree templates."""
#     try:
#         params = {
#             "action": "parse",
#             "page": page_title,
#             "prop": "wikitext",
#             "format": "json",
#         }
        
#         headers = {
#             "User-Agent": "MyWikipediaTool/1.0 (https://example.com/contact)"
#         }
        
#         response = requests.get(WIKIPEDIA_API_URL, params=params, headers=headers)
#         if response.status_code != 200:
#             return False
            
#         try:
#             data = response.json()
#         except ValueError:
#             return False
            
#         if "error" in data:
#             return False
            
#         if "parse" in data and "wikitext" in data["parse"]:
#             text = data["parse"]["wikitext"]["*"]
#             needles = ["{{Family tree", "{{Tree chart", "{{Ahnentafel", "{{Chart top"]
#             return any(n.lower() in text.lower() for n in needles)
#     except Exception as e:
#         print(f"Error checking Wikipedia tree for {page_title}: {e}")
        
#     return False

# # Test the function
# if __name__ == "__main__":
#     build_tree_from_template("Charles III")

import requests
import re
import json
import asyncio
from typing import List, Optional
from app.core.websocket_manager import WebSocketManager

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

        try:
            data = response.json()
        except ValueError as e:
            print(f"Failed to parse JSON response: {e}")
            print(f"Response text: {response.text}")
            return None

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

def clean_name(name: str) -> str:
    """Clean Wikipedia markup from names."""
    # Remove bold markup
    name = re.sub(r"'''([^']+)'''", r"\1", name)
    # Remove links [[Name|Display]] -> Display or [[Name]] -> Name
    name = re.sub(r"\[\[([^\|\]]+)\|([^\]]+)\]\]", r"\2", name)
    name = re.sub(r"\[\[([^\]]+)\]\]", r"\1", name)
    # Remove &nbsp; and other HTML entities
    name = name.replace("&nbsp;", " ")
    # Clean extra whitespace
    name = " ".join(name.split())
    return name.strip()

async def extract_ahnentafel_relationships_streaming(template_text: str, websocket_manager: Optional[WebSocketManager] = None) -> List[List[str]]:
    """Extract [child, 'child of', parent] triples and send them one by one."""
    try:
        raw_entries = re.findall(
            r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", 
            template_text
        )
        entries = {num: clean_name(re.sub(r"^\s*\d+\.\s*", "", name.strip())) for num, name in raw_entries}

        relationships = []
        for num_str, child_name in entries.items():
            try:
                num = int(num_str)
                father_num = 2 * num
                mother_num = 2 * num + 1

                if str(father_num) in entries:
                    parent_name = entries[str(father_num)]
                    relationship = [child_name, "child of", parent_name]
                    relationships.append(relationship)
                    
                    # Send relationship immediately via WebSocket
                    if websocket_manager:
                        await websocket_manager.send_message(json.dumps({
                            "type": "relationship",
                            "data": {
                                "entity1": child_name,
                                "relationship": "child of",
                                "entity2": parent_name
                            }
                        }))
                        # Small delay to ensure ordered delivery
                        await asyncio.sleep(0.1)

                if str(mother_num) in entries:
                    parent_name = entries[str(mother_num)]
                    relationship = [child_name, "child of", parent_name]
                    relationships.append(relationship)
                    
                    # Send relationship immediately via WebSocket
                    if websocket_manager:
                        await websocket_manager.send_message(json.dumps({
                            "type": "relationship",
                            "data": {
                                "entity1": child_name,
                                "relationship": "child of",
                                "entity2": parent_name
                            }
                        }))
                        # Small delay to ensure ordered delivery
                        await asyncio.sleep(0.1)

            except (ValueError, KeyError) as e:
                print(f"Error processing entry {num_str}: {e}")
                continue

        return relationships
    except Exception as e:
        print(f"Error extracting ahnentafel relationships: {e}")
        return []

async def extract_spouse_relationships_streaming(template_text: str, websocket_manager: Optional[WebSocketManager] = None) -> List[List[str]]:
    """Extract spouse entries and send them one by one."""
    try:
        spouses = re.findall(r"\|\s*spouse\d*\s*=\s*\[{2}([^\|\]]+)", template_text)
        main = re.search(r'\|\s*1\s*=\s*\[{2}([^\|\]]+)', template_text)
        
        relationships = []
        if main:
            main_person = clean_name(main.group(1))
            for spouse in spouses:
                spouse_name = clean_name(spouse.strip())
                relationship = [main_person, "spouse of", spouse_name]
                relationships.append(relationship)
                
                # Send relationship immediately via WebSocket
                if websocket_manager:
                    await websocket_manager.send_message(json.dumps({
                        "type": "relationship",
                        "data": {
                            "entity1": main_person,
                            "relationship": "spouse of",
                            "entity2": spouse_name
                        }
                    }))
                    # Small delay to ensure ordered delivery
                    await asyncio.sleep(0.1)
                    
        return relationships
    except Exception as e:
        print(f"Error extracting spouse relationships: {e}")
        return []

async def extract_relationships_from_page_streaming(title: str, websocket_manager: Optional[WebSocketManager] = None) -> List[List[str]]:
    """Main API function: extract relationships and send them one by one via WebSocket."""
    try:
        # Send initial status
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "status",
                "data": {"message": "Searching for family tree templates...", "progress": 10}
            }))

        raw_template = get_family_tree_template(title)
        if not raw_template:
            if websocket_manager:
                await websocket_manager.send_message(json.dumps({
                    "type": "status",
                    "data": {"message": "No family tree template found", "progress": 100}
                }))
            print(f"No family tree template found for: {title}")
            return []

        # Send progress update
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "status",
                "data": {"message": "Extracting relationships from template...", "progress": 30}
            }))

        # Extract child relationships (these will be sent one by one)
        child_relationships = await extract_ahnentafel_relationships_streaming(raw_template, websocket_manager)
        
        # Send progress update
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "status",
                "data": {"message": "Extracting spouse relationships...", "progress": 70}
            }))
        
        # Extract spouse relationships (these will be sent one by one)
        spouse_relationships = await extract_spouse_relationships_streaming(raw_template, websocket_manager)
        
        all_relationships = child_relationships + spouse_relationships
        
        # Send completion status
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "status",
                "data": {"message": f"Extraction complete! Found {len(all_relationships)} relationships", "progress": 100}
            }))
        
        print(f"Found {len(all_relationships)} relationships for {title}")
        return all_relationships
        
    except Exception as e:
        print(f"Error extracting relationships from page {title}: {e}")
        if websocket_manager:
            await websocket_manager.send_message(json.dumps({
                "type": "error",
                "data": {"message": f"Error extracting relationships: {str(e)}"}
            }))
        return []

# Legacy synchronous functions for backward compatibility
def extract_ahnentafel_relationships(template_text: str) -> List[List[str]]:
    """Extract [child, 'child of', parent] triples from ahnentafel template."""
    try:
        raw_entries = re.findall(
            r"\|\s*(\d+)\s*=\s*(?:\d+\.\s*)?(?:\[{2})?([^\|\]\n]+)", 
            template_text
        )
        entries = {num: clean_name(re.sub(r"^\s*\d+\.\s*", "", name.strip())) for num, name in raw_entries}

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
            main_person = clean_name(main.group(1))
            return [[main_person, "spouse of", clean_name(spouse.strip())] for spouse in spouses]
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

# Debug function
async def build_tree_from_template_streaming(title: str, websocket_manager: Optional[WebSocketManager] = None):
    """Debug function to display relationships sent one by one."""
    try:
        print(f"Building tree for {title} with streaming...")
        relationships = await extract_relationships_from_page_streaming(title, websocket_manager)
        print(f"Total relationships found: {len(relationships)}")
        return relationships
    except Exception as e:
        print(f"Error in build_tree_from_template_streaming: {e}")
        return []

# Test the function
if __name__ == "__main__":
    async def test():
        relationships = await extract_relationships_from_page_streaming("Elizabeth II")
        print(f"Found {len(relationships)} relationships")
        for rel in relationships:
            print(f"[{rel[0]}, {rel[1]}, {rel[2]}]")
    
    asyncio.run(test())