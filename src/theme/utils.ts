import { StatusTone } from "../types";
import { Theme } from "./colors";

export function toneColor(tone: StatusTone, theme: Theme) {
  const colors = {
    success: theme.emerald,
    warning: theme.amber,
    critical: theme.rose,
    info: theme.sky,
    neutral: theme.muted,
    blocked: theme.blocked,
  };
  return colors[tone];
}

export function toneBackground(tone: StatusTone, theme: Theme) {
  const colors = {
    success: theme.emeraldSoft,
    warning: theme.amberSoft,
    critical: theme.roseSoft,
    info: theme.skySoft,
    neutral: theme.surfaceAlt,
    blocked: theme.blockedSoft,
  };
  return colors[tone];
}

export function statusToneFromDocument(status: string): StatusTone {
  if (status === "approved" || status === "signed" || status === "valid" || status === "downloadable") return "success";
  if (status === "pending" || status === "waiting") return "warning";
  if (status === "correction" || status === "rejected") return "critical";
  return "info";
}

export function getDocumentStatusLabel(status: string): string {
  const map: Record<string, string> = {
    approved: "Valide", signed: "Signé", valid: "Valide", downloadable: "Disponible",
    pending: "En attente", waiting: "En attente",
    correction: "À corriger", rejected: "Rejeté"
  };
  return map[status] || status;
}
