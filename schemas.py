from pydantic import BaseModel,EmailStr
from typing import Literal,Optional

class CustomerCreate(BaseModel):
    name:str
    age:int
    email:EmailStr
    company:str

class CustomerResponse(BaseModel):
    id:int
    name:str
    age:int
    email:EmailStr
    company:str

class TicketCreate(BaseModel):
    title:str
    description:str
    priority:Literal["Low","Medium","High"]
    customer_id:int

class TicketResponse(BaseModel):
    id:int
    title:str
    description:str
    status:Literal["Open","Inprogress","Closed"]
    priority:str
    customer_id:int

 
class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[Literal["Open", "Inprogress", "Closed"]] = None
    customer_id: Optional[int] = None
