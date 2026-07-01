import type { EmployeeProfile } from "../types";

export type UserRoleId = "collaborateur" | "manager" | "rh" | "admin" | "medecine_travail" | "direction";

export function getRoleLabel(roleId: UserRoleId): string {
  switch (roleId) {
    case "admin": return "Administrateur Système";
    case "medecine_travail": return "Médecine du Travail / QVT";
    case "manager": return "Manager / Directeur";
    case "rh": return "Responsable RH";
    case "direction": return "Direction";
    case "collaborateur":
    default: return "Collaborateur";
  }
}

export function getRoleWorkspace(roleId: UserRoleId): string {
  switch (roleId) {
    case "admin": return "Espace Administration";
    case "medecine_travail": return "Espace QVT & Santé";
    case "manager": return "Espace Manager";
    case "rh": return "Espace RH";
    case "direction": return "Espace Direction";
    case "collaborateur":
    default: return "Mon Espace";
  }
}

export const isAdminRole = (role: string) => role === "admin";
export const isQvtRole = (role: string) => role === "medecine_travail";
export const isManagerRole = (role: string) => role === "manager" || role === "direction";
export const isRhRole = (role: string) => role === "rh";
export const canAccessRhWorkspace = (role: string) => isManagerRole(role) || isRhRole(role) || isAdminRole(role);

export function mapApiUserToProfile(apiUser: any, employeeData?: any): EmployeeProfile {
  const hireDateObj = employeeData?.hire_date ? new Date(employeeData.hire_date) : null;
  const createdDateObj = apiUser.created_at ? new Date(apiUser.created_at) : new Date();
  
  // Calculate tenure (seniority)
  let tenureStr = "Nouveau";
  if (hireDateObj) {
    const years = new Date().getFullYear() - hireDateObj.getFullYear();
    const months = new Date().getMonth() - hireDateObj.getMonth();
    const totalMonths = years * 12 + months;
    if (totalMonths > 12) {
      tenureStr = `${Math.floor(totalMonths / 12)} an(s)`;
    } else if (totalMonths > 0) {
      tenureStr = `${totalMonths} mois`;
    }
  }

  const managerObj = employeeData?.manager;
  let managerName = "Non défini";
  if (managerObj) {
    managerName = `${managerObj.prenom} ${managerObj.nom}`;
  } else if (employeeData?.department?.manager_prenom) {
    managerName = `${employeeData.department.manager_prenom} ${employeeData.department.manager_nom}`;
  }

  const statusMap: Record<string, string> = {
    "active": "Actif",
    "inactive": "Inactif",
    "suspended": "Suspendu",
    "on_leave": "En congé",
  };

  return {
    employeeId: employeeData?.id?.toString() || apiUser.id.toString(),
    firstName: apiUser.prenom,
    lastName: apiUser.nom,
    role: getRoleLabel(apiUser.role?.toLowerCase()?.trim() || "collaborateur"),
    roleId: apiUser.role?.toLowerCase()?.trim() || "collaborateur",
    department: employeeData?.department?.name || "Non défini",
    manager: managerName,
    startDate: (hireDateObj || createdDateObj).toLocaleDateString("fr-FR"),
    tenure: tenureStr,
    office: employeeData?.adresse || "Non renseigné",
    email: apiUser.email || "",
    avatarInitials: `${apiUser.prenom?.[0]?.toUpperCase() || 'X'}${apiUser.nom?.[0]?.toUpperCase() || 'X'}`,
    photoUrl: apiUser.photo_url || `https://i.pravatar.cc/150?u=${apiUser.id}`,
    phone: employeeData?.numero_telephone || "Non renseigné",
    location: employeeData?.adresse || "Non renseigné",
    hireDate: hireDateObj ? hireDateObj.toLocaleDateString("fr-FR") : "Non définie",
    contractType: employeeData?.contract_type || "Non défini",
    status: employeeData?.status ? (statusMap[employeeData.status.toLowerCase()] || employeeData.status) : "Actif",
    position: employeeData?.position?.title || "Non défini",
  };
}

export const roleOptions = [
  { id: "collaborateur", label: "Collaborateurs", workspace: "Collaborateur", description: "Espace personnel RH et IA" },
  { id: "rh", label: "Équipes RH", workspace: "Équipes RH", description: "Suivi RH, dossiers et validations" },
  { id: "manager", label: "Managers", workspace: "Managers", description: "Pilotage d’équipe et actions de formation" },
  { id: "admin", label: "Administrateurs", workspace: "Administrateurs", description: "Gestion des accès, paramètres et conformité" },
  { id: "medecine_travail", label: "Médecine / QVT", workspace: "Médecine / QVT", description: "Suivi santé, prévention et accompagnement" },
  { id: "direction", label: "Direction", workspace: "Direction", description: "Pilotage stratégique et KPI globaux" },
] as const;
