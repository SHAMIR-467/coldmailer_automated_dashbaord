import { Activity, Briefcase, MailCheck, Users } from "lucide-react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { JobCard } from "../components/JobCard";
import { ProgressRing } from "../components/ProgressRing";
import { StatCard } from "../components/StatCard";
import { useDashboard } from "../hooks/useDashboard";
import { useDeleteJob, useJobs, usePauseJob, useStartJob } from "../hooks/useJobs";
import { useToast } from "../hooks/useToast";

const statusColors = { pending: "#64748b", generated: "#3b82f6", sent: "#14b8a6", failed: "#ef4444" };

export function Dashboard() {
  const dashboard = useDashboard();
  const jobs = useJobs();
  const startJob = useStartJob();
  const pauseJob = usePauseJob();
  const deleteJob = useDeleteJob();
  const { showToast } = useToast();
  const stats = dashboard.data;
  const successRate = stats?.emails_by_status.sent || stats?.emails_by_status.failed
    ? Math.round((stats.emails_by_status.sent / Math.max(1, stats.emails_by_status.sent + stats.emails_by_status.failed)) * 100)
    : 0;
  const activeJobs = (jobs.data?.items ?? []).filter((job) => job.status === "running").slice(0, 3);
  const statusData = stats
    ? Object.entries(stats.emails_by_status).map(([name, value]) => ({ name, value }))
    : [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Operations Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">Live scraping and outbound email telemetry</p>
      </div>

      <div className="grid gap-4 xl:grid-cols-4">
        <StatCard loading={dashboard.isLoading} label="Total Leads" value={stats?.total_leads.toLocaleString() ?? "0"} icon={Users} color="teal" />
        <StatCard loading={dashboard.isLoading} label="Emails Sent Today" value={stats?.emails_sent_today.toLocaleString() ?? "0"} icon={MailCheck} color="blue" />
        <StatCard loading={dashboard.isLoading} label="Active Jobs" value={stats?.active_jobs ?? 0} icon={Briefcase} color="amber" />
        <StatCard loading={dashboard.isLoading} label="Success Rate" value={`${successRate}%`} icon={Activity} color="teal" trend={successRate} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[3fr_2fr]">
        <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">Emails Sent Per Day</h2>
          <div className="h-72">
            <ResponsiveContainer>
              <LineChart data={stats?.emails_per_day ?? []}>
                <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 12 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", color: "#fff" }} />
                <Line type="monotone" dataKey="count" stroke="#14b8a6" strokeWidth={3} dot={{ fill: "#14b8a6" }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">Email Status Breakdown</h2>
          <div className="h-72">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={statusData} dataKey="value" nameKey="name" innerRadius={64} outerRadius={104} paddingAngle={3}>
                  {statusData.map((entry) => <Cell key={entry.name} fill={statusColors[entry.name as keyof typeof statusColors]} />)}
                </Pie>
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", color: "#fff" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {statusData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-2 text-sm text-slate-300">
                <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: statusColors[entry.name as keyof typeof statusColors] }} />
                <span className="capitalize">{entry.name}</span>
                <span className="num ml-auto font-mono">{entry.value}</span>
              </div>
            ))}
          </div>
        </section>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
          <ProgressRing value={stats?.emails_sent_today ?? 0} max={stats?.daily_limit ?? 20000} />
          <div className="mt-5 text-center text-sm text-slate-400">{stats?.emails_sent_today ?? 0}/{stats?.daily_limit ?? 20000} used today</div>
        </section>
        <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">Top Jobs By Leads</h2>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={stats?.leads_per_job ?? []} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
                <XAxis type="number" stroke="#64748b" />
                <YAxis type="category" dataKey="keyword" stroke="#64748b" width={110} />
                <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #334155", color: "#fff" }} />
                <Bar dataKey="count" fill="#14b8a6" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-white">Active Jobs</h2>
          <Link to="/jobs" className="text-sm font-medium text-teal-300 hover:text-teal-200">View all jobs →</Link>
        </div>
        <div className="grid gap-4 xl:grid-cols-3">
          {activeJobs.length ? activeJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onStart={(id) => startJob.mutate(id, { onSuccess: () => showToast("Job started"), onError: () => showToast("Failed to start job", "error") })}
              onPause={(id) => pauseJob.mutate(id, { onSuccess: () => showToast("Job paused"), onError: () => showToast("Failed to pause job", "error") })}
              onDelete={(id) => deleteJob.mutate(id, { onSuccess: () => showToast("Job stopped"), onError: () => showToast("Failed to stop job", "error") })}
            />
          )) : <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-8 text-slate-500">No active jobs right now</div>}
        </div>
      </section>
    </div>
  );
}
