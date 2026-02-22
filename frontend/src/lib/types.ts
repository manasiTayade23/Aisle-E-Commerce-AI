export interface Product {
  id: number;
  title: string;
  price: number;
  description?: string;
  category: string;
  image: string;
  rating: {
    rate: number;
    count: number;
  };
}

export interface CartItem {
  product_id: number;
  title: string;
  price: number;
  quantity: number;
  item_total: number;
  image: string;
}

export interface ToolCallData {
  name: string;
  input: Record<string, unknown>;
}

export interface ToolResultData {
  name: string;
  data: {
    products?: Product[];
    count?: number;
    items?: CartItem[];
    total?: number;
    success?: boolean;
    [key: string]: unknown;
  };
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolCalls?: ToolCallData[];
  toolResults?: ToolResultData[];
  isStreaming?: boolean;
  timestamp?: number;
}

export interface Conversation {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: number;
  messageCount: number;
}
