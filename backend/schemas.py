from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    stock: int

class ProductCreate(ProductBase):
    vendor_id: int

class ProductUpdate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    vendor_id: int

    class Config:
        orm_mode = True
