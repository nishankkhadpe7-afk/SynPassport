"use client";

import React, { useEffect, useId, useRef, useState } from "react";

/* Shared presentation primitives. Every screen builds from these so buttons,
   cards, fields and states look and behave the same everywhere. */

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/* ---------- Buttons ---------- */

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";

const buttonBase =
  "inline-flex items-center justify-center gap-2 rounded px-4 h-10 text-base font-medium transition-colors duration-200 ease-out disabled:cursor-not-allowed disabled:opacity-50 whitespace-nowrap";

const buttonVariants: Record<ButtonVariant, string> = {
  primary: "bg-accent text-on-accent hover:bg-accent-hover disabled:hover:bg-accent",
  secondary:
    "bg-surface text-ink border border-line-strong hover:bg-surface-2 disabled:hover:bg-surface",
  ghost: "text-ink-2 hover:text-ink hover:bg-surface-2",
  danger: "bg-surface text-fail border border-line-strong hover:bg-fail-soft hover:border-fail",
};

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  loading?: boolean;
  size?: "md" | "sm";
}

export const Button: React.FC<ButtonProps> = ({
  variant = "secondary",
  loading = false,
  size = "md",
  className,
  children,
  disabled,
  ...rest
}) => (
  <button
    {...rest}
    disabled={disabled || loading}
    aria-busy={loading || undefined}
    className={cx(buttonBase, buttonVariants[variant], size === "sm" && "h-8 px-3 text-sm", className)}
  >
    {loading && <Spinner />}
    {children}
  </button>
);

export const Spinner: React.FC = () => (
  <span
    aria-hidden="true"
    className="inline-block w-4 h-4 rounded-full border-2 border-current border-r-transparent animate-spin"
  />
);

/* ---------- Layout ---------- */

interface PageHeaderProps {
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  meta?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({ title, description, actions, meta }) => (
  <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between pb-6 border-b border-line">
    <div className="space-y-2 max-w-prose">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-xl font-semibold tracking-tight text-ink">{title}</h1>
        {meta}
      </div>
      {description && <p className="text-base text-ink-2">{description}</p>}
    </div>
    {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
  </header>
);

interface CardProps {
  title?: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
  as?: "section" | "div" | "aside";
  flush?: boolean;
}

export const Card: React.FC<CardProps> = ({
  title,
  description,
  actions,
  children,
  className,
  as: Tag = "section",
  flush = false,
}) => (
  <Tag className={cx("bg-surface border border-line rounded-lg shadow", flush ? "overflow-hidden" : "p-6", className)}>
    {(title || actions) && (
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div className="space-y-1">
          {title && <h2 className="text-base font-semibold text-ink">{title}</h2>}
          {description && <p className="text-sm text-ink-2">{description}</p>}
        </div>
        {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
      </div>
    )}
    {children}
  </Tag>
);

/* ---------- Form fields ---------- */

export const inputClass =
  "w-full h-10 rounded border border-line-strong bg-surface px-3 text-base text-ink placeholder:text-ink-3 transition-[border-color,box-shadow] duration-200 ease-out hover:border-ink-3 focus:border-accent focus:outline-none focus-visible:outline-none focus:shadow-[0_0_0_3px_var(--accent-soft)]";

interface FieldProps {
  id: string;
  label: string;
  hint?: string;
  children: React.ReactNode;
}

export const Field: React.FC<FieldProps> = ({ id, label, hint, children }) => (
  <div className="space-y-2">
    <label htmlFor={id} className="block text-sm font-medium text-ink">
      {label}
    </label>
    {children}
    {hint && (
      <p id={`${id}-hint`} className="text-sm text-ink-3">
        {hint}
      </p>
    )}
  </div>
);

/* ---------- Data display ---------- */

export const Stat: React.FC<{ label: string; value: React.ReactNode; note?: React.ReactNode; tone?: string }> = ({
  label,
  value,
  note,
  tone,
}) => (
  <div className="space-y-1">
    <div className="text-sm text-ink-2">{label}</div>
    <div className={cx("text-lg font-semibold tabular-nums", tone || "text-ink")}>{value}</div>
    {note && <div className="text-sm text-ink-3">{note}</div>}
  </div>
);

export const Mono: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <code className={cx("font-mono text-sm text-ink break-all", className)}>{children}</code>
);

export const Meter: React.FC<{ value: number; max: number; tone?: "accent" | "warn" | "fail" | "pass"; label: string }> = ({
  value,
  max,
  tone = "accent",
  label,
}) => {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  const fill = { accent: "bg-accent", warn: "bg-warn", fail: "bg-fail", pass: "bg-pass" }[tone];
  return (
    <div
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      className="h-2 w-full rounded-full bg-surface-2 overflow-hidden"
    >
      <div className={cx("h-full rounded-full transition-[width] duration-500 ease-out", fill)} style={{ width: `${pct}%` }} />
    </div>
  );
};

/* ---------- States ---------- */

export const Skeleton: React.FC<{ className?: string }> = ({ className }) => (
  <div aria-hidden="true" className={cx("skeleton h-4", className)} />
);

export const SkeletonBlock: React.FC<{ lines?: number; label: string }> = ({ lines = 3, label }) => (
  <div role="status" aria-live="polite" className="space-y-3">
    <span className="sr-only">{label}</span>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton key={i} className={i === lines - 1 ? "w-2/3" : "w-full"} />
    ))}
  </div>
);

