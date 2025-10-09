import asyncio, sys
sys.path.insert(0, 'E:/Genealogy-Tree-Creator/backend/species-tree-service')
from app.api import routes

async def call():
    resp = await routes.expand_taxonomy_auto('Eukarya')
    print('type:', type(resp))
    print('total_children:', getattr(resp, 'total_children', None))
    for c in resp.children:
        print(c.rank, c.name)

if __name__ == '__main__':
    asyncio.run(call())
