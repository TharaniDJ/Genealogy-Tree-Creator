import google.generativeai as genai
import json
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import wikipediaapi

# Configure Gemini
GEMINI_API_KEY = "AIzaSyD4Sq2OL6nIMFUlZJafr_IV2uUbTASs7s0"  # Move to environment variable
genai.configure(api_key=GEMINI_API_KEY)

def normalize_name(name: str) -> str:
    """Normalize name for comparison"""
    name = name.lower().strip()
    name = ' '.join(name.split())
    name = name.replace(',', '').replace('.', '')
    if '(' in name:
        name = name.split('(')[0].strip()
    return ' '.join(name.split())

def fetch_article(name: str) -> tuple:
    """Fetch single Wikipedia article"""
    try:
        wiki = wikipediaapi.Wikipedia(language='en', user_agent='GenealogyTree/1.0')
        page = wiki.page(name)
        if page.exists():
            return (name, page.text[:8000])
    except Exception as e:
        print(f"Error fetching article for {name}: {e}")
    return (name, None)

def fetch_articles_parallel(people_list: List[str]) -> Dict[str, str]:
    """Fetch Wikipedia articles in parallel"""
    articles = {}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_article, person): person for person in people_list}
        
        for future in as_completed(futures):
            name, text = future.result()
            if text:
                articles[name] = text
    
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

async def classify_relationships(relationships: List[Dict]) -> List[Dict]:
    """
    Classify parent-child relationships as BIOLOGICAL or ADOPTIVE
    """
    print(f"Starting classification for {len(relationships)} relationships")
    
    # Filter only parent-child relationships
    parent_child_rels = [
        rel for rel in relationships 
        if 'child of' in rel.get('relationship', '').lower()
    ]
    
    if not parent_child_rels:
        print("No parent-child relationships found to classify")
        # Return all relationships with default classification
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
    
    # Fetch Wikipedia articles
    all_articles = fetch_articles_parallel(list(all_people))
    
    print(f"Fetched {len(all_articles)} articles")
    
    # Build relationship list for prompt
    rel_list = [
        f"{i+1}. {rel['entity1']} → {rel['entity2']}" 
        for i, rel in enumerate(parent_child_rels)
    ]
    
    # Build context
    context = build_compact_context(parent_child_rels, all_articles)
    
    prompt = f"""Classify ALL these parent-child relationships as BIOLOGICAL or ADOPTIVE.

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
        print("Calling Gemini API...")
        model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config=genai.GenerationConfig(
                temperature=0.0,
                max_output_tokens=1500
            )
        )
        
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        print(f"Gemini response: {result_text[:200]}...")
        
        # Extract JSON
        json_start = result_text.find('[')
        json_end = result_text.rfind(']') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_str = result_text[json_start:json_end]
            classifications = json.loads(json_str)
            
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