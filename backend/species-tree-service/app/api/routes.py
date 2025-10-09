from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from app.models.taxonomy import (
    TaxonomyResponse, 
    TaxonomyTuplesResponse, 
    ExpansionResponse, 
    ExpansionRequest,
    ErrorResponse
)
from app.services.taxonomy_extractor import TaxonomyExtractor
from app.services.taxonomy_expander import TaxonomyExpander
from app.services.gemini_taxonomy import GeminiTaxonomyService
import difflib
from datetime import datetime
from app.models.taxonomy import TaxonomicEntity
from app.models.taxonomy import ExpansionResponse, TaxonomicTuple
router = APIRouter()

# Initialize services
taxonomy_extractor = TaxonomyExtractor()
taxonomy_expander = TaxonomyExpander()
gemini_service = GeminiTaxonomyService()


# Simple print system used by endpoints (timestamp + level)
def _print_sys(level: str, message: str, *args):
    """Print a message with ISO timestamp and level. Message can be a format string with args."""
    ts = datetime.utcnow().isoformat() + 'Z'
    try:
        msg = message.format(*args) if args else message
    except Exception:
        # fallback: join args if formatting fails
        msg = message + ' ' + ' '.join(str(a) for a in args)
    print(f"[{ts}] [{level.upper()}] {msg}")

@router.get("/taxonomy/{scientific_name}", response_model=TaxonomyTuplesResponse)
async def get_taxonomies(scientific_name: str):
    """
    Get complete taxonomic hierarchy for a species in tuple format.
    
    - **scientific_name**: Scientific name of the species (e.g., "Homo sapiens", "Panthera leo")
    
    Returns taxonomic relationships as tuples (parent_taxon, has_child, child_taxon)
    """
    
    print(f"📊 Extracting taxonomy tuples for: {scientific_name}")
    
    try:
        result = taxonomy_extractor.extract_as_tuples(scientific_name)
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail=f"Could not extract taxonomic information for '{scientific_name}'. Please check the scientific name and try again."
            )
        
        print(f"✅ Successfully extracted {result.total_relationships} taxonomic relationships")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error extracting taxonomy: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error while extracting taxonomy: {str(e)}"
        )

# @router.get("/taxonomy/{scientific_name}/detailed", response_model=TaxonomyResponse)
# async def get_detailed_taxonomy(scientific_name: str):
#     """
#     Get detailed taxonomic hierarchy for a species with full information.
    
#     - **scientific_name**: Scientific name of the species (e.g., "Homo sapiens", "Panthera leo")
    
#     Returns complete taxonomic information including ranks, names, and Wikipedia links
#     """
#     print(f"📊 Extracting detailed taxonomy for: {scientific_name}")
    
#     try:
#         result = taxonomy_extractor.extract_taxonomy_realtime(scientific_name)
        
#         if not result:
#             raise HTTPException(
#                 status_code=404, 
#                 detail=f"Could not extract taxonomic information for '{scientific_name}'. Please check the scientific name and try again."
#             )
        
#         print(f"✅ Successfully extracted {result.total_taxa_found} taxonomic entries")
#         return result
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"❌ Error extracting detailed taxonomy: {e}")
#         raise HTTPException(
#             status_code=500, 
#             detail=f"Internal error while extracting taxonomy: {str(e)}"
#         )