interface EmptyStateProps {
  title: string;
  description?: React.ReactNode;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, action }) => (
  <div className="py-12 px-6 text-center space-y-2 rounded-lg border border-dashed border-line-strong">
    <p className="text-base font-medium text-ink">{title}</p>
    {description && <p className="text-sm text-ink-2 max-w-prose mx-auto">{description}</p>}
    {action && <div className="pt-2">{action}</div>}
  </div>
);

type NoticeTone = "pass" | "fail" | "warn" | "neutral";

const noticeTones: Record<NoticeTone, string> = {
  pass: "bg-pass-soft border-transparent",
  fail: "bg-fail-soft border-transparent",
  warn: "bg-warn-soft border-transparent",
  neutral: "bg-surface-2 border-line",
};

const noticeTitleTones: Record<NoticeTone, string> = {
  pass: "text-pass",
  fail: "text-fail",
  warn: "text-warn",
  neutral: "text-ink",
};

interface NoticeProps {
  tone?: NoticeTone;
  title: React.ReactNode;
  children?: React.ReactNode;
  onDismiss?: () => void;
  role?: "alert" | "status";
}

export const Notice: React.FC<NoticeProps> = ({ tone = "neutral", title, children, onDismiss, role = "status" }) => (
  <div role={role} className={cx("rounded border p-4 flex items-start justify-between gap-4", noticeTones[tone])}>
    <div className="space-y-1 min-w-0">
      <p className={cx("text-base font-semibold", noticeTitleTones[tone])}>{title}</p>
      {children && <div className="text-sm text-ink-2 break-words">{children}</div>}
    </div>
    {onDismiss && (
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss"
        className="shrink-0 h-8 w-8 rounded text-ink-2 hover:text-ink hover:bg-surface transition-colors"
      >
        ×
      </button>
    )}
  </div>
);

/* ---------- Select (custom listbox, themed in light and dark) ---------- */

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

interface SelectProps {
  id: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
  "aria-describedby"?: string;
}

/* The native <select> list is drawn by the operating system and ignores the theme,
   so this renders an accessible listbox instead: Arrow keys, Home/End, Enter/Space,
   Escape and type-to-select all work, and the label stays linked via id. */
