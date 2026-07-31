from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.auth import router as auth_router
from routers.documents import router as documents_router
from routers.chat import router as chat_router
app = FastAPI(title="DocuRAG API", description="Document QA with RAG")

# CORS (Cross-Origin Resource Sharing) ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8080",
        "http://localhost:8080",
        "https://docu-rag-kappa.vercel.app"
    ], # Frontend'e erişim yetkisi verilen adresler
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları ekliyoruz
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(chat_router)
@app.get("/")
def root():
    return {"message": "DocuRAG API is up and running!"}
