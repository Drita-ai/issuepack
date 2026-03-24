from fastapi import APIRouter

from api.github_issues.router import router

api_router = APIRouter()

# Defining all Routers
api_router.include_router(router)