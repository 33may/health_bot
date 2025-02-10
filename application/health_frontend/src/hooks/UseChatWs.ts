import { useState, useEffect } from "react";
import {ChatMessage} from "../dtos/ChatMessage.ts";

export function useChatWs() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);

  useEffect(() => {
      const socket = new WebSocket("ws://localhost:8000/ws");

      socket.onopen = () => {
        console.log("WebSocket соединение установлено");
      };

    socket.onmessage = (event: MessageEvent) => {
      setMessages((prevMessages) => {
        const updated = [...prevMessages];
        if (
            updated.length > 0 &&
            updated[updated.length - 1].role == "assistant"
        ) {
            updated[updated.length - 1].content = updated[updated.length - 1].content + event.data;
        } else {
            const new_message: ChatMessage = {
              role: "assistant",
              content: event.data
            };

          updated.push(new_message);
        }
        return updated;
      });
    };

    socket.onclose = () => {
      console.log("WebSocket соединение закрыто");
    };

    setWs(socket);

    return () => {
      socket.close();
    };
  }, []);

  const sendMessage = (userInput: string) => {
    if (ws && userInput) {
        const new_message: ChatMessage = {
            role: "assistant",
            content: userInput
        };
        setMessages((prev) => [...prev, new_message]);
        ws.send(JSON.stringify(messages));
    }
  };

  return { messages, sendMessage };
}
