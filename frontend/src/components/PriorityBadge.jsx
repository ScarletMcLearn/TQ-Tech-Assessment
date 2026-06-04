export function PriorityBadge({ priority }) {
  return (
    <span className={`priority priority-${priority.toLowerCase()}`}>{priority}</span>
  );
}
