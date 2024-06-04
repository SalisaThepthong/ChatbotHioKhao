import requests
from flask import Flask, request, jsonify
from model import db, DB_HIOKHAO
from config import Config
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import numpy as np
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import google.generativeai as genai
from flask_redis import FlaskRedis
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from publisher import publish_message
import pika
import json
app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
redis_client = FlaskRedis(app)  # Initialize Redis


app.config['JWT_SECRET_KEY'] = 'nampunJWT_SECRET_KEY'
jwt = JWTManager(app)

# ตั้งค่า API Key ของ Google Generative AI
GOOGLE_API_KEY = 'AIzaSyDLUI8dq8uGN7mGg94_rqyy9FRT1kdzCAM'
genai.configure(api_key=GOOGLE_API_KEY)

with app.app_context():
    db.create_all()

# โหลดข้อมูลจากไฟล์ CSV
df = pd.read_csv('name1.csv', engine='python')

# แปลงข้อความในคอลัมน์ 'type' ให้เป็นเวกเตอร์ตัวเลขด้วย TF-IDF Vectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['type'])

# เตรียมโมเดล KNN โดยใช้ metric cosine similarity
knn = NearestNeighbors(n_neighbors=30, metric='cosine')
knn.fit(X)


def publish_message(message):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.exchange_declare(exchange='logs', exchange_type='fanout')

    channel.basic_publish(exchange='logs', routing_key='', body=json.dumps(message))
    connection.close()

def generate_token(Customer_id, Customer_name):
    access_token = create_access_token(identity={'Customer_id': Customer_id, 'Customer_name': Customer_name})
    return access_token

# ฟังก์ชันแนะนำอาหาร
def recommend_food(Customer_id):
    customer = DB_HIOKHAO.query.filter_by(Customer_id=Customer_id).first()
    if customer:
        choose = customer.Choose

        # Retrieve previously recommended from Redis
        previously_recommended = redis_client.lrange(f"recommended:{Customer_id}", 0, -1)
        previously_recommended = [rec.decode('utf-8') for rec in previously_recommended]

        genre_vector = vectorizer.transform([choose])
        distances, indices = knn.kneighbors(genre_vector, n_neighbors=20)

        recommended = df.iloc[indices[0]]
        recommended = recommended[~recommended['name'].isin(previously_recommended)]

        if recommended.empty:
            return None, None

        recommended_title = np.random.choice(recommended['name'].unique(), 1, replace=False)[0]
        recommended_url = recommended.loc[recommended['name'] == recommended_title, 'url'].values[0]

        # Update previously recommended in Redis
        redis_client.rpush(f"recommended:{Customer_id}", recommended_title)

        return recommended_title, recommended_url
    else:
        return None, None

# เพิ่มผู้ใช้
@app.route('/users', methods=['POST'])
def add_user():
    Customer_id = request.args.get('Customer_id')
    Customer_name = request.args.get('Customer_name')
    type = request.args.get('type')
    Choose = request.args.get('Choose')
    Selection = request.args.get('Selection')
    comment = request.args.get('comment')

    existing_user = DB_HIOKHAO.query.filter_by(Customer_id=Customer_id).first()

    if existing_user:
        existing_user.Customer_name = Customer_name
        existing_user.type = type
        existing_user.Choose = Choose
        existing_user.Selection = Selection
        existing_user.comment = comment
        db.session.commit()
        message = 'อัพเดตผู้ใช้สำเร็จ'
        health = existing_user.health
    else:
        token = generate_token(Customer_id, Customer_name)
        new_user = DB_HIOKHAO(
            Customer_id=Customer_id,
            Customer_name=Customer_name,
            type=type,
            Choose=Choose,
            Selection=Selection,
            comment=comment,
            health=health
        )
        new_user.Token = token
        db.session.add(new_user)
        db.session.commit()
        message = 'เพิ่มผู้ใช้สำเร็จ'
    #print("AA")
    publish_message({'Customer_id': Customer_id, 'message': message})
    print("เข้าเเล้ว")
    return jsonify({'message': message, 'access_token': token}), 201


#รับคำแนะนำ
@app.route('/recommendation', methods=['POST'])
def get_recommendation():
    customer_id = request.args.get('Customer_id')
    if customer_id:
        recommended_food, recommended_url = recommend_food(customer_id)
        if recommended_food:
            user = DB_HIOKHAO.query.filter_by(Customer_id=customer_id).first()
            if user:
                user.Selection = recommended_food
                db.session.commit()

                # ใช้โมเดล Generative AI เพื่อสร้างเนื้อหา
                model = genai.GenerativeModel('gemini-1.5-pro-latest')
                response = model.generate_content(f"โภชนาการของ {recommended_food}").text
                response_text = f"โภชนาการของ {recommended_food} {response}"
                return jsonify({'recommendation': recommended_food,
                                 'url': recommended_url, 
                                 'response': response_text
                                 
                                 }), 200
            else:
                return jsonify({'message': 'ไม่พบผู้ใช้'}), 404
        else:
            return jsonify({'message': 'ไม่มีคำแนะนำอาหาร'}), 404
    else:
        return jsonify({'message': 'จำเป็นต้องมี Customer_id'}), 400

# เพิ่มความคิดเห็น
@app.route('/comment', methods=['POST'])
def add_comment():
    customer_id = request.args.get('Customer_id')
    comment = request.args.get('comment')

    if not customer_id or not comment:
        return jsonify({'message': 'จำเป็นต้องมี Customer_id และ comment'}), 400

    user = DB_HIOKHAO.query.filter_by(Customer_id=customer_id).first()

    if user:
        user.comment = comment
        db.session.commit()
        return jsonify({'message': 'เพิ่มความคิดเห็นสำเร็จ'}), 200
    else:
        return jsonify({'message': 'ไม่พบผู้ใช้'}), 404

if __name__ == '__main__':
    app.run(debug=True)