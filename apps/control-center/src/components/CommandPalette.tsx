import { useEffect, useMemo, useRef, useState } from "react";
import { commandPaletteItems } from "../routes";

interface CommandPaletteProps {
  activePath: string;
}

export function CommandPalette({ activePath }: CommandPaletteProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setOpen(true);
      }
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (open) {
      window.setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setQuery("");
    }
  }, [open]);

  const visibleItems = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return commandPaletteItems.slice(0, 12);
    }
    return commandPaletteItems
      .filter((item) =>
        [item.label, item.group, item.status, ...item.keywords]
          .join(" ")
          .toLowerCase()
          .includes(normalized),
      )
      .slice(0, 12);
  }, [query]);

  return (
    <>
      <button
        aria-label="Find route or action"
        className="palette-trigger"
        onClick={() => setOpen(true)}
        type="button"
      >
        Find
        <span>Cmd K</span>
      </button>
      {open ? (
        <div className="palette-backdrop" role="presentation">
          <div
            aria-label="Command palette"
            aria-modal="true"
            className="command-palette"
            role="dialog"
          >
            <div className="palette-search-row">
              <input
                aria-label="Search routes and actions"
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search routes and safe actions"
                ref={inputRef}
                type="search"
                value={query}
              />
              <button onClick={() => setOpen(false)} type="button">
                Close
              </button>
            </div>
            <div className="palette-results" role="listbox">
              {visibleItems.map((item) => (
                <div
                  aria-selected={item.path === activePath}
                  className={`palette-result${item.path === activePath ? " active" : ""}`}
                  key={item.id}
                  role="option"
                >
                  <div>
                    <strong>{item.label}</strong>
                    <span>
                      {item.group} - {item.status}
                    </span>
                    {item.disabledReason ? (
                      <small>{item.disabledReason}</small>
                    ) : null}
                  </div>
                  {item.path ? (
                    <a href={item.path} onClick={() => setOpen(false)}>
                      View
                    </a>
                  ) : (
                    <span className="command-disabled">Unavailable</span>
                  )}
                </div>
              ))}
              {visibleItems.length === 0 ? (
                <div className="palette-empty">No safe route matched.</div>
              ) : null}
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
