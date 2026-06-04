import { Inbox } from "lucide-react";

import { PriorityBadge } from "./PriorityBadge";

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function NotificationTable({ notifications, isLoading }) {
  if (!isLoading && notifications.length === 0) {
    return (
      <section className="empty-state" aria-live="polite">
        <Inbox size={28} aria-hidden="true" />
        <div>
          <h2>No important emails yet</h2>
          <p>Run the agent or wait for the next poll to classify mock emails.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="table-panel" aria-label="Important email notifications">
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Sender</th>
              <th>Subject</th>
              <th>Priority</th>
              <th>Category</th>
              <th>Reason</th>
              <th>Time received</th>
            </tr>
          </thead>
          <tbody>
            {notifications.map((notification) => (
              <tr key={notification.email_id}>
                <td data-label="Sender">
                  <span className="sender">{notification.sender}</span>
                </td>
                <td data-label="Subject">
                  <span className="subject">{notification.subject}</span>
                </td>
                <td data-label="Priority">
                  <PriorityBadge priority={notification.priority} />
                </td>
                <td data-label="Category">
                  <span className="category">{notification.category}</span>
                </td>
                <td className="reason" data-label="Reason">
                  {notification.reason}
                </td>
                <td className="time" data-label="Time received">
                  {formatDate(notification.received_at)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
