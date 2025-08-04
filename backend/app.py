"""
Student Chatbot Application
A professional Flask application for student query resolution using RAG and AI.
"""

import os
from flask import Flask
from flask_cors import CORS
from flask_mail import Mail

# Import configurations
from config.config import config
from config.database import db_instance

# Import services
from services.email_service import EmailService

# Import routes
from routes.auth_routes import create_auth_routes
from routes.chat_routes import create_chat_routes
from routes.admin_routes import create_admin_routes, create_legacy_admin_routes

# Import middleware
from middleware.middleware import (
    CORSMiddleware, 
    EnvironmentMiddleware, 
    ErrorHandlingMiddleware
)

# Import utilities
from utils.pdf_utils import create_embeddings

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    cors = CORS(app)
    mail = Mail(app)
    
    # Initialize middleware
    EnvironmentMiddleware(app)
    CORSMiddleware(app)
    ErrorHandlingMiddleware(app)
    
    # Initialize database
    if not db_instance.connect():
        raise Exception("Failed to connect to database")
    
    # Initialize email service
    email_service = EmailService()
    email_service.init_app(app)
    
    # Store email service in app config for global access
    app.config['EMAIL_SERVICE'] = email_service
    
    # Create embeddings and vectorstore
    print("Initializing embeddings...")
    try:
        vectorstore_global = create_embeddings()
        print("Embeddings initialized successfully!")
    except Exception as e:
        print(f"Error initializing embeddings: {str(e)}")
        raise
    
    # Register blueprints (routes)
    app.register_blueprint(create_auth_routes(app))
    app.register_blueprint(create_chat_routes(vectorstore_global))
    app.register_blueprint(create_admin_routes(email_service))
    app.register_blueprint(create_legacy_admin_routes(email_service))  # For backward compatibility
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return {"status": "healthy", "message": "Student Chatbot API is running"}, 200
    
    # Debug endpoint to list all routes
    @app.route('/debug/routes', methods=['GET'])
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                "endpoint": rule.endpoint,
                "methods": list(rule.methods),
                "url": str(rule)
            })
        return {"routes": routes}, 200
    
    # Debug endpoint to test email service
    @app.route('/debug/email', methods=['GET'])
    def test_email():
        email_service = app.config.get('EMAIL_SERVICE')
        if not email_service:
            return {"error": "Email service not found"}, 500
        
        if not email_service.mail:
            return {"error": "Mail instance not initialized"}, 500
        
        return {
            "status": "Email service is working",
            "mail_server": app.config.get('MAIL_SERVER'),
            "mail_username": app.config.get('MAIL_USERNAME'),
            "mail_configured": email_service.mail is not None
        }, 200
    
    # Test endpoint to send a test email
    @app.route('/debug/send-test-email', methods=['POST'])
    def send_test_email():
        email_service = app.config.get('EMAIL_SERVICE')
        if not email_service or not email_service.mail:
            return {"error": "Email service not available"}, 500
        
        try:
            # Send test email to the configured email address
            from flask_mail import Message
            msg = Message(
                subject="Test Email from Chatbot",
                sender=app.config.get('MAIL_USERNAME'),
                recipients=[app.config.get('MAIL_USERNAME')],  # Send to self
                body="This is a test email to verify email service is working."
            )
            email_service.mail.send(msg)
            return {"status": "Test email sent successfully"}, 200
        except Exception as e:
            return {"error": f"Failed to send test email: {str(e)}"}, 500
    
    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return {
            "message": "Welcome to Student Chatbot API",
            "version": "2.0.0",
            "endpoints": {
                "auth": "/api/signup, /api/login, /api/admin/login",
                "chat": "/api/query, /api/chat-history, /api/add-response",
                "admin": "/api/admin/stats, /api/admin/chat-history, /api/admin/query-analytics"
            }
        }, 200
    
    return app

def main():
    """Main function to run the application"""
    # Get environment
    env = os.getenv('FLASK_ENV', 'development')
    
    # Create app
    app = create_app(env)
    
    # Run app
    debug_mode = env == 'development'
    port = int(os.getenv('PORT', 5000))
    
    print(f"Starting Student Chatbot API in {env} mode...")
    print(f"Server running on http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

if __name__ == "__main__":
    main()
