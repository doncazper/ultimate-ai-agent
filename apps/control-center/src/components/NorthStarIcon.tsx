type NorthStarIconProps = {
  className?: string;
  name: string;
};

export function NorthStarIcon({ className, name }: NorthStarIconProps) {
  return (
    <svg
      aria-hidden="true"
      className={className ? `north-star-icon ${className}` : "north-star-icon"}
      fill="none"
      viewBox="0 0 24 24"
    >
      {iconForName(name)}
    </svg>
  );
}

function iconForName(name: string) {
  switch (normalizeIconName(name)) {
    case "activity":
      return <path d="M3 12h4l2-6 4 12 2-6h6" />;
    case "archive":
      return (
        <>
          <path d="M4 7h16" />
          <path d="M6 7v12h12V7" />
          <path d="M4.5 4h15l.5 3H4z" />
          <path d="M10 11h4" />
        </>
      );
    case "arrow-right":
      return (
        <>
          <path d="M5 12h14" />
          <path d="m13 6 6 6-6 6" />
        </>
      );
    case "brain":
      return (
        <>
          <path d="M9 5a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3.5 3.5 0 0 0 4 5" />
          <path d="M15 5a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3.5 3.5 0 0 1-4 5" />
          <path d="M9 5v14" />
          <path d="M15 5v14" />
          <path d="M9 9h3m0 4h3" />
        </>
      );
    case "briefcase":
      return (
        <>
          <path d="M9 7V5h6v2" />
          <rect height="12" rx="2" width="18" x="3" y="7" />
          <path d="M3 13h18" />
        </>
      );
    case "calendar":
      return (
        <>
          <rect height="16" rx="2" width="16" x="4" y="5" />
          <path d="M8 3v4m8-4v4M4 10h16" />
        </>
      );
    case "chat":
      return (
        <>
          <path d="M5 6h14v9H9l-4 4z" />
          <path d="M8 10h8M8 13h5" />
        </>
      );
    case "check":
    case "check-circle":
      return (
        <>
          <circle cx="12" cy="12" r="8" />
          <path d="m8.5 12.5 2.2 2.2 4.8-5.2" />
        </>
      );
    case "chevron-left":
      return <path d="m14 6-6 6 6 6" />;
    case "chevron-right":
      return <path d="m10 6 6 6-6 6" />;
    case "clock":
      return (
        <>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 8v5l3 2" />
        </>
      );
    case "clipboard":
      return (
        <>
          <path d="M9 5h6l1 2h2v14H6V7h2z" />
          <path d="M9 11h6M9 15h6" />
        </>
      );
    case "copy":
      return (
        <>
          <rect height="11" rx="2" width="11" x="8" y="5" />
          <path d="M5 8v11h11" />
        </>
      );
    case "cube":
      return (
        <>
          <path d="m12 3 8 4.5v9L12 21l-8-4.5v-9z" />
          <path d="M4 7.5 12 12l8-4.5M12 12v9" />
        </>
      );
    case "database":
      return (
        <>
          <ellipse cx="12" cy="6" rx="7" ry="3" />
          <path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6" />
          <path d="M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6" />
        </>
      );
    case "edit":
    case "pencil":
      return (
        <>
          <path d="M5 19h4l10-10-4-4L5 15z" />
          <path d="m13 7 4 4" />
        </>
      );
    case "eye":
      return (
        <>
          <path d="M3 12s3.5-6 9-6 9 6 9 6-3.5 6-9 6-9-6-9-6z" />
          <circle cx="12" cy="12" r="2.5" />
        </>
      );
    case "file":
    case "file-text":
      return (
        <>
          <path d="M7 3h7l4 4v14H7z" />
          <path d="M14 3v5h5" />
          <path d="M9 12h6M9 16h6" />
        </>
      );
    case "flag":
      return (
        <>
          <path d="M6 21V4" />
          <path d="M6 5h10l-1.5 4L16 13H6" />
        </>
      );
    case "gear":
    case "settings":
      return (
        <>
          <circle cx="12" cy="12" r="3" />
          <path d="M12 3v3m0 12v3M3 12h3m12 0h3M5.6 5.6l2.1 2.1m8.6 8.6 2.1 2.1M18.4 5.6l-2.1 2.1m-8.6 8.6-2.1 2.1" />
        </>
      );
    case "globe":
      return (
        <>
          <circle cx="12" cy="12" r="8" />
          <path d="M4 12h16M12 4a12 12 0 0 1 0 16M12 4a12 12 0 0 0 0 16" />
        </>
      );
    case "heart":
      return <path d="M20 8.5c0 5-8 10-8 10s-8-5-8-10A4.5 4.5 0 0 1 12 6a4.5 4.5 0 0 1 8 2.5z" />;
    case "inbox":
      return (
        <>
          <path d="M4 13 7 5h10l3 8v6H4z" />
          <path d="M4 13h5l1.5 3h3L15 13h5" />
        </>
      );
    case "info":
      return (
        <>
          <circle cx="12" cy="12" r="8" />
          <path d="M12 11v5M12 8h.01" />
        </>
      );
    case "link":
      return (
        <>
          <path d="M10 7h-2a5 5 0 0 0 0 10h2" />
          <path d="M14 7h2a5 5 0 0 1 0 10h-2" />
          <path d="M9 12h6" />
        </>
      );
    case "list":
    case "list-check":
      return (
        <>
          <path d="M9 6h11M9 12h11M9 18h11" />
          <path d="m4 6 .8.8L6.5 5M4 12h2.5M4 18h2.5" />
        </>
      );
    case "lock":
      return (
        <>
          <rect height="10" rx="2" width="14" x="5" y="10" />
          <path d="M8 10V7a4 4 0 0 1 8 0v3" />
        </>
      );
    case "map":
      return (
        <>
          <path d="m4 6 5-2 6 2 5-2v14l-5 2-6-2-5 2z" />
          <path d="M9 4v14M15 6v14" />
        </>
      );
    case "play":
      return <path d="M8 5v14l11-7z" />;
    case "plug":
      return (
        <>
          <path d="M9 7V3M15 7V3M7 7h10v5a5 5 0 0 1-10 0z" />
          <path d="M12 17v4" />
        </>
      );
    case "route":
      return (
        <>
          <circle cx="6" cy="6" r="2" />
          <circle cx="18" cy="18" r="2" />
          <path d="M8 6h4a4 4 0 0 1 0 8H9a3 3 0 0 0 0 6h7" />
        </>
      );
    case "shield":
    case "shield-check":
      return (
        <>
          <path d="M12 3 19 6v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" />
          <path d="m8.5 12 2.2 2.2 4.8-5" />
        </>
      );
    case "sliders":
      return (
        <>
          <path d="M4 6h10M18 6h2M4 12h2M10 12h10M4 18h8M16 18h4" />
          <circle cx="16" cy="6" r="2" />
          <circle cx="8" cy="12" r="2" />
          <circle cx="14" cy="18" r="2" />
        </>
      );
    case "spark":
      return (
        <>
          <path d="M12 3 14 9l6 3-6 3-2 6-2-6-6-3 6-3z" />
          <path d="m5 4 1 2 2 1-2 1-1 2-1-2-2-1 2-1z" />
        </>
      );
    case "sun":
      return (
        <>
          <circle cx="12" cy="12" r="3.5" />
          <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9 7 7M17 17l2.1 2.1M19.1 4.9 17 7M7 17l-2.1 2.1" />
        </>
      );
    case "target":
      return (
        <>
          <circle cx="12" cy="12" r="8" />
          <circle cx="12" cy="12" r="4" />
          <path d="M12 12h8" />
        </>
      );
    case "terminal":
      return (
        <>
          <path d="m5 7 5 5-5 5" />
          <path d="M12 17h7" />
        </>
      );
    case "trash":
      return (
        <>
          <path d="M5 7h14M9 7V5h6v2M8 7l1 14h6l1-14" />
          <path d="M10 11v6M14 11v6" />
        </>
      );
    case "undo":
      return (
        <>
          <path d="M9 7 5 11l4 4" />
          <path d="M5 11h8a5 5 0 1 1 0 10h-2" />
        </>
      );
    case "upload":
      return (
        <>
          <path d="M12 17V5" />
          <path d="m7 10 5-5 5 5" />
          <path d="M5 19h14" />
        </>
      );
    case "user":
    case "user-circle":
      return (
        <>
          <circle cx="12" cy="8" r="3" />
          <path d="M5 20a7 7 0 0 1 14 0" />
        </>
      );
    case "warning":
      return (
        <>
          <path d="m12 4 9 16H3z" />
          <path d="M12 9v5M12 17h.01" />
        </>
      );
    case "x":
      return <path d="m6 6 12 12M18 6 6 18" />;
    default:
      return (
        <>
          <path d="M7 3h7l4 4v14H7z" />
          <path d="M14 3v5h5" />
        </>
      );
  }
}

function normalizeIconName(name: string): string {
  const normalized = name.toLowerCase().trim();
  const aliases: Record<string, string> = {
    act: "list-check",
    actions: "check-circle",
    approve: "check-circle",
    block: "shield",
    briefing: "map",
    db: "database",
    det: "info",
    effect: "activity",
    ev: "file",
    evidence: "file-text",
    export: "upload",
    memory: "brain",
    model: "cube",
    net: "globe",
    plan: "list",
    plans: "list",
    rec: "receipt",
    receipt: "clipboard",
    req: "list-check",
    review: "eye",
    run: "play",
    safe: "shield-check",
    source: "database",
    src: "database",
    state: "check-circle",
    term: "terminal",
    today: "sun",
    warn: "warning",
    write: "pencil",
    you: "user-circle",
  };
  return aliases[normalized] ?? normalized;
}
