from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Body

# -----------------------------
# Database setup
# -----------------------------
DATABASE_URL = "postgresql://postgres:hmltyhh@localhost:5432/vendor_test"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class RegisterRequest(BaseModel):
    email: str
    password: str

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# -----------------------------
# Password hashing
# -----------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -----------------------------
# JWT configuration
# -----------------------------
SECRET_KEY = "your_secret_key_here"  # change this to a random string
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict, expires_delta: int = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# -----------------------------
# FastAPI setup
# -----------------------------
app = FastAPI()
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Pydantic schemas
# -----------------------------
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str

# -----------------------------
# Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/register")
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(Vendor).filter(Vendor.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = pwd_context.hash(request.password)
    new_vendor = Vendor(email=request.email, hashed_password=hashed)
    db.add(new_vendor)
    db.commit()
    return {"message": "Vendor registered successfully"}
# -----------------------------
# Login endpoint
# -----------------------------
@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).filter(Vendor.email == request.email).first()
    if not vendor:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not pwd_context.verify(request.password, vendor.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token_data = {"sub": vendor.email}
    token = create_access_token(token_data)

    return {
        "access_token": token,
        "token_type": "bearer",
        "vendor_id": vendor.id   # ✅ added vendor_id
    }
