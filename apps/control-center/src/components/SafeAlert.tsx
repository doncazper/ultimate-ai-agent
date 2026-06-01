interface SafeAlertProps {
  title: string;
  message: string;
  tone?: "info" | "warning" | "danger";
}

export function SafeAlert({ title, message, tone = "info" }: SafeAlertProps) {
  return (
    <section className={`safe-alert ${tone}`} role={tone === "danger" ? "alert" : "status"}>
      <strong>{title}</strong>
      <span>{message}</span>
    </section>
  );
}
