import datetime
from time import time
from langchain.chains import ConversationalRetrievalChain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate
from config.config import Config
from models.models import Query, ChatHistory
from utils.helpers import is_general_chat
from utils.pdf_utils import update_vectorstore

# Global variables for session management
conversation_memories = {}  # Store conversation memories by session
session_timestamps = {}    # Track last activity time for each session

# Template for AI responses
template = """
You are a knowledgeable academic assistant helping students with their queries. Use the following context to provide accurate, helpful answers.

INSTRUCTIONS:
- Answer based ONLY on the provided context
- If the context doesn't contain enough information, respond with exactly "I do not know."
- Provide clear, concise answers
- Be helpful and professional in your tone
- If multiple pieces of information are relevant, organize them clearly

Context: {context}

Question: {question}

Answer:
"""

class ChatService:
    """Service for handling chat operations"""
    
    def __init__(self, vectorstore):
        self.vectorstore = vectorstore
        self.query_model = Query()
        self.chat_history_model = ChatHistory()
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions if needed"""
        current_time = time()
        expired_sessions = [
            sid for sid, last_active in session_timestamps.items()
            if current_time - last_active > Config.SESSION_TIMEOUT
        ]
        
        for sid in expired_sessions:
            if sid in conversation_memories:
                del conversation_memories[sid]
            if sid in session_timestamps:
                del session_timestamps[sid]
        
        if expired_sessions:
            print(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def update_session_timestamp(self, session_id):
        """Update last activity time for a session"""
        session_timestamps[session_id] = time()
    
    def get_conversation_chain(self, session_id):
        """Create or retrieve a conversation chain for a session"""
        self.update_session_timestamp(session_id)
        
        if session_id not in conversation_memories:
            memory = ConversationBufferMemory(
                memory_key='chat_history',
                return_messages=True
            )
            conversation_memories[session_id] = memory
        else:
            memory = conversation_memories[session_id]

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.15,
            google_api_key=Config.GOOGLE_API_KEY
        )

        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=self.vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 8}),
            memory=memory,
            combine_docs_chain_kwargs={"prompt": ChatPromptTemplate.from_template(template)}
        )
        return conversation_chain
    
    def process_query(self, question, session_id, user_id=None):
        """Process a user query and return response"""
        try:
            # Cleanup expired sessions
            self.cleanup_expired_sessions()
            
            # Generate session ID if not provided
            if not session_id:
                session_id = str(datetime.datetime.now().timestamp())
            
            print("\n" + "="*50)
            print(f"Session: {session_id}")
            print("Question received:", question)
            print("="*50)

            # Check if it's general chat
            general_response = is_general_chat(question)
            if general_response:
                # Get chat history for this session
                memory = conversation_memories.get(session_id)
                chat_history = []
                if memory:
                    memory.chat_memory.add_user_message(question)
                    memory.chat_memory.add_ai_message(general_response)
                    chat_history = [str(msg) for msg in memory.chat_memory.messages]
                
                return {
                    "answer": general_response,
                    "chat_history": chat_history,
                    "status": "answered",
                    "session_id": session_id
                }, 200

            # Get conversation chain for this session
            chat_chain = self.get_conversation_chain(session_id)
            
            # Get response
            result = chat_chain({"question": question})
            answer = result["answer"].strip()
            
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
                
                # Store unanswered query
                self.query_model.create_query(question, user_id, answered=False)
                
                return {
                    "answer": "I apologize, but I don't have enough information to answer this question accurately. Your query has been logged for manual review.",
                    "status": "unanswered",
                    "session_id": session_id
                }, 404
            
            # Store chat history if user is logged in and query was answered
            if user_id and "i do not know" not in answer.lower():
                try:
                    self.chat_history_model.create_chat(user_id, question, answer)
                except Exception as e:
                    print(f"Error storing chat history: {str(e)}")
            
            # Get chat history for this session
            memory = conversation_memories.get(session_id)
            chat_history = []
            if memory:
                chat_history = [str(msg) for msg in memory.chat_memory.messages]
            
            return {
                "answer": answer,
                "chat_history": chat_history,
                "status": "answered",
                "session_id": session_id
            }, 200
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            print("\nError:", error_msg)
            print("="*50 + "\n")
            return {
                "error": error_msg,
                "session_id": session_id
            }, 500
    
    def add_response_to_query(self, query_id, response):
        """Add admin response to unanswered query"""
        try:
            # Get the question from the database
            query_doc = self.query_model.find_by_id(query_id)
            if not query_doc:
                return {"error": "Query not found"}, 404
            
            # Update database
            self.query_model.update_query(query_id, response)
            
            # Append to PDF and update vectorstore
            from utils.pdf_utils import append_to_pdf
            success = append_to_pdf(query_doc["question"], response)
            
            if success:
                try:
                    update_vectorstore(self.vectorstore, query_doc["question"], response)
                except Exception as e:
                    print(f"Error updating vectorstore: {str(e)}")
            
            # Send email notification if user exists
            user_id = query_doc.get("user_id")
            if user_id:
                try:
                    from flask import current_app
                    print("trying to mail")
                    email_service = current_app.config.get('EMAIL_SERVICE')
                    if email_service:
                        email_service.send_query_response_notification(user_id, query_doc["question"], response)
                    else:
                        print("Email service not found in app config")
                except Exception as e:
                    print(f"Error sending email: {str(e)}")
            
            return {"message": "Response added successfully"}, 200
            
        except Exception as e:
            return {"error": f"Failed to add response: {str(e)}"}, 500
