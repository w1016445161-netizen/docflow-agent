from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.chat import router as chat_router
from backend.routers.document import router as document_router


app = FastAPI(
    title="DocFlow Agent API",
    description="文档智能体后端服务",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "DocFlow Agent backend is running."
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }


app.include_router(chat_router)
app.include_router(document_router)