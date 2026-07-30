import sys
import os

# "services" modülünün bulunabilmesi için sys.path'e bulunduğumuz klasörü ekliyoruz
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.supabase_client import get_admin_client

def test_supabase_connection():
    print("Supabase admin client test ediliyor...")
    try:
        # Admin client oluştur
        admin_client = get_admin_client()
        print("Admin client başarıyla oluşturuldu.")
        
        # 'documents' tablosundan 5 satır çekmeyi dene
        print("'documents' tablosuna sorgu atılıyor...")
        response = admin_client.table("documents").select("*").limit(5).execute()
        
        # Yanıtı yazdır
        data = response.data
        print(f"Sorgu başarılı. {len(data)} adet kayıt bulundu.")
        print("Veri:", data)
        
    except Exception as e:
        print("\nBir hata oluştu (Tablo mevcut olmayabilir veya kimlik doğrulama hatası vs.):")
        print(str(e))

if __name__ == "__main__":
    test_supabase_connection()
