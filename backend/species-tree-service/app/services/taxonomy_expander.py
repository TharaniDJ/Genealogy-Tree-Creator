"""
Simplified Taxonomy Expander with direct SPARQL queries for Species Tree Service.
Optimized for performance with specific QID lookups.
"""

from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Dict, Optional, List
import time
import logging
from app.models.taxonomy import TaxonomicTuple, ExpansionResponse, TaxonomicEntity

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
            self.sparql.setTimeout(10)  # 10 second timeout
            results = self.sparql.query().convert()
            time.sleep(0.1)  # Small delay to be respectful
            return results
            
        except Exception as e:
            logger.warning(f"Query failed: {e}")
            return None
    
    def query_children(self, parent_name: str, target_rank: str) -> List[str]:
        """Query for children of a given taxonomic entity"""
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
        LIMIT 50
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
    
    def expand_taxonomy(self, taxon_name: str, current_rank: str, target_rank: str = None) -> ExpansionResponse:
        """
        Expand taxonomy from a given taxon to show its children.
        Returns results in tuple format.
        """
        if target_rank is None:
            target_rank = self.get_next_rank(current_rank)
        
        if target_rank is None:
            return ExpansionResponse(
                parent_taxon=TaxonomicEntity(rank=current_rank, name=taxon_name),
                children=[],
                tuples=[],
                total_children=0
            )
        
        # Get children for the target rank
        children = self.query_children(taxon_name, target_rank)
        
        # Create tuples
        tuples = []
        for child in children:
            tuples.append(TaxonomicTuple(
                parent_taxon=TaxonomicEntity(rank=current_rank, name=taxon_name),
                has_child=True,  # Assume children might have their own children
                child_taxon=TaxonomicEntity(rank=target_rank, name=child)
            ))
        
        # Create TaxonomicEntity objects for children
        children_entities = [TaxonomicEntity(rank=target_rank, name=child) for child in children]
        
        return ExpansionResponse(
            parent_taxon=TaxonomicEntity(rank=current_rank, name=taxon_name),
            children=children_entities,
            tuples=tuples,
            total_children=len(children)
        )
    
    # Domain functions
    def get_domain(self) -> List[str]:
        """Get all biological domains."""
        return ["Bacteria", "Archaea", "Eukarya"]
    
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
    
    def detect_taxonomic_rank(self, taxon_name: str) -> Optional[str]:
        """
        Auto-detect the taxonomic rank of a given taxon name.
        Returns the rank as a string or None if not found.
        """
        query = f"""
        SELECT DISTINCT ?rankLabel WHERE {{
          ?taxon wdt:P225 "{taxon_name}" ;
                 wdt:P105 ?rank .
          ?rank rdfs:label ?rankLabel .
          FILTER(LANG(?rankLabel) = "en")
        }}
        LIMIT 1
        """
        
        results = self._execute_query(query, f"rank_{taxon_name}")
        if results and results.get("results", {}).get("bindings"):
            rank_label = results["results"]["bindings"][0]["rankLabel"]["value"].lower()
            # Map common rank names to our standard names
            rank_mapping = {
                "taxonomic class": "class",
                "taxonomic order": "order", 
                "taxonomic family": "family",
                "taxonomic genus": "genus",
                "taxonomic species": "species",
                "biological kingdom": "kingdom",
                "phylum": "phylum"
            }
            return rank_mapping.get(rank_label, rank_label)
        
        return None
    
    def expand_auto_detect(self, taxon_name: str, target_rank: str = None) -> ExpansionResponse:
        """
        Expand taxonomy with automatic rank detection.
        Auto-detects the current rank and expands to the next level or target rank.
        """
        # Auto-detect current rank
        current_rank = self.detect_taxonomic_rank(taxon_name)
        
        if current_rank is None:
            return ExpansionResponse(
                parent_taxon=TaxonomicEntity(rank="unknown", name=taxon_name),
                children=[],
                tuples=[],
                total_children=0
            )
        
        return self.expand_taxonomy(taxon_name, current_rank, target_rank)

    def expand_from_rank(self, taxon_name: str, rank: str) -> ExpansionResponse:
        """Convenience method to expand from any rank to the next level"""
        return self.expand_taxonomy(taxon_name, rank)