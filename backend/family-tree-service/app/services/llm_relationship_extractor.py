# from typing import List, Dict, Optional, Tuple
# import google.generativeai as genai
# import wikipediaapi
# import numpy as np
# import time
# from app.core.config import settings

# GEMINI_API_KEY = "AIzaSyD4Sq2OL6nIMFUlZJafr_IV2uUbTASs7s0"

# # Configure Gemini
# genai.configure(api_key=GEMINI_API_KEY)

# class LLMRelationshipExtractor:
#     def __init__(self):
#         self.wiki = wikipediaapi.Wikipedia(
#             language="en",
#             user_agent="GenealogyApp/1.0"
#         )
    
#     async def extract_relationships_for_person(
#         self, 
#         person_name: str,
#         qid: Optional[str] = None
#     ) -> Dict[str, List[Tuple[str, str]]]:
#         """
#         Extract relationships using LLM when Wikidata is incomplete.
#         Returns: {
#             "child_of": [(person, parent), ...],
#             "spouse_of": [(person, spouse), ...],
#             "adopted_by": [(person, adopter), ...]
#         }
#         """
#         # Step 1: Get Wikipedia text
#         wiki_text = await self._get_wikipedia_text(person_name)
#         if not wiki_text:
#             return {"child_of": [], "spouse_of": [], "adopted_by": []}
        
#         # Step 2: Chunk and find relevant sections
#         chunks = self._chunk_text(wiki_text, max_size=2000)
#         relevant_chunks = await self._find_relevant_chunks(chunks, top_k=3)
#         combined_text = "\n\n".join(relevant_chunks)
        
#         # Step 3: Extract with Gemini
#         relationships = await self._extract_with_gemini(person_name, combined_text)
        
#         return relationships
    
#     async def _get_wikipedia_text(self, name: str) -> str:
#         """Fetch Wikipedia page focusing on family sections"""
#         try:
#             page = self.wiki.page(name)
#             if not page.exists():
#                 return ""
            
#             family_keywords = [
#                 "personal life", "family", "marriage", "children", 
#                 "early life", "biography", "relationships", "spouse"
#             ]
            
#             relevant_text = page.summary + "\n\n"
            
#             def collect_sections(sections):
#                 text = ""
#                 for section in sections:
#                     title_lower = (section.title or "").lower()
#                     if any(kw in title_lower for kw in family_keywords):
#                         text += f"\n{section.title}:\n{section.text}\n"
#                     text += collect_sections(section.sections)
#                 return text
            
#             relevant_text += collect_sections(page.sections)
            
#             # Fallback to full text if no specific sections found
#             if len(relevant_text) < 500:
#                 relevant_text = page.text[:10000]
            
#             return relevant_text
            
#         except Exception as e:
#             print(f"Error fetching Wikipedia for {name}: {e}")
#             return ""
    
#     def _chunk_text(self, text: str, max_size: int = 2000) -> List[str]:
#         """Split text into chunks"""
#         paragraphs = text.split('\n\n')
#         chunks = []
#         current = ""
        
#         for para in paragraphs:
#             if len(current) + len(para) > max_size and current:
#                 chunks.append(current.strip())
#                 current = para
#             else:
#                 current += "\n\n" + para if current else para
        
#         if current.strip():
#             chunks.append(current.strip())
        
#         return chunks
    
#     async def _find_relevant_chunks(
#         self, 
#         chunks: List[str], 
#         top_k: int = 3
#     ) -> List[str]:
#         """Find most relevant chunks using embeddings"""
#         if not chunks:
#             return []
        
#         try:
#             query = """family relationships marriage spouse children parents 
#                       father mother married wife husband son daughter adopted adoption"""
            
#             # Get query embedding
#             query_emb = np.array(genai.embed_content(
#                 model="models/text-embedding-004",
#                 content=query
#             )["embedding"])
            
#             chunk_scores = []
#             for i, chunk in enumerate(chunks):
#                 try:
#                     chunk_emb = np.array(genai.embed_content(
#                         model="models/text-embedding-004",
#                         content=chunk
#                     )["embedding"])
                    
#                     # Cosine similarity
#                     similarity = np.dot(query_emb, chunk_emb) / (
#                         np.linalg.norm(query_emb) * np.linalg.norm(chunk_emb)
#                     )
#                     chunk_scores.append((chunk, similarity, i))
#                     time.sleep(0.5)  # Rate limiting
                    
