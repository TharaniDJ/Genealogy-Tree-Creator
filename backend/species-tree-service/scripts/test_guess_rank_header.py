import asyncio, sys
sys.path.insert(0, 'E:/Genealogy-Tree-Creator/backend/species-tree-service')
from fastapi import Response
from app.api import routes
from app.models.taxonomy import TaxonomicEntity

# Mock taxonomy_expander to accept guessed rank and return a simple response
class DummyResp:
    parent_taxon = TaxonomicEntity(rank='class', name='Mammalia')
    children = [TaxonomicEntity(rank='order', name='Carnivora')]
    tuples = []
    total_children = 1

routes.taxonomy_expander = type('E', (), {
    'expand_taxonomy': lambda self, name, rank, target: DummyResp(),
    'taxonomic_ranks': ['domain','kingdom','phylum','class','order','family','genus','species']
})()

async def call():
    resp = Response()
    result = await routes.expand_taxonomies('Mammalia','not specified', response=resp)
    print('Header X-Guessed-Rank:', resp.headers.get('X-Guessed-Rank'))
    print('Result total_children:', result.total_children)

if __name__ == '__main__':
    asyncio.run(call())
