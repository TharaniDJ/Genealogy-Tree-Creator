import asyncio, sys
sys.path.insert(0, 'E:/Genealogy-Tree-Creator/backend/species-tree-service')
from app.api import routes
from app.models.taxonomy import TaxonomicEntity, ExpansionResponse, TaxonomicTuple

# Create a fake Gemini response matching the user's example
fake_gemini = {
    'status': 'success',
    'taxon_name': 'Amorphea',
    'rank': 'Supergroup',
    'child_rank': 'Not specified',
    'direct_children': [
        {'name': 'Amoebozoa', 'rank': 'Not specified', 'common_name': ''},
        {'name': 'Obazoa', 'rank': 'Not specified', 'common_name': ''}
    ],
    'summary': 'Fake summary',
    'source_url': 'https://en.wikipedia.org/wiki/Amorphea'
}

# Patch the gemini service used in routes
routes.gemini_service = type('S', (), {'enabled': True, 'analyze_taxon': lambda n, rank_hint=None: fake_gemini})()

async def call():
    # Force a taxonomy_expander result with no children so augmentation will be used
    class DummyResp:
        parent_taxon = TaxonomicEntity(rank='Supergroup', name='Amorphea')
        children = []
        tuples = []
        total_children = 0

    routes.taxonomy_expander = type('E', (), {
        'expand_auto_detect': lambda self, name, target: DummyResp(),
        'expand_taxonomy': lambda self, name, rank, target: DummyResp(),
        'taxonomic_ranks': ['supergroup']
    })()

    resp = await routes.expand_taxonomy_auto('Amorphea')
    print('Response type:', type(resp))
    print('parent:', resp.parent_taxon)
    print('total_children:', resp.total_children)
    for i,c in enumerate(resp.children,1):
        print(i, c.rank, c.name)

if __name__ == '__main__':
    asyncio.run(call())
