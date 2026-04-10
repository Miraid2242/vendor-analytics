# create_vendor.py
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

DATABASE_URL = "postgresql://postgres:hmltyhh@localhost:5432/vendor_test"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Vendor(Base):
    __tablename__ = "vendors"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash("password123")

db = SessionLocal()
email = "vendor@example.com"
existing = db.query(Vendor).filter(Vendor.email == email).first()
if existing:
    print(f"Vendor '{email}' already exists!")
else:
    new_vendor = Vendor(email=email, hashed_password=hashed_password)
    db.add(new_vendor)
    db.commit()
    print(f"Vendor '{email}' created successfully!")
db.close()
