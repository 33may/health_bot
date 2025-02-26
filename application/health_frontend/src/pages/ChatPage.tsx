import React, { useState, useRef, ChangeEvent } from "react";
import ReactMarkdown from "react-markdown";
import { useChatWs } from "../hooks/UseChatWs.ts";
import {Box, Paper, Typography} from "@mui/material";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";



const decodeDocName = (doc: string): string => {
  try {
    // Wrap in quotes and parse to decode Unicode escapes
    return JSON.parse('"' + doc + '"');
  } catch (error) {
    return doc;
  }
};

interface DocumentsBlockProps {
  docs: string[];
}

const DocumentsBlock: React.FC<DocumentsBlockProps> = ({ docs }) => {
  return (
    <Paper elevation={1} sx={{ p: 1, borderRadius: 2, mb: 1 }}>
      {docs.map((doc, index) => (
        <Box key={index} sx={{ display: "flex", alignItems: "center", gap: 1, mb: 0.5 }}>
          <InsertDriveFileIcon color="action" sx={{ fontSize: 20 }} />
          <Typography variant="body2">{decodeDocName(doc)}</Typography>
        </Box>
      ))}
    </Paper>
  );
};


const ReasoningBlock: React.FC<{ reasoning: string }> = ({ reasoning }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`relative p-2 border border-gray-300 rounded bg-gray-100 cursor-pointer transition-all duration-200 ${
        expanded ? "max-h-full" : "max-h-24 overflow-hidden"
      }`}
      onClick={() => setExpanded(!expanded)}
      title="Натисніть, щоб розгорнути/згорнути"
    >
      <ReactMarkdown>{reasoning}</ReactMarkdown>
      <div className="absolute right-2 bottom-2">
        <ExpandMoreIcon
          className={`transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
        />
      </div>
    </div>
  );
};

const ChatPage: React.FC = () => {
  const [input, setInput] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const { messages, sendMessage } = useChatWs();

  return (
    <div className="min-h-screen w-[60vw] mx-auto p-4 flex flex-col">
      {/* Chat messages container */}
      <div className="rounded p-4 bg-white flex-1 overflow-y-scroll mb-4 space-y-2">
        {messages.map((msg, index) => {
          const isUser = msg.role === "user";
          return (
            <div
              key={index}
              className={`flex ${isUser ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`px-5 py-4 rounded-lg shadow markdown-content ${
                  isUser
                    ? "bg-blue-500 text-white max-w-[60%]"
                    : "bg-gray-200 text-gray-900 max-w-[80%]"
                }`}
              >
                {/* Render supporting documents in their own block */}
                {msg.supporting_documents && (
                  <DocumentsBlock docs={msg.supporting_documents} />
                )}

                {/* Render reasoning block if available */}
                {msg.reasoning && <ReasoningBlock reasoning={msg.reasoning} />}

                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      <div className="flex items-center gap-2">
        <input
          type="text"
          className="flex-grow p-2 border border-gray-300 rounded"
          value={input}
          placeholder="Введіть повідомлення..."
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            setInput(e.target.value)
          }
        />
        <button
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          onClick={() => {
            sendMessage(input);
            setInput("");
          }}
        >
          Надіслати
        </button>
      </div>
    </div>
  );
};

export default ChatPage;
