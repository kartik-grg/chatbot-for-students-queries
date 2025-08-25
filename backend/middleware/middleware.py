from flask import request, jsonify
import os

class CORSMiddleware:
    """Middleware for handling CORS"""
    
    def __init__(self, app):
        self.app = app
        self.init_app(app)
    
    def init_app(self, app):
        """Initialize CORS middleware"""
        app.after_request(self.after_request)
    
    def after_request(self, response):
        """Add CORS headers to response"""
        # Get origins from environment variable
        cors_origins = os.environ.get('CORS_ORIGINS', '*')
        
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response.headers.add('Access-Control-Allow-Origin', cors_origins)
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            response.headers.add('Access-Control-Max-Age', '3600')
        else:
            response.headers.add('Access-Control-Allow-Origin', cors_origins)
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            response.headers.add('Access-Control-Allow-Credentials', 'true')
            
        return response

class EnvironmentMiddleware:
    """Middleware for setting up environment variables"""
    
    def __init__(self, app):
        self.app = app
        self.setup_environment()
    
    def setup_environment(self):
        """Set up LangChain environment variables"""
        from config.config import Config
        
        # Set environment variables for LangChain
        os.environ["LANGCHAIN_TRACING_V2"] = Config.LANGCHAIN_TRACING_V2
        os.environ["LANGCHAIN_PROJECT"] = Config.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_ENDPOINT"] = Config.LANGCHAIN_ENDPOINT
        
        if Config.LANGSMITH_API_KEY:
            os.environ["LANGSMITH_API_KEY"] = Config.LANGSMITH_API_KEY

        # Set environment variables for Pinecone
        if Config.PINECONE_API_KEY:
            os.environ["PINECONE_API_KEY"] = Config.PINECONE_API_KEY

class SessionCleanupMiddleware:
    """Middleware for cleaning up expired sessions"""
    
    def __init__(self, app, chat_service):
        self.app = app
        self.chat_service = chat_service
        self.init_app(app)
    
    def init_app(self, app):
        """Initialize session cleanup middleware"""
        app.before_request(self.before_request)
    
    def before_request(self):
        """Run cleanup before each request"""
        if hasattr(self.chat_service, 'cleanup_expired_sessions'):
            self.chat_service.cleanup_expired_sessions()

class ErrorHandlingMiddleware:
    """Middleware for global error handling"""
    
    def __init__(self, app):
        self.app = app
        self.init_app(app)
    
    def init_app(self, app):
        """Initialize error handling middleware"""
        app.errorhandler(404)(self.handle_404)
        app.errorhandler(500)(self.handle_500)
        app.errorhandler(Exception)(self.handle_exception)
    
    def handle_404(self, error):
        """Handle 404 errors"""
        return jsonify({'error': 'Endpoint not found'}), 404
    
    def handle_500(self, error):
        """Handle 500 errors"""
        return jsonify({'error': 'Internal server error'}), 500
    
    def handle_exception(self, error):
        """Handle general exceptions"""
        print(f"Unhandled exception: {str(error)}")
        return jsonify({'error': 'An unexpected error occurred'}), 500
