import google.generativeai as genai
from services.embedding import embed_text
from services.supabase_client import get_admin_client

# Model ismini belirliyoruz
MODEL_NAME = "gemini-2.5-flash"

async def answer_question(question: str, user_id: str, document_id: str | None = None) -> dict:
    """
    Kullanıcının sorusunu alır, RAG yöntemiyle bağlamı bulur ve Gemini ile yanıtlar.
    """
    admin_client = get_admin_client()
    
    # 1. Soruyu embed et
    query_embedding = embed_text(question)
    
    # 2. Supabase match_chunks RPC'sini çağır
    rpc_params = {
        "query_embedding": query_embedding,
        "match_user_id": user_id,
        "match_count": 5
    }
    
    if document_id is not None:
        rpc_params["match_document_id"] = document_id
        
    res = admin_client.rpc("match_chunks", rpc_params).execute()
    chunks = res.data
    
    if not chunks:
        # Eğer hiç benzer chunk bulunamadıysa doğrudan boş cevap dön
        return {
            "answer": "Bu bilgi yüklenen dökümanlarda bulunamadı",
            "sources": []
        }
        
    # 3. Dönen chunk'ların content'lerini birleştir
    context = "\n\n---\n\n".join([chunk.get("content", "") for chunk in chunks])
    
    # 4. Gemini'ye sistem talimatıyla birlikte gönder
    prompt = f"""Sana verilen CONTEXT dışında hiçbir bilgi kullanma. Eğer cevap context'te yoksa, sadece "Bu bilgi yüklenen dökümanlarda bulunamadı" de.

CONTEXT:
{context}

SORU:
{question}
"""
    
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    
    # 5. Formatlanmış sonucu dön
    formatted_sources = [
        {
            "content": chunk.get("content", ""),
            "similarity_score": chunk.get("similarity", 0),
            "chunk_index": chunk.get("chunk_index", None),
            "document_id": chunk.get("document_id", None),
        }
        for chunk in chunks
    ]
    
    return {
        "answer": response.text.strip(),
        "sources": formatted_sources
    }
