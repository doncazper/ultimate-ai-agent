import type { ButtonHTMLAttributes, ReactNode } from "react";
import {
  NorthStarIcon,
  type IconReference,
  type IconTone,
} from "../components/NorthStarIcon";

export function Icon({
  name,
  size = 18,
  tone = "current",
}: {
  name: IconReference;
  size?: number;
  tone?: IconTone;
}) {
  return <NorthStarIcon name={name} size={size} tone={tone} />;
}

export function Button({
  children,
  icon,
  tone = "secondary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  icon?: IconReference;
  tone?: "primary" | "secondary" | "danger" | "quiet";
}) {
  return (
    <button className={`ns-button ${tone}`} type="button" {...props}>
      {icon ? <Icon name={icon} size={16} /> : null}
      <span>{children}</span>
    </button>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "blue" | "green" | "orange" | "red" | "purple" | "neutral";
}) {
  return <span className={`ns-badge ${tone}`}>{children}</span>;
}

export function Panel({
  children,
  className = "",
  title,
  icon,
  action,
}: {
  children: ReactNode;
  className?: string;
  title?: ReactNode;
  icon?: IconReference;
  action?: ReactNode;
}) {
  return (
    <section className={`ns-panel ${className}`.trim()}>
      {title ? (
        <header className="ns-panel-header">
          <div className="ns-panel-title">
            {icon ? <Icon name={icon} size={19} /> : null}
            <h2>{title}</h2>
          </div>
          {action ? <div className="ns-panel-action">{action}</div> : null}
        </header>
      ) : null}
      {children}
    </section>
  );
}

export function Toolbar({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children?: ReactNode;
}) {
  return (
    <header className="ns-route-toolbar">
      <div className="ns-route-heading">
        <h1>{title}</h1>
        {subtitle ? <p>{subtitle}</p> : null}
      </div>
      <div className="ns-route-actions">{children}</div>
    </header>
  );
}

export function SearchField({
  disabled,
  onChange,
  placeholder,
  value,
}: {
  disabled?: boolean;
  onChange?: (value: string) => void;
  placeholder: string;
  value?: string;
}) {
  const unavailable = disabled ?? !onChange;
  return (
    <label className={`ns-search ${unavailable ? "disabled" : ""}`} title={unavailable ? "Search is unavailable until this surface has a searchable data contract" : undefined}>
      <span className="sr-only">{placeholder}</span>
      <Icon name="search" size={16} />
      <input aria-label={placeholder} disabled={unavailable} onChange={onChange ? (event) => onChange(event.target.value) : undefined} placeholder={placeholder} type="search" value={onChange ? value ?? "" : undefined} />
    </label>
  );
}

export function Tabs({
  active,
  items,
  onChange,
}: {
  active: string;
  items: string[];
  onChange?: (value: string) => void;
}) {
  return (
    <div className="ns-tabs" role="tablist">
      {items.map((item) => (
        <button
          aria-selected={active === item}
          className={active === item ? "active" : ""}
          disabled={!onChange}
          key={item}
          onClick={() => onChange?.(item)}
          role="tab"
          title={!onChange ? "Only the current view is implemented on this surface" : undefined}
          type="button"
        >
          {item}
        </button>
      ))}
    </div>
  );
}

export function StatusDot({ tone = "green" }: { tone?: "green" | "orange" | "red" | "gray" | "blue" }) {
  return <span className={`ns-status-dot ${tone}`} aria-hidden="true" />;
}

export function Avatar({ initials, tone = "blue" }: { initials: string; tone?: "blue" | "purple" | "green" | "orange" | "teal" | "gray" }) {
  return <span className={`ns-avatar ${tone}`}>{initials}</span>;
}

export function MetaRow({
  icon,
  label,
  value,
  tone,
}: {
  icon: IconReference;
  label: string;
  value: ReactNode;
  tone?: "green" | "orange" | "red" | "blue";
}) {
  return (
    <div className="ns-meta-row">
      <Icon name={icon} size={15} />
      <span>{label}</span>
      <strong className={tone ? `tone-${tone}` : ""} title={typeof value === "string" ? value : undefined}>{value}</strong>
    </div>
  );
}
