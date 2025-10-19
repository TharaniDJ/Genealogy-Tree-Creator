# import google.generativeai as genai
# import json
# from typing import List, Dict, Optional
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import wikipediaapi

# # Configure Gemini
# GEMINI_API_KEY = ""  # Move to environment variable
# genai.configure(api_key=GEMINI_API_KEY)

# def normalize_name(name: str) -> str:
#     """Normalize name for comparison"""
#     name = name.lower().strip()
#     name = ' '.join(name.split())
#     name = name.replace(',', '').replace('.', '')
#     if '(' in name:
#         name = name.split('(')[0].strip()
#     return ' '.join(name.split())

# def fetch_article(name: str) -> tuple:
#     """Fetch single Wikipedia article"""
#     try:
#         wiki = wikipediaapi.Wikipedia(language='en', user_agent='GenealogyTree/1.0')
#         page = wiki.page(name)
#         if page.exists():
#             return (name, page.text[:8000])
#     except Exception as e:
#         print(f"Error fetching article for {name}: {e}")
#     return (name, None)

# def fetch_articles_parallel(people_list: List[str]) -> Dict[str, str]:
#     """Fetch Wikipedia articles in parallel"""
#     articles = {}
    
#     with ThreadPoolExecutor(max_workers=10) as executor:
#         futures = {executor.submit(fetch_article, person): person for person in people_list}
        
#         for future in as_completed(futures):
#             name, text = future.result()
#             if text:
#                 articles[name] = text
    
#     return articles

# def build_compact_context(relationships: List[Dict], all_articles: Dict[str, str]) -> str:
#     """Build context for classification"""
#     contexts = []
    
#     for i, rel in enumerate(relationships, 1):
#         child = rel['entity1']
#         parent = rel['entity2']
        
#         child_article = all_articles.get(child, "")
#         parent_article = all_articles.get(parent, "")
        
#         snippets = []
        
#         for article, source in [(child_article[:2000], child), (parent_article[:2000], parent)]:
#             if not article:
#                 continue
            
#             sentences = article.split('.')
#             for sent in sentences[:15]:
#                 sent_lower = sent.lower()
#                 has_keyword = any(kw in sent_lower for kw in ['adopt', 'born', 'birth', 'heir', 'son', 'daughter', 'child'])
                
#                 if has_keyword:
#                     snippet = sent.strip()[:200]
#                     snippets.append(snippet)
#                     if len(snippets) >= 2:
#                         break
        
#         context_text = " ".join(snippets[:2]) if snippets else "No specific info found."
#         contexts.append(f"{i}. {child}→{parent}: {context_text[:300]}")
    
#     return "\n".join(contexts)

# async def classify_relationships(relationships: List[Dict]) -> List[Dict]:
#     """
#     Classify parent-child relationships as BIOLOGICAL or ADOPTIVE
#     """
#     print(f"Starting classification for {len(relationships)} relationships")
    
#     # Filter only parent-child relationships
#     parent_child_rels = [
#         rel for rel in relationships 
#         if 'child of' in rel.get('relationship', '').lower()
#     ]
    
#     if not parent_child_rels:
#         print("No parent-child relationships found to classify")
#         # Return all relationships with default classification
#         return [
#             {**rel, "classification": "BIOLOGICAL"}
#             for rel in relationships
#         ]
    
#     print(f"Found {len(parent_child_rels)} parent-child relationships to classify")
    
#     # Get unique people
#     all_people = set()
#     for rel in parent_child_rels:
#         all_people.add(rel['entity1'])
#         all_people.add(rel['entity2'])
    
#     print(f"Fetching Wikipedia articles for {len(all_people)} people...")
    
#     # Fetch Wikipedia articles
#     all_articles = fetch_articles_parallel(list(all_people))
    
#     print(f"Fetched {len(all_articles)} articles")
    
#     # Build relationship list for prompt
#     rel_list = [
#         f"{i+1}. {rel['entity1']} → {rel['entity2']}" 
#         for i, rel in enumerate(parent_child_rels)
#     ]
    
#     # Build context
#     context = build_compact_context(parent_child_rels, all_articles)
    
