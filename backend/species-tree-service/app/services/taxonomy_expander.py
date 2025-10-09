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
            
    # Full list of taxonomic ranks in hierarchical order
    major_taxonomic_ranks = ['domain', 'kingdom', 'phylum', 'class', 'order', 'family', 'genus', 'species']
    taxonomic_ranks = [
        'domain', 'subdomain', 'superkingdom', 'kingdom', 'subkingdom', 'infrakingdom',
        'superphylum', 'phylum', 'subphylum', 'infraphylum', 'microphylum',
        'superclass', 'class', 'subclass', 'infraclass', 'parvclass',
        'superorder', 'order', 'suborder', 'infraorder', 'parvorder',
        'superfamily', 'family', 'subfamily', 'tribe', 'subtribe',
        'genus', 'subgenus', 'section', 'subsection', 'series', 'subseries',
        'species', 'species group', 'species subgroup', 'subspecies', 'variety',
        'subvariety', 'form', 'subform', 'morph', 'strain', 'cultivar','clade'
    ]

    # Wikidata QIDs for taxonomic ranks (use placeholders for unknowns)
    rank_qids = {
        'clade': 'wd:Q713623',
        'domain': 'wd:Q3624078',
        'subdomain': 'wd:Q2136103',
        'superkingdom': 'wd:Q3624078',
        'kingdom': 'wd:Q36732',
        'subkingdom': 'wd:Q3978005',
        'infrakingdom': 'wd:Q2136103',
        'superphylum': 'wd:Q2136103',
        'phylum': 'wd:Q38348',
        'subphylum': 'wd:Q2362355',
        'infraphylum': 'wd:Q2136103',
        'microphylum': 'wd:Q2136103',
        'superclass': 'wd:Q2361851',
        'class': 'wd:Q37517',
        'subclass': 'wd:Q5867051',
        'infraclass': 'wd:Q2007442',
        'parvclass': 'wd:Q2136103',
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
        'section': 'wd:Q2136103',
        'subsection': 'wd:Q2136103',
        'series': 'wd:Q2136103',
        'subseries': 'wd:Q2136103',
        'species': 'wd:Q7432',
        'species group': 'wd:Q2136103',
        'species subgroup': 'wd:Q2136103',
        'subspecies': 'wd:Q68947',
        'variety': 'wd:Q767728',
        'subvariety': 'wd:Q2136103',
        'form': 'wd:Q2136103',
        'subform': 'wd:Q2136103',
        'morph': 'wd:Q2136103',
        'strain': 'wd:Q2136103',
        'cultivar': 'wd:Q2136103',
    }


    def _execute_query(self, query: str) -> Optional[Dict]:
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
    
    def query_children(self, parent_name: str) -> List[Dict]:
            """Query for children of a given taxonomic entity.

            Returns a list of dicts with keys: childQID, childTaxonName, taxonRank, taxonRankLabel
            """

            # Escape quotes in parent name
            safe_name = parent_name.replace('"', '\\"')

            query = f"""
            SELECT DISTINCT ?child ?childTaxonName ?childQID ?taxonRank ?taxonRankLabel
            WHERE {{
                ?parent wdt:P225 "{safe_name}" .
                ?child wdt:P171 ?parent .
                ?child wdt:P225 ?childTaxonName .
                OPTIONAL {{
                    ?child wdt:P105 ?taxonRank .
                    ?taxonRank rdfs:label ?taxonRankLabel .
                    FILTER(LANG(?taxonRankLabel) = "en")
                }}
                BIND(STRAFTER(STR(?child), "entity/") AS ?childQID)
            }}
            LIMIT 100
            """

            results = self._execute_query(query)
            rows = results.get("results", {}).get("bindings", []) if results else []

            out = []
            for r in rows:
                    out.append({
                            'childQID': r.get('childQID', {}).get('value') if r.get('childQID') else None,
                            'childTaxonName': r.get('childTaxonName', {}).get('value') if r.get('childTaxonName') else None,
                            'taxonRank': r.get('taxonRank', {}).get('value') if r.get('taxonRank') else None,
                            'taxonRankLabel': r.get('taxonRankLabel', {}).get('value') if r.get('taxonRankLabel') else None,
                    })

            return out

    def _get_rank_index(self, rank_label: Optional[str]) -> int:
        """Return the index of the rank_label in taxonomic_ranks. Unknown ranks return a large index so they sort last."""
        if not rank_label:
            return len(self.taxonomic_ranks) + 100
        try:
            return self.taxonomic_ranks.index(rank_label.lower())
        except ValueError:
            return len(self.taxonomic_ranks) + 50

    def get_next_ranks(self, current_rank: str) -> Optional[str]:
        """Get the next lower taxonomic rank."""
        try:
            idx = self.taxonomic_ranks.index(current_rank.lower())
            if idx + 1 < len(self.taxonomic_ranks):
                return self.taxonomic_ranks[idx + 1:idx+5]
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
    
    def expand_taxonomy(self, taxon_name: str, current_rank: str, target_rank: Optional[str] = None) -> ExpansionResponse:
        """Expand taxonomy from a given taxon to show its children.

        Returns results in tuple format.
        """

        # Fetch children (with metadata)
        child_records = self.query_children(taxon_name) or []

        # Sort children by rank index (known ranks first) then by taxon name
        child_records.sort(key=lambda r: (self._get_rank_index(r.get('taxonRankLabel')), (r.get('childTaxonName') or '').lower()))
        # If there are children, try to select a meaningful set of ranks to return.
        if child_records:
            first_rank_label = child_records[0].get('taxonRankLabel')

            # If parent rank is a major rank (domain/kingdom/phylum/...), include all ranks
            # from just below the parent up to the next major rank (inclusive). Example: domain -> include up to kingdom.
            if current_rank and current_rank.lower() in [r.lower() for r in self.major_taxonomic_ranks]:
                try:
                    # find parent's position in taxonomic_ranks
                    parent_idx = self.taxonomic_ranks.index(current_rank.lower())
                except ValueError:
                    parent_idx = None

                if parent_idx is not None:
                    # find next major rank after parent
                    try:
                        maj_idx = [r.lower() for r in self.major_taxonomic_ranks].index(current_rank.lower())
                        if maj_idx + 1 < len(self.major_taxonomic_ranks):
                            next_major = self.major_taxonomic_ranks[maj_idx + 1]
                            if next_major in self.taxonomic_ranks:
                                target_idx = self.taxonomic_ranks.index(next_major)
                                allowed_slice = self.taxonomic_ranks[parent_idx + 1: target_idx + 1]
                            else:
                                allowed_slice = self.taxonomic_ranks[parent_idx + 1: parent_idx + 6]
                        else:
                            allowed_slice = self.taxonomic_ranks[parent_idx + 1: parent_idx + 6]
                    except ValueError:
                        allowed_slice = self.taxonomic_ranks[parent_idx + 1: parent_idx + 6]

                    allowed_ranks = {r.lower() for r in allowed_slice}
                    # filter child_records to allowed ranks
                    child_records = [r for r in child_records if (r.get('taxonRankLabel') or '').lower() in allowed_ranks]

            else:
                # fallback: use first child's rank and progressively include next lower ranks until we hit a major rank
                if first_rank_label:
                    fr_lower = first_rank_label.lower()
                    allowed_ranks = {fr_lower}

                    # include next ranks initially
                    nxt = self.get_next_ranks(fr_lower) or []
                    allowed_ranks.update([r.lower() for r in nxt])

                    # initial filter
                    filtered = [r for r in child_records if (r.get('taxonRankLabel') or '').lower() in allowed_ranks]

                    # If too few results, expand allowed_ranks to include more lower ranks until we have enough or run out
                    threshold = 5
                    if len(filtered) < threshold:
                        next_ranks = self.get_next_ranks(fr_lower) or []
                        for rk in next_ranks:
                            if rk.lower() not in allowed_ranks:
                                allowed_ranks.add(rk.lower())
                            if len([r for r in child_records if (r.get('taxonRankLabel') or '').lower() in allowed_ranks]) >= threshold:
                                break

                        filtered = [r for r in child_records if (r.get('taxonRankLabel') or '').lower() in allowed_ranks]

                    child_records = filtered
                else:
                    # keep only those without an explicit rank label
                    child_records = [r for r in child_records if not r.get('taxonRankLabel')]
            
        tuples: List[TaxonomicTuple] = []
        children_entities: List[TaxonomicEntity] = []

        for rec in child_records:
            child_name = rec.get('childTaxonName') or 'Unknown'
            child_rank_label = rec.get('taxonRankLabel')
            child_rank = child_rank_label.lower() if child_rank_label else 'unknown'

            tuples.append(TaxonomicTuple(
                parent_taxon=TaxonomicEntity(rank=current_rank, name=taxon_name),
                has_child=True,
                child_taxon=TaxonomicEntity(rank=child_rank, name=child_name)
            ))

            children_entities.append(TaxonomicEntity(rank=child_rank, name=child_name))

        return ExpansionResponse(
            parent_taxon=TaxonomicEntity(rank=current_rank, name=taxon_name),
            children=children_entities,
            tuples=tuples,
            total_children=len(children_entities)
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

        results = self._execute_query(query)
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