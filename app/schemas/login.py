from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    """
    Schema para la petición de login.
    """
    user: str = Field(..., min_length=1, max_length=50, description="Nombre de usuario o email")
    password: str = Field(..., min_length=6, description="Contraseña del usuario")


class LoginResponse(BaseModel):
    """
    Schema para la respuesta exitosa de login.
    """
    success: bool
    message: str
    user_id: int
    email: str
    user: str
    role: str | None = None
