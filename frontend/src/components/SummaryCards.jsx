import { AlertTriangle, Bell, CheckCircle2 } from "lucide-react";

const cards = [
  { key: "HIGH", label: "High priority", icon: AlertTriangle },
  { key: "MEDIUM", label: "Medium priority", icon: Bell },
  { key: "LOW", label: "Low priority", icon: CheckCircle2 },
];

export function SummaryCards({ counts }) {
  return (
    <section className="summary-grid" aria-label="Priority summary">
      {cards.map(({ key, label, icon: Icon }) => (
        <article className={`summary-card summary-${key.toLowerCase()}`} key={key}>
          <div className="summary-icon">
            <Icon size={18} aria-hidden="true" />
          </div>
          <div>
            <span>{label}</span>
            <strong>{counts[key] || 0}</strong>
          </div>
        </article>
      ))}
    </section>
  );
}
