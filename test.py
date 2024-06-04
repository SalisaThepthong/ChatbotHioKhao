from flask import Flask, request, jsonify
from model import db, DB_HIOKHAO
from config import Config
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import numpy as np
import schedule
import time
import os

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

# Load data from CSV
df = pd.read_csv('name1.csv', engine='python')

# Convert text in 'type' column to numerical vectors using TF-IDF Vectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['type'])

# Prepare KNN model using cosine similarity metric
knn = NearestNeighbors(n_neighbors=50, metric='cosine')
knn.fit(X)

# Function to recommend food
def recommend_food(Customer_id):
    customer = DB_HIOKHAO.query.filter_by(Customer_id=Customer_id).first()
    if customer:
        choose = customer.Choose
        genre_vector = vectorizer.transform([choose])
        distances, indices = knn.kneighbors(genre_vector, n_neighbors=30)
        recommended = df.iloc[indices[0]]
        recommended_title = np.random.choice(recommended['name'].unique(), 1, replace=False)[0]
        recommended_url = recommended.loc[recommended['name'] == recommended_title, 'url'].values[0]
        return recommended_title, recommended_url
    else:
        return None, None
#---------------------------------------------------------------------------------------------------------------
def recommend_food(Customer_id):
    customer = DB_HIOKHAO.query.filter_by(Customer_id=Customer_id).first()
    if customer:
        choose = customer.Choose
        previously_recommended = customer.Previously_recommended.split(',') if customer.Previously_recommended else []

        genre_vector = vectorizer.transform([choose])
        distances, indices = knn.kneighbors(genre_vector, n_neighbors=100)

        recommended = df.iloc[indices[0]]
        recommended = recommended[~recommended['name'].isin(previously_recommended)]

        if recommended.empty:
            return None, None

        recommended_title = np.random.choice(recommended['name'].unique(), 1, replace=False)[0]
        recommended_url = recommended.loc[recommended['name'] == recommended_title, 'url'].values[0]

        # อัปเดตรายการที่แนะนำก่อนหน้านี้
        previously_recommended.append(recommended_title)
        customer.Previously_recommended = ','.join(previously_recommended)
        db.session.commit()

        return recommended_title, recommended_url
    else:
        return None, None

#---------------------------------------------------------------------------------------------------------------
@app.route('/users', methods=['POST'])
def add_user():
    Customer_id = request.args.get('Customer_id')
    Customer_name = request.args.get('Customer_name')
    type = request.args.get('type')
    Choose = request.args.get('Choose')
    Selection = request.args.get('Selection')
    comment = request.args.get('comment')
    print(Customer_id, Customer_name, type, Choose, Selection, comment)

    # Check if user already exists
    existing_user = DB_HIOKHAO.query.filter_by(Customer_id=Customer_id).first()

    if existing_user:
        # Update existing user
        existing_user.Customer_name = Customer_name
        existing_user.type = type
        existing_user.Choose = Choose
        existing_user.Selection = Selection
        existing_user.comment = comment
        db.session.commit()
        message = 'User updated successfully'
    else:
        # Add new user
        # Add new user
        new_user = DB_HIOKHAO(
            Customer_id=Customer_id,
            Customer_name=Customer_name,
            type=type,
            Choose=Choose,
            Selection=Selection,
            comment=comment,
            Previously_recommended=''  # Add this line to initialize Previously_recommended
)
        db.session.add(new_user)
        db.session.commit()
        message = 'User added successfully'


        return jsonify({'message': message}), 201
#------------------------------------------------------------------------------------------------------
 


#-------------------------------------------------------------------------------------------------------
#Add comment ลง Database 
@app.route('/comment', methods=['POST'])
def add_comment():
    customer_id = request.args.get('Customer_id')
    comment = request.args.get('comment')

    if not customer_id or not comment:
        return jsonify({'message': 'Customer_id and comment are required parameters'}), 400

    user = DB_HIOKHAO.query.filter_by(Customer_id=customer_id).first()

    if user:
        user.comment = comment
        db.session.commit()
        return jsonify({'message': 'Comment added successfully'}), 200
    else:
        return jsonify({'message': 'User not found'}), 404



if __name__ == "__main__":
    app.run(debug=True)