#     prompt = f"""Classify ALL these parent-child relationships as BIOLOGICAL or ADOPTIVE. Using the CONTEXT. Please note that when you identify that if a child is not a direct biological child of a person, then classify as ADOPTIVE. 
#                 Don't just tell adoptive, you need to be very very sure about the other relationship,like if you see if the person 1 is a grandparent or uncle of the second person,then the relationship can be adoptive.
#                 In the real world many relationships are biological so before saying that they are adoptive you need to be very very sure about that.
#                 If you are unsure, default to BIOLOGICAL.

# RELATIONSHIPS ({len(parent_child_rels)} total):
# {chr(10).join(rel_list)}

# CONTEXT:
# {context}

# RULES:
# - BIOLOGICAL: Born to parent (natural birth)
# - ADOPTIVE: Adopted, heir designation, testament, raised by non-biological parent
# - Keywords: "adopted"→ADOPTIVE, "born to"→BIOLOGICAL
# - DEFAULT: If unclear→BIOLOGICAL

# Respond with JSON array ONLY (no other text):
# [
#   {{"id": 1, "class": "BIOLOGICAL"}},
#   {{"id": 2, "class": "ADOPTIVE"}},
#   ...
# ]"""

#     try:
#         print("Calling Gemini API...")
#         model = genai.GenerativeModel(
#             'gemini-2.0-flash-exp',
#             generation_config=genai.GenerationConfig(
#                 temperature=0.0,
#                 max_output_tokens=1500
#             )
#         )
        
#         response = model.generate_content(prompt)
#         result_text = response.text.strip()
        
#         print(f"Gemini response: {result_text[:200]}...")
        
#         # Extract JSON
#         json_start = result_text.find('[')
#         json_end = result_text.rfind(']') + 1
        
#         if json_start >= 0 and json_end > json_start:
#             json_str = result_text[json_start:json_end]
#             classifications = json.loads(json_str)
            
#             print(f"Parsed {len(classifications)} classifications")
            
#             # Add classifications to relationships
#             for i, rel in enumerate(parent_child_rels):
#                 match = next((c for c in classifications if c.get('id') == i+1), None)
#                 classification = match.get('class', 'BIOLOGICAL').upper() if match else 'BIOLOGICAL'
#                 rel['classification'] = classification
#                 print(f"  {rel['entity1']} → {rel['entity2']}: {classification}")
    
#     except Exception as e:
#         print(f"Classification error: {e}")
#         import traceback
#         traceback.print_exc()
#         # Default to BIOLOGICAL on error
#         for rel in parent_child_rels:
#             rel['classification'] = 'BIOLOGICAL'
    
#     # Return ALL relationships (classified ones have the classification key)
#     result = []
#     for rel in relationships:
#         # Find if this relationship was classified
#         classified = next(
#             (r for r in parent_child_rels 
#              if r['entity1'] == rel['entity1'] and r['entity2'] == rel['entity2']),
#             None
#         )
#         if classified:
#             result.append(classified)
#         else:
#             result.append({**rel, "classification": "BIOLOGICAL"})
    
#     print(f"Returning {len(result)} relationships with classifications")
#     return result
# fifth code attempt
# import google.generativeai as genai
# import os  # ADD THIS
# from dotenv import load_dotenv  # ADD THIS
# import json
# from typing import List, Dict, Optional
# from concurrent.futures import ThreadPoolExecutor, as_completed
# import wikipediaapi

# # Configure Gemini
# load_dotenv()
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# genai.configure(api_key=GEMINI_API_KEY)

# def normalize_name(name: str) -> str:
#     """Normalize name for comparison"""
#     name = name.lower().strip()
#     name = ' '.join(name.split())
#     name = name.replace(',', '').replace('.', '')
#     if '(' in name:
#         name = name.split('(')[0].strip()
#     return ' '.join(name.split())

# def fetch_article(name: str) -> tuple:
#     """Fetch single Wikipedia article"""
#     try:
#         wiki = wikipediaapi.Wikipedia(language='en', user_agent='GenealogyTree/1.0')
#         page = wiki.page(name)
#         if page.exists():
#             return (name, page.text[:8000])
#     except Exception as e:
#         print(f"Error fetching article for {name}: {e}")
#     return (name, None)

