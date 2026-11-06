import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
};
const variants = {
  primary: "button primary",
  secondary: "button secondary",
  ghost: "",
};

/** Preserves native submit behavior; use type="button" for auxiliary form actions. */
export function Button({ className = "", type = "submit", variant = "ghost", ...props }: ButtonProps) {
  return <button type={type} className={`ui-button inline-flex items-center justify-center gap-2 transition-colors disabled:pointer-events-none ${variants[variant]} ${className}`} {...props} />;
}

export function Card({ className = "", ...props }: HTMLAttributes<HTMLElement>) {
  return <section className={`panel ui-card min-w-0 rounded-2xl border border-slate-200 bg-white shadow-sm ${className}`} {...props} />;
}

export function PanelHeader({ eyebrow, title, action }: { eyebrow?: string; title: string; action?: ReactNode }) {
  return <div className="panel-heading flex flex-wrap items-center justify-between gap-3">
    <div className="min-w-0">{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>
    {action}
  </div>;
}

export function Alert({ children, className = "", ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div role="alert" className={`error-box rounded-xl border border-red-200 bg-red-50 p-4 text-sm leading-relaxed text-red-800 ${className}`} {...props}>{children}</div>;
}

export function StatCard({ label, value, note, icon }: { label: string; value: ReactNode; note: string; icon: ReactNode }) {
  return <Card className="stat"><div className="stat-icon">{icon}</div><span>{label}</span><strong>{value}</strong><small>{note}</small></Card>;
}
