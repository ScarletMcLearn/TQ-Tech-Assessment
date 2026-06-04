import { useCallback, useEffect, useMemo, useState } from "react";
import { Play, RefreshCw } from "lucide-react";

import { getHealth, getNotifications, runAgentOnce } from "./api";
import { NotificationTable } from "./components/NotificationTable";
import { StatusStrip } from "./components/StatusStrip";
import { SummaryCards } from "./components/SummaryCards";
import { sortNotifications } from "./utils/notifications";

function buildCounts(notifications) {
  return notifications.reduce(
    (counts, notification) => {
      counts[notification.priority] = (counts[notification.priority] || 0) + 1;
      return counts;
    },
    { HIGH: 0, MEDIUM: 0, LOW: 0 },
  );
}

function App() {
  const [health, setHealth] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastRunSummary, setLastRunSummary] = useState(null);

  const refreshDashboard = useCallback(async ({ silent = false } = {}) => {
    if (!silent) {
      setIsLoading(true);
    }
    setError("");

    try {
      const [nextHealth, nextNotifications] = await Promise.all([
        getHealth(),
        getNotifications(),
      ]);
      setHealth(nextHealth);
      setNotifications(sortNotifications(nextNotifications));
      setLastUpdated(new Date());
    } catch (nextError) {
      setError(nextError.message || "Could not load dashboard data.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void refreshDashboard();
    const timer = window.setInterval(() => {
      void refreshDashboard({ silent: true });
    }, 6000);

    return () => window.clearInterval(timer);
  }, [refreshDashboard]);

  const counts = useMemo(() => buildCounts(notifications), [notifications]);

  const handleRunAgent = useCallback(async () => {
    setIsRunning(true);
    setError("");
    try {
      const response = await runAgentOnce();
      setLastRunSummary(response.summary);
      await refreshDashboard({ silent: true });
    } catch (nextError) {
      setError(nextError.message || "Agent run failed.");
    } finally {
      setIsRunning(false);
    }
  }, [refreshDashboard]);

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>AI Email Reading Agent</h1>
          <p>Important classified emails from the mock inbox.</p>
        </div>
        <div className="actions">
          <button
            className="button button-secondary icon-button"
            type="button"
            onClick={() => refreshDashboard()}
            disabled={isLoading || isRunning}
            title="Refresh dashboard"
            aria-label="Refresh dashboard"
          >
            <RefreshCw size={17} aria-hidden="true" />
          </button>
          <button
            className="button button-primary"
            type="button"
            onClick={handleRunAgent}
            disabled={isRunning}
          >
            <Play size={17} aria-hidden="true" />
            {isRunning ? "Running..." : "Run Agent Now"}
          </button>
        </div>
      </header>

      <StatusStrip health={health} lastUpdated={lastUpdated} />
      <SummaryCards counts={counts} />

      {error ? (
        <div className="alert" role="alert">
          {error}
        </div>
      ) : null}

      {lastRunSummary ? (
        <section className="run-summary" aria-live="polite">
          <strong>Last run:</strong>
          <span>{lastRunSummary.fetched} fetched</span>
          <span>{lastRunSummary.classified} classified</span>
          <span>{lastRunSummary.notifications_created} notifications</span>
          <span>{lastRunSummary.skipped_duplicates} duplicates skipped</span>
          <span>{lastRunSummary.ignored} ignored</span>
        </section>
      ) : null}

      <NotificationTable notifications={notifications} isLoading={isLoading} />
    </main>
  );
}

export default App;
