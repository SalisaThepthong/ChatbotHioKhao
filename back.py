import atexit
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
from publisher import publish_message_to_queue
import pika
import json
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
redis_client = FlaskRedis(app)

# ตั้งค่า API Key สำหรับ Google Generative AI
genai.configure(api_key='AIzaSyDLUI8dq8uGN7mGg94_rqyy9FRT1kdzCAM')

with app.app_context():
    db.create_all()

# Load data from CSV file
df = pd.read_csv('name1.csv', engine='python')

# Prepare TF-IDF vectorization
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['type'])

# Prepare KNN model with cosine similarity metric
knn = NearestNeighbors(n_neighbors=30, metric='cosine')
knn.fit(X)

# Start ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=4)

# Function to recommend food with context
def recommend_food_with_context(customer_id):
    with app.app_context():
        return recommend_food(customer_id)
    

# Function to recommend food
def recommend_food(Customer_id):
    customer = DB_HIOKHAO.query.filter_by(Customer_id=Customer_id).first()
    if customer:
        app.logger.info(f"Found customer: {customer}")
        choose = customer.Choose
        app.logger.info(f"Customer's choice: {choose}")

        previously_recommended = redis_client.lrange(f"recommended:{Customer_id}", 0, -1)
        previously_recommended = [rec.decode('utf-8') for rec in previously_recommended]
        app.logger.info(f"Previously recommended: {previously_recommended}")

        genre_vector = vectorizer.transform([choose])
        app.logger.info(f"Genre vector: {genre_vector.toarray()}")

        distances, indices = knn.kneighbors(genre_vector, n_neighbors=20)
        app.logger.info(f"KNN distances: {distances}, indices: {indices}")

        recommended = df.iloc[indices[0]]
        app.logger.info(f"Initial recommendations: {recommended}")

        recommended = recommended[~recommended['name'].isin(previously_recommended)]
        app.logger.info(f"Filtered recommendations: {recommended}")

        if recommended.empty:
            app.logger.warning("No new recommendations available")
            return None, None

        recommended_title = np.random.choice(recommended['name'].unique(), 1, replace=False)[0]
        recommended_url = recommended.loc[recommended['name'] == recommended_title, 'url'].values[0]

        redis_client.rpush(f"recommended:{Customer_id}", recommended_title)
        app.logger.info(f"Recommended title: {recommended_title}, URL: {recommended_url}")

        return recommended_title, recommended_url
    else:
        app.logger.warning(f"No customer found with Customer_id: {Customer_id}")
        return None, None


# Route to add user
@app.route('/users', methods=['POST'])
def add_user():
    Customer_id = request.args.get('Customer_id')
    Customer_name = request.args.get('Customer_name')
    type = request.args.get('type')
    Choose = request.args.get('Choose')
    Selection = request.args.get('Selection')
    comment = request.args.get('comment')
    health= request.args.get('health')

    existing_user = DB_HIOKHAO.query.filter_by(Customer_id=Customer_id).first()

    if existing_user:
        existing_user.Customer_name = Customer_name
        existing_user.type = type
        existing_user.Choose = Choose
        existing_user.Selection = Selection
        existing_user.comment = comment
        existing_user.health = health
        db.session.commit()
        message = 'อัพเดตผู้ใช้สำเร็จ'
    else:
        new_user = DB_HIOKHAO(
            Customer_id=Customer_id,
            Customer_name=Customer_name,
            type=type,
            Choose=Choose,
            Selection=Selection,
            comment=comment,
            health=health
        )
        db.session.add(new_user)
        db.session.commit()
        message = 'เพิ่มผู้ใช้สำเร็จ'

    return jsonify({'message': message}), 201

def analyze_nutrition(recommendation, health):
    # ทำการวิเคราะห์โภชนาการร่วมกับข้อมูลสุขภาพที่นี่
    # นี่เป็นตัวอย่างง่ายๆ ที่แสดงให้เห็นวิธีการวิเคราะห์
    analysis_result = f"ผลวิเคราะห์โภชนาการ: {recommendation} เหมาะกับโรค: {health} หรือไม่?"
    # ส่งผลวิเคราะห์ไปยังหน่วยงานที่ต้องการ
    return analysis_result