#                 except Exception as e:
#                     print(f"Embedding error for chunk {i}: {e}")
#                     chunk_scores.append((chunk, 0, i))
            
#             chunk_scores.sort(key=lambda x: x[1], reverse=True)
#             return [chunk for chunk, _, _ in chunk_scores[:top_k]]
            
#         except Exception as e:
#             print(f"Embedding search failed: {e}, falling back to keyword matching")
#             # Fallback: keyword matching
#             scored = []
#             keywords = ["married", "wife", "husband", "spouse", "son", "daughter",
#                        "children", "parents", "father", "mother"]
#             for i, chunk in enumerate(chunks):
#                 score = sum(1 for kw in keywords if kw.lower() in chunk.lower())
#                 scored.append((chunk, score, i))
#             scored.sort(key=lambda x: x[1], reverse=True)
#             return [chunk for chunk, _, _ in scored[:top_k]]
    
#     async def _extract_with_gemini(
#         self, 
#         subject: str, 
#         text: str
#     ) -> Dict[str, List[Tuple[str, str]]]:
#         """Extract relationships using Gemini"""
#         prompt = f"""Extract ALL family relationships for {subject} from the text below.

# CRITICAL RULES:

# 1. Always use the SUBJECT NAME exactly as provided: "{subject}"
# 2. For other people, use their MOST COMMON/POPULAR name
# 3. Format each relationship as one of:
#    - "{subject} child of [Parent]" (when {subject} is someone's child)
#    - "[Child] child of {subject}" (when {subject} is someone's parent)
#    - "{subject} spouse of [Spouse]" (for marriages)
#    - "{subject} adopted by [Adopter]" (for adoptions)
# 4. Extract relationships for {subject} ONLY


# TEXT:
# {text}

# Return ONLY the relationship statements, one per line, in the exact format shown above.
# Example output format:
# {subject} child of John Doe
# Alice Doe child of {subject}
# {subject} spouse of Jane Smith
# {subject} adopted by Robert Johnson
# """
        
#         try:
#             model = genai.GenerativeModel('gemini-2.0-flash-exp')
#             response = model.generate_content(prompt)
#             raw_text = response.text.strip()
            
#             # Parse relationships
#             result = {
#                 "child_of": [],
#                 "spouse_of": [],
#                 "adopted_by": []
#             }
            
#             for line in raw_text.split('\n'):
#                 line = line.strip()
#                 # Remove bullets/numbers
#                 line = line.lstrip('•-*0123456789. ')
    
#                 if " child of " in line.lower():
#                     parts = line.split(" child of ", 1)
#                     if len(parts) == 2:
#                         child = parts[0].strip()
#                         parent = parts[1].strip()
#                         result["child_of"].append((child, parent))
    
#                 elif " spouse of " in line.lower():
#                     parts = line.split(" spouse of ", 1)
#                     if len(parts) == 2:
#                         result["spouse_of"].append((parts[0].strip(), parts[1].strip()))
    
#                 elif " adopted by " in line.lower():
#                     parts = line.split(" adopted by ", 1)
#                     if len(parts) == 2:
#                         result["adopted_by"].append((parts[0].strip(), parts[1].strip()))
            
#             return result
            
#         except Exception as e:
#             print(f"Gemini error: {e}")
#             return {"child_of": [], "spouse_of": [], "adopted_by": []}

# second code
# from typing import List, Dict, Optional, Tuple, Set
# import google.generativeai as genai
# import wikipediaapi
# import numpy as np
# import time
# from difflib import SequenceMatcher
# from app.core.config import settings

# GEMINI_API_KEY = "AIzaSyD4Sq2OL6nIMFUlZJafr_IV2uUbTASs7s0"

# # Configure Gemini
# genai.configure(api_key=GEMINI_API_KEY)

# class LLMRelationshipExtractor:
#     def __init__(self):
#         self.wiki = wikipediaapi.Wikipedia(
#             language="en",
#             user_agent="GenealogyApp/1.0"
#         )
    
