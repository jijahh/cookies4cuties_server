from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from datetime import datetime

class OrderItemSchema(BaseModel):
    product_id: Literal["box_of_6", "single"]
    quantity: int = Field(..., gt=0)
    unit_price: float

class OrderSubmitSchema(BaseModel):
    email: EmailStr
    phone_number: str
    items: List[OrderItemSchema]
    total_price: float
    payment_method: Literal["CASH_PICKUP", "CASH_DELIVERY", "ONLINE"]
    pickup_location: Literal["LOCATION_A", "LOCATION_B", "LOCATION_C"]

class OrderResponseSchema(OrderSubmitSchema):
    id: str
    created_at: datetime
    order_status: str
    is_verified: bool
    proof_of_payment_url: Optional[str] = None