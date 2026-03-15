import { create } from "zustand";
import type { Meeting } from "@/types";
import { meetingsService } from "@/services/meetings";

interface MeetingsState {
  meetings: Meeting[];
  loading: boolean;
  fetchMeetings: (googleToken: string) => Promise<void>;
  createMeeting: (
    payload: {
      title: string;
      description?: string;
      start_time: string;
      end_time: string;
      participants: string[];
      goal_id: string;
    },
    googleToken: string,
  ) => Promise<void>;
}

export const useMeetingsStore = create<MeetingsState>((set, get) => ({
  meetings: [],
  loading: false,
  fetchMeetings: async (googleToken) => {
    set({ loading: true });
    const meetings = await meetingsService.getMeetings(googleToken);
    set({ meetings, loading: false });
  },
  createMeeting: async (payload, googleToken) => {
    await meetingsService.createMeeting(payload, googleToken);
    await get().fetchMeetings(googleToken);
  },
}));
