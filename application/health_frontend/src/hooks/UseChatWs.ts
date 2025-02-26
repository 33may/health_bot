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
                const lastMessage =
                    updated.length > 0 && updated[updated.length - 1].role === "system"
                        ? updated[updated.length - 1]
                        : null;

                // Helper to ensure document content is an array of strings.
                const parseDocs = (content: any): string[] => {
                    let docs: string[] = [];
                    if (typeof content === "string") {
                        try {
                            docs = JSON.parse(content);
                            if (!Array.isArray(docs)) {
                                docs = [content];
                            }
                        } catch (e) {
                            docs = [content];
                        }
                    } else if (Array.isArray(content)) {
                        docs = content;
                    } else {
                        docs = [String(content)];
                    }
                    return docs;
                };

                const isOccupied = (msg: ChatMessage): boolean =>
                    Boolean(msg.content?.length)


                if (lastMessage) {
                    switch (data.type) {
                        case "message":
                            // Always append message content.
                            lastMessage.content += data.content;
                            break;
                        case "think":
                            if (isOccupied(lastMessage)) {
                                // Start a new system message if the last one is occupied.
                                const newMessage: ChatMessage = {role: "system", content: ""};
                                newMessage.reasoning = data.content;
                                updated.push(newMessage);
                            } else {
                                // Otherwise, append to the existing reasoning.
                                lastMessage.reasoning = lastMessage.reasoning
                                    ? lastMessage.reasoning + data.content
                                    : data.content;
                            }
                            break;
                        case "sup_docs": {
                            const docs = parseDocs(data.content);
                            if (isOccupied(lastMessage)) {
                                const newMessage: ChatMessage = {role: "system", content: ""};
                                newMessage.supporting_documents = docs;
                                updated.push(newMessage);
                            } else {
                                if (!lastMessage.supporting_documents) {
                                    lastMessage.supporting_documents = [];
                                }
                                lastMessage.supporting_documents.push(...docs);
                            }
                            break;
                        }
                        default:
                            break;
                    }
                } else {
                    // No existing system message: create a new one.
                    const newMessage: ChatMessage = {role: "system", content: ""};
                    switch (data.type) {
                        case "message":
                            newMessage.content = data.content;
                            break;
                        case "think":
                            newMessage.reasoning = data.content;
                            break;
                        case "sup_docs":
                            newMessage.supporting_documents = parseDocs(data.content);
                            break;
                        default:
                            break;
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