#     def _calculate_name_similarity(self, name1: str, name2: str) -> float:
#         """Calculate similarity between two names (0-1 scale)."""
#         # Normalize names: lowercase, remove extra spaces
#         n1 = " ".join(name1.lower().split())
#         n2 = " ".join(name2.lower().split())
        
#         # Use SequenceMatcher for fuzzy matching
#         return SequenceMatcher(None, n1, n2).ratio()
    
#     def _is_duplicate_entity(
#         self, 
#         name: str, 
#         existing_entities: Set[str], 
#         threshold: float = 0.85  # INCREASED from 0.80
#     ) -> bool:
#         """
#         Check if a name is too similar to existing entities.
#         Uses stricter matching to avoid false positives.
#         """
#         name_normalized = " ".join(name.lower().split())
        
#         for existing in existing_entities:
#             existing_normalized = " ".join(existing.lower().split())
            
#             # Exact match (case-insensitive)
#             if name_normalized == existing_normalized:
#                 print(f"🔴 Exact duplicate: '{name}' == '{existing}'")
#                 return True
            
#             # Check if one name is a substring of the other (likely same person)
#             # Example: "Doris Schweitzer" vs "Doris Aude Ascher Schweitzer"
#             if name_normalized in existing_normalized or existing_normalized in name_normalized:
#                 similarity = self._calculate_name_similarity(name, existing)
#                 if similarity >= 0.70:  # If substring and >70% similar
#                     print(f"🟡 Substring duplicate: '{name}' overlaps '{existing}' ({similarity:.2%})")
#                     return True
            
#             # Fuzzy match with STRICTER threshold
#             similarity = self._calculate_name_similarity(name, existing)
#             if similarity >= threshold:
#                 print(f"🟠 Fuzzy duplicate: '{name}' is {similarity:.2%} similar to '{existing}'")
#                 return True
        
#         return False
    
#     async def extract_relationships_for_person(
#         self, 
#         person_name: str,
#         qid: Optional[str] = None,
#         existing_entities: Optional[Set[str]] = None
#     ) -> Dict[str, List[Tuple[str, str]]]:
#         """
#         Extract relationships using LLM when Wikidata is incomplete.
        
#         Args:
#             person_name: Name of the person to extract relationships for
#             qid: Optional Wikidata QID
#             existing_entities: Set of entity names already in the tree
        
#         Returns: {
#             "child_of": [(person, parent), ...],
#             "spouse_of": [(person, spouse), ...],
#             "adopted_by": [(person, adopter), ...]
#         }
#         """
#         if existing_entities is None:
#             existing_entities = set()
        
#         print(f"\n🔍 LLM extraction for: {person_name}")
#         print(f"📋 Existing entities count: {len(existing_entities)}")
        
#         # Step 1: Get Wikipedia text
#         wiki_text = await self._get_wikipedia_text(person_name)
#         if not wiki_text:
#             print(f"⚠️  No Wikipedia text found for {person_name}")
#             return {"child_of": [], "spouse_of": [], "adopted_by": []}
        
#         # Step 2: Chunk and find relevant sections
#         chunks = self._chunk_text(wiki_text, max_size=2000)
#         relevant_chunks = await self._find_relevant_chunks(chunks, top_k=3)
#         combined_text = "\n\n".join(relevant_chunks)
        
#         # Step 3: Extract with Gemini (pass existing entities)
#         relationships = await self._extract_with_gemini(
#             person_name, 
#             combined_text, 
#             existing_entities
#         )
        
#         print(f"🤖 LLM raw extraction: {len(relationships['child_of'])} children, {len(relationships['spouse_of'])} spouses, {len(relationships['adopted_by'])} adoptions")
        
#         # Step 4: Filter out duplicates
#         filtered_relationships = self._filter_duplicate_relationships(
#             relationships, 
#             existing_entities,
#             person_name  # Pass subject name to preserve it
#         )
        
#         print(f"✅ After filtering: {len(filtered_relationships['child_of'])} children, {len(filtered_relationships['spouse_of'])} spouses, {len(filtered_relationships['adopted_by'])} adoptions")
        
#         return filtered_relationships
    