# def fetch_articles_parallel(people_list: List[str]) -> Dict[str, str]:
#     """Fetch Wikipedia articles in parallel"""
#     articles = {}
    
#     with ThreadPoolExecutor(max_workers=10) as executor:
#         futures = {executor.submit(fetch_article, person): person for person in people_list}
        
#         for future in as_completed(futures):
#             name, text = future.result()
#             if text:
#                 articles[name] = text
    
#     return articles

# def build_compact_context(relationships: List[Dict], all_articles: Dict[str, str]) -> str:
#     """Build context for classification"""
#     contexts = []
    
#     for i, rel in enumerate(relationships, 1):
#         child = rel['entity1']
#         parent = rel['entity2']
        
#         child_article = all_articles.get(child, "")
#         parent_article = all_articles.get(parent, "")
        
#         snippets = []
        
#         for article, source in [(child_article[:2000], child), (parent_article[:2000], parent)]:
#             if not article:
#                 continue
            
#             sentences = article.split('.')
#             for sent in sentences[:15]:
#                 sent_lower = sent.lower()
#                 has_keyword = any(kw in sent_lower for kw in ['adopt', 'born', 'birth', 'heir', 'son', 'daughter', 'child'])
                
#                 if has_keyword:
#                     snippet = sent.strip()[:200]
#                     snippets.append(snippet)
#                     if len(snippets) >= 2:
#                         break
        
#         context_text = " ".join(snippets[:2]) if snippets else "No specific info found."
#         contexts.append(f"{i}. {child}→{parent}: {context_text[:300]}")
    
#     return "\n".join(contexts)

# async def classify_relationships(relationships: List[Dict]) -> List[Dict]:
#     """
#     Classify parent-child relationships as BIOLOGICAL or ADOPTIVE
#     """
#     print(f"Starting classification for {len(relationships)} relationships")
    
#     # Filter only parent-child relationships
#     parent_child_rels = [
#         rel for rel in relationships 
#         if 'child of' in rel.get('relationship', '').lower()
#     ]
    
#     if not parent_child_rels:
#         print("No parent-child relationships found to classify")
#         # Return all relationships with default classification
#         return [
#             {**rel, "classification": "BIOLOGICAL"}
#             for rel in relationships
#         ]
    
#     print(f"Found {len(parent_child_rels)} parent-child relationships to classify")
    
#     # Get unique people
#     all_people = set()
#     for rel in parent_child_rels:
#         all_people.add(rel['entity1'])
#         all_people.add(rel['entity2'])
    
#     print(f"Fetching Wikipedia articles for {len(all_people)} people...")
    
#     # Fetch Wikipedia articles
#     all_articles = fetch_articles_parallel(list(all_people))
    
#     print(f"Fetched {len(all_articles)} articles")
    
#     # Build relationship list for prompt
#     rel_list = [
#         f"{i+1}. {rel['entity1']} → {rel['entity2']}" 
#         for i, rel in enumerate(parent_child_rels)
#     ]
    
#     # Build context
#     context = build_compact_context(parent_child_rels, all_articles)
    
#     prompt = f"""Classify ALL these parent-child relationships as BIOLOGICAL or ADOPTIVE. Using the CONTEXT. Please note that when you identify that if a child is not a direct biological child of a person, then classify as ADOPTIVE. 
#                 Don't just tell adoptive, you need to be very very sure about the other relationship,like if you see if the person 1 is a grandparent or uncle of the second person,then the relationship can be adoptive.
#                 In the real world many relationships are biological so before saying that they are adoptive you need to be very very sure about that.
#                 If you are unsure, default to BIOLOGICAL.

# RELATIONSHIPS ({len(parent_child_rels)} total):
# {chr(10).join(rel_list)}

# CONTEXT:
# {context}

# RULES:
# - BIOLOGICAL: Born to parent (natural birth)
# - ADOPTIVE: Adopted, heir designation, testament, raised by non-biological parent
# - Keywords: "adopted"→ADOPTIVE, "born to"→BIOLOGICAL
# - DEFAULT: If unclear→BIOLOGICAL

# Respond with JSON array ONLY (no other text):
# [
#   {{"id": 1, "class": "BIOLOGICAL"}},
#   {{"id": 2, "class": "ADOPTIVE"}},
#   ...
# ]"""

