import os
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client, ClientOptions

# .env dosyasını yükle
load_dotenv()

# Modül seviyesinde admin client instance'ı (singleton benzeri yapı)
_admin_client: Optional[Client] = None

def get_admin_client() -> Client:
    """
    Supabase için service_role yetkilerine sahip admin client döndürür.
    Performans için aynı instance'ı tekrar kullanır.
    """
    global _admin_client
    
    if _admin_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_service_key:
            raise ValueError("SUPABASE_URL ve SUPABASE_SERVICE_ROLE_KEY .env dosyasında bulunamadı.")
            
        _admin_client = create_client(supabase_url, supabase_service_key)
        
    return _admin_client

def get_scoped_client(access_token: Optional[str] = None) -> Client:
    """
    Supabase için anon_key yetkilerine sahip client oluşturur.
    Eğer access_token verilmişse, client'ın isteklerini bu kullanıcının token'ı ile yapar.
    Scoped client her çağrıda yeni bir instance olarak oluşturulur çünkü token'lar farklılık gösterebilir.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_anon_key:
        raise ValueError("SUPABASE_URL ve SUPABASE_ANON_KEY .env dosyasında bulunamadı.")
    
    if access_token:
        # access_token varsa, authorization header'ı override ederek client oluşturuyoruz
        options = ClientOptions(headers={"Authorization": f"Bearer {access_token}"})
        client = create_client(supabase_url, supabase_anon_key, options=options)
        
        # supabase-py'de bazen doğrudan set_session da kullanılabilir:
        # client.auth.set_session({'access_token': access_token, 'refresh_token': ''})
    else:
        client = create_client(supabase_url, supabase_anon_key)
        
    return client
