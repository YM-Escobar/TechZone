from fastapi import APIRouter

from app.api.endpoints import admin, advisory, auth, builds, community, products, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(admin.router)
api_router.include_router(products.router)
api_router.include_router(builds.router)
api_router.include_router(community.router)
api_router.include_router(advisory.router)
