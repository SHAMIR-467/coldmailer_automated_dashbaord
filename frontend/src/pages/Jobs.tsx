import { Plus } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { JobCard } from "../components/JobCard";
import { JobStatus } from "../lib/api";
import { useCreateJob, useDeleteJob, useJobs, usePauseJob, useStartJob } from "../hooks/useJobs";

const tabs: Array<"all" | JobStatus> = ["all", "running", "paused", "done", "failed"];

export function Jobs() {
  const jobs = useJobs();
  const createJob = useCreateJob();
  const startJob = useStartJob();
  const pauseJob = usePauseJob();
  const deleteJob = useDeleteJob();
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<"all" | JobStatus>("all");
  const [keyword, setKeyword] = useState("");
  const [cities, setCities] = useState("");
  const [autoCities, setAutoCities] = useState(true);

  const filtered = useMemo(() => (jobs.data?.items ?? []).filter((job) => tab === "all" || job.status === tab), [jobs.data?.items, tab]);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    createJob.mutate({
      keyword,
      cities: autoCities ? null : cities.split(",").map((city) => city.trim()).filter(Boolean)
    });
    setKeyword("");
    setCities("");
    setOpen(false);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Jobs</h1>
          <p className="mt-1 text-sm text-slate-500">Launch and monitor city-based scraping runs</p>
        </div>
        <button onClick={() => setOpen((value) => !value)} className="flex items-center gap-2 rounded-lg bg-teal-500 px-4 py-2 font-semibold text-slate-950 hover:bg-teal-400">
          <Plus className="h-4 w-4" />
          New Job
        </button>
      </div>

      {open && (
        <form onSubmit={submit} className="grid gap-4 rounded-xl border border-slate-700/50 bg-slate-800/50 p-5">
          <input value={keyword} onChange={(event) => setKeyword(event.target.value)} required placeholder="Keyword, e.g. roofers" className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none focus:border-teal-400" />
          <textarea value={cities} onChange={(event) => setCities(event.target.value)} disabled={autoCities} placeholder="Optional cities, comma separated" className="min-h-24 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white outline-none disabled:opacity-50" />
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input type="checkbox" checked={autoCities} onChange={(event) => setAutoCities(event.target.checked)} className="h-4 w-4 accent-teal-500" />
            Auto-generate cities
          </label>
          <button className="w-fit rounded-lg bg-teal-500 px-4 py-2 font-semibold text-slate-950 hover:bg-teal-400">Create and Start</button>
        </form>
      )}

      <div className="flex flex-wrap gap-2">
        {tabs.map((item) => (
          <button key={item} onClick={() => setTab(item)} className={`rounded-full px-4 py-2 text-sm capitalize ${tab === item ? "bg-teal-400/20 text-teal-300" : "bg-slate-800 text-slate-400 hover:text-white"}`}>
            {item}
          </button>
        ))}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {filtered.length ? filtered.map((job) => (
          <JobCard key={job.id} job={job} onStart={startJob.mutate} onPause={pauseJob.mutate} onDelete={deleteJob.mutate} />
        )) : <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-10 text-slate-500">No jobs in this view</div>}
      </div>
    </div>
  );
}
