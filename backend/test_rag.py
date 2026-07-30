import asyncio
from services.rag import answer_question
from services.supabase_client import get_admin_client

async def test_rag():
    admin_client = get_admin_client()
    
    print("Veritabanından rastgele bir döküman aranıyor...")
    # Sisteme en son yüklenen 1 dökümanı alalım
    res = admin_client.table("documents").select("*").order("created_at", desc=True).limit(1).execute()
    
    if not res.data:
        print("Veritabanında döküman bulunamadı. Lütfen sistemi kullanarak bir dosya yükleyin.")
        return
        
    doc = res.data[0]
    user_id = doc["user_id"]
    document_id = doc["id"]
    filename = doc["filename"]
    
    print(f"Döküman bulundu: {filename}")
    print(f"User ID: {user_id}")
    print(f"Document ID: {document_id}")
    
    # Apex Dynamics PDF'sine uygun bir soru
    question = "Apex Dynamics'in CEO'su kimdir ve Ar-Ge merkezi nerededir?"
    print(f"\nSORU: {question}")
    print("-" * 50)
    
    print("RAG Süreci başlatılıyor (Embedding -> Vector Search -> Gemini)...")
    
    try:
        # RAG fonksiyonunu çalıştır
        result = await answer_question(question, user_id, document_id)
        
        print("\nCEVAP:")
        print(result["answer"])
        print("-" * 50)
        print("KAYNAK CHUNK ID'leri:")
        for source in result["sources"]:
            print(f"- {source}")
            
    except Exception as e:
        print(f"\nRAG işlemi sırasında hata oluştu: {e}")

if __name__ == "__main__":
    # Async fonksiyonu çalıştır
    asyncio.run(test_rag())