#     try:
#         print("Calling Gemini API...")
#         model = genai.GenerativeModel(
#             'gemini-2.0-flash-exp',
#             generation_config=genai.GenerationConfig(
#                 temperature=0.0,
#                 max_output_tokens=1500
#             )
#         )
        
#         response = model.generate_content(prompt)
#         result_text = response.text.strip()
        
#         print(f"Gemini response: {result_text[:200]}...")
        
#         # Extract JSON
#         json_start = result_text.find('[')
#         json_end = result_text.rfind(']') + 1
        
#         if json_start >= 0 and json_end > json_start:
#             json_str = result_text[json_start:json_end]
#             classifications = json.loads(json_str)
            
#             print(f"Parsed {len(classifications)} classifications")
            
#             # Add classifications to relationships
#             for i, rel in enumerate(parent_child_rels):
#                 match = next((c for c in classifications if c.get('id') == i+1), None)
#                 classification = match.get('class', 'BIOLOGICAL').upper() if match else 'BIOLOGICAL'
#                 rel['classification'] = classification
#                 print(f"  {rel['entity1']} → {rel['entity2']}: {classification}")
    
#     except Exception as e:
#         print(f"Classification error: {e}")
#         import traceback
#         traceback.print_exc()
#         # Default to BIOLOGICAL on error
#         for rel in parent_child_rels:
#             rel['classification'] = 'BIOLOGICAL'
    
#     # Return ALL relationships (classified ones have the classification key)
#     result = []
#     for rel in relationships:
#         # Find if this relationship was classified
#         classified = next(
#             (r for r in parent_child_rels 
#              if r['entity1'] == rel['entity1'] and r['entity2'] == rel['entity2']),
#             None
#         )
#         if classified:
#             result.append(classified)
#         else:
#             result.append({**rel, "classification": "BIOLOGICAL"})
    
#     print(f"Returning {len(result)} relationships with classifications")
#     return result

# code
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
import wikipediaapi
import asyncio
from functools import wraps
import time

# Configure Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Model fallback list (in order of preference)
FALLBACK_MODELS = [
    "gemini-2.0-flash-exp",
    "models/gemini-2.5-flash-lite",
    "models/gemini-2.0-flash",
    "models/gemini-2.5-flash-preview-05-20",
    "models/gemini-2.0-flash-lite-001",
    "models/gemini-2.5-pro-preview-06-05",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-flash-preview-09-2025"
]

# Configuration
MAX_TOTAL_TIME = 60  # Maximum 60 seconds for entire classification
MAX_MODEL_TIMEOUT = 15  # Maximum 15 seconds per model attempt
MAX_WIKIPEDIA_TIME = 20  # Maximum 20 seconds for Wikipedia fetching

