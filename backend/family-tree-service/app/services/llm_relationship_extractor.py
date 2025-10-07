from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
import wikipediaapi
import numpy as np
import time
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
    
    async def extract_relationships_for_person(
        self, 
        person_name: str,
        qid: Optional[str] = None
    ) -> Dict[str, List[Tuple[str, str]]]:
        """
        Extract relationships using LLM when Wikidata is incomplete.
        Returns: {
            "child_of": [(person, parent), ...],
            "spouse_of": [(person, spouse), ...],
            "adopted_by": [(person, adopter), ...]
        }
        """
        # Step 1: Get Wikipedia text
        wiki_text = await self._get_wikipedia_text(person_name)
        if not wiki_text:
            return {"child_of": [], "spouse_of": [], "adopted_by": []}
        
        # Step 2: Chunk and find relevant sections
        chunks = self._chunk_text(wiki_text, max_size=2000)
        relevant_chunks = await self._find_relevant_chunks(chunks, top_k=3)
        combined_text = "\n\n".join(relevant_chunks)
        
        # Step 3: Extract with Gemini
        relationships = await self._extract_with_gemini(person_name, combined_text)
        
        return relationships
    
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
            keywords = ["married", "wife", "husband", "spouse", 
                       "children", "parents", "father", "mother"]
            for i, chunk in enumerate(chunks):
                score = sum(1 for kw in keywords if kw.lower() in chunk.lower())
                scored.append((chunk, score, i))
            scored.sort(key=lambda x: x[1], reverse=True)
            return [chunk for chunk, _, _ in scored[:top_k]]
    
    async def _extract_with_gemini(
        self, 
        subject: str, 
        text: str
    ) -> Dict[str, List[Tuple[str, str]]]:
        """Extract relationships using Gemini"""
        prompt = f"""Extract ALL family relationships for {subject} from the text below.

CRITICAL RULES:
1. Extract ONLY relationships that are EXPLICITLY stated in the text
2. Always use the SUBJECT NAME exactly as provided: "{subject}"
3. For other people, use their MOST COMMON/POPULAR name
4. Format each relationship as one of:
   - "{subject} child of [Parent]" (for biological parents)
   - "{subject} spouse of [Spouse]" (for marriages)
   - "{subject} adopted by [Adopter]" (for adoptions)
5. Extract relationships for {subject} ONLY
6. DO NOT invent or infer relationships not in the text
7. If you cannot find a person's full name, do not include that relationship

TEXT:
{text}

Return ONLY the relationship statements, one per line, in the exact format shown above.
Example output format:
{subject} child of John Doe
{subject} spouse of Jane Smith
{subject} adopted by Robert Johnson
"""
        
        try:
            model = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model.generate_content(prompt)
            raw_text = response.text.strip()
            
            # Parse relationships
            result = {
                "child_of": [],
                "spouse_of": [],
                "adopted_by": []
            }
            
            for line in raw_text.split('\n'):
                line = line.strip()
                # Remove bullets/numbers
                line = line.lstrip('•-*0123456789. ')
                
                if " child of " in line.lower():
                    parts = line.split(" child of ", 1)
                    if len(parts) == 2:
                        result["child_of"].append((parts[0].strip(), parts[1].strip()))
                
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