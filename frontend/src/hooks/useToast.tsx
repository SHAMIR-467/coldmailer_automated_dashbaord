import { createContext, ReactNode, useContext, useState } from "react";

type Toast = { id: number; message: string; type: "success" | "error" };
type ToastContextValue = { showToast: (message: string, type?: Toast["type"]) => void };

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  function showToast(message: string, type: Toast["type"] = "success") {
    const id = Date.now() + Math.random();
    setToasts((items) => [...items, { id, message, type }]);
    window.setTimeout(() => setToasts((items) => items.filter((toast) => toast.id !== id)), 4000);
  }

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="fixed bottom-5 right-5 z-[60] grid gap-3">
        {toasts.map((toast) => (
          <div key={toast.id} className={`min-w-72 rounded-lg border px-4 py-3 shadow-lg ${toast.type === "success" ? "border-teal-400/40 bg-teal-950 text-teal-100" : "border-red-400/40 bg-red-950 text-red-100"}`}>
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside ToastProvider");
  return context;
}
