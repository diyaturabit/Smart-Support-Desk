from app import db

class Customer(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(20),unique=True,nullable=False)
    age=db.Column(db.Integer)
    email=db.Column(db.String(120),unique=True,nullable=False)
    company=db.Column(db.String(120),nullable=False)
    created_at=db.Column(db.DateTime,nullable=False,default=db.func.current_timestamp())
    updated_at=db.Column(db.DateTime,nullable=False,default=db.func.current_timestamp(),onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"Name: {self.name} , Company: {self.company}"

class Ticket(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(100),nullable=False)
    description=db.Column(db.Text,nullable=False)
    status=db.Column(db.String(20),nullable=False,default='Open')
    priority=db.Column(db.String(20),nullable=False,default='Medium')
    customer_id=db.Column(db.Integer,db.ForeignKey('customer.id'),nullable=False)
    created_at=db.Column(db.DateTime,nullable=False,default=db.func.current_timestamp())
    updated_at=db.Column(db.DateTime,nullable=False,default=db.func.current_timestamp(),onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f"Name: {self.name} , Company: {self.company} -- Status:{self.status}"
