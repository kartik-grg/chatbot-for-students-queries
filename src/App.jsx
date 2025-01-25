import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import ChatButton from "./components/ChatButton";
import ChatBox from "./components/ChatBox";
import Squares from "./components/ui/Squares";
import LoginAdmin from './components/LoginAdmin';
import Admin from './components/Admin';

// Simple auth check - replace with your actual auth logic
const isAuthenticated = () => {
  // Add your authentication check logic here
  return localStorage.getItem('adminToken') !== null;
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/admin" replace />;
  }
  return children;
};

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    const handleKeyPress = (event) => {
      // Toggle chat with Ctrl + /
      if (event.ctrlKey && event.key === '/') {
        event.preventDefault();
        setIsChatOpen(prev => !prev);
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  return (
    <Router>
      <Routes>
        {/* Main chat route */}
        <Route path="/" element={
          <div className="h-screen w-screen bg-cyan-950">
            <Squares
              speed={0.5}
              squareSize={40}
              direction="diagonal" // up, down, left, right, diagonal
              borderColor="#fff"
              hoverFillColor="#222"
            />
            <div className="relative">
              {isChatOpen && <ChatBox onClose={() => setIsChatOpen(false)} />}
              {!isChatOpen && (
                <div onClick={() => setIsChatOpen(true)}>
                  <ChatButton />
                </div>
              )}
            </div>
          </div>
        } />
        
        {/* Admin routes */}
        <Route path="/admin" element={<LoginAdmin />} />
        <Route 
          path="/admin/dashboard" 
          element={
            <ProtectedRoute>
              <Admin />
            </ProtectedRoute>
          } 
        />
      </Routes>
    </Router>
  );
}

export default App;