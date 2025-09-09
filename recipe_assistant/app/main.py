# app/main.py
from fastapi import FastAPI
from .api.endpoints import router
from .core.config import settings
from ..rag import init_qdrant

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="A recipe assistant based on a RAG that handles users' questions and feedbacks"
)

app.include_router(router, prefix="/api/v1")

@app.on_event("startup")
async def startup_event():
    init_qdrant()

@app.get("/")
async def root():
    return {"message": "Welcome to the recipe assistant application!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Add a debug endpoint to see all routes
@app.get("/debug/routes")
async def debug_routes():
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, 'path', 'N/A'),
            "methods": getattr(route, 'methods', 'N/A'),
            "name": getattr(route, 'name', 'N/A')
        })
    return {"routes": routes}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)