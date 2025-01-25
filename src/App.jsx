import React, { useState, useEffect } from "react";
import ChatButton from "./components/ChatButton";
import ChatBox from "./components/ChatBox";
import Squares from "./components/ui/Squares";

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
  );
}

export default App;
