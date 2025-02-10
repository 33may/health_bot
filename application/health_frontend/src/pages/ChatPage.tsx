import React, { useState, useRef, ChangeEvent } from "react";
import ReactMarkdown from "react-markdown";
import {useChatWs} from "../hooks/UseChatWs.ts";

const ChatPage: React.FC = () => {
  const [input, setInput] = useState<string>("");

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  const {messages, sendMessage} = useChatWs()

    console.log(messages)

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <div className="border border-gray-300 rounded p-4 bg-white h-96 overflow-y-scroll mb-4">
        {messages.map((msg, index) => (
          <div key={index} className="text-left p-2 border-b border-gray-200">
            {msg.role}: <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      <div className="flex items-center gap-2">
        <input
          type="text"
          className="flex-grow p-2 border border-gray-300 rounded"
          value={input}
          placeholder="Введите сообщение..."
          onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
        />
        <button
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          onClick={() => sendMessage(input)}
        >
          Отправить
        </button>
      </div>
    </div>
  );
};

export default ChatPage;
