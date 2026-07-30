import logging
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from dependencies import get_current_user
from services.rag import answer_question
from services.supabase_client import get_admin_client

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

logger = logging.getLogger(__name__)

class ChatQueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None

@router.post("/query")
async def chat_query(request: ChatQueryRequest, user_id: str = Depends(get_current_user)):
    """
    Kullanıcıdan gelen soruyu (ve opsiyonel document_id) alıp RAG servisine iletir.
    Üretilen cevabı 'chat_history' tablosuna kaydeder ve yanıtlar.
    """
    try:
        # 1. RAG ile cevabı üret
        result = await answer_question(
            question=request.question,
            user_id=user_id,
            document_id=request.document_id
        )
        
        answer = result["answer"]
        sources = result["sources"]
        
        # 2. Soruyu ve cevabı veritabanındaki sohbet geçmişine (chat_history) ekle
        admin_client = get_admin_client()
        admin_client.table("chat_history").insert({
            "user_id": user_id,
            "document_id": request.document_id,
            "question": request.question,
            "answer": answer
        }).execute()
        
        # 3. Sonucu kullanıcıya dön
        return {
            "answer": answer,
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Chat sorgusu işlenirken hata oluştu: {e}")
        raise HTTPException(status_code=500, detail="Soru cevaplanırken sistemsel bir hata oluştu.")

@router.get("/history")
async def get_chat_history(
    document_id: Optional[str] = Query(None, description="Opsiyonel döküman filtreleme"),
    user_id: str = Depends(get_current_user)
):
    """
    Kullanıcının sohbet geçmişini (isteğe bağlı olarak belirli bir dökümana göre) kronolojik olarak listeler.
    """
    try:
        admin_client = get_admin_client()
        
        # Tüm kayıtları varsayılan olarak ilgili kullanıcıya filtrele
        query = admin_client.table("chat_history").select("*").eq("user_id", user_id)
        
        # Eğer document_id verildiyse o dökümana göre ek filtre koy
        if document_id:
            query = query.eq("document_id", document_id)
            
        # created_at sütununa göre eskiden yeniye sırala
        res = query.order("created_at", desc=False).execute()
        
        return {"history": res.data}
        
    except Exception as e:
        logger.error(f"Sohbet geçmişi getirilirken hata: {e}")
        raise HTTPException(status_code=500, detail="Sohbet geçmişi alınamadı.")
