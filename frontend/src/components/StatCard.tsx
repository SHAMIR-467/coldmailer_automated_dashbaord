import { LucideIcon } from "lucide-react";

type Props = {
  label: string;
  value: string | number;
  icon: LucideIcon;
  trend?: number;
  color?: "teal" | "blue" | "amber" | "red";
  loading?: boolean;
};

const colors = {
  teal: "bg-teal-400/20 text-teal-300",
  blue: "bg-blue-400/20 text-blue-300",
  amber: "bg-amber-400/20 text-amber-300",
  red: "bg-red-400/20 text-red-300"
};

export function StatCard({ label, value, icon: Icon, trend, color = "teal", loading = false }: Props) {
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-6 shadow-lg shadow-black/10">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-slate-400">{label}</span>
        <span className={`rounded-lg p-2 ${colors[color]}`}>
          <Icon className="h-5 w-5" />
        </span>
      </div>
      <div className="mt-4 flex items-end justify-between gap-3">
        {loading ? <div className="h-9 w-28 animate-pulse rounded bg-slate-700" /> : <div className="num font-mono text-3xl font-bold text-white">{value}</div>}
        {typeof trend === "number" && (
          <div className={`text-sm font-semibold ${trend >= 0 ? "text-emerald-400" : "text-red-400"}`}>
            {trend >= 0 ? "↑" : "↓"} {Math.abs(trend)}%
          </div>
        )}
      </div>
    </div>
  );
}
