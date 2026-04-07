import { create } from "zustand";
import type { Meeting } from "@/types";
import { meetingsService } from "@/services/meetings";

interface MeetingsState {
  meetings: Meeting[];
  loading: boolean;
  fetchMeetings: () => Promise<void>;
  createMeeting: (
    payload: {
      title: string;
      meeting_type?: "CHECKIN" | "GENERAL" | "HR" | "REVIEW";
      description?: string;
      start_time: string;
      end_time: string;
      participants: string[];
      checkin_id?: string;
      goal_id?: string;
    }
  ) => Promise<void>;
}

export const useMeetingsStore = create<MeetingsState>((set, get) => ({
  meetings: [],
  loading: false,
  fetchMeetings: async () => {
    set({ loading: true });
    const meetings = await meetingsService.getMeetings();
    set({ meetings, loading: false });
  },
  createMeeting: async (payload) => {
    await meetingsService.createMeeting(payload);
    await get().fetchMeetings();
  },
}));
