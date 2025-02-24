export interface ChatMessage {
  role: "user" | "system";
  content: string;
  reasoning?: string;
  supporting_documents?: string[]
}

export interface ChatToken {
  type: "user" | "message"| "think" | "sup_docs";
  content: string;
}

export interface WSMessage {
  role: "user" | "system";
  content: string;
}