#     def _filter_duplicate_relationships(
#         self,
#         relationships: Dict[str, List[Tuple[str, str]]],
#         existing_entities: Set[str],
#         subject_name: str
#     ) -> Dict[str, List[Tuple[str, str]]]:
#         """
#         Remove relationships involving duplicate entities.
#         IMPORTANT: Never filter the subject person themselves.
#         """
#         filtered = {
#             "child_of": [],
#             "spouse_of": [],
#             "adopted_by": []
#         }
        
#         for rel_type, tuples in relationships.items():
#             for entity1, entity2 in tuples:
#                 # NEVER filter the subject person
#                 entity1_is_subject = entity1.lower().strip() == subject_name.lower().strip()
#                 entity2_is_subject = entity2.lower().strip() == subject_name.lower().strip()
                
#                 # Check entity1 (but skip if it's the subject)
#                 if not entity1_is_subject and self._is_duplicate_entity(entity1, existing_entities):
#                     print(f"🚫 Skipping: {entity1} ({rel_type}) - duplicate of existing entity")
#                     continue
                
#                 # Check entity2 (but skip if it's the subject)
#                 if not entity2_is_subject and self._is_duplicate_entity(entity2, existing_entities):
#                     print(f"🚫 Skipping: {entity2} ({rel_type}) - duplicate of existing entity")
#                     continue
                
#                 # Keep this relationship
#                 filtered[rel_type].append((entity1, entity2))
#                 print(f"✅ Keeping: {entity1} {rel_type} {entity2}")
        
#         return filtered
    
#     async def _get_wikipedia_text(self, name: str) -> str:
#         """Fetch Wikipedia page focusing on family sections"""
#         try:
#             page = self.wiki.page(name)
#             if not page.exists():
#                 return ""
            
#             family_keywords = [
#                 "personal life", "family", "marriage", "children", 
#                 "early life", "biography", "relationships", "spouse"
#             ]
            
#             relevant_text = page.summary + "\n\n"
            
#             def collect_sections(sections):
#                 text = ""
#                 for section in sections:
#                     title_lower = (section.title or "").lower()
#                     if any(kw in title_lower for kw in family_keywords):
#                         text += f"\n{section.title}:\n{section.text}\n"
#                     text += collect_sections(section.sections)
#                 return text
            
#             relevant_text += collect_sections(page.sections)
            
#             # Fallback to full text if no specific sections found
#             if len(relevant_text) < 500:
#                 relevant_text = page.text[:10000]
            
#             return relevant_text
            
#         except Exception as e:
#             print(f"Error fetching Wikipedia for {name}: {e}")
#             return ""
    
#     def _chunk_text(self, text: str, max_size: int = 2000) -> List[str]:
#         """Split text into chunks"""
#         paragraphs = text.split('\n\n')
#         chunks = []
#         current = ""
        
#         for para in paragraphs:
#             if len(current) + len(para) > max_size and current:
#                 chunks.append(current.strip())
#                 current = para
#             else:
#                 current += "\n\n" + para if current else para
        
#         if current.strip():
#             chunks.append(current.strip())
        
#         return chunks
    
#     async def _find_relevant_chunks(
#         self, 
#         chunks: List[str], 
#         top_k: int = 3
#     ) -> List[str]:
#         """Find most relevant chunks using embeddings"""
#         if not chunks:
#             return []
        
#         try:
#             query = """family relationships marriage spouse children parents 
#                       father mother married wife husband son daughter adopted adoption"""
            
#             # Get query embedding
#             query_emb = np.array(genai.embed_content(
#                 model="models/text-embedding-004",
#                 content=query
#             )["embedding"])
            
#             chunk_scores = []
#             for i, chunk in enumerate(chunks):
#                 try:
#                     chunk_emb = np.array(genai.embed_content(
#                         model="models/text-embedding-004",
#                         content=chunk
#                     )["embedding"])
                    
#                     # Cosine similarity
#                     similarity = np.dot(query_emb, chunk_emb) / (
#                         np.linalg.norm(query_emb) * np.linalg.norm(chunk_emb)
#                     )
#                     chunk_scores.append((chunk, similarity, i))
#                     time.sleep(0.5)  # Rate limiting
                    
#                 except Exception as e:
#                     print(f"Embedding error for chunk {i}: {e}")
#                     chunk_scores.append((chunk, 0, i))
            
#             chunk_scores.sort(key=lambda x: x[1], reverse=True)
#             return [chunk for chunk, _, _ in chunk_scores[:top_k]]
            