def timeout_handler(timeout_seconds):
    """Decorator to add timeout to async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                print(f"Function {func.__name__} timed out after {timeout_seconds} seconds")
                raise TimeoutError(f"Operation timed out after {timeout_seconds} seconds")
        return wrapper
    return decorator

def normalize_name(name: str) -> str:
    """Normalize name for comparison"""
    name = name.lower().strip()
    name = ' '.join(name.split())
    name = name.replace(',', '').replace('.', '')
    if '(' in name:
        name = name.split('(')[0].strip()
    return ' '.join(name.split())

def fetch_article(name: str) -> tuple:
    """Fetch single Wikipedia article with timeout"""
    try:
        wiki = wikipediaapi.Wikipedia(language='en', user_agent='GenealogyTree/1.0')
        page = wiki.page(name)
        if page.exists():
            return (name, page.text[:8000])
    except Exception as e:
        print(f"Error fetching article for {name}: {e}")
    return (name, None)

def fetch_articles_parallel(people_list: List[str], max_time: int = MAX_WIKIPEDIA_TIME) -> Dict[str, str]:
    """Fetch Wikipedia articles in parallel with timeout"""
    articles = {}
    start_time = time.time()
    
    try:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(fetch_article, person): person for person in people_list}
            
            for future in as_completed(futures, timeout=max_time):
                # Check if we've exceeded time limit
                if time.time() - start_time > max_time:
                    print(f"Wikipedia fetching exceeded {max_time}s, stopping...")
                    break
                    
                try:
                    name, text = future.result(timeout=5)  # 5s per article
                    if text:
                        articles[name] = text
                except Exception as e:
                    print(f"Error processing article: {e}")
                    continue
    except TimeoutError:
        print(f"Wikipedia fetching timed out after {max_time}s")
    except Exception as e:
        print(f"Error in parallel fetch: {e}")
    
    return articles

def build_compact_context(relationships: List[Dict], all_articles: Dict[str, str]) -> str:
    """Build context for classification"""
    contexts = []
    
    for i, rel in enumerate(relationships, 1):
        child = rel['entity1']
        parent = rel['entity2']
        
        child_article = all_articles.get(child, "")
        parent_article = all_articles.get(parent, "")
        
        snippets = []
        
        for article, source in [(child_article[:2000], child), (parent_article[:2000], parent)]:
            if not article:
                continue
            
            sentences = article.split('.')
            for sent in sentences[:15]:
                sent_lower = sent.lower()
                has_keyword = any(kw in sent_lower for kw in ['adopt', 'born', 'birth', 'heir', 'son', 'daughter', 'child'])
                
                if has_keyword:
                    snippet = sent.strip()[:200]
                    snippets.append(snippet)
                    if len(snippets) >= 2:
                        break
        
        context_text = " ".join(snippets[:2]) if snippets else "No specific info found."
        contexts.append(f"{i}. {child}→{parent}: {context_text[:300]}")
    
    return "\n".join(contexts)

def generate_with_fallback(prompt: str, max_time: int = MAX_MODEL_TIMEOUT) -> str:
    """Try to generate content with model fallback and timeout"""
    last_error = None
    start_time = time.time()
    
    for model_name in FALLBACK_MODELS:
        # Check if we've exceeded total time
        if time.time() - start_time > max_time:
            print(f"Model attempts exceeded {max_time}s timeout")
            break
            
        try:
            print(f"Attempting to use model: {model_name}")
            model = genai.GenerativeModel(
                model_name,
                generation_config=genai.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=2000,
                    response_mime_type="application/json"
                )
            )
            
            response = model.generate_content(prompt)
            
            # Check if response has text
            if not response.text or len(response.text.strip()) == 0:
                print(f"Model {model_name} returned empty response, trying next model")
                continue
                
            print(f"Successfully used model: {model_name}")
            return response.text.strip()
            
        except Exception as e:
            error_msg = str(e)
            print(f"Model {model_name} failed: {error_msg[:200]}")
            last_error = e
            
            # Skip waiting for quota errors
            if "429" not in error_msg and "quota" not in error_msg.lower():
                time.sleep(1)  # Brief pause between attempts
            continue
    
    # If all models fail, raise the last error
    raise Exception(f"All fallback models failed. Last error: {str(last_error)}")

@timeout_handler(MAX_TOTAL_TIME)
async def classify_relationships(relationships: List[Dict]) -> List[Dict]:
    """
    Classify parent-child relationships as BIOLOGICAL or ADOPTIVE with timeout protection
    """
    try:
        print(f"Starting classification for {len(relationships)} relationships (max {MAX_TOTAL_TIME}s)")
        
        # Filter only parent-child relationships
        parent_child_rels = [
            rel for rel in relationships 
            if 'child of' in rel.get('relationship', '').lower()
        ]
        
        if not parent_child_rels:
            print("No parent-child relationships found to classify")
            return [
                {**rel, "classification": "BIOLOGICAL"}
                for rel in relationships
            ]
        
        print(f"Found {len(parent_child_rels)} parent-child relationships to classify")
        
        # Get unique people
        all_people = set()
        for rel in parent_child_rels:
            all_people.add(rel['entity1'])
            all_people.add(rel['entity2'])
        
        print(f"Fetching Wikipedia articles for {len(all_people)} people...")
        
        # Fetch Wikipedia articles with timeout
        all_articles = fetch_articles_parallel(list(all_people))
        
        print(f"Fetched {len(all_articles)} articles")
        
        # Build relationship list for prompt
        rel_list = [
            f"{i+1}. {rel['entity1']} → {rel['entity2']}" 
            for i, rel in enumerate(parent_child_rels)
        ]
        
        # Build context
        context = build_compact_context(parent_child_rels, all_articles)
        
        prompt = f"""Classify ALL these parent-child relationships as BIOLOGICAL or ADOPTIVE. Using the CONTEXT. Please note that when you identify that if a child is not a direct biological child of a person, then classify as ADOPTIVE. 
                    Don't just tell adoptive, you need to be very very sure about the other relationship,like if you see if the person 1 is a grandparent or uncle of the second person,then the relationship can be adoptive.
                    In the real world many relationships are biological so before saying that they are adoptive you need to be very very sure about that adoptive relationship.
                    If you are unsure, default to BIOLOGICAL.

