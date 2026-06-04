const priorityRank = {
  HIGH: 0,
  MEDIUM: 1,
  LOW: 2,
};

export function sortNotifications(notifications) {
  return [...notifications].sort((a, b) => {
    const priorityDelta =
      (priorityRank[a.priority] ?? 9) - (priorityRank[b.priority] ?? 9);
    if (priorityDelta !== 0) {
      return priorityDelta;
    }
    return new Date(b.received_at).getTime() - new Date(a.received_at).getTime();
  });
}