#         except Exception as e:
#             print(f"Embedding search failed: {e}, falling back to keyword matching")
#             # Fallback: keyword matching
#             scored = []
#             keywords = ["married", "wife", "husband", "spouse", "son", "daughter",
#                        "children", "parents", "father", "mother"]
#             for i, chunk in enumerate(chunks):
#                 score = sum(1 for kw in keywords if kw.lower() in chunk.lower())
#                 scored.append((chunk, score, i))
#             scored.sort(key=lambda x: x[1], reverse=True)
#             return [chunk for chunk, _, _ in scored[:top_k]]
    
#     async def _extract_with_gemini(
#         self, 
#         subject: str, 
#         text: str,
#         existing_entities: Set[str]
#     ) -> Dict[str, List[Tuple[str, str]]]:
#         """Extract relationships using Gemini"""
        
#         # Format existing entities for the prompt
#         existing_list = "\n".join(f"- {name}" for name in sorted(existing_entities))
        
#         prompt = f"""Extract ALL family relationships for {subject} from the text below.

# CRITICAL RULES:

# 1. Always use the SUBJECT NAME exactly as provided: "{subject}"
# 2. For other people, use their MOST COMMON/POPULAR name as it appears in the text
# 3. Format each relationship as one of:
#    - "{subject} child of [Parent]" (when {subject} is someone's child)
#    - "[Child] child of {subject}" (when {subject} is someone's parent)
#    - "{subject} spouse of [Spouse]" (for marriages)
#    - "{subject} adopted by [Adopter]" (for adoptions)
# 4. Extract relationships for {subject} ONLY

# **DUPLICATE DETECTION - READ CAREFULLY:**
# The following people are ALREADY in the family tree:
# {existing_list if existing_list else "None - this is the first extraction"}

# Guidelines for handling duplicates:
# - If someone appears EXACTLY as listed above, skip them
# - If someone is CLEARLY the same person (e.g., "Fanny Koch" and "Fanny Einstein" refer to the same woman with different surnames), skip them
# - However, if you find relationships with people NOT in the list above, INCLUDE them
# - Example: If "Hans Albert Einstein" is in the list, but "Frieda Einstein" (his sister) is NOT, then include "Frieda Einstein"

# **IMPORTANT**: Don't be too cautious - if someone is clearly NOT in the existing list, include them even if their name is similar.

# TEXT:
# {text}

# Return ONLY the relationship statements, one per line, in the exact format shown above.
# Example output:
# {subject} child of John Doe
# Alice Smith child of {subject}
# {subject} spouse of Jane Johnson
# """
        
#         try:
#             model = genai.GenerativeModel('gemini-2.0-flash-exp')
#             response = model.generate_content(prompt)
#             raw_text = response.text.strip()
            
#             print(f"\n🤖 LLM Raw Response:\n{raw_text}\n")
            
#             # Parse relationships
#             result = {
#                 "child_of": [],
#                 "spouse_of": [],
#                 "adopted_by": []
#             }
            
#             for line in raw_text.split('\n'):
#                 line = line.strip()
#                 if not line:
#                     continue
                    
#                 # Remove bullets/numbers
#                 line = line.lstrip('•-*0123456789. ')
    
#                 if " child of " in line.lower():
#                     parts = line.split(" child of ", 1)
#                     if len(parts) == 2:
#                         child = parts[0].strip()
#                         parent = parts[1].strip()
#                         result["child_of"].append((child, parent))
    
#                 elif " spouse of " in line.lower():
#                     parts = line.split(" spouse of ", 1)
#                     if len(parts) == 2:
#                         result["spouse_of"].append((parts[0].strip(), parts[1].strip()))
    
#                 elif " adopted by " in line.lower():
#                     parts = line.split(" adopted by ", 1)
#                     if len(parts) == 2:
#                         result["adopted_by"].append((parts[0].strip(), parts[1].strip()))
            
#             return result
            
#         except Exception as e:
#             print(f"Gemini error: {e}")
#             return {"child_of": [], "spouse_of": [], "adopted_by": []}

from typing import List, Dict, Optional, Tuple, Set
import google.generativeai as genai
import wikipediaapi
import numpy as np
import time
from difflib import SequenceMatcher
from app.core.config import settings

