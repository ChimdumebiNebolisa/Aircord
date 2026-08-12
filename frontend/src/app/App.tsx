import { useEffect, useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { api, type DemoSummary } from "../api/aircord";
import { LandingPage } from "../pages/LandingPage";
import { TrustExplorer } from "../pages/TrustExplorer";

export default function App() {
  const [demo, setDemo] = useState<DemoSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api
      .demoSummary()
      .then((summary) => {
        if (active) setDemo(summary);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        const message = reason instanceof Error ? reason.message : String(reason);
        setError(`The live API and static snapshot could not be loaded. ${message}`);
      });
    return () => {
      active = false;
    };
  }, []);

  const routeState = {
    demo,
    error,
    loading: !demo && !error,
  };

  return (
    <Routes>
      <Route path="/" element={<LandingPage {...routeState} />} />
      <Route path="/app" element={<TrustExplorer {...routeState} />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