RELATIONSHIPS ({len(parent_child_rels)} total):
{chr(10).join(rel_list)}

CONTEXT:
{context}

RULES:
- BIOLOGICAL: Born to parent (natural birth)
- ADOPTIVE: Adopted, heir designation, testament, raised by non-biological parent
- Keywords: "adopted"→ADOPTIVE, "born to"→BIOLOGICAL
- DEFAULT: If unclear→BIOLOGICAL

Respond with JSON array ONLY (no other text):
[
  {{"id": 1, "class": "BIOLOGICAL"}},
  {{"id": 2, "class": "ADOPTIVE"}},
  ...
]"""

        try:
            print("Calling Gemini API with fallback...")
            result_text = generate_with_fallback(prompt)
            
            print(f"Gemini response: {result_text[:200]}...")
            
            # Clean up response - remove markdown code blocks
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0]
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0]
            
            # Extract JSON
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end].strip()
                
                # Try to fix common JSON issues
                json_str = json_str.replace("'", '"')  # Replace single quotes
                json_str = json_str.replace('\n', ' ')  # Remove newlines
                
                try:
                    classifications = json.loads(json_str)
                except json.JSONDecodeError as je:
                    print(f"JSON parsing error: {je}")
                    print(f"Problematic JSON: {json_str[:500]}...")
                    # Try alternative parsing - look for individual objects
                    import re
                    pattern = r'\{\s*"id"\s*:\s*(\d+)\s*,\s*"class"\s*:\s*"(BIOLOGICAL|ADOPTIVE)"\s*\}'
                    matches = re.findall(pattern, json_str, re.IGNORECASE)
                    if matches:
                        classifications = [{"id": int(m[0]), "class": m[1].upper()} for m in matches]
                        print(f"Recovered {len(classifications)} classifications using regex")
                    else:
                        raise
                
                print(f"Parsed {len(classifications)} classifications")
                
                # Add classifications to relationships
                for i, rel in enumerate(parent_child_rels):
                    match = next((c for c in classifications if c.get('id') == i+1), None)
                    classification = match.get('class', 'BIOLOGICAL').upper() if match else 'BIOLOGICAL'
                    rel['classification'] = classification
                    print(f"  {rel['entity1']} → {rel['entity2']}: {classification}")
        
        except Exception as e:
            print(f"Classification error: {e}")
            import traceback
            traceback.print_exc()
            # Default to BIOLOGICAL on error
            for rel in parent_child_rels:
                rel['classification'] = 'BIOLOGICAL'
        
        # Return ALL relationships (classified ones have the classification key)
        result = []
        for rel in relationships:
            # Find if this relationship was classified
            classified = next(
                (r for r in parent_child_rels 
                 if r['entity1'] == rel['entity1'] and r['entity2'] == rel['entity2']),
                None
            )
            if classified:
                result.append(classified)
            else:
                result.append({**rel, "classification": "BIOLOGICAL"})
        
        print(f"Returning {len(result)} relationships with classifications")
        return result
        
    except TimeoutError as te:
        print(f"TIMEOUT: Classification exceeded maximum time limit: {te}")
        # Return all relationships with default BIOLOGICAL classification
        return [
            {**rel, "classification": "BIOLOGICAL"}
            for rel in relationships
        ]
    except Exception as e:
        print(f"FATAL ERROR in classify_relationships: {e}")
        import traceback
        traceback.print_exc()
        # Always return something to prevent infinite loading
        return [
            {**rel, "classification": "BIOLOGICAL"}
            for rel in relationships
        ]