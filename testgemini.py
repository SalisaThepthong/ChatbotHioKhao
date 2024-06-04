from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Set your Google API Key
GOOGLE_API_KEY = 'AIzaSyDLUI8dq8uGN7mGg94_rqyy9FRT1kdzCAM'
genai.configure(api_key=GOOGLE_API_KEY)

# Route to list models
@app.route('/models', methods=['GET'])
def list_models():
    models = [f"โภชนาการของ {m.name}" for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]


    #models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    return jsonify(models)

# Route to generate content
@app.route('/generate', methods=['POST'])
def generate_content():
    prompt = request.args.get('prompt')
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    response = model.generate_content(prompt)
    return jsonify({"content": response.text})

if __name__ == '__main__':
    app.run(debug=True)
