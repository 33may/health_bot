import React, { useState, useRef, ChangeEvent } from "react";
import ReactMarkdown from "react-markdown";
import { useChatWs } from "../hooks/UseChatWs.ts";

const ChatPage: React.FC = () => {
  const [input, setInput] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const { messages, sendMessage } = useChatWs();

  return (
    <div className="min-h-screen w-[60vw] mx-auto p-4 flex flex-col">
      {/* Chat messages container */}
      <div className=" rounded p-4 bg-white flex-1 overflow-y-scroll mb-4 space-y-2">
        {messages.map((msg, index) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={index}
              className={`flex ${isUser ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`px-5 py-4 rounded-lg shadow markdown-content
                  ${isUser ? "bg-blue-500 text-white max-w-[60%]" : "bg-gray-200 text-gray-900 max-w-[80%]"}`
                }
              >
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input and send button */}
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
          onClick={() => {
            sendMessage(input);
            setInput("");
          }}
        >
          Отправить
        </button>
      </div>
    </div>
  );
};

export default ChatPage;
