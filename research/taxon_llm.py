import wikipedia
import google.generativeai as genai
import os
from typing import List, Dict
import json
import re

class TaxonomyBotWithGemini:
    """Bot to find direct children of a given taxonomic rank using Wikipedia + Gemini"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize the bot with Google Gemini API key
        
        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env variable)
        """
        self.api_key = api_key or os.environ.get('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Please provide Google API key or set GOOGLE_API_KEY environment variable")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def get_first_paragraph(self, content: str) -> str:
        """
        Extract the first paragraph from Wikipedia content
        
        Args:
            content: Full Wikipedia article content
            
        Returns:
            First paragraph text
        """
        # Split by double newlines to get paragraphs
        paragraphs = content.split('\n\n')
        
        # Find the first substantial paragraph (skip short headers/metadata)
        for para in paragraphs:
            para = para.strip()
            # Skip if it's too short, looks like a header, or is metadata
            if len(para) > 100 and not para.startswith('==') and not para.startswith('='):
                return para
        
        # Fallback: return first 1500 characters
        return content[:1500]
    
    def search_taxonomy(self, taxon_name: str) -> Dict:
        """
        Search for a taxonomic group and find its direct children using Gemini
        
        Args:
            taxon_name: Name of the taxonomic group (e.g., 'Mammalia', 'Carnivora')
            
        Returns:
            Dictionary containing taxon info and its direct children
        """
        try:
            # Search Wikipedia
            print(f"🔍 Searching Wikipedia for: {taxon_name}")
            search_results = wikipedia.search(taxon_name, results=5)
            
            if not search_results:
                return {
                    'status': 'error',
                    'message': f'No Wikipedia pages found for "{taxon_name}"'
                }
            
            # Try to get the page
            page = None
            for result in search_results:
                try:
                    page = wikipedia.page(result, auto_suggest=False)
                    break
                except wikipedia.DisambiguationError as e:
                    try:
                        page = wikipedia.page(e.options[0], auto_suggest=False)
                        break
                    except:
                        continue
                except:
                    continue
            
            if not page:
                return {
                    'status': 'error',
                    'message': f'Could not find page for "{taxon_name}"'
                }
            
            print(f"📄 Found Wikipedia page: {page.title}")
            
            # Extract first paragraph only
            first_para = self.get_first_paragraph(page.content)
            print(f"📝 Using first paragraph ({len(first_para)} characters)")
            print(f"🤖 Analyzing with Gemini AI...")
            
            # Use Gemini to extract taxonomic information
            result = self.analyze_with_gemini(page.title, first_para)
            
            result['status'] = 'success'
            result['url'] = page.url
            
            return result
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error: {str(e)}'
            }
    
    def analyze_with_gemini(self, title: str, content: str) -> Dict:
        """
        Use Gemini to analyze Wikipedia content and extract taxonomic information
        
        Args:
            title: Page title
            content: Wikipedia page content
            
        Returns:
            Dictionary with taxonomic information
        """
        prompt = f"""You are a taxonomic expert. Analyze this Wikipedia article about "{title}" and extract taxonomic information.

Wikipedia Content:
{content}

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
2. Examples:
   - If this is Class Mammalia, find Orders (like Carnivora, Primates, Rodentia, etc.)
   - If this is Order Carnivora, find Families (like Felidae, Canidae, Ursidae, etc.)
   - If this is Family Felidae, find Genera (like Panthera, Felis, Lynx, etc.)
   - If this is Genus Panthera, find Species (like Panthera leo, Panthera tigris, etc.)
3. Include up to 25 direct children if available
4. Only include children explicitly mentioned in the Wikipedia article
5. For hierarchy, include all levels from Domain down to the current taxon
6. Return ONLY valid JSON, no markdown formatting, no code blocks, no additional text
7. Ensure all strings are properly escaped for JSON

Return the JSON now:"""

        try:
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # Clean up response - remove markdown code blocks if present
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            elif response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Try to parse as direct JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not parse Gemini response as JSON")
            
            return result
            
        except Exception as e:
            print(f"Error in Gemini analysis: {e}")
            raise


def main():
    """Main function to run the taxonomy bot"""
    print("=" * 70)
    print("🧬 WIKIPEDIA TAXONOMY BOT WITH GEMINI AI")
    print("Find direct children of any taxonomic rank using AI analysis")
    print("=" * 70)
    print()
    
    # Check for API key
    api_key = os.environ.get('GOOGLE_API_KEY')
    if not api_key:
        print("⚠️  Google API key not found in environment variables")
        print()
        print("To get a free API key:")
        print("1. Visit: https://makersuite.google.com/app/apikey")
        print("2. Click 'Create API Key'")
        print("3. Copy your key")
        print()
        print("Then set it as an environment variable:")
        print("   export GOOGLE_API_KEY='your-key-here'")
        print()
        print("Or enter it now (will only be used for this session):")
        api_key = input("Enter Google API key (or press Enter to exit): ").strip()
        if not api_key:
            print("No API key provided. Exiting.")
            return
    
    try:
        bot = TaxonomyBotWithGemini(api_key=api_key)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n✅ Bot initialized successfully!")
    print("\n💡 Try queries like: Mammalia, Carnivora, Felidae, Panthera, Primates\n")
    
    while True:
        taxon = input("Enter taxonomic name (or 'quit' to exit): ").strip()
        
        if taxon.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        if not taxon:
            print("⚠️  Please enter a valid taxonomic name.")
            continue
        
        print("\n" + "=" * 70)
        result = bot.search_taxonomy(taxon)
        
        if result['status'] == 'error':
            print(f"❌ ERROR: {result['message']}")
        else:
            print(f"📊 Taxon: {result.get('taxon_name', 'N/A')}")
            print(f"📍 Rank: {result.get('rank', 'Unknown')}")
            print(f"🔗 URL: {result.get('url', 'N/A')}")
            print()
            
            if result.get('summary'):
                print(f"📝 Summary:")
                print(f"   {result['summary']}")
                print()
            
            if result.get('hierarchy'):
                print("🌳 Taxonomic Hierarchy:")
                for level in result['hierarchy']:
                    print(f"   │  {level}")
                print()
            
            direct_children = result.get('direct_children', [])
            child_rank = result.get('child_rank', 'Unknown')
            
            if direct_children:
                print(f"👶 Direct Children ({len(direct_children)} {child_rank}{'s' if len(direct_children) > 1 else ''}):")
                print()
                for i, child in enumerate(direct_children, 1):
                    name = child.get('name', 'Unknown')
                    rank = child.get('rank', 'Unknown')
                    common = child.get('common_name', '')
                    
                    if common and common.strip():
                        print(f"   {i:2d}. {name} ({rank})")
                        print(f"       └─ Common name: {common}")
                    else:
                        print(f"   {i:2d}. {name} ({rank})")
            else:
                print("👶 No direct children found.")
                print("   This may be a species-level taxon or the lowest taxonomic level.")
        
        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Install required packages:
    # pip install wikipedia google-generativeai
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║  Prerequisites:                                                   ║
║  pip install wikipedia google-generativeai                       ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    main()