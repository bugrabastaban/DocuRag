from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.supabase_client import get_admin_client

# FastAPI security scheme (Header'dan Bearer token'ı otomatik alır)
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Kullanıcının gönderdiği Bearer token'ı (JWT) alır, Supabase üzerinden doğrular
    ve geçerliyse kullanıcının benzersiz kimliğini (user_id) döndürür.
    Geçersiz veya süresi dolmuş token durumunda 401 hatası fırlatır.
    """
    token = credentials.credentials
    admin_client = get_admin_client()
    
    try:
        # Supabase auth üzerinden jwt parametresi ile token doğrulama
        user_response = admin_client.auth.get_user(jwt=token)
        
        if user_response and user_response.user:
            # user.id uuid formatında bir string'tir
            return user_response.user.id
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Geçersiz veya süresi dolmuş token"
        )
        
    except Exception:
        # Token geçersiz olduğunda fırlatılan Supabase hatalarını yakala ve 401 döndür
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Geçersiz veya süresi dolmuş token"
        )
