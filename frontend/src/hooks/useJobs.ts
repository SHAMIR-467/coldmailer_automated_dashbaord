import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CreateJobRequest, jobs, LeadQueryParams } from "../lib/api";

export function useJobs() {
  return useQuery({
    queryKey: ["jobs"],
    queryFn: jobs.getJobs,
    refetchInterval: 5000
  });
}

export function useJob(id?: string) {
  return useQuery({
    queryKey: ["job", id],
    queryFn: () => jobs.getJob(id!),
    enabled: Boolean(id),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 3000 : false)
  });
}

export function useCreateJob() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateJobRequest) => jobs.createJob(payload),
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["jobs"] });
      void client.invalidateQueries({ queryKey: ["dashboard"] });
    }
  });
}

export function useStartJob() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: jobs.startJob,
    onSuccess: (job) => {
      void client.invalidateQueries({ queryKey: ["jobs"] });
      void client.invalidateQueries({ queryKey: ["job", job.id] });
    }
  });
}

export function usePauseJob() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: jobs.pauseJob,
    onSuccess: (job) => {
      void client.invalidateQueries({ queryKey: ["jobs"] });
      void client.invalidateQueries({ queryKey: ["job", job.id] });
    }
  });
}

export function useDeleteJob() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: jobs.deleteJob,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["jobs"] });
      void client.invalidateQueries({ queryKey: ["dashboard"] });
    }
  });
}

export function useJobLeads(id?: string, params: LeadQueryParams = {}) {
  return useQuery({
    queryKey: ["job-leads", id, params],
    queryFn: () => jobs.getJobLeads(id!, params),
    enabled: Boolean(id),
    refetchInterval: 5000
  });
}
