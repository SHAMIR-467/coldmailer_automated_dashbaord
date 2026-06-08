import { ReactNode, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Dashboard } from "./pages/Dashboard";
import { Emails } from "./pages/Emails";
import { JobDetail } from "./pages/JobDetail";
import { Jobs } from "./pages/Jobs";
import { Leads } from "./pages/Leads";
import { Settings } from "./pages/Settings";

function Spinner() {
  return <div className="flex min-h-[50vh] items-center justify-center text-teal-300">Loading...</div>;
}

function Page({ children }: { children: ReactNode }) {
  return <ErrorBoundary>{children}</ErrorBoundary>;
}

export default function App() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Page><Dashboard /></Page>} />
          <Route path="/jobs" element={<Page><Jobs /></Page>} />
          <Route path="/jobs/new" element={<Page><Jobs /></Page>} />
          <Route path="/jobs/:id" element={<Page><JobDetail /></Page>} />
          <Route path="/leads" element={<Page><Leads /></Page>} />
          <Route path="/emails" element={<Page><Emails /></Page>} />
          <Route path="/settings" element={<Page><Settings /></Page>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
