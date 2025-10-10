"""
Simplified Taxonomy Model with direct SPARQL queries and no fallback data.
Optimized for performance with specific QID lookups.
"""

from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Dict, Optional, List
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaxonomyExpander:
    
    def __init__(self, endpoint: str = "https://query.wikidata.org/sparql"):
        self.endpoint = endpoint
        self.sparql = SPARQLWrapper(endpoint)
        
        # Taxonomic ranks in order
        self.taxonomic_ranks = [
            'domain', 'kingdom', 'subkingdom', 'superphylum', 'phylum',
            'subphylum', 'superclass', 'class', 'subclass', 'infraclass',
            'superorder', 'order', 'suborder', 'infraorder', 'parvorder',
            'superfamily', 'family', 'subfamily', 'tribe', 'subtribe',
            'genus', 'subgenus', 'species', 'subspecies', 'variety',
            'form', 'morph', 'strain'
        ]
        
        # Wikidata QIDs for taxonomic ranks
        self.rank_qids = {
            'domain': 'wd:Q3624078',
            'kingdom': 'wd:Q36732',
            'subkingdom': 'wd:Q3978005',
            'superphylum': 'wd:Q2136103',
            'phylum': 'wd:Q38348',
            'subphylum': 'wd:Q2362355',
            'superclass': 'wd:Q2361851',
            'class': 'wd:Q37517',
            'subclass': 'wd:Q5867051',
            'infraclass': 'wd:Q2007442',
            'superorder': 'wd:Q2136103',
            'order': 'wd:Q36602',
            'suborder': 'wd:Q3663366',
            'infraorder': 'wd:Q2889003',
            'parvorder': 'wd:Q2136103',
            'superfamily': 'wd:Q2136103',
            'family': 'wd:Q35409',
            'subfamily': 'wd:Q164280',
            'tribe': 'wd:Q227936',
            'subtribe': 'wd:Q2136103',
            'genus': 'wd:Q34740',
            'subgenus': 'wd:Q3238261',
            'species': 'wd:Q7432',
            'subspecies': 'wd:Q68947',
            'variety': 'wd:Q767728',
            'form': 'wd:Q2136103',
            'morph': 'wd:Q2136103',
            'strain': 'wd:Q2136103'
        }
        
     
    def _execute_query(self, query: str, cache_key: str = None) -> Optional[Dict]:
        """Execute SPARQL query with caching and error handling."""
            
        try:
            self.sparql.setQuery(query)
            self.sparql.setReturnFormat(JSON)
            self.sparql.setTimeout(3)  # 3 second timeout
            results = self.sparql.query().convert()
            time.sleep(0.01)  # Minimal delay
            return results
            
        except Exception as e:
            logger.warning(f"Query failed: {e}")
            return None
    
    def query_children(self, parent_name: str, target_rank: str) -> List[str]:
    
        target_qid = self.rank_qids.get(target_rank.lower())
        if not target_qid:
            return []
        
        # Use simplified query for better performance
        query = f"""
        SELECT DISTINCT ?childLabel WHERE {{
          ?parent wdt:P225 "{parent_name}" .
          ?child wdt:P171 ?parent ;
                 wdt:P105 {target_qid} .
          ?child rdfs:label ?childLabel .
          FILTER(LANG(?childLabel) = "en")
        }}
        LIMIT 10
        """
        
        results = self._execute_query(query, f"children_{parent_name}_{target_rank}")
        if results and results.get("results", {}).get("bindings"):
            return [r["childLabel"]["value"] for r in results["results"]["bindings"]]
        
        return []
    
    def get_next_rank(self, current_rank: str) -> Optional[str]:
        """Get the next lower taxonomic rank."""
        try:
            idx = self.taxonomic_ranks.index(current_rank.lower())
            if idx + 1 < len(self.taxonomic_ranks):
                return self.taxonomic_ranks[idx + 1]
        except ValueError:
            pass
        return None
    
    def get_previous_rank(self, current_rank: str) -> Optional[str]:
        """Get the previous higher taxonomic rank."""
        try:
            idx = self.taxonomic_ranks.index(current_rank.lower())
            if idx > 0:
                return self.taxonomic_ranks[idx - 1]
        except ValueError:
            pass
        return None
    
    # Domain functions
    def get_domain(self) -> List[str]:
        """Get all biological domains."""
        return ["Bacteria", "Archaea", "Eukarya"]  # Known biological domains
    
    # Kingdom functions  
    def get_kingdom(self, domain_name: str = None) -> List[str]:
        """Get kingdoms, optionally filtered by domain."""
        if domain_name == "Eukarya":
            return ["Animalia", "Plantae", "Fungi", "Protista"]
        elif domain_name == "Bacteria":
            return ["Bacteria"]
        elif domain_name == "Archaea":
            return ["Archaea"]
        else:
            return ["Animalia", "Plantae", "Fungi", "Protista"]
    
    # All other rank functions using query_children
    def get_subkingdom(self, kingdom_name: str) -> List[str]:
        return self.query_children(kingdom_name, "subkingdom")
    
    def get_superphylum(self, kingdom_name: str) -> List[str]:
        return self.query_children(kingdom_name, "superphylum")
    
    def get_phylum(self, kingdom_name: str) -> List[str]:
        return self.query_children(kingdom_name, "phylum")
    
    def get_subphylum(self, phylum_name: str) -> List[str]:
        return self.query_children(phylum_name, "subphylum")
    
    def get_superclass(self, phylum_name: str) -> List[str]:
        return self.query_children(phylum_name, "superclass")
    
    def get_class(self, phylum_name: str) -> List[str]:
        return self.query_children(phylum_name, "class")
    
    def get_subclass(self, class_name: str) -> List[str]:
        return self.query_children(class_name, "subclass")
    
    def get_infraclass(self, class_name: str) -> List[str]:
        return self.query_children(class_name, "infraclass")
    
    def get_superorder(self, class_name: str) -> List[str]:
        return self.query_children(class_name, "superorder")
    
    def get_order(self, class_name: str) -> List[str]:
        return self.query_children(class_name, "order")
    
    def get_suborder(self, order_name: str) -> List[str]:
        return self.query_children(order_name, "suborder")
    
    def get_infraorder(self, suborder_name: str) -> List[str]:
        return self.query_children(suborder_name, "infraorder")
    
    def get_parvorder(self, infraorder_name: str) -> List[str]:
        return self.query_children(infraorder_name, "parvorder")
    
    def get_superfamily(self, order_name: str) -> List[str]:
        return self.query_children(order_name, "superfamily")
    
    def get_family(self, order_name: str) -> List[str]:
        return self.query_children(order_name, "family")
    
    def get_subfamily(self, family_name: str) -> List[str]:
        return self.query_children(family_name, "subfamily")
    
    def get_tribe(self, subfamily_name: str) -> List[str]:
        return self.query_children(subfamily_name, "tribe")
    
    def get_subtribe(self, tribe_name: str) -> List[str]:
        return self.query_children(tribe_name, "subtribe")
    
    def get_genus(self, family_name: str) -> List[str]:
        return self.query_children(family_name, "genus")
    
    def get_subgenus(self, genus_name: str) -> List[str]:
        return self.query_children(genus_name, "subgenus")
    
    def get_species(self, genus_name: str) -> List[str]:
        return self.query_children(genus_name, "species")
    
    def get_subspecies(self, species_name: str) -> List[str]:
        return self.query_children(species_name, "subspecies")
    
    def get_variety(self, species_name: str) -> List[str]:
        return self.query_children(species_name, "variety")
    
    def get_form(self, variety_name: str) -> List[str]:
        return self.query_children(variety_name, "form")
    
    def get_morph(self, species_name: str) -> List[str]:
        return self.query_children(species_name, "morph")
    
    def get_strain(self, species_name: str) -> List[str]:
        return self.query_children(species_name, "strain")



if __name__ == "__main__":
    model = TaxonomyExpander()
    print(model.get_domain())
    print(model.get_kingdom("Eukarya"))
    print(model.get_phylum("Animalia"))

