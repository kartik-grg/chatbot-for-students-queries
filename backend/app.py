from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
import jwt
import datetime
from bson import ObjectId

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = "your_secret_key"  # Use a secure secret key

bcrypt = Bcrypt(app)

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["chatbot"]  # Replace with your database name
queries_collection = db["queries"]  # Replace with your collection name
users_collection = db["users"]  # Replace with your collection name

@app.route('/api/inspect-routes', methods=['GET'])
def inspect_routes():
    return jsonify({rule.rule: rule.endpoint for rule in app.url_map.iter_rules()})

@app.route('/', methods=['GET'])
def home():
    return "Welcome to the Flask Backend!"

# Signup Route
@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    if users_collection.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
    users_collection.insert_one({"username": username, "email": email, "password": hashed_password})
    return jsonify({"message": "User registered successfully"}), 201

# Login Route
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    print('username: ', username, "passs: ", password)
    user = users_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):
        token = jwt.encode(
            {"user_id": str(user["_id"]), "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            app.config["SECRET_KEY"],
            algorithm="HS256"
        )
        return jsonify({"token": token}), 200

    return jsonify({"error": "Invalid credentials"}), 401

# Login Route for Admin
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if email == "admin@example.com" and password == "admin123":
        token = jwt.encode({"role": "admin"}, app.config["SECRET_KEY"], algorithm="HS256")
        return jsonify({"token": token}), 200
    
    return jsonify({"error": "Invalid credentials"}), 401

# Search and Save Query
@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    question = data.get("question")

    if not question:
        return jsonify({"error": "Question not provided"}), 400 

    # Search in the main collection
    query = queries_collection.find_one({"question": question})
    if query and query["answered"]!=False:
        return jsonify({"answer": query["answer"]})

    # Add to unanswered collection if not found
    queries_collection.insert_one({"question": question, "answered": False})
    return jsonify({"message": "Query not found, added to unanswered collection"}), 404

# # Get Unanswered Queries
# @app.route('/api/unanswered-queries', methods=['GET'])
# def get_unanswered_queries():
#     # print("Get Unanswered Queries Route")
#     unanswered = list(queries_collection.find({"answered": False}))
#     return jsonify({"queries": unanswered})

@app.route('/api/unanswered-queries', methods=['GET'])
def get_unanswered_queries():
    unanswered = list(queries_collection.find({"answered": False}))
    # Convert ObjectId to string for each query
    for query in unanswered:
        query["_id"] = str(query["_id"])

    print(unanswered)

    return jsonify({"queries": unanswered}), 200

# Add Response to Query
@app.route('/api/add-response', methods=['POST'])
def add_response():
    data = request.json
    query_id = data.get("id")
    response = data.get("response")

    if not query_id or not response:
        return jsonify({"error": "Missing query ID or response"}), 400

    queries_collection.update_one(
        {"_id": ObjectId(query_id)},
        {"$set": {"answer": response, "answered": True}}
    )
    return jsonify({"message": "Response added successfully"})



if __name__ == "__main__":
    app.run(debug=True)
