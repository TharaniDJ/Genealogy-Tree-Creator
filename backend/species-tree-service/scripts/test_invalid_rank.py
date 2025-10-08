import asyncio, sys
sys.path.insert(0, 'E:/Genealogy-Tree-Creator/backend/species-tree-service')
from fastapi import HTTPException
from app.api import routes

async def call():
    try:
        await routes.expand_taxonomies('Mammalia','mirorder')
    except HTTPException as e:
        print('HTTPException status:', e.status_code)
        print('detail:', e.detail)
    except Exception as e:
        print('Other exception:', e)

if __name__ == '__main__':
    asyncio.run(call())