@router.get("/expand/{taxon_name}", response_model=ExpansionResponse)
async def expand_taxonomy_auto(taxon_name: str, target_rank: Optional[str] = None, response: Response = None, prefer_llm: bool = False, force_llm: bool = False):
    """
    Expand taxonomic tree from a given taxon with automatic rank detection.
    
    - **taxon_name**: Name of the taxonomic entity (e.g., "Homo sapiens", "Mammalia", "Carnivora")
    - **target_rank**: Optional target rank to expand to (e.g., "order", "family", "genus")
    
    Returns children of the given taxon in tuple format (parent_taxon, has_child, child_taxon)
    """
    _print_sys('info', "🔍 Expanding taxonomy from {} (auto-detecting rank) to {}", taxon_name, target_rank or 'next rank')
    
    try:
        if target_rank:
            valid_ranks = taxonomy_expander.taxonomic_ranks
            if target_rank.lower() not in valid_ranks:
                # attempt an automatic guess (use a lower cutoff to be more permissive)
                guesses = difflib.get_close_matches(target_rank.lower(), valid_ranks, n=1, cutoff=0.4)
                if guesses:
                    guessed = guesses[0]
                    if response is not None:
                        response.headers['X-Guessed-Target-Rank'] = guessed
                    target_rank = guessed
                else:
                    # no close single guess; provide suggestions and fail
                    suggestions = difflib.get_close_matches(target_rank.lower(), valid_ranks, n=3, cutoff=0.6)
                    suggestion_msg = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid target rank '{target_rank}'. Valid ranks are: {', '.join(valid_ranks)}{suggestion_msg}"
                    )
        
        # If user provided a domain-like taxon (e.g., Eukarya), return kingdoms directly
        try:
            domains = taxonomy_expander.get_domain()
            if taxon_name in domains and (target_rank is None or target_rank.lower() == 'kingdom'):
                kingdoms = taxonomy_expander.get_kingdom(taxon_name)
                children_entities = [TaxonomicEntity(rank='kingdom', name=k) for k in kingdoms]
                tuples = []
                for k in kingdoms:
                    tuples.append({
                        'parent_taxon': {'rank': 'domain', 'name': taxon_name},
                        'has_child': True,
                        'child_taxon': {'rank': 'kingdom', 'name': k}
                    })
                from app.models.taxonomy import ExpansionResponse, TaxonomicTuple
                tuples_models = [TaxonomicTuple(parent_taxon=TaxonomicEntity(rank='domain', name=taxon_name), has_child=True, child_taxon=TaxonomicEntity(rank='kingdom', name=k)) for k in kingdoms]
                return ExpansionResponse(parent_taxon=TaxonomicEntity(rank='domain', name=taxon_name), children=children_entities, tuples=tuples_models, total_children=len(children_entities))
        except Exception:
            # fallback to normal flow if domain handling fails
            pass

        result = taxonomy_expander.expand_auto_detect(taxon_name, target_rank)

        # If expander returns few or no children, try Gemini to augment results
        try:
            need_gemini = (result.total_children == 0) or (result.total_children < 5)
        except Exception:
            need_gemini = True

        parent_rank = getattr(result.parent_taxon, 'rank', '') or ''
        prefer_high_level = parent_rank.lower() in {'domain', 'superkingdom', 'kingdom', 'clade'}

        # Decide whether to call LLM/fallback
        use_llm = force_llm or prefer_llm or prefer_high_level or need_gemini

        gemini_res = None
        if use_llm and gemini_service.enabled:
            gemini_res = gemini_service.analyze_taxon(taxon_name)
        elif use_llm and not gemini_service.enabled:
            gemini_res = gemini_service.simple_wikipedia_children(taxon_name)
            if gemini_res.get('status') == 'success':
                children = []
                for child in gemini_res.get('direct_children', [])[:50]:
                    name = child.get('name')
                    rank = child.get('rank') or gemini_res.get('child_rank') or 'Not specified'
                    suggested = child.get('suggested_rank')
                    suggestion_src = child.get('suggestion_source')
                    if name:
                        children.append(TaxonomicEntity(rank=rank, name=name, suggested_rank=suggested, suggestion_source=suggestion_src))

                # Merge unique children by name
                existing_names = {c.name for c in result.children}
                new_children = [c for c in children if c.name not in existing_names]
                merged_children = result.children + new_children

                # Build tuples: parent -> each child
                tuples = result.tuples or []
                for c in new_children:
                    tuples.append(
                        {
                            'parent_taxon': {
                                'rank': result.parent_taxon.rank,
                                'name': result.parent_taxon.name
                            },
                            'has_child': True,
                            'child_taxon': {'rank': c.rank, 'name': c.name}
                        }
                    )

                # Convert tuple dicts to TaxonomicTuple objects via model validation by creating a new ExpansionResponse
                from app.models.taxonomy import ExpansionResponse, TaxonomicTuple

                tuples_models = []
                for t in tuples:
                    try:
                        tuples_models.append(TaxonomicTuple(
                            parent_taxon=TaxonomicEntity(rank=t['parent_taxon']['rank'], name=t['parent_taxon']['name']),
                            has_child=t.get('has_child', True),
                            child_taxon=TaxonomicEntity(rank=t['child_taxon']['rank'], name=t['child_taxon']['name'])
                        ))
                    except Exception:
                        # skip invalid tuple
                        continue

                response = ExpansionResponse(
                    parent_taxon=result.parent_taxon,
                    children=merged_children,
                    tuples=tuples_models,
                    total_children=len(merged_children)
                )
        _print_sys('info', "✅ Successfully augmented children using Gemini: total {}", response.total_children)
        return response

    except HTTPException:
        raise
    except Exception as e:
        _print_sys('error', "Error expanding taxonomy: {}", str(e))
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error while expanding taxonomy: {str(e)}"
        )

