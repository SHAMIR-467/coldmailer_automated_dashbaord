import { Download, Inbox, Search } from "lucide-react";
import { useMemo, useState } from "react";
import { EmailPreview } from "./EmailPreview";
import { jobs, LeadEmailStatus, LeadResponse } from "../lib/api";
import { useJobLeads } from "../hooks/useJobs";

type Props = { jobId: string };

const statusClass: Record<LeadEmailStatus, string> = {
  pending: "bg-slate-500/20 text-slate-300",
  generated: "bg-blue-400/20 text-blue-300",
  sent: "bg-teal-400/20 text-teal-300",
  failed: "bg-red-400/20 text-red-300",
  bounced: "bg-amber-400/20 text-amber-300"
};

export function LeadsTable({ jobId }: Props) {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [emailStatus, setEmailStatus] = useState<LeadEmailStatus | "">("");
  const [hasEmail, setHasEmail] = useState(false);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [preview, setPreview] = useState<LeadResponse | null>(null);
  const leads = useJobLeads(jobId, { page, size: 50, city, email_status: emailStatus || null, has_email: hasEmail ? true : null });

  const items = useMemo(() => {
    const query = search.trim().toLowerCase();
    if (!query) return leads.data?.items ?? [];
    return (leads.data?.items ?? []).filter((lead) =>
      [lead.business_name, lead.city, lead.email, lead.phone, lead.category].filter(Boolean).some((value) => value!.toLowerCase().includes(query))
    );
  }, [leads.data?.items, search]);

  const cities = useMemo(() => Array.from(new Set((leads.data?.items ?? []).map((lead) => lead.city))).sort(), [leads.data?.items]);

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/40">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-500" />
            <input value={search} onChange={(event) => setSearch(event.target.value)} className="w-64 rounded-lg border border-slate-700 bg-slate-950 py-2 pl-9 pr-3 text-sm text-white outline-none focus:border-teal-400" placeholder="Search leads" />
          </div>
          <select value={city} onChange={(event) => setCity(event.target.value)} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
            <option value="">All cities</option>
            {cities.map((name) => <option key={name} value={name}>{name}</option>)}
          </select>
          <select value={emailStatus} onChange={(event) => setEmailStatus(event.target.value as LeadEmailStatus | "")} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white">
            <option value="">All statuses</option>
            {(["pending", "generated", "sent", "failed", "bounced"] as LeadEmailStatus[]).map((status) => <option key={status} value={status}>{status}</option>)}
          </select>
          <label className="flex items-center gap-2 text-sm text-slate-300">
            <input type="checkbox" checked={hasEmail} onChange={(event) => setHasEmail(event.target.checked)} className="h-4 w-4 accent-teal-500" />
            Has email
          </label>
        </div>
        <button onClick={() => jobs.exportLeadsCSV(jobId)} className="flex items-center gap-2 rounded-lg bg-teal-500 px-3 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400">
          <Download className="h-4 w-4" />
          Export CSV
        </button>
      </div>

      {leads.isLoading ? (
        <div className="p-4">
          {Array.from({ length: 5 }).map((_, index) => <div key={index} className="mb-3 h-12 animate-pulse rounded bg-slate-700/50" />)}
        </div>
      ) : items.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-slate-500">
          <Inbox className="h-10 w-10" />
          <div className="mt-3 text-sm">No leads match the current filters</div>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Business Name</th>
                <th className="px-4 py-3">City</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Phone</th>
                <th className="px-4 py-3">Category</th>
                <th className="px-4 py-3">Rating</th>
                <th className="px-4 py-3">Email Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((lead) => (
                <>
                  <tr key={lead.id} onClick={() => setExpanded(expanded === lead.id ? null : lead.id)} className="cursor-pointer border-t border-slate-800 hover:bg-slate-900/60">
                    <td className="px-4 py-3 font-medium text-white">{lead.business_name}</td>
                    <td className="px-4 py-3 text-slate-300">{lead.city}</td>
                    <td className="px-4 py-3 text-teal-300">{lead.email || "-"}</td>
                    <td className="px-4 py-3 text-slate-300">{lead.phone || "-"}</td>
                    <td className="px-4 py-3 text-slate-300">{lead.category || "-"}</td>
                    <td className="num px-4 py-3 text-slate-300">{lead.rating ?? "-"}</td>
                    <td className="px-4 py-3"><span className={`rounded-full px-2 py-1 text-xs capitalize ${statusClass[lead.email_status]}`}>{lead.email_status}</span></td>
                  </tr>
                  {expanded === lead.id && (
                    <tr className="border-t border-slate-800 bg-slate-950/70">
                      <td colSpan={7} className="px-4 py-4">
                        <div className="grid gap-3 text-sm text-slate-300 md:grid-cols-2">
                          <div><span className="text-slate-500">Address:</span> {lead.address || "Not captured"}</div>
                          <div><span className="text-slate-500">Website:</span> {lead.website ? <a className="text-teal-300" href={lead.website} target="_blank" rel="noreferrer">{lead.website}</a> : "Not captured"}</div>
                          <div><span className="text-slate-500">Maps:</span> {lead.maps_url ? <a className="text-teal-300" href={lead.maps_url} target="_blank" rel="noreferrer">Open in Maps</a> : "Not captured"}</div>
                          <div>{lead.latest_email_log ? <button onClick={(event) => { event.stopPropagation(); setPreview(lead); }} className="text-teal-300 hover:text-teal-200">View email preview</button> : <span className="text-slate-500">No email preview yet</span>}</div>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center justify-between border-t border-slate-800 p-4 text-sm text-slate-400">
        <span>Page {leads.data?.page ?? page} of {leads.data?.pages || 1}</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))} className="rounded-lg border border-slate-700 px-3 py-1.5 disabled:opacity-40">Prev</button>
          <button disabled={page >= (leads.data?.pages || 1)} onClick={() => setPage((value) => value + 1)} className="rounded-lg border border-slate-700 px-3 py-1.5 disabled:opacity-40">Next</button>
        </div>
      </div>
      {preview?.latest_email_log && <EmailPreview emailLog={preview.latest_email_log} onClose={() => setPreview(null)} />}
    </div>
  );
}
