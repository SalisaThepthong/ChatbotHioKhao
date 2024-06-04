import os
class Config:
   # SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mydatabase.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = "redis://localhost:6379/0"  # Redis URL
    
   
# RabbitMQ Configuration
rabbitmq_host = os.environ.get('RABBITMQ_HOST') or 'localhost'
rabbitmq_port = os.environ.get('RABBITMQ_PORT') or 5672
rabbitmq_username = os.environ.get('RABBITMQ_USERNAME') or 'guest'
rabbitmq_password = os.environ.get('RABBITMQ_PASSWORD') or 'guest'
# class Config:
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///data.db')
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your_jwt_secret_key')  # คุณสามารถเปลี่ยนเป็นคีย์ลับของคุณเอง