# Route to add health data
@app.route('/health', methods=['POST'])
def add_health_data():
    customer_id = request.args.get('Customer_id')
    health = request.args.get('health')

    if not customer_id or not health:
        return jsonify({'message': 'จำเป็นต้องมี Customer_id และ health_data'}), 400

    user = DB_HIOKHAO.query.filter_by(Customer_id=customer_id).first()

    if user:
        user.health = health
        db.session.commit()
        return jsonify({'message': 'เพิ่มข้อมูลสุขภาพสำเร็จ'}), 200
    else:
        return jsonify({'message': 'ไม่พบผู้ใช้'}), 404

@app.route('/recommendation', methods=['POST'])
def get_recommendation():
    customer_id = request.args.get('Customer_id')
    app.logger.info(f"Received request for recommendation with Customer_id: {customer_id}")
    
    if customer_id:
        recommended_food, recommended_url = recommend_food(customer_id)
        app.logger.info(f"Recommended food: {recommended_food}, URL: {recommended_url}")
        
        if recommended_food:
            user = DB_HIOKHAO.query.filter_by(Customer_id=customer_id).first()
            app.logger.info(f"Found user: {user}")
            
            if user:
                user.Selection = recommended_food
                db.session.commit()

                # ใช้โมเดล Generative AI เพื่อสร้างเนื้อหา
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro-latest')
                    response = model.generate_content(f"โภชนาการของ {recommended_food}").text
                    response_text = f"โภชนาการของ {recommended_food}: {response}"
                except Exception as e:
                    app.logger.error(f"Error generating nutrition content: {e}")
                    response_text = "ไม่สามารถสร้างข้อมูลโภชนาการได้"

                # ดึงข้อมูลสุขภาพจากฐานข้อมูล
                health = user.health
                print(health)
                print("ออกละรับข้อมูลสุขภาพ")
                # วิเคราะห์โภชนาการร่วมกับข้อมูลสุขภาพ
                try:
                    model1 = genai.GenerativeModel('gemini-1.5-pro-latest')
                    health_analysis = model1.generate_content(f"ผลวิเคราะห์โภชนาการ: {recommended_food} เหมาะกับโรค: {health}").text
                    if health_analysis:
                        analysis_result = f"ผลวิเคราะห์โภชนาการ: {recommended_food} เหมาะกับโรค: {health} {health_analysis}"
                    else:
                        analysis_result = f"ผลวิเคราะห์โภชนาการ: {recommended_food} เหมาะกับโรค: {health} ไม่สามารถวิเคราะห์ได้"
                except Exception as e:
                    app.logger.error(f"Error in health analysis: {e}")
                    analysis_result = f"ผลวิเคราะห์โภชนาการ: {recommended_food} เหมาะกับโรค: {health} ไม่สามารถวิเคราะห์ได้"

                return jsonify({
                    'recommendation': recommended_food,
                    'url': recommended_url,
                    'response': response_text,
                    'health_analysis': analysis_result
                }), 200
            else:
                app.logger.warning(f"No user found with Customer_id: {customer_id}")
                return jsonify({'message': 'ไม่พบผู้ใช้'}), 403
        else:
            app.logger.warning(f"No food recommendation found for Customer_id: {customer_id}")
            return jsonify({'message': 'ไม่มีคำแนะนำอาหาร'}), 404
    else:
        app.logger.warning("Customer_id is required")
        return jsonify({'message': 'จำเป็นต้องมี Customer_id'}), 400



    

# Route to add comment
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




# Function to clear Redis database
def clear_redis():
    redis_client.flushdb()
    app.logger.info("Cleared Redis database")

# Register function to clear Redis on exit
atexit.register(clear_redis)


if __name__ == '__main__':
    app.run(debug=True)