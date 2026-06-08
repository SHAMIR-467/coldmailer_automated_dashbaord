import { useQuery } from "@tanstack/react-query";
import { dashboard } from "../lib/api";

export function useDashboard() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: dashboard.getStats,
    refetchInterval: 10000
  });
}
