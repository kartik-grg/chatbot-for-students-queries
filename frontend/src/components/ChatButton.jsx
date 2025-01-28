import React from "react";
import { RiChatAiFill } from "react-icons/ri";
import Magnet from "./ui/Magnet";

function ChatButton() {
  return (
    <div className="fixed bottom-8 right-8">
      <Magnet>
        <button>
          <RiChatAiFill className="text-4xl text-primary lg:text-6xl" />
        </button>
      </Magnet>
    </div>
  );
}

export default ChatButton;
