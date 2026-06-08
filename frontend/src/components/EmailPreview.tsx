import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { createPortal } from "react-dom";
import { EmailLogResponse } from "../lib/api";
import { useResendEmail } from "../hooks/useEmails";

type Props = { emailLog: EmailLogResponse; onClose: () => void };

export function EmailPreview({ emailLog, onClose }: Props) {
  const resend = useResendEmail();
  const [mount, setMount] = useState<HTMLElement | null>(null);

  useEffect(() => {
    const node = document.createElement("div");
    document.body.appendChild(node);
    setMount(node);
    return () => node.remove();
  }, []);

  if (!mount) return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-6">
      <div className="w-full max-w-2xl rounded-xl border border-slate-700 bg-slate-900 shadow-2xl">
        <div className="flex items-start justify-between border-b border-slate-800 p-5">
          <div>
            <div className="font-semibold text-white">{emailLog.lead_business_name || "Email preview"}</div>
            <div className="mt-1 text-xs text-slate-500">{emailLog.sent_at ? new Date(emailLog.sent_at).toLocaleString() : emailLog.status}</div>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white">
            <X className="h-5 w-5" />
          </button>
        </div>
        <div className="p-5">
          <div className="text-sm uppercase tracking-wide text-teal-300">Subject</div>
          <div className="mt-1 text-lg font-semibold text-white">{emailLog.subject}</div>
          <div className="mt-5 whitespace-pre-wrap rounded-lg bg-slate-950 p-5 leading-7 text-slate-200">{emailLog.body}</div>
          <div className="mt-5 flex justify-end">
            <button onClick={() => resend.mutate(emailLog.id)} className="rounded-lg bg-teal-500 px-4 py-2 text-sm font-semibold text-slate-950 hover:bg-teal-400">
              Resend
            </button>
          </div>
        </div>
      </div>
    </div>,
    mount
  );
}
