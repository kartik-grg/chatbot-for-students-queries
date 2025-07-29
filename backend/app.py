from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import jwt
import datetime
from bson import ObjectId
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import CSVLoader
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from langsmith import Client
import uvicorn
from langchain.prompts import ChatPromptTemplate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os.path
from time import time
from difflib import SequenceMatcher
from textblob import TextBlob
from collections import defaultdict, Counter
from flask_mail import Mail, Message

# Load environment variables
load_dotenv()   
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
LANGSMITH_API_KEY = os.environ["LANGSMITH_API_KEY"]

os.environ["LANGSMITH_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Faculty Chatbot"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"

app = Flask(__name__)
CORS(app)

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # or another SMTP
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv("EMAIL_USER")
app.config['MAIL_PASSWORD'] = os.getenv("EMAIL_PASS")

mail = Mail(app)

app.config["SECRET_KEY"] = "your_secret_key"  # Use a secure secret key

bcrypt = Bcrypt(app)

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client["chatbot"]
queries_collection = db["queries"]
users_collection = db["users"]

# Create chat_history collection with indexes if it doesn't exist
if "chat_history" not in db.list_collection_names():
    chat_history_collection = db.create_collection("chat_history")
    # Create indexes for better query performance
    chat_history_collection.create_index([("user_id", 1)])
    chat_history_collection.create_index([("timestamp", -1)])
else:
    chat_history_collection = db["chat_history"]

template = """
You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. 
If the provided context does not contain enough information to answer the question accurately, respond with exactly "I do not know."
Keep the answer concise and within three sentences.

Question: {question} 
Context: {context} 
Answer:
"""

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            # Skip if PDF has no pages
            if len(pdf_reader.pages) == 0:
                print(f"Skipping empty PDF: {pdf}")
                continue
            for page in pdf_reader.pages:
                text += page.extract_text()
        except Exception as e:
            print(f"Error reading PDF {pdf}: {str(e)}")
            continue
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",    # Changed from 'separators' to 'separator'
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

def get_vectore_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY,
        task_type="retrieval_query" 
    )
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    return vectorstore

def create_embeddings():
    resources_dir = os.path.join(os.getcwd(), "resources")
    pdf_files = []
    
    # Collect valid PDF files
    for filename in os.listdir(resources_dir):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(resources_dir, filename)
            try:
                # Try to open the PDF to check if it's valid
                with open(filepath, 'rb') as f:
                    pdf = PdfReader(f)
                    if len(pdf.pages) > 0:
                        pdf_files.append(filepath)
                    else:
                        print(f"Skipping empty PDF: {filename}")
            except Exception as e:
                print(f"Error checking PDF {filename}: {str(e)}")
                continue
    
    if not pdf_files:
        raise Exception("No valid PDF files found in resources directory")
    
    print(f"Found {len(pdf_files)} valid PDF files")
    text = get_pdf_text(pdf_files)
    chunks = get_text_chunks(text)
    vectorstore = get_vectore_store(chunks)
    print("Embeddings created successfully!")
    return vectorstore

# Build the vector store once at startup
vectorstore_global = create_embeddings()

# Session management constants
SESSION_CLEANUP_INTERVAL = 3600  # Cleanup every hour
SESSION_TIMEOUT = 7200  # Session timeout after 2 hours of inactivity
conversation_memories = {}  # Store conversation memories by session
session_timestamps = {}    # Track last activity time for each session

def cleanup_if_needed():
    """Clean up expired sessions if needed"""
    current_time = time()
    expired_sessions = [
        sid for sid, last_active in session_timestamps.items()
        if current_time - last_active > SESSION_TIMEOUT
    ]
    
    for sid in expired_sessions:
        if sid in conversation_memories:
            del conversation_memories[sid]
        if sid in session_timestamps:
            del session_timestamps[sid]
    
    if expired_sessions:
        print(f"Cleaned up {len(expired_sessions)} expired sessions")

@app.before_request
def before_request():
    """Run cleanup before each request"""
    cleanup_if_needed()

