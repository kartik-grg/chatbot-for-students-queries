import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import SpotlightCard from "./ui/SpotlightCard";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import { IoSend, IoClose } from "react-icons/io5";
import { Label } from "./ui/label";
import GradientText from "./ui/GradientText";
import { IoMdSettings } from "react-icons/io";
import { SkeletonDemo } from "./ui/SkeletonDemo";
import { IoMdLogIn } from "react-icons/io";
import { FaHistory } from "react-icons/fa";

function ChatBox({ onClose }) {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [chatHistory, setChatHistory] = useState([
    // Sample history data - replace with actual data from your backend
    { id: 1, query: "Sample question 1", response: "Sample answer 1" },
    { id: 2, query: "Sample question 2", response: "Sample answer 2" },
  ]);

  useEffect(() => {
    // Check if user is logged in
    const userToken = localStorage.getItem("userToken");
    setIsLoggedIn(!!userToken);
  }, []);

  const handleSettingsClick = () => {
    navigate("/admin");
  };

  const handleLoginClick = () => {
    navigate("/login");
  };

  const handleHistoryClick = () => {
    setShowHistory(!showHistory);
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
            // colors={["#40ffaa", "#4079ff", "#40ffaa", "#4079ff", "#40ffaa"]}
            // colors={["#7f40ff", "#4079ff", "#7f40ff", "#4079ff", "#7f40ff"]}
            // colors={["#a240ff", "#6040ff", "#4064ff", "#4079ff", "#60a4ff"]}
            // colors={["#9b5de5", "#574ae2", "#3a86ff", "#574ae2", "#9b5de5"]}
            // colors={["#9b5de5", "#4361ee", "#3a86ff", "#00f5d4", "#ff4d6d"]}
            animationSpeed={3}
            showBorder={false}
            className="custom-class text-3xl mb-3"
          >
            Welcome to Sahayak
          </GradientText>

          {!isLoggedIn && (
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

        <div className="flex-1 overflow-y-auto p-4">
          {showHistory ? (
            <div className="space-y-4">
              {chatHistory.map((chat) => (
                <div key={chat.id} className="bg-gray-800 rounded-lg p-3">
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
        </div>

        <div className="p-4 ">
          <div className="flex gap-2 items-end">
            <div className="flex-1">
              <Label htmlFor="message" className="text-white sr-only">
                Your Query
              </Label>
              <Textarea
                placeholder="Type your message here."
                id="message"
                className="min-h-[50px] max-h-[100px] text-white"
              />
            </div>
            <Button className="h-[50px] px-4">
              <IoSend className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </SpotlightCard>
    </div>
  );
}

export default ChatBox;
