import { ArrowLeft, Radio } from "lucide-react";
import { Link, useParams } from "react-router-dom";
import { EmailPreview } from "../components/EmailPreview";
import { LeadsTable } from "../components/LeadsTable";
import { useEmails, useResendEmail } from "../hooks/useEmails";
import { useJob, usePauseJob } from "../hooks/useJobs";
import { useState } from "react";
import { EmailLogResponse, jobs } from "../lib/api";

type Tab = "leads" | "emails" | "cities";

export function JobDetail() {
  const { id } = useParams();
  const job = useJob(id);
  const emails = useEmails({ job_id: id, size: 50 });
  const resend = useResendEmail();
  const pauseJob = usePauseJob();
  const [tab, setTab] = useState<Tab>("leads");
  const [preview, setPreview] = useState<EmailLogResponse | null>(null);
  const item = job.data;
  const successRate = item?.total_emailed && emails.data?.total ? Math.round((item.total_emailed / emails.data.total) * 100) : 0;

  if (!item) return <div className="text-slate-400">Loading job...</div>;

  function stopAndExport() {
    if (!id) return;
    pauseJob.mutate(id, { onSuccess: () => jobs.exportLeadsCSV(id) });
  }

  return (
    <div className="space-y-6">
      <Link to="/jobs" className="inline-flex items-center gap-2 text-sm text-slate-400 hover:text-teal-300"><ArrowLeft className="h-4 w-4" /> Back to jobs</Link>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-white">{item.keyword}</h1>
            <span className="rounded-full bg-teal-400/20 px-2.5 py-1 text-xs capitalize text-teal-300">{item.status}</span>
            {item.status === "running" && <span className="flex items-center gap-1 text-xs text-teal-300"><Radio className="h-3 w-3 animate-pulse" /> Live</span>}
          </div>
          <p className="mt-1 text-sm text-slate-500">Created {new Date(item.created_at).toLocaleString()}</p>
        </div>
        <button onClick={stopAndExport} className="rounded-lg bg-teal-500 px-4 py-2 font-semibold text-slate-950 hover:bg-teal-400">Stop & Export</button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {[
          ["Extracted Leads", item.total_extracted],
          ["Emails Sent", item.total_emailed],
          ["Cities Processed", `${item.current_city_index}/${item.cities.length}`],
          ["Success Rate", `${successRate}%`]
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
            <div className="text-xs text-slate-500">{label}</div>
            <div className="num mt-2 font-mono text-2xl font-bold text-white">{value}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
        <div className="mb-2 flex justify-between text-sm text-slate-400"><span>Scraping progress</span><span>{Math.round(item.progress)}%</span></div>
        <div className="h-2 rounded-full bg-slate-900"><div className="h-2 rounded-full bg-teal-400" style={{ width: `${item.progress}%` }} /></div>
      </div>

      <div className="flex gap-2 border-b border-slate-800">
        {(["leads", "emails", "cities"] as Tab[]).map((name) => (
          <button key={name} onClick={() => setTab(name)} className={`px-4 py-3 text-sm capitalize ${tab === name ? "border-b-2 border-teal-400 text-teal-300" : "text-slate-400 hover:text-white"}`}>{name}</button>
        ))}
      </div>

      {tab === "leads" && <LeadsTable jobId={item.id} />}
      {item.status === "running" && (
        <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-4">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">Latest Email Composition</h2>
          <div className="max-h-56 space-y-3 overflow-y-auto">
            {(emails.data?.items ?? []).slice(0, 3).map((log) => (
              <button key={log.id} onClick={() => setPreview(log)} className="block w-full rounded-lg bg-slate-950 p-3 text-left hover:bg-slate-900">
                <div className="text-sm font-semibold text-teal-300">{log.subject}</div>
                <div className="mt-1 line-clamp-2 text-sm text-slate-400">{log.body}</div>
              </button>
            ))}
          </div>
        </section>
      )}
      {tab === "emails" && (
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/40">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Subject</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Created</th><th className="px-4 py-3"></th></tr></thead>
            <tbody>{(emails.data?.items ?? []).map((log) => (
              <tr key={log.id} className="border-t border-slate-800">
                <td className="px-4 py-3 text-white">{log.subject}</td>
                <td className="px-4 py-3 capitalize text-slate-300">{log.status}</td>
                <td className="px-4 py-3 text-slate-400">{new Date(log.created_at).toLocaleString()}</td>
                <td className="px-4 py-3 text-right"><button onClick={() => setPreview(log)} className="text-teal-300">Preview</button><button onClick={() => resend.mutate(log.id)} className="ml-4 text-slate-300">Resend</button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {tab === "cities" && (
        <div className="grid gap-3 md:grid-cols-4">
          {item.cities.map((city, index) => (
            <div key={city} className={`rounded-lg border px-3 py-2 text-sm ${index < item.current_city_index ? "border-emerald-400/40 bg-emerald-400/10 text-emerald-300" : index === item.current_city_index ? "border-amber-400/40 bg-amber-400/10 text-amber-300" : "border-slate-700 bg-slate-800/40 text-slate-400"}`}>{city}</div>
          ))}
        </div>
      )}
      {preview && <EmailPreview emailLog={preview} onClose={() => setPreview(null)} />}
    </div>
  );
}
