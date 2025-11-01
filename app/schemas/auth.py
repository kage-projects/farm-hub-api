from pydantic import BaseModel, EmailStr, Field

class UserRegister(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72) 

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., max_length=100)  

class LoginData(BaseModel):
    token: str

class RegisterData(BaseModel):
    id: str
    name: str
    email: str

class LoginResponse(BaseModel):
    success: bool
    message: str
    data: LoginData

class RegisterResponse(BaseModel):
    success: bool
    message: str
    data: RegisterData