export const Select: React.FC<SelectProps> = ({ id, value, options, onChange, ...aria }) => {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(() => Math.max(0, options.findIndex((o) => o.value === value)));
  const wrapRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const listRef = useRef<HTMLUListElement>(null);
  const listId = useId();
  const typed = useRef<{ text: string; at: number }>({ text: "", at: 0 });

  const selected = options.find((o) => o.value === value) || options[0];

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, [open]);

  // Highlight the current value only at the moment the list opens
  const openList = () => {
    setActive(Math.max(0, options.findIndex((o) => o.value === value)));
    setOpen(true);
  };

  useEffect(() => {
    if (open) listRef.current?.focus({ preventScroll: true });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    // Scroll inside the list only; scrolling the page would move options under a resting
    // pointer and change the highlight without the user doing anything.
    const list = listRef.current;
    const el = list?.querySelector<HTMLElement>(`[data-index="${active}"]`);
    if (list && el) {
      if (el.offsetTop < list.scrollTop) list.scrollTop = el.offsetTop;
      else if (el.offsetTop + el.offsetHeight > list.scrollTop + list.clientHeight)
        list.scrollTop = el.offsetTop + el.offsetHeight - list.clientHeight;
    }
  }, [active, open]);

  const choose = (index: number) => {
    const opt = options[index];
    if (opt) onChange(opt.value);
    setOpen(false);
    buttonRef.current?.focus();
  };

  const typeAhead = (key: string) => {
    const now = Date.now();
    typed.current.text = now - typed.current.at > 600 ? key : typed.current.text + key;
    typed.current.at = now;
    const match = options.findIndex((o) => o.label.toLowerCase().startsWith(typed.current.text.toLowerCase()));
    if (match >= 0) setActive(match);
  };

  const onButtonKey = (e: React.KeyboardEvent) => {
    if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
      e.preventDefault();
      openList();
    }
  };

  const onListKey = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActive((i) => Math.min(options.length - 1, i + 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActive((i) => Math.max(0, i - 1));
        break;
      case "Home":
        e.preventDefault();
        setActive(0);
        break;
      case "End":
        e.preventDefault();
        setActive(options.length - 1);
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        choose(active);
        break;
      case "Escape":
        e.preventDefault();
        setOpen(false);
        buttonRef.current?.focus();
        break;
      case "Tab":
        setOpen(false);
        break;
      default:
        if (e.key.length === 1) typeAhead(e.key);
    }
  };

  return (
    <div ref={wrapRef} className="relative">
      <button
        ref={buttonRef}
        id={id}
        type="button"
        role="combobox"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-describedby={aria["aria-describedby"]}
        onClick={() => (open ? setOpen(false) : openList())}
        onKeyDown={onButtonKey}
        className={cx(inputClass, "flex items-center justify-between gap-2 text-left", open && "border-accent shadow-[0_0_0_3px_var(--accent-soft)]")}
      >
        <span className="truncate">{selected?.label}</span>
        <svg
          aria-hidden="true"
          viewBox="0 0 16 16"
          className={cx("w-4 h-4 shrink-0 text-ink-2 transition-transform duration-200 ease-out", open && "rotate-180")}
        >
          <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>

      {open && (
        <ul
          ref={listRef}
          id={listId}
          role="listbox"
          tabIndex={-1}
          aria-labelledby={id}
          aria-activedescendant={`${listId}-${active}`}
          onKeyDown={onListKey}
          className="absolute z-30 mt-1 w-full max-h-64 overflow-auto rounded border border-line bg-surface p-1 shadow-overlay focus:outline-none"
        >
          {options.map((opt, i) => {
            const isSelected = opt.value === value;
            const isActive = i === active;
            return (
              <li
                key={opt.value}
                id={`${listId}-${i}`}
                data-index={i}
                role="option"
                aria-selected={isSelected}
                onMouseMove={() => active !== i && setActive(i)}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => choose(i)}
                className={cx(
                  "flex items-center justify-between gap-3 rounded-sm px-3 py-2 cursor-pointer text-base",
                  isActive ? "bg-surface-2 text-ink" : "text-ink",
                  isSelected && "font-medium"
                )}
              >
                <span className="min-w-0">
                  <span className="block truncate">{opt.label}</span>
                  {opt.description && <span className="block text-sm text-ink-2 font-normal">{opt.description}</span>}
                </span>
                {isSelected && (
                  <svg aria-hidden="true" viewBox="0 0 16 16" className="w-4 h-4 shrink-0 text-accent">
                    <path d="M3.5 8.5l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
};
