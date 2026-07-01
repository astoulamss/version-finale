import { describe, expect, it } from "vitest";
const employeeProfile: any = { role: "collaborateur" };
const onboardingWeeks: any = [
  {
    id: "w1",
    title: "Semaine 1",
    theme: "Intégration",
    progress: 50,
    tasks: [
      { id: "t1", title: "Task 1", status: "done" },
      { id: "t2", title: "Task 2", status: "todo" }
    ]
  }
];
const notifications: any = [];
import {
  calculateOnboardingProgress,
  generateAssistantReply,
  generateDocumentDraft,
  getDocumentStatusLabel,
  getLateOnboardingTasks,
  getUnreadNotifications,
  validateDocumentDraft,
} from "./aiEngine";

describe("aiEngine", () => {
  it("computes collaborator onboarding progress", () => {
    const progress = calculateOnboardingProgress(onboardingWeeks);
    expect(progress).toBeGreaterThan(0);
    expect(progress).toBeLessThanOrEqual(100);
  });

  it("blocks confidential questions about another employee", () => {
    const reply = generateAssistantReply("Quel est le salaire de mon collegue ?", employeeProfile);
    expect(reply.kind).toBe("permission-denied");
    expect(reply.source).toContain("confidentialit");
  });

  it("detects sensitive HR escalation cases", () => {
    const reply = generateAssistantReply("Je veux signaler un harcelement", employeeProfile);
    expect(reply.kind).toBe("escalation");
  });
});