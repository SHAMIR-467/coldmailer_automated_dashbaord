import { useState } from "react";
import { EmailPreview } from "../components/EmailPreview";
import { useEmails, useResendEmail } from "../hooks/useEmails";
import { EmailLogResponse, EmailLogStatus } from "../lib/api";

export function Emails() {
  const [status, setStatus] = useState<EmailLogStatus | "">("");
  const [page, setPage] = useState(1);
  const [preview, setPreview] = useState<EmailLogResponse | null>(null);
  const emails = useEmails({ status: status || null, page, size: 50 });
  const resend = useResendEmail();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Emails</h1>
        <p className="mt-1 text-sm text-slate-500">Generated outreach and delivery status</p>
      </div>
      <select value={status} onChange={(event) => setStatus(event.target.value as EmailLogStatus | "")} className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white">
        <option value="">All statuses</option>
        <option value="generated">Generated</option>
        <option value="sent">Sent</option>
        <option value="failed">Failed</option>
      </select>
      <div className="rounded-xl border border-slate-700/50 bg-slate-800/40">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-slate-500"><tr><th className="px-4 py-3">Business</th><th className="px-4 py-3">Subject</th><th className="px-4 py-3">Status</th><th className="px-4 py-3">Created</th><th className="px-4 py-3"></th></tr></thead>
          <tbody>{(emails.data?.items ?? []).map((log) => (
            <tr key={log.id} className="border-t border-slate-800">
              <td className="px-4 py-3 text-slate-300">{log.lead_business_name || "-"}</td>
              <td className="px-4 py-3 text-white">{log.subject}</td>
              <td className="px-4 py-3 capitalize text-slate-300">{log.status}</td>
              <td className="px-4 py-3 text-slate-400">{new Date(log.created_at).toLocaleString()}</td>
              <td className="px-4 py-3 text-right"><button onClick={() => setPreview(log)} className="text-teal-300">Preview</button><button onClick={() => resend.mutate(log.id)} className="ml-4 text-slate-300">Resend</button></td>
            </tr>
          ))}</tbody>
        </table>
        <div className="flex items-center justify-between border-t border-slate-800 p-4 text-sm text-slate-400">
          <span>Page {emails.data?.page ?? page} of {emails.data?.pages || 1}</span>
          <div className="flex gap-2">
            <button disabled={page <= 1} onClick={() => setPage((value) => Math.max(1, value - 1))} className="rounded-lg border border-slate-700 px-3 py-1.5 disabled:opacity-40">Prev</button>
            <button disabled={page >= (emails.data?.pages || 1)} onClick={() => setPage((value) => value + 1)} className="rounded-lg border border-slate-700 px-3 py-1.5 disabled:opacity-40">Next</button>
          </div>
        </div>
      </div>
      {preview && <EmailPreview emailLog={preview} onClose={() => setPreview(null)} />}
    </div>
  );
}
