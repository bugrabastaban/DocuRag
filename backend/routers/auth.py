from fastapi import APIRouter, HTTPException, Depends, status
from models import RegisterRequest, LoginRequest
from services.supabase_client import get_scoped_client
from dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
def register_user(request: RegisterRequest):
    client = get_scoped_client()
    try:
        response = client.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        return {"message": "Kayıt başarılı", "user": response.user}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=str(e)
        )

@router.post("/login")
def login_user(request: LoginRequest):
    client = get_scoped_client()
    try:
        response = client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.session or not response.user:
            raise HTTPException(status_code=400, detail="Token oluşturulamadı.")
            
        return {
            "access_token": response.session.access_token,
            "user_id": response.user.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Giriş başarısız veya hatalı e-posta/şifre"
        )

@router.get("/me")
def get_me(user_id: str = Depends(get_current_user)):
    """
    Bu endpoint korumalıdır. Sadece geçerli token ile istek atılabilir.
    """
    return {"user_id": user_id}
