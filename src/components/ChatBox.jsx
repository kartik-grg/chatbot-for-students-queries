import React from "react";
import { useNavigate } from "react-router-dom";
import SpotlightCard from "./ui/SpotlightCard";
import { Textarea } from "./ui/textarea";
import { Button } from "./ui/button";
import { IoSend, IoClose } from "react-icons/io5";
import { Label } from "./ui/label";
import GradientText from "./ui/GradientText";
import { IoMdSettings } from "react-icons/io";
import { SkeletonDemo } from "./ui/SkeletonDemo";

function ChatBox({ onClose }) {
  const navigate = useNavigate();

  const handleSettingsClick = () => {
    navigate('/admin');
  };

  return (
    <div className="fixed bottom-24 right-8 h-[80%] w-[40%]">
      <SpotlightCard
        className="custom-spotlight-card h-full flex flex-col"
        spotlightColor="rgba(0, 229, 255, 0.2)"
      >
        <div className="p-2 border-b border-neutral-800 flex justify-between items-center">
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
          {/* Chat messages will go here */}
          <div className="mt-3">
            <SkeletonDemo className="mt-3"/>
          </div>
          <div className="mt-3">
            <SkeletonDemo className="mt-3"/>
          </div>
          

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