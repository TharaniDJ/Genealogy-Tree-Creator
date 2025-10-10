import os
import json
import re
from typing import Dict, List, Optional

try:
    import wikipedia
except Exception:  # wikipedia may not be installed in test environments
    wikipedia = None

try:
    import google.generativeai as genai
except Exception:
    genai = None


class GeminiTaxonomyService:
    """Service wrapper around a Gemini analysis for taxonomy extraction.

    This adapts the user's TaxonomyBotWithGemini code for programmatic use in the
    species-tree-service. It is defensive: if dependencies or API key are missing,
    methods return empty/partial results instead of raising during import.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.model_name = model_name
        self.enabled = True

        if genai is None or wikipedia is None:
            # If packages aren't installed, disable the service but don't crash imports
            self.enabled = False
            return

        if not self.api_key:
            # Not fatal here: service can be constructed but will be disabled
            self.enabled = False
            return

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def _get_first_paragraph(self, content: str) -> str:
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            para = para.strip()
            if len(para) > 100 and not para.startswith('==') and not para.startswith('='):
                return para
        return content[:1500]

    def analyze_taxon(self, taxon_name: str, rank_hint: Optional[str] = None) -> Dict:
        """Analyze a taxon name using Wikipedia + Gemini and return a JSON-like dict.

        Returns a dict similar to the user's CLI output. On any internal error or if
        the service is disabled, returns an object with status 'disabled' or 'error'.
        """
        if not self.enabled:
            return {"status": "disabled", "message": "Gemini service not available or not configured"}

        try:
            # Search Wikipedia
            search_results = wikipedia.search(taxon_name, results=5)
            if not search_results:
                return {"status": "error", "message": f'No Wikipedia pages found for "{taxon_name}"'}

            page = None
            for result in search_results:
                try:
                    page = wikipedia.page(result, auto_suggest=False)
                    break
                except wikipedia.DisambiguationError as e:
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                        break
                    except Exception:
                        continue
                except Exception:
                    continue

            if not page:
                return {"status": "error", "message": f'Could not find page for "{taxon_name}"'}

            first_para = self._get_first_paragraph(page.content)

            prompt = f"""You are a taxonomic expert. Analyze this Wikipedia article about \"{page.title}\" and extract taxonomic information.

Wikipedia Content:
{first_para}

Please provide a JSON response with the following structure:
{{
    "taxon_name": "The scientific name of this taxon",
    "rank": "The taxonomic rank (e.g., Kingdom, Phylum, Class, Order, Family, Genus, Species)",
    "direct_children": [
        {{
            "name": "Child taxon name",
            "rank": "Child rank",
            "common_name": "Common name if available or empty string"
        }}
    ],
    "hierarchy": [
        "Domain: name",
        "Kingdom: name",
        "Phylum: name",
        "Class: name",
        "Order: name",
        "Family: name",
        "Genus: name"
    ],
    "child_rank": "What rank are the direct children (e.g., if this is a Class, children are Orders)",
    "summary": "Brief 2-3 sentence description of this taxon"
}}

CRITICAL INSTRUCTIONS:
1. Extract ONLY the DIRECT children of this taxon (one level down in the hierarchy)
2. Include up to 25 direct children if available
3. Only include children explicitly mentioned in the Wikipedia article
4. For hierarchy, include all levels from Domain down to the current taxon
5. Return ONLY valid JSON, no markdown formatting, no code blocks, no additional text
6. Ensure all strings are properly escaped for JSON

