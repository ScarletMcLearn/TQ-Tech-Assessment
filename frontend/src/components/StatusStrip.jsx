import { Clock, Database, RefreshCw, ShieldCheck } from "lucide-react";

function StatusItem({ icon: Icon, label, value }) {
  return (
    <div className="status-item">
      <Icon size={16} aria-hidden="true" />
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function StatusStrip({ health, lastUpdated }) {
  const source = health?.email_source || "mock";
  const interval = health?.scheduler?.poll_interval_seconds ?? 30;
  const database = health?.database || "checking";
  const updatedLabel = lastUpdated
    ? new Intl.DateTimeFormat(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      }).format(lastUpdated)
    : "pending";

  return (
    <section className="status-strip" aria-label="Agent status">
      <StatusItem icon={Database} label="Source" value={source.toUpperCase()} />
      <StatusItem icon={Clock} label="Poll" value={`${interval}s`} />
      <StatusItem icon={ShieldCheck} label="Database" value={database.toUpperCase()} />
      <StatusItem icon={RefreshCw} label="Refreshed" value={updatedLabel} />
    </section>
  );
}
