import logging
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from services.supabase_client import get_admin_client
from dependencies import get_current_user
from services.chunking import extract_text_from_pdf, chunk_text
from services.embedding import embed_batch

router = APIRouter(
    prefix="/documents",
    tags=["documents"]
)

logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...), 
    user_id: str = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları desteklenmektedir.")

    admin_client = get_admin_client()
    
    # 1. 'documents' tablosuna 'processing' statüsüyle yeni satır ekle
    try:
        doc_res = admin_client.table("documents").insert({
            "user_id": user_id,
            "filename": file.filename,
            "status": "processing"
        }).execute()
        
        if not doc_res.data:
            raise Exception("Döküman kaydı oluşturulamadı.")
            
        document_id = doc_res.data[0]["id"]
    except Exception as e:
        logger.error(f"Döküman kaydı oluşturulurken hata: {e}")
        raise HTTPException(status_code=500, detail="Döküman işlemi başlatılamadı.")

    try:
        # Dosya byte'larını oku
        file_bytes = await file.read()
        
        # 2. Metni çıkar
        text = extract_text_from_pdf(file_bytes)
        if not text.strip():
            raise Exception("PDF'den metin çıkarılamadı veya dosya boş.")
            
        # 3. Metni parçala (chunk)
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        if not chunks:
            raise Exception("Metin parçalara (chunk) ayrılamadı.")
            
        # 4. Parçaları embed et
        texts_to_embed = [c["content"] for c in chunks]
        embeddings = embed_batch(texts_to_embed)
        
        if len(embeddings) != len(chunks):
            raise Exception("Chunk sayısı ile embedding sayısı uyuşmuyor.")
            
        # 5. document_chunks tablosuna yaz
        chunks_data = []
        for i, chunk in enumerate(chunks):
            chunks_data.append({
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": chunk["chunk_index"],
                "content": chunk["content"],
                "embedding": embeddings[i]
            })
            
        # Chunk'ları toplu halde (batch) Supabase'e ekle
        admin_client.table("document_chunks").insert(chunks_data).execute()
        
        # 6. Döküman statüsünü 'ready' yap
        admin_client.table("documents").update({"status": "ready"}).eq("id", document_id).execute()
        
        return {
            "message": "Döküman başarıyla işlendi.", 
            "document_id": document_id, 
            "chunks_count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Döküman {document_id} işlenirken hata: {e}")
        # Hata durumunda statüyü 'failed' yap
        try:
            admin_client.table("documents").update({"status": "failed"}).eq("id", document_id).execute()
        except Exception as update_err:
            logger.error(f"Statü 'failed' yapılamadı: {update_err}")
            
        raise HTTPException(status_code=500, detail=f"Döküman işleme hatası: {str(e)}")

@router.get("")
async def list_documents(user_id: str = Depends(get_current_user)):
    """
    Mevcut kullanıcının dökümanlarını listeler.
    RLS haricinde ek bir güvenlik olarak sorguya user_id filtresi eklenir.
    """
    try:
        admin_client = get_admin_client()
        res = admin_client.table("documents").select("*").eq("user_id", user_id).execute()
        return {"documents": res.data}
    except Exception as e:
        logger.error(f"Dökümanlar listelenirken hata: {e}")
        raise HTTPException(status_code=500, detail="Dökümanlar getirilemedi.")

@router.delete("/{document_id}")
async def delete_document(document_id: str, user_id: str = Depends(get_current_user)):
    """
    İlgili dökümanı siler.
    (SQL şemasında Cascade tanımlıysa document_chunks tablosundaki bağlı chunk'lar otomatik silinir).
    """
    try:
        admin_client = get_admin_client()
        # Kullanıcının sadece kendi dökümanını silebilmesi için eq("user_id", user_id) kullanıyoruz
        res = admin_client.table("documents").delete().eq("id", document_id).eq("user_id", user_id).execute()
        
        # Eğer dönen veri yoksa, döküman ya yoktur ya da bu kullanıcıya ait değildir
        if not res.data:
            raise HTTPException(status_code=404, detail="Döküman bulunamadı veya yetkiniz yok.")
            
        return {"message": "Döküman başarıyla silindi."}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Döküman ({document_id}) silinirken hata: {e}")
        raise HTTPException(status_code=500, detail="Döküman silinemedi.")