@router.get("/expand/{taxon_name}/{rank}", response_model=ExpansionResponse)
async def expand_taxonomies(taxon_name: str, rank: str, target_rank: Optional[str] = None, response: Response = None):
    """
    Expand taxonomic tree from a given taxon and rank to show children.
    
    - **taxon_name**: Name of the taxonomic entity (e.g., "Mammalia", "Carnivora")
    - **rank**: Current taxonomic rank (e.g., "class", "order", "family")
    - **target_rank**: Optional target rank to expand to (e.g., "order", "family", "genus")
    
    Returns children of the given taxon in tuple format (parent_taxon, has_child, child_taxon)
    """
    print(f"🔍 Expanding taxonomy from {taxon_name} ({rank}) to {target_rank or 'next rank'}")
    
    try:
                
        result = taxonomy_expander.expand_taxonomy(taxon_name, rank)
        print(result)
        # gemini_res = gemini_service.analyze_taxon(taxon_name, rank_hint=rank)
 
        # if gemini_res.get('status') == 'success':
        #     children = []
        #     for child in gemini_res.get('direct_children', [])[:50]:
        #         name = child.get('name')
        #         r = child.get('rank') or gemini_res.get('child_rank') or 'Not specified'
        #         suggested = child.get('suggested_rank')
        #         suggestion_src = child.get('suggestion_source')
        #         if name:
        #             children.append(TaxonomicEntity(rank=r, name=name, suggested_rank=suggested, suggestion_source=suggestion_src))

        #     existing_names = {c.name for c in result.children}
        #     new_children = [c for c in children if c.name not in existing_names]
        #     merged_children = result.children + new_children

        #     # Build tuples
        #     tuples = result.tuples or []
        #     for c in new_children:
        #         tuples.append(
        #             {
        #                 'parent_taxon': {
        #                     'rank': result.parent_taxon.rank,
        #                     'name': result.parent_taxon.name
        #                 },
        #                 'has_child': True,
        #                 'child_taxon': {'rank': c.rank, 'name': c.name}
        #             }
        #         )

           
        #     tuples_models = []
        #     for t in tuples:
        #         try:
        #             tuples_models.append(TaxonomicTuple(
        #                 parent_taxon=TaxonomicEntity(rank=t['parent_taxon']['rank'], name=t['parent_taxon']['name']),
        #                 has_child=t.get('has_child', True),
        #                 child_taxon=TaxonomicEntity(rank=t['child_taxon']['rank'], name=t['child_taxon']['name'])
        #             ))
        #         except Exception:
        #             continue

        #     response = ExpansionResponse(
        #         parent_taxon=result.parent_taxon,
        #         children=merged_children,
        #         tuples=tuples_models,
        #         total_children=len(merged_children)
        #     )

        #     print(f"✅ Successfully augmented children using Gemini: total {response.total_children}")
        #     return response

        # print(f"✅ Successfully found {result.total_children} children")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error expanding taxonomy: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error while expanding taxonomy: {str(e)}"
        )

@router.get("/expand/domains", response_model=List[str])
async def get_domains():
    """
    Get all biological domains.
    
    Returns list of domain names
    """
    try:
        domains = taxonomy_expander.get_domain()
        return domains
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting domains: {str(e)}"
        )

@router.get("/expand/kingdoms", response_model=List[str])
async def get_kingdoms(domain: Optional[str] = None):
    """
    Get kingdoms, optionally filtered by domain.
    
    - **domain**: Optional domain name to filter by (e.g., "Eukarya", "Bacteria", "Archaea")
    
    Returns list of kingdom names
    """
    try:
        kingdoms = taxonomy_expander.get_kingdom(domain)
        return kingdoms
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting kingdoms: {str(e)}"
        )

@router.get("/ranks", response_model=List[str])
async def get_taxonomic_ranks():
    """
    Get all available taxonomic ranks in hierarchical order.
    
    Returns list of taxonomic ranks from domain to strain
    """
    try:
        return taxonomy_expander.taxonomic_ranks
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting taxonomic ranks: {str(e)}"
        )