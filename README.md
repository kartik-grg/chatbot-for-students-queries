# Student Query Resolution Chatbot

An interactive chatbot system designed to help resolve student queries efficiently. The system features both user and admin interfaces, allowing for dynamic query handling and response management.

## Key Features

- User Authentication System
  - Secure signup and login
  - JWT-based authentication
  - Password encryption
  
- Query Management
  - Ask questions and receive instant answers
  - Automatic query storage
  - Historical query search
  
- Admin Dashboard
  - Dedicated admin login
  - Manage unanswered queries
  - Add and update responses

## Technology Stack

### Backend
- Flask (Python web framework)
- MongoDB (Database)
- JWT (Authentication)
- Bcrypt (Password hashing)
- Flask-CORS (Cross-origin resource sharing)

### API Endpoints

#### Authentication
```
POST /api/signup        - Register new user
POST /api/login         - User login
POST /api/admin/login   - Admin login
```

#### Query Handling
```
POST /api/query                 - Submit new query
GET /api/unanswered-queries    - Fetch pending queries
POST /api/add-response         - Add query response
```

## Getting Started

1. Clone the repository:
```bash
git clone [repository-url]
cd ai-chat-bot
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # For Windows: venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create `.env` file with:
```
MONGO_URI=your_mongodb_connection_string
```

5. Start the server:
```bash
python backend/app.py
```

## Admin Access
Default credentials:
- Email: admin@example.com
- Password: admin123

## Database Schema

### Users Collection
```json
{
  "username": "string",
  "email": "string",
  "password": "hashed_string"
}
```

### Queries Collection
```json
{
  "question": "string",
  "answer": "string",
  "answered": "boolean"
}
```

## Security Features
- Password hashing using Bcrypt
- JWT token authentication
- Protected admin routes
- Secure API endpoints

## Contributing
1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Submit pull request

## License
MIT License
