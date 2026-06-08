import { useMemo, useState } from "react";
import { LeadsTable } from "../components/LeadsTable";
import { useJobs } from "../hooks/useJobs";

export function Leads() {
  const jobs = useJobs();
  const firstJobId = jobs.data?.items[0]?.id ?? "";
  const [selectedJobId, setSelectedJobId] = useState("");
  const activeJobId = selectedJobId || firstJobId;
  const options = useMemo(() => jobs.data?.items ?? [], [jobs.data?.items]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Leads</h1>
        <p className="mt-1 text-sm text-slate-500">Browse captured leads by job</p>
      </div>
      <select value={activeJobId} onChange={(event) => setSelectedJobId(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white">
        {options.map((job) => <option key={job.id} value={job.id}>{job.keyword}</option>)}
      </select>
      {activeJobId ? <LeadsTable jobId={activeJobId} /> : <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-10 text-slate-500">Create a job to collect leads</div>}
    </div>
  );
}
