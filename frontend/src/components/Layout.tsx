import { Briefcase, LayoutDashboard, Mail, Settings, Users } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useDashboard } from "../hooks/useDashboard";

const navItems = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/jobs", label: "Jobs", icon: Briefcase },
  { to: "/leads", label: "Leads", icon: Users },
  { to: "/emails", label: "Emails", icon: Mail },
  { to: "/settings", label: "Settings", icon: Settings }
];

export function Layout() {
  const dashboard = useDashboard();
  const connected = !dashboard.isError;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-30 flex w-60 flex-col border-r border-slate-800 bg-slate-950">
        <div className="px-6 py-6">
          <div className="text-2xl font-bold tracking-tight text-teal-400">LeadGen</div>
          <div className="mt-1 text-xs uppercase tracking-[0.24em] text-slate-500">AI Automation</div>
        </div>
        <nav className="flex-1 space-y-1 px-3">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                `flex items-center gap-3 border-l-2 px-3 py-3 text-sm font-medium ${
                  isActive
                    ? "border-teal-400 bg-teal-400/10 text-teal-300"
                    : "border-transparent text-slate-400 hover:bg-slate-900 hover:text-slate-100"
                }`
              }
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-slate-800 p-4">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className={`h-2.5 w-2.5 rounded-full ${connected ? "bg-emerald-400" : "bg-red-400"}`} />
            Backend status
          </div>
          <div className="mt-1 text-sm font-medium text-slate-200">{connected ? "Connected" : "Unavailable"}</div>
        </div>
      </aside>
      <main className="ml-60 min-h-screen overflow-y-auto bg-slate-950 p-6">
        <Outlet />
      </main>
    </div>
  );
}