def update_session_timestamp(session_id):
    """Update last activity time for a session"""
    session_timestamps[session_id] = time()

def get_conversation_chain(vectorstore, session_id):
    """Create or retrieve a conversation chain for a session"""
    update_session_timestamp(session_id)
    
    if session_id not in conversation_memories:
        memory = ConversationBufferMemory(
            memory_key='chat_history',
            return_messages=True
        )
        conversation_memories[session_id] = memory
    else:
        memory = conversation_memories[session_id]

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-pro",
        temperature=0,
        google_api_key=GOOGLE_API_KEY
    )

    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3}),
        memory=memory,
        combine_docs_chain_kwargs={"prompt": ChatPromptTemplate.from_template(template)}
    )
    return conversation_chain

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

def similar(a, b):
    """Calculate similarity ratio between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def is_general_chat(text):
    """Detect if the input is general chat with improved matching"""
    general_phrases = {
        'greetings': {
            'patterns': ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening'],
            'response': 'Hello! How can I help you today?'
        },
        'farewell': {
            'patterns': ['bye', 'goodbye', 'see you', 'good night'],
            'response': 'Goodbye! Have a great day!'
        },
        'thanks': {
            'patterns': ['thanks', 'thank you', 'appreciate it', 'thx'],
            'response': 'You\'re welcome! Let me know if you need anything else.'
        },
        'acknowledgment': {
            'patterns': ['nice', 'ok', 'okay', 'great', 'good', 'understood', 'alright'],
            'response': 'Is there anything specific you\'d like to know?'
        },
        'well_being': {
            'patterns': ['how are you', 'how do you do', 'how\'s it going'],
            'response': 'I\'m functioning well, thank you! How can I assist you today?'
        }
    }
    
    text_lower = text.lower().strip()
    
    # Check for matches with similarity threshold
    for category in general_phrases.values():
        for pattern in category['patterns']:
            # Check if pattern is fully contained in text
            if pattern in text_lower:
                return category['response']
            
            # Check for similar patterns with 0.85 similarity threshold
            if len(text_lower) <= len(pattern) * 1.5 and similar(text_lower, pattern) > 0.85:
                return category['response']
            
            # Check for partial matches in longer sentences
            words = text_lower.split()
            if len(words) <= 4:  # Only check short phrases
                for word in words:
                    if similar(word, pattern) > 0.9:
                        return category['response']
    
    return None

# Updated Search and Save Query endpoint with Conversational Retrieval Chain
@app.route('/api/query', methods=['POST'])
def query():
    data = request.json
    question = data.get("question")
    session_id = data.get("session_id")  # Frontend should provide this
    user_token = request.headers.get('Authorization')
    
    if not question:
        return jsonify({"error": "Question not provided"}), 400
    
    if not session_id:
        session_id = str(datetime.datetime.now().timestamp())  # Fallback session ID
    
    print("\n" + "="*50)
    print(f"Session: {session_id}")
    print("Question received:", question)
    print("="*50)

    # Check if it's general chat
    general_response = is_general_chat(question)
    if (general_response):
        # Get chat history for this session
        memory = conversation_memories.get(session_id)
        chat_history = []
        if memory:
            memory.chat_memory.add_user_message(question)
            memory.chat_memory.add_ai_message(general_response)
            chat_history = [str(msg) for msg in memory.chat_memory.messages]
        
        return jsonify({
            "answer": general_response,
            "chat_history": chat_history,
            "status": "answered",
            "session_id": session_id
        }), 200

    try:
        # Get conversation chain for this session
        chat_chain = get_conversation_chain(vectorstore_global, session_id)
        
        # Get response
        result = chat_chain({"question": question})
        answer = result["answer"].strip()  # Remove .lower() to preserve case
        
        print("\nGenerated answer:", answer)
        print("="*50 + "\n")
        
        # Check for various forms of "no answer" responses
        no_answer_phrases = [
            "i do not know",
            "i don't know",
            "cannot find",
            "no information",
            "insufficient information",
            "the document does not contain",
            "no relevant information",
            "cannot answer",
            "unable to answer"
        ]
        
        if any(phrase in answer.lower() for phrase in no_answer_phrases):
            print("No answer found - adding to unanswered queries")
            # Default user_id to None
            user_id = None
            
            if user_token:
                try:
                    # Decode token to get user_id
                    payload = jwt.decode(user_token.split(' ')[1], 
                                    app.config["SECRET_KEY"], 
                                    algorithms=["HS256"])
                    user_id = ObjectId(payload.get('user_id'))
                except Exception as e:
                    print(f"Error decoding token for unanswered query: {str(e)}")

            queries_collection.insert_one({
                "question": question, 
                "answered": False,
                "user_id": user_id,
                "timestamp": datetime.datetime.utcnow()
            })
            return jsonify({
                "answer": "I apologize, but I don't have enough information to answer this question accurately. Your query has been logged for manual review.",
                "status": "unanswered",
                "session_id": session_id
            }), 404
        
        # Store chat history if user is logged in and query was answered
        if user_token and "i do not know" not in answer.lower():
            try:
                # Decode token to get user_id
                payload = jwt.decode(user_token.split(' ')[1], 
                                  app.config["SECRET_KEY"], 
                                  algorithms=["HS256"])
                user_id = payload.get('user_id')
                
                # Convert ObjectId to string for storage
                user_id = ObjectId(user_id)
                
                # Store the conversation in database
                chat_history_collection.insert_one({
                    "user_id": user_id,
                    "question": question,
                    "answer": answer,
                    "timestamp": datetime.datetime.utcnow()
                })
            except Exception as e:
                print(f"Error storing chat history: {str(e)}")
        
        # Get chat history for this session
        memory = conversation_memories.get(session_id)
        chat_history = []
        if memory:
            chat_history = [str(msg) for msg in memory.chat_memory.messages]
        
        return jsonify({
            "answer": result["answer"],
            "chat_history": chat_history,
            "status": "answered",
            "session_id": session_id
        }), 200
        
    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        print("\nError:", error_msg)
        print("="*50 + "\n")
        return jsonify({
            "error": error_msg,
            "session_id": session_id
        }), 500

@app.route('/api/unanswered-queries', methods=['GET'])
def get_unanswered_queries():
    unanswered = list(queries_collection.find({"answered": False}))
    for query in unanswered:
        query["_id"] = str(query["_id"])
        if query.get("user_id"):  # Check if user_id exists in the query
            query["user_id"] = str(query["user_id"])
    print("Unanswered queries:", unanswered)
    return jsonify({"queries": unanswered}), 200

@app.route('/api/delete-query/<query_id>', methods=['DELETE'])
def delete_query(query_id):
    try:
        result = queries_collection.delete_one({"_id": ObjectId(query_id)})
        if result.deleted_count > 0:
            return jsonify({"message": "Query deleted successfully"}), 200
        return jsonify({"error": "Query not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def append_to_pdf(question, answer):
    pdf_path = os.path.join(os.getcwd(), "resources", "extra.pdf")
    
    # Create resources directory if it doesn't exist
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
    
    try:
        # Try to read existing PDF
        if os.path.exists(pdf_path):
            try:
                existing_pdf = PdfReader(pdf_path)
                # If successfully read, create temp file
                c = canvas.Canvas(pdf_path + ".tmp", pagesize=letter)
                # Copy existing content by creating blank pages
                for _ in range(len(existing_pdf.pages)):
                    c.showPage()
            except:
                # If reading fails, start fresh
                print("Creating new PDF file due to corruption or empty file")
                c = canvas.Canvas(pdf_path, pagesize=letter)
        else:
            # If file doesn't exist, create new
            c = canvas.Canvas(pdf_path, pagesize=letter)
        
        # Add new content
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 750, f"Question:")
        c.setFont("Helvetica", 12)
        c.drawString(50, 730, question)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 690, f"Answer:")
        c.setFont("Helvetica", 12)
        c.drawString(50, 670, answer)
        
        c.showPage()
        c.save()
        
        # If temp file exists and main operation succeeded, replace original
        if os.path.exists(pdf_path + ".tmp"):
            os.replace(pdf_path + ".tmp", pdf_path)
            
        return True
        
    except Exception as e:
        print(f"Error in append_to_pdf: {str(e)}")
        # If anything fails, try to create a new PDF with just this Q&A
        try:
            c = canvas.Canvas(pdf_path, pagesize=letter)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 750, f"Question:")
            c.setFont("Helvetica", 12)
            c.drawString(50, 730, question)
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, 690, f"Answer:")
            c.setFont("Helvetica", 12)
            c.drawString(50, 670, answer)
            c.showPage()
            c.save()
            return True
        except Exception as e2:
            print(f"Critical error creating new PDF: {str(e2)}")
            return False

def update_vectorstore(question, answer):
    """Update the vectorstore with new Q&A"""
    global vectorstore_global
    
    # Create text chunk from new Q&A
    new_text = f"Question: {question}\nAnswer: {answer}"
    chunks = get_text_chunks(new_text)
    
    # Create embeddings for new chunks
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY,
        task_type="retrieval_query"
    )
    
    # Add new chunks to existing vectorstore
    vectorstore_global.add_texts(chunks)
    print("Vectorstore updated with new Q&A")

@app.route('/api/add-response', methods=['POST'])
def add_response():
    data = request.json
    query_id = data.get("id")
    response = data.get("response")

    if not query_id or not response:
        return jsonify({"error": "Missing query ID or response"}), 400

    # Get the question from the database
    query_doc = queries_collection.find_one({"_id": ObjectId(query_id)})
    if not query_doc:
        return jsonify({"error": "Query not found"}), 404
    
    user_id = query_doc.get("user_id")

    # Update database
    queries_collection.update_one(
        {"_id": ObjectId(query_id)},
        {"$set": {"answer": response, "answered": True}}
    )

    success = False
    # Append to PDF
    try:
        append_to_pdf(query_doc["question"], response)
        print(f"Added Q&A to extra.pdf: Question: {query_doc['question']}, Answer: {response}")
        success = True
    except Exception as e:
        print(f"Error adding to PDF: {str(e)}")
    
    # Update vectorstore if PDF was updated successfully
    if success:
        try:
            update_vectorstore(query_doc["question"], response)
        except Exception as e:
            print(f"Error updating vectorstore: {str(e)}")
            # Continue even if vectorstore update fails

    # ✅ Notify user via email
    try:
        if user_id:
            user = users_collection.find_one({"_id": ObjectId(user_id)})
            if user and user.get("email"):
                email = user["email"]
                msg = Message(
                    subject="Your query has been answered!",
                    sender=app.config["MAIL_USERNAME"],
                    recipients=[email],
                    body=f"""Hello,

