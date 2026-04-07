import { api } from "@/services/api";
import type { CycleTimelineState } from "@/types";

export const employeeService = {
  async getCycleTimelineState(params?: { employeeId?: string; cycleId?: string }) {
    const { data } = await api.get<CycleTimelineState>("/employee/timeline/state", {
      params: {
        employeeId: params?.employeeId,
        cycleId: params?.cycleId,
      },
      ...( { skipErrorToast: true } as object),
    });
    return data;
  },
};
