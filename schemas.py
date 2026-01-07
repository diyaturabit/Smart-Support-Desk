from pydantic import BaseModel,EmailStr
from typing import Literal

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

    

