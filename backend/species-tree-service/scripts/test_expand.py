import asyncio, sys
sys.path.insert(0, 'E:/Genealogy-Tree-Creator/backend/species-tree-service')
from app.api import routes

async def call():
    try:
        resp = await routes.expand_taxonomies('Mammalia','class')
        print('Call returned type:', type(resp))
        try:
            print('total_children:', getattr(resp, 'total_children', None))
        except Exception as e:
            print('Could not access total_children:', e)
    except Exception as e:
        print('Endpoint call raised:', e)

if __name__ == '__main__':
    asyncio.run(call())
