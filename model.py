from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class DB_HIOKHAO(db.Model):
    __tablename__ = "Data_Hiokhao"
    Date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    Customer_id = db.Column(db.String, nullable=False, primary_key=True)  
    Customer_name = db.Column(db.String(20), unique=False, nullable=False)
    type = db.Column(db.String(20), unique=False, nullable=True)
    Choose = db.Column(db.String(100), unique=False, nullable=True)
    Selection = db.Column(db.String(), unique=False, nullable=True)
    comment = db.Column(db.String(), unique=False, nullable=True)
    Previously_recommended = db.Column(db.Text, nullable=True)  # คอลัมน์ใหม่
    health = db.Column(db.String(), unique=False, nullable=True)
    key = db.Column(db.String(), unique=False, nullable=True)

    def __repr__(self):
        return f'<User {self.Customer_name}>'

# class DB_HIOKHAO(db.Model):
#     __tablename__ = "Data_Hiokhao"
#     Date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
#     Customer_id = db.Column(db.String, nullable=False, primary_key=True)  
#     Customer_name = db.Column(db.String(20), unique=False, nullable=False)
#     type = db.Column(db.String(20), unique=False, nullable=True)
#     Choose = db.Column(db.String(100), unique=False, nullable=True)
#     Selection = db.Column(db.String(), unique=False, nullable=True)
#     comment = db.Column(db.String(), unique=False, nullable=True)
#     Previously_recommended = db.Column(db.Text, nullable=True)  # คอลัมน์ใหม่
#     health = db.Column(db.String(), unique=False, nullable=True)

#     def __repr__(self):
#         return f'<User {self.Customer_name}>'
