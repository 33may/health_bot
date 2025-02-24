import {useState, useEffect} from "react";
import {ChatMessage, ChatToken, WSMessage} from "../dtos/ChatMessage.ts";

export function useChatWs() {
    const [ws, setWs] = useState<WebSocket | null>(null);
    const [messages, setMessages] = useState<ChatMessage[]>([]);

    useEffect(() => {
        const socket = new WebSocket("ws://localhost:8000/ws");

        socket.onopen = () => {
            console.log("WebSocket соединение установлено");
        };

        socket.onmessage = (event: MessageEvent) => {

            const data: ChatToken = JSON.parse(event.data);

            setMessages((prevMessages) => {
                const updated = [...prevMessages];

                if (updated.length > 0 && updated[updated.length - 1].role === "system") {
                    const lastMessage = updated[updated.length - 1];
                    if (data.type === "message") {
                        lastMessage.content += data.content;
                    }
                    else if (data.type === "think") {
                        lastMessage.reasoning = lastMessage.reasoning
                            ? lastMessage.reasoning + data.content
                            : data.content;
                    }
                    else if (data.type === "sup_docs") {
                        lastMessage.supporting_documents?.push(data.content);
                    }
                } else {
                    const newMessage: ChatMessage = {role: "system", content: ""};
                    if (data.type === "message") {
                        newMessage.content = data.content;
                    } else if (data.type === "think") {
                        newMessage.reasoning = data.content;
                    }
                    updated.push(newMessage);
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
            setMessages((prev) => {
                const newMessage: ChatMessage = {
                    role: "user",
                    content: userInput,
                };
                const updated = [...prev, newMessage];

                console.log(updated);

                const chat_context = updated.map((msg) => {
                const content = msg.reasoning
                    ? `<think>${msg.reasoning}</think>\n${msg.content}`
                    : msg.content;

                return {
                    role: msg.role,
                    content: content,
                } as WSMessage;
            });
            ws.send(JSON.stringify(chat_context));

                return updated;
            })
        }
    };


    return {messages, sendMessage};
}
