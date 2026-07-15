import type { ReactNode } from "react";
import type { IconReference } from "../components/NorthStarIcon";
import { Badge, Icon } from "./primitives";

export function LegacyPanel({
  action,
  children,
  className = "",
  icon,
  title,
}: {
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  icon?: IconReference;
  title?: ReactNode;
}) {
  return (
    <section className={`legacy-panel ${className}`.trim()}>
      {title ? (
        <header>
          <div>{icon ? <Icon name={icon} size={18} /> : null}<h2>{title}</h2></div>
          {action ? <span>{action}</span> : null}
        </header>
      ) : null}
      {children}
    </section>
  );
}

export function LegacyStatus({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "blue" | "green" | "orange" | "red" | "purple" | "neutral";
}) {
  return <Badge tone={tone}>{children}</Badge>;
}

export function LegacyMeta({
  icon,
  label,
  tone,
  value,
}: {
  icon?: IconReference;
  label: string;
  tone?: "green" | "orange" | "red" | "blue";
  value: ReactNode;
}) {
  return (
    <div className="legacy-meta">
      {icon ? <Icon name={icon} size={15} /> : null}
      <span>{label}</span>
      <strong className={tone ? `tone-${tone}` : ""}>{value}</strong>
    </div>
  );
}

export function LegacyListRow({
  detail,
  icon = "file-text",
  selected = false,
  status,
  title,
}: {
  detail?: ReactNode;
  icon?: IconReference;
  selected?: boolean;
  status?: ReactNode;
  title: ReactNode;
}) {
  return (
    <div className={`legacy-list-row ${selected ? "selected" : ""}`}>
      <span className="legacy-row-icon"><Icon name={icon} size={17} /></span>
      <span><strong>{title}</strong>{detail ? <small>{detail}</small> : null}</span>
      {status ? <span className="legacy-row-status">{status}</span> : null}
    </div>
  );
}

export function LegacyProgress({ value, tone = "blue" }: { value: number; tone?: "blue" | "green" | "orange" | "red" }) {
  return <span className={`legacy-progress ${tone}`}><i style={{ width: `${value}%` }} /></span>;
}

export function LegacyEmptyLine({ width = "80%" }: { width?: string }) {
  return <span className="legacy-empty-line" style={{ width }} />;
}
