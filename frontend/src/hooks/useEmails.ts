import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { EmailQueryParams, emails } from "../lib/api";

export function useEmails(params: EmailQueryParams = {}) {
  return useQuery({
    queryKey: ["emails", params],
    queryFn: () => emails.getEmails(params),
    refetchInterval: 10000
  });
}

export function useEmailStats(jobId?: string) {
  return useQuery({
    queryKey: ["email-stats", jobId],
    queryFn: () => emails.getEmailStats(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: 5000
  });
}

export function useResendEmail() {
  const client = useQueryClient();
  return useMutation({
    mutationFn: emails.resendEmail,
    onSuccess: () => {
      void client.invalidateQueries({ queryKey: ["emails"] });
      void client.invalidateQueries({ queryKey: ["dashboard"] });
    }
  });
}