GEMINI_API_KEY = "AIzaSyD4Sq2OL6nIMFUlZJafr_IV2uUbTASs7s0"

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

class LLMRelationshipExtractor:
    def __init__(self):
        self.wiki = wikipediaapi.Wikipedia(
            language="en",
            user_agent="GenealogyApp/1.0"
        )
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (0-1 scale)."""
        # Normalize names: lowercase, remove extra spaces
        n1 = " ".join(name1.lower().split())
        n2 = " ".join(name2.lower().split())
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, n1, n2).ratio()
    
    def _is_duplicate_entity(
        self, 
        name: str, 
        existing_entities: Set[str], 
        threshold: float = 0.85  # INCREASED from 0.80
    ) -> bool:
        """
        Check if a name is too similar to existing entities.
        Uses stricter matching to avoid false positives.
        """
        name_normalized = " ".join(name.lower().split())
        
        for existing in existing_entities:
            existing_normalized = " ".join(existing.lower().split())
            
            # Exact match (case-insensitive)
            if name_normalized == existing_normalized:
                print(f"🔴 Exact duplicate: '{name}' == '{existing}'")
                return True
            
            # Check if one name is a substring of the other (likely same person)
            # Example: "Doris Schweitzer" vs "Doris Aude Ascher Schweitzer"
            if name_normalized in existing_normalized or existing_normalized in name_normalized:
                similarity = self._calculate_name_similarity(name, existing)
                if similarity >= 0.70:  # If substring and >70% similar
                    print(f"🟡 Substring duplicate: '{name}' overlaps '{existing}' ({similarity:.2%})")
                    return True
            
            # Fuzzy match with STRICTER threshold
            similarity = self._calculate_name_similarity(name, existing)
            if similarity >= threshold:
                print(f"🟠 Fuzzy duplicate: '{name}' is {similarity:.2%} similar to '{existing}'")
                return True
        
        return False
    
    async def extract_relationships_for_person(
        self, 
        person_name: str,
        qid: Optional[str] = None,
        existing_entities: Optional[Set[str]] = None
    ) -> Dict[str, List[Tuple[str, str]]]:
        """
        Extract relationships using LLM when Wikidata is incomplete.
        
        Args:
            person_name: Name of the person to extract relationships for
            qid: Optional Wikidata QID
            existing_entities: Set of entity names already in the tree
        
        Returns: {
            "child_of": [(person, parent), ...],
            "spouse_of": [(person, spouse), ...],
            "adopted_by": [(person, adopter), ...]
        }
        """
        if existing_entities is None:
            existing_entities = set()
        
        print(f"\n🔍 LLM extraction for: {person_name}")
        print(f"📋 Existing entities count: {len(existing_entities)}")
        
        # Step 1: Get Wikipedia text
        wiki_text = await self._get_wikipedia_text(person_name)
        if not wiki_text:
            print(f"⚠️  No Wikipedia text found for {person_name}")
            return {"child_of": [], "spouse_of": [], "adopted_by": []}
        
        # Step 2: Chunk and find relevant sections
        chunks = self._chunk_text(wiki_text, max_size=2000)
        relevant_chunks = await self._find_relevant_chunks(chunks, top_k=3)
        combined_text = "\n\n".join(relevant_chunks)
        
        # Step 3: Extract with Gemini (pass existing entities)
        relationships = await self._extract_with_gemini(
            person_name, 
            combined_text, 
            existing_entities
        )
        
        print(f"🤖 LLM raw extraction: {len(relationships['child_of'])} children, {len(relationships['spouse_of'])} spouses, {len(relationships['adopted_by'])} adoptions")
        
        # Step 4: Filter out duplicates
        filtered_relationships = self._filter_duplicate_relationships(
            relationships, 
            existing_entities,
            person_name  # Pass subject name to preserve it
        )
        
        print(f"✅ After filtering: {len(filtered_relationships['child_of'])} children, {len(filtered_relationships['spouse_of'])} spouses, {len(filtered_relationships['adopted_by'])} adoptions")
        
        return filtered_relationships
    
    def _filter_duplicate_relationships(
        self,
        relationships: Dict[str, List[Tuple[str, str]]],
        existing_entities: Set[str],
        subject_name: str
    ) -> Dict[str, List[Tuple[str, str]]]:
        """
        Remove relationships involving duplicate entities.
        IMPORTANT: 
        - Never filter the subject person themselves
        - Allow child_of relationships even if child already exists (to connect children to new spouse)
        """
        filtered = {
            "child_of": [],
            "spouse_of": [],
            "adopted_by": []
        }
        
        for rel_type, tuples in relationships.items():
            for entity1, entity2 in tuples:
                # NEVER filter the subject person
                entity1_is_subject = entity1.lower().strip() == subject_name.lower().strip()
                entity2_is_subject = entity2.lower().strip() == subject_name.lower().strip()
                
                # SPECIAL CASE: For child_of relationships, allow if child exists but we're adding new parent
                # This handles: "Thomas child of Doris" where Thomas already exists
                if rel_type == "child_of":
                    # Check if child (entity1) exists and parent (entity2) is new
                    child_exists = entity1 in existing_entities or self._is_duplicate_entity(entity1, existing_entities)
                    parent_is_new = entity2 not in existing_entities and not self._is_duplicate_entity(entity2, existing_entities)
                    parent_is_subject = entity2_is_subject
                    
                    # Allow if: child exists + (parent is new OR parent is subject)
                    if child_exists and (parent_is_new or parent_is_subject):
                        filtered[rel_type].append((entity1, entity2))
                        print(f"✅ Keeping (connecting existing child to new parent): {entity1} {rel_type} {entity2}")
                        continue
                
                # Check entity1 (but skip if it's the subject)
                if not entity1_is_subject and self._is_duplicate_entity(entity1, existing_entities):
                    # Don't skip if this is a child_of and we're connecting to a new parent (already handled above)
                    if rel_type != "child_of":
                        print(f"🚫 Skipping: {entity1} ({rel_type}) - duplicate of existing entity")
                        continue
                
                # Check entity2 (but skip if it's the subject)
                if not entity2_is_subject and self._is_duplicate_entity(entity2, existing_entities):
                    print(f"🚫 Skipping: {entity2} ({rel_type}) - duplicate of existing entity")
                    continue
                
                # Keep this relationship
                filtered[rel_type].append((entity1, entity2))
                print(f"✅ Keeping: {entity1} {rel_type} {entity2}")
        
        return filtered
    
    async def _get_wikipedia_text(self, name: str) -> str:
        """Fetch Wikipedia page focusing on family sections"""
        try:
            page = self.wiki.page(name)
            if not page.exists():
                return ""
            
            family_keywords = [
                "personal life", "family", "marriage", "children", 
                "early life", "biography", "relationships", "spouse"
            ]
            
            relevant_text = page.summary + "\n\n"
            
            def collect_sections(sections):
                text = ""
                for section in sections:
                    title_lower = (section.title or "").lower()
                    if any(kw in title_lower for kw in family_keywords):
                        text += f"\n{section.title}:\n{section.text}\n"
                    text += collect_sections(section.sections)
                return text
            
            relevant_text += collect_sections(page.sections)
            
            # Fallback to full text if no specific sections found
            if len(relevant_text) < 500:
                relevant_text = page.text[:10000]
            
            return relevant_text
            
        except Exception as e:
            print(f"Error fetching Wikipedia for {name}: {e}")
            return ""
    
    def _chunk_text(self, text: str, max_size: int = 2000) -> List[str]:
        """Split text into chunks"""
        paragraphs = text.split('\n\n')
        chunks = []
        current = ""
        
        for para in paragraphs:
            if len(current) + len(para) > max_size and current:
                chunks.append(current.strip())
                current = para
            else:
                current += "\n\n" + para if current else para
        
        if current.strip():
            chunks.append(current.strip())
        
        return chunks
    
    async def _find_relevant_chunks(
        self, 
        chunks: List[str], 
        top_k: int = 3
    ) -> List[str]:
        """Find most relevant chunks using embeddings"""
        if not chunks:
            return []
        
        try:
            query = """family relationships marriage spouse children parents 
                      father mother married wife husband son daughter adopted adoption"""
            
            # Get query embedding
            query_emb = np.array(genai.embed_content(
                model="models/text-embedding-004",
                content=query
            )["embedding"])
            
            chunk_scores = []
            for i, chunk in enumerate(chunks):
                try:
                    chunk_emb = np.array(genai.embed_content(
                        model="models/text-embedding-004",
                        content=chunk
                    )["embedding"])
                    
                    # Cosine similarity
                    similarity = np.dot(query_emb, chunk_emb) / (
                        np.linalg.norm(query_emb) * np.linalg.norm(chunk_emb)
                    )
                    chunk_scores.append((chunk, similarity, i))
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    print(f"Embedding error for chunk {i}: {e}")
                    chunk_scores.append((chunk, 0, i))
            
            chunk_scores.sort(key=lambda x: x[1], reverse=True)
            return [chunk for chunk, _, _ in chunk_scores[:top_k]]
            
        except Exception as e:
            print(f"Embedding search failed: {e}, falling back to keyword matching")
            # Fallback: keyword matching
            scored = []
            keywords = ["married", "wife", "husband", "spouse", "son", "daughter",
                       "children", "parents", "father", "mother"]
            for i, chunk in enumerate(chunks):
                score = sum(1 for kw in keywords if kw.lower() in chunk.lower())
                scored.append((chunk, score, i))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [chunk for chunk, _, _ in scored[:top_k]]
    
    async def _extract_with_gemini(
        self, 
        subject: str, 
        text: str,
        existing_entities: Set[str]
    ) -> Dict[str, List[Tuple[str, str]]]:
        """Extract relationships using Gemini"""
        
        # Format existing entities for the prompt
        existing_list = "\n".join(f"- {name}" for name in sorted(existing_entities))
        
        prompt = f"""Extract ALL family relationships for {subject} from the text below.

