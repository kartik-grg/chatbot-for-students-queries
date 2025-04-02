import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import SpotlightCard from "./ui/SpotlightCard";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import { IoSend, IoClose } from "react-icons/io5";
import { Label } from "./ui/label";
import GradientText from "./ui/GradientText";
import { IoMdSettings, IoMdLogOut } from "react-icons/io";
import { SkeletonDemo } from "./ui/SkeletonDemo";
import { IoMdLogIn } from "react-icons/io";
import { FaHistory } from "react-icons/fa";
import axios from "axios";

function ChatBox({ onClose }) {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [message, setMessage] = useState("");
  const [showConversation, setShowConversation] = useState(false);
  const conversationRef = useRef(null);

  useEffect(() => {
    // Check if user is logged in
    const userToken = localStorage.getItem("userToken");
    setIsLoggedIn(!!userToken);
  }, []);

  useEffect(() => {
    if (conversationRef.current) {
      conversationRef.current.scrollTop = conversationRef.current.scrollHeight;
    }
  }, [chatHistory, showConversation]);

  const handleSettingsClick = () => {
    navigate("/admin");
  };

  const handleLoginClick = () => {
    navigate("/login");
  };

  const handleLogout = () => {
    localStorage.removeItem("userToken");
    setIsLoggedIn(false);
    setShowHistory(false);
  };

  const handleHistoryClick = () => {
    setShowHistory(!showHistory);
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    try {
      const token = localStorage.getItem("userToken");
      const response = await axios.post("/api/query", 
        {
          question: message,
        },
        {
          headers: { 
            Authorization: token ? `Bearer ${token}` : undefined
          }
        }
      );

      setChatHistory((prev) => [
        ...prev,
        { query: message, response: response.data.answer || "No answer found" },
      ]);
    } catch (error) {
      if (error.response && error.response.status === 404) {
        setChatHistory((prev) => [
          ...prev,
          { query: message, response: "No answer found. Your query has been logged." },
        ]);
      } else {
        console.error("Error sending message:", error);
      }
    }
    setShowConversation(true)
    setMessage("");
  };

  return (
    <div className="fixed bottom-24 right-8 h-[80%] w-[40%]">
      <SpotlightCard
        className="custom-spotlight-card h-full flex flex-col"
        spotlightColor="rgba(0, 229, 255, 0.2)"
      >
        <div className="p-2 border-b border-neutral-800 flex justify-between items-center">
          {isLoggedIn && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleHistoryClick}
              className="text-blue-500 text-3xl hover:bg-blue-800 hover:text-white"
            >
              <FaHistory />
            </Button>
          )}
          <GradientText
            colors={["#b185db", "#5a8dee", "#59c3e3", "#ff85a1", "#d25ca8"]}
            animationSpeed={3}
            showBorder={false}
            className="custom-class text-3xl mb-3"
          >
            Welcome to Sahayak
          </GradientText>

          {isLoggedIn ? (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-pink-500 text-3xl hover:bg-pink-800 hover:text-white"
            >
              <IoMdLogOut />
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLoginClick}
              className="text-pink-500 text-3xl hover:bg-pink-800 hover:text-white"
            >
              <IoMdLogIn />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={handleSettingsClick}
            className="text-blue-500 text-3xl hover:bg-blue-800 hover:text-white"
          >
            <IoMdSettings />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-red-500 hover:bg-red-800 hover:text-white"
          >
            <IoClose className="h-6 w-6" />
          </Button>
        </div>

        {/* <div className="flex-1 overflow-y-auto p-4">
          {showHistory ? (
            isLoggedIn ? (
              <div className="space-y-4">
                {chatHistory.map((chat) => (
                  <div key={chat.id} className="bg-gray-800 rounded-lg p-3">
                    <p className="text-blue-400 font-medium">Query: {chat.query}</p>
                    <p className="text-white mt-2">Response: {chat.response}</p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center text-white py-4">
                Please login to see chat history
                <Button
                  variant="ghost"
                  onClick={handleLoginClick}
                  className="ml-2 text-pink-500 hover:bg-pink-800 hover:text-white"
                >
                  Login
                </Button>
              </div>
            )
          ) : (
            <>
              <div className="mt-3">
                <SkeletonDemo className="mt-3" />
              </div>
              <div className="mt-3">
                <SkeletonDemo className="mt-3" />
              </div>
            </>
          )}
        </div> */}

        {showConversation ? (
          <div
            ref={conversationRef}
            className="space-y-4 overflow-y-auto"
            style={{
              scrollbarWidth: "none" /* Firefox */,
              msOverflowStyle: "none" /* IE and Edge */
            }}
          >
            {console.log(chatHistory)}
          {chatHistory.map((chat) => (
            <div key={chat.query.length} className="bg-gray-800 rounded-lg p-3">
              <p className="text-blue-400 font-medium">Query: {chat.query}</p>
              <p className="text-white mt-2">Response: {chat.response}</p>
            </div>  
          ))}
        </div>
        ) : (
          <>
            <div className="mt-3">
              <SkeletonDemo className="mt-3" />
            </div>
            <div className="mt-3">
              <SkeletonDemo className="mt-3" />
            </div>
          </>
        )}
        
        {/* <div className="p-4 "> */}
        <div className="mt-auto p-4">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <Label htmlFor="message" className="text-white sr-only">
                Your Query
              </Label>
              <Textarea
                placeholder="Type your message here."
                id="message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="min-h-[50px] max-h-[100px] text-white"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
              />
            </div>
            <Button className="h-[50px] px-4" onClick={handleSendMessage}>
              <IoSend className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </SpotlightCard>
    </div>
  );
}

export default ChatBox;
