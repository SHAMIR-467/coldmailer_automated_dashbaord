import { useMutation, useQuery } from "@tanstack/react-query";
import { settingsApi } from "../lib/api";

export function Settings() {
  const settings = useQuery({ queryKey: ["settings"], queryFn: settingsApi.getSettings });
  const testSmtp = useMutation({ mutationFn: settingsApi.testSmtp });
  const testOllama = useMutation({ mutationFn: settingsApi.testOllama });
  const save = useMutation({ mutationFn: settingsApi.saveSettings });
  const data = settings.data;

  const inputClass = "rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-300 outline-none";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-slate-500">Read-only environment configuration for this MVP</p>
      </div>

      <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-white">Email Configuration</h2>
          <button onClick={() => testSmtp.mutate()} className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-teal-400 hover:text-teal-300">Test Connection</button>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <input className={inputClass} value={data?.smtp_host ?? ""} readOnly placeholder="SMTP Host" />
          <input className={inputClass} value={data?.smtp_port ?? ""} readOnly placeholder="Port" />
          <input className={inputClass} value={data?.smtp_user ?? ""} readOnly placeholder="SMTP User" />
          <input className={inputClass} value="********" readOnly placeholder="Password" />
          <input className={inputClass} value={data?.smtp_from_name ?? ""} readOnly placeholder="From Name" />
          <input className={inputClass} value={data?.smtp_from_email ?? ""} readOnly placeholder="From Email" />
        </div>
        {testSmtp.data && <div className="mt-3 text-sm text-slate-400">{testSmtp.data.message}</div>}
      </section>

      <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-white">AI Configuration</h2>
          <button onClick={() => testOllama.mutate()} className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-teal-400 hover:text-teal-300">Test Ollama</button>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <input className={inputClass} value={data?.ollama_base_url ?? ""} readOnly placeholder="Ollama URL" />
          <select className={inputClass} value={data?.ollama_model ?? "llama3"} disabled>
            {["llama3", "mistral", "llama2", "codellama"].map((model) => <option key={model}>{model}</option>)}
          </select>
          <input className={inputClass} value={data?.daily_email_limit ?? ""} readOnly placeholder="Daily limit" />
        </div>
        {testOllama.data && <div className={`mt-3 text-sm ${testOllama.data.ok ? "text-emerald-300" : "text-red-300"}`}>Ollama {testOllama.data.ok ? "connected" : "unavailable"}</div>}
      </section>

      <section className="rounded-xl border border-slate-700/50 bg-slate-800/40 p-5">
        <h2 className="mb-4 font-semibold text-white">Scraping Configuration</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <label className="grid gap-2 text-sm text-slate-400">Batch size<input type="range" min="10" max="50" value={data?.scrape_batch_size ?? 20} readOnly /></label>
          <input className={inputClass} value={data?.scrape_delay_min ?? ""} readOnly placeholder="Min delay" />
          <input className={inputClass} value={data?.scrape_delay_max ?? ""} readOnly placeholder="Max delay" />
        </div>
      </section>

      <button onClick={() => save.mutate()} className="rounded-lg bg-teal-500 px-4 py-2 font-semibold text-slate-950 hover:bg-teal-400">Save</button>
      {save.data && <span className="ml-3 text-sm text-slate-400">{save.data.status}</span>}
    </div>
  );
}
