import { create } from "zustand";
import { aiService } from "@/services/ai";
import type { AIChatMessage } from "@/types";

interface AIState {
  messages: AIChatMessage[];
  suggestedActions: string[];
  loading: boolean;
  ask: (message: string, page?: string) => Promise<void>;
}

export const useAIStore = create<AIState>((set, get) => ({
  messages: [],
  suggestedActions: [],
  loading: false,
  ask: async (message: string, page?: string) => {
    const userMessage: AIChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: message,
      createdAt: Date.now(),
    };
    set({ messages: [...get().messages, userMessage], loading: true });

    try {
      const response = await aiService.ask(message, page);
      const assistantMessage: AIChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.response,
        createdAt: Date.now(),
      };
      set({
        messages: [...get().messages, assistantMessage],
        suggestedActions: response.suggested_actions || [],
        loading: false,
      });
    } catch {
      const assistantMessage: AIChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "I cannot answer right now. Please try again.",
        createdAt: Date.now(),
      };
      set({ messages: [...get().messages, assistantMessage], loading: false });
    }
  },
}));
