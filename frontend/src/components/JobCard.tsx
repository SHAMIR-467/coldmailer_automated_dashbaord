import { Pause, Play, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { JobDetailResponse, JobResponse } from "../lib/api";

type Props = {
  job: JobDetailResponse | JobResponse;
  onStart: (id: string) => void;
  onPause: (id: string) => void;
  onDelete: (id: string) => void;
};

const statusClass = {
  pending: "bg-slate-500/20 text-slate-300",
  running: "bg-teal-400/20 text-teal-300 animate-pulse",
  paused: "bg-amber-400/20 text-amber-300",
  done: "bg-emerald-400/20 text-emerald-300",
  failed: "bg-red-400/20 text-red-300"
};

export function JobCard({ job, onStart, onPause, onDelete }: Props) {
  const progress = job.cities.length ? Math.min(100, Math.round((job.current_city_index / job.cities.length) * 100)) : 0;
  return (
    <div className={`rounded-xl border bg-slate-800/50 p-5 ${job.status === "running" ? "border-teal-400/60 shadow-lg shadow-teal-950/50" : "border-slate-700/50"}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${statusClass[job.status]}`}>{job.status}</span>
          <Link to={`/jobs/${job.id}`} className="mt-3 block text-xl font-semibold text-white hover:text-teal-300">
            {job.keyword}
          </Link>
          <div className="mt-1 text-xs text-slate-500">Created {new Date(job.created_at).toLocaleString()}</div>
        </div>
        <div className="flex gap-2">
          <button onClick={() => onStart(job.id)} className="rounded-lg border border-slate-700 p-2 text-slate-300 hover:border-teal-400 hover:text-teal-300" title="Start">
            <Play className="h-4 w-4" />
          </button>
          <button onClick={() => onPause(job.id)} className="rounded-lg border border-slate-700 p-2 text-slate-300 hover:border-amber-400 hover:text-amber-300" title="Pause">
            <Pause className="h-4 w-4" />
          </button>
          <button onClick={() => onDelete(job.id)} className="rounded-lg border border-slate-700 p-2 text-slate-300 hover:border-red-400 hover:text-red-300" title="Delete">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="mt-5">
        <div className="mb-2 flex justify-between text-xs text-slate-400">
          <span>{job.current_city_index}/{job.cities.length} cities</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2 rounded-full bg-slate-900">
          <div className="h-2 rounded-full bg-teal-400 transition-all" style={{ width: `${progress}%` }} />
        </div>
      </div>
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-slate-900/70 p-3">
          <div className="text-xs text-slate-500">Leads Found</div>
          <div className="num mt-1 font-mono text-2xl font-bold text-white">{job.total_extracted.toLocaleString()}</div>
        </div>
        <div className="rounded-lg bg-slate-900/70 p-3">
          <div className="text-xs text-slate-500">Emails Sent</div>
          <div className="num mt-1 font-mono text-2xl font-bold text-white">{job.total_emailed.toLocaleString()}</div>
        </div>
      </div>
    </div>
  );
}

export function JobCardSkeleton() {
  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5">
      <div className="h-5 w-24 animate-pulse rounded bg-slate-700" />
      <div className="mt-4 h-7 w-48 animate-pulse rounded bg-slate-700" />
      <div className="mt-5 h-2 animate-pulse rounded bg-slate-700" />
      <div className="mt-5 grid grid-cols-2 gap-3">
        <div className="h-20 animate-pulse rounded-lg bg-slate-900" />
        <div className="h-20 animate-pulse rounded-lg bg-slate-900" />
      </div>
    </div>
  );
}
