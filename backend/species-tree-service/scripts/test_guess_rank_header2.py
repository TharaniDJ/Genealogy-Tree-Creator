import asyncio, sys
sys.path.insert(0, 'E:/Genealogy-Tree-Creator/backend/species-tree-service')
from fastapi import Response
from app.api import routes
from app.models.taxonomy import TaxonomicEntity

# Mock expander to return no children
class DummyResp:
    parent_taxon = TaxonomicEntity(rank='clade', name='Amorphea')
    children = []
    tuples = []
    total_children = 0

routes.taxonomy_expander = type('E', (), {
    'expand_taxonomy': lambda self, name, rank, target: DummyResp(),
    'taxonomic_ranks': ['domain','kingdom','phylum','class','order','family','genus','species','clade']
})()

# Ensure gemini fallback will produce something
routes.gemini_service.enabled = False

async def call():
    resp = Response()
    result = await routes.expand_taxonomies('Amorphea','not specified', response=resp)
    print('Response headers:', resp.headers)
    print('total_children:', getattr(result, 'total_children', None))

if __name__ == '__main__':
    asyncio.run(call())
