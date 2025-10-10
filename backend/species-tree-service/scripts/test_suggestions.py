import asyncio, sys
sys.path.insert(0, 'E:/Genealogy-Tree-Creator/backend/species-tree-service')
from app.api import routes
from app.models.taxonomy import TaxonomicEntity

# Force gemini service disabled so fallback used
routes.gemini_service.enabled = False

# Mock expander to return no children so fallback triggers
class DummyResp:
    parent_taxon = TaxonomicEntity(rank='clade', name='Amorphea')
    children = []
    tuples = []
    total_children = 0

routes.taxonomy_expander = type('E', (), {
    'expand_auto_detect': lambda self, name, target: DummyResp(),
    'expand_taxonomy': lambda self, name, rank, target: DummyResp(),
    'taxonomic_ranks': ['clade']
})()

async def call():
    resp = await routes.expand_taxonomy_auto('Amorphea')
    print('total_children:', resp.total_children)
    for i,c in enumerate(resp.children,1):
        print(i, c.name, 'rank=', c.rank, 'suggested=', c.suggested_rank, 'src=', c.suggestion_source)

if __name__ == '__main__':
    asyncio.run(call())