Return the JSON now:"""

            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Remove markdown fences if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            elif response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    return {"status": "error", "message": "Could not parse Gemini response as JSON", "raw": response_text}

            # Normalize fields and children to avoid empty values downstream
            result = dict(result)
            result["taxon_name"] = result.get("taxon_name") or page.title
            result["rank"] = result.get("rank") or "Not specified"
            result["child_rank"] = result.get("child_rank") or "Not specified"
            # Normalize direct_children list
            children = result.get("direct_children") or []
            normalized_children = []
            for ch in children:
                if not isinstance(ch, dict):
                    # if child is a simple string, treat as name only
                    name = str(ch)
                    rank = result.get("child_rank") or self.guess_child_rank(result.get("rank"))
                    normalized_children.append({"name": name, "rank": rank or "Not specified", "common_name": "", "suggested_rank": rank if rank and rank != 'Not specified' else None, "suggestion_source": 'heuristic' if rank and rank != 'Not specified' else None})
                    continue

                name = ch.get("name") or ch.get("taxon") or ch.get("scientific_name") or "Unknown"
                rank = ch.get("rank") or result.get("child_rank") or self.guess_child_rank(result.get("rank")) or "Not specified"
                common = ch.get("common_name") or ch.get("common") or ""
                suggested = None
                suggestion_src = None
                if (not ch.get("rank") or ch.get("rank") in [None, '', 'Not specified']) and rank and rank != 'Not specified':
                    suggested = rank
                    suggestion_src = 'heuristic'
                normalized_children.append({"name": name, "rank": rank, "common_name": common, "suggested_rank": suggested, "suggestion_source": suggestion_src})

            result["direct_children"] = normalized_children

            # Attach source url if available
            result["source_url"] = getattr(page, 'url', None)
            result["status"] = "success"
            return result

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def simple_wikipedia_children(self, taxon_name: str) -> Dict:
        """A lightweight fallback that extracts candidate direct children from the
        Wikipedia article using heuristic text parsing. This does not use Gemini
        and can be used when the LLM or API key is unavailable.

        Returns a dict with 'status' and 'direct_children' similar to analyze_taxon.
        """
        if wikipedia is None:
            return {"status": "disabled", "message": "wikipedia package not available"}

        try:
            search_results = wikipedia.search(taxon_name, results=5)
            if not search_results:
                return {"status": "error", "message": f'No Wikipedia pages found for "{taxon_name}"'}

            page = None
            for result in search_results:
                try:
                    page = wikipedia.page(result, auto_suggest=False)
                    break
                except wikipedia.DisambiguationError as e:
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                        break
                    except Exception:
                        continue
                except Exception:
                    continue

            if not page:
                return {"status": "error", "message": f'Could not find page for "{taxon_name}"'}

            first_para = self._get_first_paragraph(page.content)

            # Look for phrases like 'comprises ...', 'includes ...', 'consists of ...'
            m = re.search(r"(?:comprise|comprises|include|includes|consist of|consists of|contain|contains)\s+(.+?)(?:\.|;|$)", first_para, re.IGNORECASE)
            candidates = []
            if m:
                segment = m.group(1)
                # Split by commas and ' and '
                parts = re.split(r",| and |;", segment)
                for p in parts:
                    p = p.strip()
                    # Extract capitalized tokens as taxon names
                    names = re.findall(r"[A-Z][a-zA-Z0-9\-]+", p)
                    if names:
                        # prefer longer token (e.g., 'Amoebozoa')
                        candidates.append(names[-1])

            # Also look for simple bullet lists in the whole content as a fallback
            if not candidates:
                bullets = re.findall(r"^\*\s*(.+)$", page.content, re.MULTILINE)
                for b in bullets:
                    names = re.findall(r"[A-Z][a-zA-Z0-9\-]+", b)
                    if names:
                        candidates.append(names[0])

            # Deduplicate and normalize
            seen = set()
            children = []
            # Suggest ranks based on parent rank
            parent_rank = None
            try:
                parent_rank = page.title and page.title
            except Exception:
                parent_rank = None

            guessed = self.guess_child_rank(parent_rank)

            for name in candidates:
                n = name.strip()
                if n and n not in seen:
                    seen.add(n)
                    children.append({"name": n, "rank": "Not specified", "common_name": "", "suggested_rank": guessed if guessed and guessed != 'Not specified' else None, "suggestion_source": 'heuristic' if guessed and guessed != 'Not specified' else None})

            return {"status": "success", "taxon_name": page.title, "rank": "Not specified", "child_rank": "Not specified", "direct_children": children, "source_url": getattr(page, 'url', None)}

        except Exception as e:
            return {"status": "error", "message": str(e)}

    def guess_child_rank(self, parent_rank: Optional[str]) -> str:
        """Simple heuristic to guess the rank of direct children given the parent's rank."""
        if not parent_rank:
            return "Not specified"

        mapping = {
            'domain': 'kingdom',
            'kingdom': 'phylum',
            'phylum': 'class',
            'class': 'order',
            'order': 'family',
            'family': 'genus',
            'genus': 'species',
            'supergroup': 'kingdom',
            'clade': 'Not specified'
        }

        pr = parent_rank.lower() if isinstance(parent_rank, str) else parent_rank
        return mapping.get(pr, 'Not specified')
