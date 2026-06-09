import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { settingsApi, type SettingsResponse } from "../lib/api";

const defaultSettings: SettingsResponse = {
  database_url: "sqlite+aiosqlite:///backend/data/leadgen.db",
  redis_url: "redis://localhost:6379/0",
  proxy_url: "",
  smtp_pass: "",
  smtp_host: "",
  smtp_port: 587,
  smtp_user: "",
  smtp_from_name: "",
  smtp_from_email: "",
  ollama_base_url: "http://localhost:11434",
  ollama_model: "llama3",
  daily_email_limit: 20000,
  scrape_batch_size: 20,
  scrape_delay_min: 2,
  scrape_delay_max: 5,
  cors_origins: ["http://localhost:5173"],
};

export function Settings() {
  const queryClient = useQueryClient();
  const settings = useQuery({ queryKey: ["settings"], queryFn: settingsApi.getSettings });
  const testSmtp = useMutation({ mutationFn: settingsApi.testSmtp });
  const testOllama = useMutation({ mutationFn: settingsApi.testOllama });
  const save = useMutation({ mutationFn: settingsApi.saveSettings, onSuccess: (data) => queryClient.setQueryData(["settings"], data) });
  const [form, setForm] = useState<SettingsResponse>(defaultSettings);

  useEffect(() => {
    if (settings.data) {
      setForm(settings.data);
    }
  }, [settings.data]);

  const inputClass = "w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-slate-300 outline-none";
  const sectionClass = "rounded-xl border border-slate-700/50 bg-slate-800/40 p-5";
  const update = <K extends keyof SettingsResponse>(key: K, value: SettingsResponse[K]) => setForm((current) => ({ ...current, [key]: value }));
  const originText = useMemo(() => form.cors_origins.join(", "), [form.cors_origins]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Settings</h1>
        <p className="mt-1 text-sm text-slate-500">Edit the runtime configuration directly from the app.</p>
      </div>

      <section className={sectionClass}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-white">Database</h2>
          <span className="text-xs text-slate-500">SQLite recommended</span>
        </div>
        <input className={inputClass} value={form.database_url} onChange={(e) => update("database_url", e.target.value)} placeholder="Database URL" />
      </section>

      <section className={sectionClass}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-white">Email Configuration</h2>
          <button onClick={() => testSmtp.mutate()} className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-teal-400 hover:text-teal-300">Test Connection</button>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <input className={inputClass} value={form.smtp_host} onChange={(e) => update("smtp_host", e.target.value)} placeholder="SMTP Host" />
          <input className={inputClass} type="number" value={form.smtp_port} onChange={(e) => update("smtp_port", Number(e.target.value))} placeholder="Port" />
          <input className={inputClass} value={form.smtp_user} onChange={(e) => update("smtp_user", e.target.value)} placeholder="SMTP User" />
          <input className={inputClass} value={form.smtp_pass} onChange={(e) => update("smtp_pass", e.target.value)} placeholder="Password" />
          <input className={inputClass} value={form.smtp_from_name} onChange={(e) => update("smtp_from_name", e.target.value)} placeholder="From Name" />
          <input className={inputClass} value={form.smtp_from_email} onChange={(e) => update("smtp_from_email", e.target.value)} placeholder="From Email" />
        </div>
        {testSmtp.data && <div className="mt-3 text-sm text-slate-400">{testSmtp.data.message}</div>}
      </section>

      <section className={sectionClass}>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-semibold text-white">AI Configuration</h2>
          <button onClick={() => testOllama.mutate()} className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 hover:border-teal-400 hover:text-teal-300">Test Ollama</button>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          <input className={inputClass} value={form.ollama_base_url} onChange={(e) => update("ollama_base_url", e.target.value)} placeholder="Ollama URL" />
          <select className={inputClass} value={form.ollama_model} onChange={(e) => update("ollama_model", e.target.value)} >
            {["llama3", "mistral", "llama2", "codellama"].map((model) => <option key={model}>{model}</option>)}
          </select>
          <input className={inputClass} type="number" value={form.daily_email_limit} onChange={(e) => update("daily_email_limit", Number(e.target.value))} placeholder="Daily limit" />
        </div>
        {testOllama.data && <div className={`mt-3 text-sm ${testOllama.data.ok ? "text-emerald-300" : "text-red-300"}`}>Ollama {testOllama.data.ok ? "connected" : "unavailable"}</div>}
      </section>

      <section className={sectionClass}>
        <h2 className="mb-4 font-semibold text-white">Scraping Configuration</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <input className={inputClass} type="number" min={1} max={500} value={form.scrape_batch_size} onChange={(e) => update("scrape_batch_size", Number(e.target.value))} placeholder="Batch size" />
          <input className={inputClass} type="number" min={0} step="0.1" value={form.scrape_delay_min} onChange={(e) => update("scrape_delay_min", Number(e.target.value))} placeholder="Min delay" />
          <input className={inputClass} type="number" min={0} step="0.1" value={form.scrape_delay_max} onChange={(e) => update("scrape_delay_max", Number(e.target.value))} placeholder="Max delay" />
        </div>
      </section>

      <section className={sectionClass}>
        <h2 className="mb-4 font-semibold text-white">Connectivity</h2>
        <div className="grid gap-4 md:grid-cols-2">
          <input className={inputClass} value={form.redis_url} onChange={(e) => update("redis_url", e.target.value)} placeholder="Redis URL" />
          <input className={inputClass} value={form.proxy_url} onChange={(e) => update("proxy_url", e.target.value)} placeholder="Proxy URL" />
          <textarea
            className={`${inputClass} min-h-24 md:col-span-2`}
            value={originText}
            onChange={(e) => update("cors_origins", e.target.value.split(",").map((item) => item.trim()).filter(Boolean))}
            placeholder="CORS origins, comma separated"
          />
        </div>
      </section>

      <div className="flex items-center gap-3">
        <button
          onClick={() => save.mutate(form)}
          className="rounded-lg bg-teal-500 px-4 py-2 font-semibold text-slate-950 hover:bg-teal-400 disabled:opacity-60"
          disabled={save.isPending}
        >
          {save.isPending ? "Saving..." : "Save Configuration"}
        </button>
        {save.data && <span className="text-sm text-slate-400">Configuration saved</span>}
        {save.error && <span className="text-sm text-red-300">Save failed</span>}
      </div>
    </div>
  );
}
