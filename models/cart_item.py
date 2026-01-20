from pydantic import BaseModel


class CartItem(BaseModel):
    name: str
    quantity: str
    price: float
    color: str