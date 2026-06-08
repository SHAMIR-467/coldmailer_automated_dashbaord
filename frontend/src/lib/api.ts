import axios from "axios";

export const api = axios.create({ baseURL: "/api", timeout: 30000 });

export type JobStatus = "pending" | "running" | "paused" | "done" | "failed";
export type LeadEmailStatus = "pending" | "generated" | "sent" | "failed" | "bounced";
export type EmailLogStatus = "generated" | "sent" | "failed";

export type CreateJobRequest = { keyword: string; cities?: string[] | null };

export type JobResponse = {
  id: string;
  keyword: string;
  cities: string[];
  status: JobStatus;
  total_extracted: number;
  total_emailed: number;
  batch_size: number;
  daily_limit: number;
  current_city_index: number;
  created_at: string;
  updated_at: string;
};

export type EmailLogResponse = {
  id: string;
  lead_id: string;
  job_id: string;
  subject: string;
  body: string;
  sent_at: string | null;
  status: EmailLogStatus;
  error_message: string | null;
  ollama_model: string;
  created_at: string;
  lead_business_name?: string | null;
};

export type LeadResponse = {
  id: string;
  job_id: string;
  business_name: string;
  email: string | null;
  phone: string | null;
  address: string | null;
  website: string | null;
  category: string | null;
  city: string;
  rating: number | null;
  review_count: number | null;
  maps_url: string | null;
  scraped_at: string;
  email_status: LeadEmailStatus;
  latest_email_log?: EmailLogResponse | null;
};

export type JobDetailResponse = JobResponse & {
  progress: number;
  leads: LeadResponse[];
  email_logs: EmailLogResponse[];
};

export type JobListResponse = { items: JobResponse[]; total: number };
export type LeadQueryParams = { page?: number; size?: number; has_email?: boolean | null; city?: string | null; email_status?: LeadEmailStatus | null };
export type LeadListResponse = { items: LeadResponse[]; total: number; page: number; size: number; pages: number };
export type EmailQueryParams = { job_id?: string | null; status?: EmailLogStatus | null; page?: number; size?: number };
export type EmailListResponse = { items: EmailLogResponse[]; total: number; page: number; size: number; pages: number };
export type EmailStats = { total_generated: number; total_sent: number; total_failed: number; success_rate: number };

export type DashboardStats = {
  total_jobs: number;
  active_jobs: number;
  total_leads: number;
  leads_with_email: number;
  total_emails_sent: number;
  emails_sent_today: number;
  daily_limit: number;
  daily_quota_used_pct: number;
  emails_by_status: { pending: number; generated: number; sent: number; failed: number };
  emails_per_day: Array<{ date: string; count: number }>;
  leads_per_job: Array<{ job_id: string; keyword: string; count: number }>;
};

export type SettingsResponse = {
  smtp_host: string;
  smtp_port: number;
  smtp_user: string;
  smtp_from_name: string;
  smtp_from_email: string;
  ollama_base_url: string;
  ollama_model: string;
  daily_email_limit: number;
  scrape_batch_size: number;
  scrape_delay_min: number;
  scrape_delay_max: number;
};

function cleanParams<T extends Record<string, unknown>>(params?: T) {
  return Object.fromEntries(Object.entries(params ?? {}).filter(([, value]) => value !== undefined && value !== null && value !== ""));
}

export const jobs = {
  async getJobs(): Promise<JobListResponse> {
    const response = await api.get<JobListResponse>("/jobs");
    return response.data;
  },
  async getJob(id: string): Promise<JobDetailResponse> {
    const response = await api.get<JobDetailResponse>(`/jobs/${id}`);
    return response.data;
  },
  async createJob(data: CreateJobRequest): Promise<JobResponse> {
    const response = await api.post<JobResponse>("/jobs", data);
    return response.data;
  },
  async startJob(id: string): Promise<JobResponse> {
    const response = await api.post<JobResponse>(`/jobs/${id}/start`);
    return response.data;
  },
  async pauseJob(id: string): Promise<JobResponse> {
    const response = await api.post<JobResponse>(`/jobs/${id}/pause`);
    return response.data;
  },
  async deleteJob(id: string): Promise<void> {
    await api.delete(`/jobs/${id}`);
  },
  async getJobLeads(id: string, params: LeadQueryParams = {}): Promise<LeadListResponse> {
    const response = await api.get<LeadListResponse>(`/jobs/${id}/leads`, { params: cleanParams(params) });
    return response.data;
  },
  exportLeadsCSV(id: string): void {
    void api.get(`/jobs/${id}/leads/export`, { responseType: "blob" }).then((response) => {
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.download = `leads_${id}.csv`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    });
  }
};

export const emails = {
  async getEmails(params: EmailQueryParams = {}): Promise<EmailListResponse> {
    const response = await api.get<EmailListResponse>("/emails", { params: cleanParams(params) });
    return response.data;
  },
  async resendEmail(id: string): Promise<EmailLogResponse> {
    const response = await api.post<EmailLogResponse>(`/emails/${id}/resend`);
    return response.data;
  },
  async getEmailStats(jobId: string): Promise<EmailStats> {
    const response = await api.get<EmailStats>(`/jobs/${jobId}/emails/stats`);
    return response.data;
  }
};

export const dashboard = {
  async getStats(): Promise<DashboardStats> {
    const response = await api.get<DashboardStats>("/dashboard/stats");
    return response.data;
  }
};

export const settingsApi = {
  async getSettings(): Promise<SettingsResponse> {
    const response = await api.get<SettingsResponse>("/settings");
    return response.data;
  },
  async testSmtp(): Promise<{ ok: boolean; message: string }> {
    const response = await api.post<{ ok: boolean; message: string }>("/settings/test-smtp");
    return response.data;
  },
  async testOllama(): Promise<{ ok: boolean }> {
    const response = await api.post<{ ok: boolean }>("/settings/test-ollama");
    return response.data;
  },
  async saveSettings(): Promise<{ status: string }> {
    const response = await api.put<{ status: string }>("/settings");
    return response.data;
  }
};
