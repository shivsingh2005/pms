import { api } from "@/services/api";
import type { GeneratedReportPayload } from "@/types";

interface GenerateReportRequest {
  report_type: "individual" | "team" | "business";
  employee_id?: string;
  manager_id?: string;
}

export const reportsService = {
  async generate(payload: GenerateReportRequest) {
    const { data } = await api.post<GeneratedReportPayload>("/reports/generate", payload);
    return data;
  },
};
