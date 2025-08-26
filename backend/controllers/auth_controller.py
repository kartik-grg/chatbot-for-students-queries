from flask import request, jsonify
from services.auth_service import AuthService

class AuthController:
    """Controller for handling authentication endpoints"""
    
    def __init__(self, app):
        self.auth_service = AuthService(app)
    
    def signup(self):
        """Handle user signup"""
        try:
            data = request.json
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")

            if not username or not email or not password:
                return jsonify({"error": "All fields are required"}), 400

            result, status_code = self.auth_service.register_user(username, email, password)
            return jsonify(result), status_code
            
        except Exception as e:
            return jsonify({"error": f"Signup failed: {str(e)}"}), 500
    
    def login(self):
        """Handle user login"""
        try:
            # Log request details for debugging
            print(f"Login request received: {request.method} {request.path}")
            print(f"Request headers: {request.headers}")
            
            # Get JSON data
            data = request.json
            if not data:
                return jsonify({"error": "No data provided or invalid JSON"}), 400
                
            username = data.get("username")
            password = data.get("password")
            
            print(f"Login attempt for user: {username}")
            
            if not username or not password:
                return jsonify({"error": "Username and password are required"}), 400
            
            result, status_code = self.auth_service.login_user(username, password)
            print(f"Login result for {username}: status {status_code}")
            return jsonify(result), status_code
            
        except Exception as e:
            import traceback
            print(f"Login failed with error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": f"Login failed: {str(e)}"}), 500
    
    def admin_login(self):
        """Handle admin login"""
        try:
            # Log request details for debugging
            print(f"Admin login request received: {request.method} {request.path}")
            print(f"Request headers: {request.headers}")
            
            # Get JSON data
            data = request.json
            if not data:
                return jsonify({"error": "No data provided or invalid JSON"}), 400
                
            email = data.get('email')
            password = data.get('password')
            
            print(f"Admin login attempt for email: {email}")
            
            if not email or not password:
                return jsonify({"error": "Email and password are required"}), 400
            
            result, status_code = self.auth_service.login_admin(email, password)
            print(f"Admin login result for {email}: status {status_code}")
            return jsonify(result), status_code
            
        except Exception as e:
            import traceback
            print(f"Admin login failed with error: {str(e)}")
            print(traceback.format_exc())
            return jsonify({"error": f"Admin login failed: {str(e)}"}), 500