CRITICAL RULES:

1. Always use the SUBJECT NAME exactly as provided: "{subject}"
2. For other people, use their MOST COMMON/POPULAR name as it appears in the text
3. Format each relationship as one of:
   - "{subject} child of [Parent]" (when {subject} is someone's child)
   - "[Child] child of {subject}" (when {subject} is someone's parent)
   - "{subject} spouse of [Spouse]" (for marriages)
   - "{subject} adopted by [Adopter]" (for adoptions)
4. If you identify the spouse of the subject then search for children of that spouse and format those relationships as well like below
   - "[Child] child of [spouse]" (when spouse is someone's parent)

**DUPLICATE DETECTION - READ CAREFULLY:**
The following people are ALREADY in the family tree:
{existing_list if existing_list else "None - this is the first extraction"}

Guidelines for handling duplicates:
- If someone appears EXACTLY as listed above, skip them
- If someone is CLEARLY the same person (e.g., "Fanny Koch" and "Fanny Einstein" refer to the same woman with different surnames), skip them
- However, if you find relationships with people NOT in the list above, INCLUDE them
- Example: If "Hans Albert Einstein" is in the list, but "Frieda Einstein" (his sister) is NOT, then include "Frieda Einstein"

**IMPORTANT**: Don't be too cautious - if someone is clearly NOT in the existing list, include them even if their name is similar.

TEXT:
{text}

Return ONLY the relationship statements, one per line, in the exact format shown above.
Example output:
{subject} child of John Doe
Alice Smith child of {subject}
{subject} spouse of Jane Johnson
"""
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            print(f"\n🤖 LLM Raw Response:\n{raw_text}\n")
            
            # Parse relationships
            result = {
                "child_of": [],
                "spouse_of": [],
                "adopted_by": []
            }
            
            for line in raw_text.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Remove bullets/numbers
                line = line.lstrip('•-*0123456789. ')
    
                if " child of " in line.lower():
                    parts = line.split(" child of ", 1)
                    if len(parts) == 2:
                        child = parts[0].strip()
                        parent = parts[1].strip()
                        result["child_of"].append((child, parent))
    
                elif " spouse of " in line.lower():
                    parts = line.split(" spouse of ", 1)
                    if len(parts) == 2:
                        result["spouse_of"].append((parts[0].strip(), parts[1].strip()))
    
                elif " adopted by " in line.lower():
                    parts = line.split(" adopted by ", 1)
                    if len(parts) == 2:
                        result["adopted_by"].append((parts[0].strip(), parts[1].strip()))
            
            return result
            
        except Exception as e:
            print(f"Gemini error: {e}")
            return {"child_of": [], "spouse_of": [], "adopted_by": []}