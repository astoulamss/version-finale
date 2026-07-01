import type { AiReply, DocumentDraft, EmployeeProfile, HrNotification, OnboardingTask, OnboardingWeek, RecentDocument } from "../types";

export function calculateOnboardingProgress(weeks: OnboardingWeek[]) {
  const tasks = weeks.flatMap((week) => week.tasks);
  if (tasks.length === 0) {
    return 0;
  }

  const completed = tasks.filter((task) => task.status === "done").length;
  return Math.round((completed / tasks.length) * 100);
}

export function getLateOnboardingTasks(weeks: OnboardingWeek[]) {
  return weeks.flatMap((week) => week.tasks).filter((task) => task.status === "late");
}

export function getNextOnboardingTask(weeks: OnboardingWeek[]): OnboardingTask | undefined {
  return weeks
    .flatMap((week) => week.tasks)
    .find((task) => task.status === "late" || task.status === "active" || task.status === "todo");
}

export function getUnreadNotifications(notifications: HrNotification[]) {
  return notifications.filter((notification) => notification.unread).length;
}

export function getDocumentStatusLabel(status: RecentDocument["status"]) {
  const labels = {
    pending: "En attente",
    approved: "Valide",
    rejected: "Refuse",
    correction: "Correction demandee",
    downloadable: "Téléchargeable",
  };
  return labels[status];
}

export function generateDocumentDraft(template: string, profile: EmployeeProfile): DocumentDraft {
  const baseFields = [
    { label: "Nom", value: profile.lastName, editable: false },
    { label: "Prénom", value: profile.firstName, editable: false },
    { label: "Matricule", value: profile.employeeId, editable: false },
    { label: "Poste", value: profile.role, editable: false },
    { label: "Département", value: profile.department, editable: false },
    { label: "Date d'entrée", value: profile.startDate, editable: false },
    { label: "Ancienneté", value: profile.tenure, editable: false },
  ];

  const requestFields = template.toLowerCase().includes("conge")
    ? [
        { label: "Type de congé", value: "Congé payé", editable: true },
        { label: "Date de début", value: "", editable: true },
        { label: "Date de fin", value: "", editable: true },
      ]
    : template.toLowerCase().includes("teletravail")
      ? [
          { label: "Jour demandé", value: "", editable: true },
          { label: "Motif", value: "Travail concentré", editable: true },
        ]
      : [];

  return {
    template,
    fields: [...baseFields, ...requestFields],
    warnings: validateDraftFields([...baseFields, ...requestFields]),
  };
}

export function validateDocumentDraft(draft: DocumentDraft) {
  return validateDraftFields(draft.fields);
}

function validateDraftFields(fields: DocumentDraft["fields"]) {
  const missing = fields.filter((field) => field.editable && field.value.trim().length === 0);
  if (missing.length === 0) {
    return [];
  }

  return missing.map((field) => `Champ manquant : ${field.label}`);
}

export function generateAssistantReply(prompt: string, profile: EmployeeProfile): AiReply {
  const normalized = prompt.toLowerCase();

  if (normalized.includes("salaire") && (normalized.includes("collegue") || normalized.includes("collaborateur"))) {
    return {
      kind: "permission-denied",
      title: "Donnée confidentielle protégée",
      text: "Je ne peux pas communiquer le salaire ou le dossier RH d'un autre collaborateur. Ces informations sont protégées par la politique de confidentialité RH.",
      source: "Politique confidentialité RH 2026",
      actions: ["Voir mes permissions IA", "Contacter RH"],
    };
  }

  if (
    normalized.includes("harcelement") ||
    normalized.includes("conflit") ||
    normalized.includes("plainte") ||
    normalized.includes("demission") ||
    normalized.includes("erreur paie")
  ) {
    return {
      kind: "escalation",
      title: "Situation sensible détectée",
      text: "Cette demande peut nécessiter un accompagnement humain. Je peux préparer un ticket RH confidentiel ou planifier un entretien avec un People Partner.",
      source: "Procédure d'escalade RH",
      actions: ["Contacter RH", "Creer ticket RH", "Planifier entretien"],
    };
  }

  if (normalized.includes("conge") && !normalized.includes("reste") && !normalized.includes("solde")) {
    return {
      kind: "clarification",
      title: "Clarification nécessaire",
      text: "Quel type de congé souhaitez-vous poser ?",
      source: "Politique congés 2026",
      actions: ["Continuer"],
      options: ["Congé payé", "Congé maladie", "Congé exceptionnel"],
    };
  }

  if (normalized.includes("reste") || normalized.includes("solde") || normalized.includes("mes conges")) {
    return {
      kind: "answer",
      title: "Solde congés",
      text: `${profile.firstName}, il vous reste 12 jours de congés disponibles. Vous pouvez les poser depuis la section correspondante.`,
      source: "Base RH autorisée",
      actions: ["Poser un congé"],
    };
  }

  return {
    kind: "answer",
    title: "Information RH",
    text: "Je peux vous aider avec vos congés, attestations, paie et onboarding.",
    source: "Assistant IA",
    actions: ["Voir mes documents"],
  };
}