Your question: "{query_doc['question']}"
Has been answered: "{response}"

Thank you for your patience!

- Sahayak: The Support Team
"""
                )
                mail.send(msg)
                print(f"Email sent to {email}")
    except Exception as e:
        print(f"Error sending email: {str(e)}")
    
    return jsonify({"message": "Response added successfully"})

# Add new route to fetch chat history
@app.route('/api/chat-history', methods=['GET'])
def get_chat_history():
    user_token = request.headers.get('Authorization')
    if not user_token:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        # Decode token to get user_id
        payload = jwt.decode(user_token.split(' ')[1], 
                           app.config["SECRET_KEY"], 
                           algorithms=["HS256"])
        user_id = payload.get('user_id')
        
        # Convert user_id to ObjectId for MongoDB query
        user_id = ObjectId(user_id)
        
        # Fetch chat history for the user
        history = list(chat_history_collection.find(
            {"user_id": user_id},
            {"_id": 1, "question": 1, "answer": 1, "timestamp": 1}
        ).sort("timestamp", -1))  # Sort by newest first
        
        # Convert ObjectId and datetime for JSON serialization
        for chat in history:
            chat["_id"] = str(chat["_id"])
            chat["timestamp"] = chat["timestamp"].isoformat()
        
        return jsonify({"history": history}), 200
        
    except Exception as e:
        print(f"Error fetching chat history: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Add new route to fetch all users' chat history for admin
@app.route('/api/admin/chat-history', methods=['GET'])
def get_admin_chat_history():
    admin_token = request.headers.get('Authorization')
    if not admin_token:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        # Verify admin token
        payload = jwt.decode(admin_token.split(' ')[1], app.config["SECRET_KEY"], algorithms=["HS256"])
        if payload.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        # Fetch all chat history with user details
        pipeline = [
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$unwind": "$user"
            },
            {
                "$project": {
                    "question": 1,
                    "answer": 1,
                    "timestamp": 1,
                    "username": "$user.username"
                }
            },
            {
                "$sort": {"timestamp": -1}
            }
        ]
        
        history = list(chat_history_collection.aggregate(pipeline))
        
        # Convert ObjectId and datetime for JSON serialization
        for chat in history:
            chat["_id"] = str(chat["_id"])
            chat["timestamp"] = chat["timestamp"].isoformat()
        
        return jsonify({"history": history}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add new route to get dashboard statistics
@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    admin_token = request.headers.get('Authorization')
    if not admin_token:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        # Verify admin token
        payload = jwt.decode(admin_token.split(' ')[1], app.config["SECRET_KEY"], algorithms=["HS256"])
        if payload.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403
        
        # Get counts from different collections
        total_users = users_collection.count_documents({})
        total_chats = chat_history_collection.count_documents({})
        unanswered_queries = queries_collection.count_documents({"answered": False})
        
        return jsonify({
            "total_users": total_users,
            "total_chats": total_chats,
            "unanswered_queries": unanswered_queries
        }), 200
        
    except Exception as e:
        print(f"Error fetching stats: {str(e)}")
        return jsonify({"error": str(e)}), 500

import datetime  # make sure datetime is imported if not already

@app.route('/api/admin/query-analytics', methods=['GET'])
def get_query_analytics():
    admin_token = request.headers.get('Authorization')
    if not admin_token:
        return jsonify({"error": "Authentication required"}), 401
    try:
        # Verify admin token
        payload = jwt.decode(admin_token.split(' ')[1], app.config["SECRET_KEY"], algorithms=["HS256"])
        if payload.get('role') != 'admin':
            return jsonify({"error": "Admin access required"}), 403

        # Query chat_history_collection to fetch all questions with timestamps
        # (Here we assume questions from users are stored in "question")
        queries = list(chat_history_collection.find({}, {"question": 1, "timestamp": 1}))

        sentiment_by_date = defaultdict(list)
        word_counter = Counter()
        # A simple stopwords list – extend it as needed.
        stopwords = set(["the", "is", "at", "on", "and", "a", "an", "to", "of", "in", "i", "you", "it"])

        for record in queries:
            question = record.get("question")
            ts = record.get("timestamp")
            if not question or not ts:
                continue

            # Convert the timestamp to date string:
            if isinstance(ts, datetime.datetime):
                date_str = ts.date().isoformat()
            else:
                date_str = str(ts).split("T")[0]

            # Analyze sentiment using TextBlob
            polarity = TextBlob(question).sentiment.polarity
            sentiment_by_date[date_str].append(polarity)

            # Count words for trending topics (do a simple word count)
            for word in question.lower().split():
                # Remove non-alphanumeric characters
                word = ''.join([ch for ch in word if ch.isalnum()])
                if word and word not in stopwords:
                    word_counter[word] += 1

        # Prepare sentiment analytics: average sentiment per date
        sentiment_analytics = []
        for date, polarities in sentiment_by_date.items():
            avg_sentiment = sum(polarities) / len(polarities)
            sentiment_analytics.append({
                "date": date,
                "avg_sentiment": avg_sentiment,
                "count": len(polarities)
            })

        # Get trending topics – top 5 words
        trending_topics = word_counter.most_common(5)

        return jsonify({
            "sentiment_analytics": sentiment_analytics,
            "trending_topics": trending_topics
        }), 200

    except Exception as e:
        print(f"Error in analytics endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
