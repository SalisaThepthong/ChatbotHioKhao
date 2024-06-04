import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
import numpy as np

# โหลดข้อมูลจากไฟล์ Excel
df = pd.read_csv('name1.csv', engine='python')
#, sheet_name='name1')

# แปลงข้อความหมวดหมู่หนังเป็นtypeเชิงตัวเลข
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['type'])

# เตรียมโมเดล KNN
knn = NearestNeighbors(n_neighbors=50, metric='cosine')
knn.fit(X)

# ฟังก์ชันเพื่อแนะอาหาร
def recommend_movies(genre_input, df, knn, vectorizer):
    genre_vector = vectorizer.transform([genre_input])
    distances, indices = knn.kneighbors(genre_vector, n_neighbors=30)
    
    recommended_titles = df.iloc[indices[0]]['name'].unique()
    return np.random.choice(recommended_titles, 1, replace=False)

# รับอินพุตจากผู้ใช้
user_input = 'littleSweet'#Mild|Medium|Hot|littleSw|mediumSweet|verySweet

# ให้คำแนะนำ
recommended_movies = recommend_movies(user_input, df, knn, vectorizer)
print("สิ่งที่คุณสามารถทำนายได้:", recommended_movies)
print("สิ่งที่คุณสามารถทำนายได้:", 'type')