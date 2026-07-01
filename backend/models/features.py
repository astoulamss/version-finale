from sqlalchemy import Column, Integer, String, DateTime, Date, Numeric, ForeignKey, Enum, Text, Boolean, func, UniqueConstraint
from sqlalchemy.orm import relationship
from database.db import Base
from datetime import datetime
import enum


class LeaveStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveTypeEnum(str, enum.Enum):
    VACATION = "vacation"
    SICK = "sick"
    MATERNITY = "maternity"
    PERSONAL = "personal"
    UNPAID = "unpaid"


class LeaveType(Base):
    __tablename__ = "leave_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    max_days = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)

    def __repr__(self):
        return f"<LeaveType(id={self.id}, name={self.name}, max_days={self.max_days})>"


class Leave(Base):
    __tablename__ = "leaves"
    __table_args__ = (
        UniqueConstraint('employee_id', 'start_date', 'end_date', name='uq_leave_employee_dates'),
    )

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LeaveStatusEnum), default=LeaveStatusEnum.PENDING, nullable=False)
    reason = Column(Text, nullable=True)
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_archived = Column(Boolean, default=False, nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])
    leave_type_relation = relationship("LeaveType", foreign_keys=[leave_type_id])

    @property
    def leave_type(self) -> str:
        name = self.leave_type_relation.name.lower() if self.leave_type_relation else ""
        if "maladie" in name:
            return "sick"
        elif "payé" in name:
            return "vacation"
        elif "matern" in name:
            return "maternity"
        elif "personnel" in name:
            return "personal"
        elif "solde" in name:
            return "unpaid"
        return "vacation"

    def __repr__(self):
        return f"<Leave(id={self.id}, employee_id={self.employee_id}, status={self.status})>"


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey("leave_types.id"), nullable=False)
    remaining_days = Column(Numeric(5, 1), default=25.0, nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])
    leave_type = relationship("LeaveType", foreign_keys=[leave_type_id])

    @property
    def leave_type_name(self) -> str:
        return self.leave_type.name if self.leave_type else ""

    def __repr__(self):
        return f"<LeaveBalance(id={self.id}, employee_id={self.employee_id}, type_id={self.leave_type_id}, remaining={self.remaining_days})>"


class OnboardingStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class OnboardingPlanTypeEnum(str, enum.Enum):
    SEVEN_DAYS = "7_days"
    THIRTY_DAYS = "30_days"
    NINETY_DAYS = "90_days"


class OnboardingPlan(Base):
    __tablename__ = "onboarding_plans"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(OnboardingStatusEnum, name='onboardingstatusenum'), default=OnboardingStatusEnum.PENDING, nullable=False)
    plan_type = Column(Enum(OnboardingPlanTypeEnum, name='onboardingplantypeenum'), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])

    def __repr__(self):
        return f"<OnboardingPlan(id={self.id}, employee_id={self.employee_id}, status={self.status})>"


class OnboardingTaskStatusEnum(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class OnboardingTask(Base):
    __tablename__ = "onboarding_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("onboarding_plans.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("onboarding_steps.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(Enum(OnboardingTaskStatusEnum, name='onboardingtaskstatusenum'), default=OnboardingTaskStatusEnum.TODO, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relations
    plan = relationship("OnboardingPlan", foreign_keys=[plan_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<OnboardingTask(id={self.id}, plan_id={self.plan_id}, title={self.title}, status={self.status})>"

class OnboardingStep(Base):
    __tablename__ = "onboarding_steps"

    id = Column(Integer, primary_key=True, index=True)
    onboarding_id = Column(Integer, ForeignKey("onboarding_plans.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    step_order = Column(Integer, nullable=False)

    # Relations
    onboarding_plan = relationship("OnboardingPlan", foreign_keys=[onboarding_id])

    def __repr__(self):
        return f"<OnboardingStep(id={self.id}, onboarding_id={self.onboarding_id}, title={self.title}, order={self.step_order})>"

class OnboardingFeedback(Base):
    __tablename__ = "onboarding_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    onboarding_id = Column(Integer, ForeignKey("onboarding_plans.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    onboarding_plan = relationship("OnboardingPlan", foreign_keys=[onboarding_id])
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<OnboardingFeedback(id={self.id}, onboarding_id={self.onboarding_id}, author_id={self.author_id})>"



class OffboardingStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OffboardingPlan(Base):
    __tablename__ = "offboarding_plans"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    departure_date = Column(Date, nullable=False)
    departure_reason = Column(Text, nullable=True)
    status = Column(Enum(OffboardingStatusEnum, name='offboardingstatusenum'), default=OffboardingStatusEnum.PENDING, nullable=False)
    equipment_returned = Column(Boolean, default=False, nullable=False)
    administrative_closed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])

    def __repr__(self):
        return f"<OffboardingPlan(id={self.id}, employee_id={self.employee_id}, status={self.status})>"


class OffboardingTaskStatusEnum(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class OffboardingTask(Base):
    __tablename__ = "offboarding_tasks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("offboarding_plans.id"), nullable=False)
    step_id = Column(Integer, ForeignKey("offboarding_steps.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(Enum(OffboardingTaskStatusEnum, name='offboardingtaskstatusenum'), default=OffboardingTaskStatusEnum.TODO, nullable=False)

    # Relations
    plan = relationship("OffboardingPlan", foreign_keys=[plan_id])
    assigned_user = relationship("User", foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<OffboardingTask(id={self.id}, plan_id={self.plan_id}, title={self.title}, status={self.status})>"

class OffboardingStep(Base):
    __tablename__ = "offboarding_steps"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("offboarding_plans.id"), nullable=False)
    title = Column(String(255), nullable=False)
    step_order = Column(Integer, nullable=False)

    # Relations
    offboarding_plan = relationship("OffboardingPlan", foreign_keys=[plan_id])

    def __repr__(self):
        return f"<OffboardingStep(id={self.id}, plan_id={self.plan_id}, title={self.title}, order={self.step_order})>"



class OffboardingFeedback(Base):
    __tablename__ = "offboarding_feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("offboarding_plans.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    offboarding_plan = relationship("OffboardingPlan", foreign_keys=[plan_id])
    author = relationship("User", foreign_keys=[author_id])

    def __repr__(self):
        return f"<OffboardingFeedback(id={self.id}, plan_id={self.plan_id}, author_id={self.author_id})>"



class Survey(Base):
    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Survey(id={self.id}, title={self.title})>"

class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    survey = relationship("Survey", foreign_keys=[survey_id])
    employee = relationship("User", foreign_keys=[employee_id])

    def __repr__(self):
        return f"<SurveyResponse(id={self.id}, survey_id={self.survey_id}, employee_id={self.employee_id})>"
class QuestionTypeEnum(str, enum.Enum):
    FREE_TEXT = "free_text"
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    RATING = "rating"
    YES_NO = "yes_no"

class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    id = Column(Integer, primary_key=True, index=True)
    survey_id = Column(Integer, ForeignKey("surveys.id"), nullable=False)
    question = Column(Text, nullable=False)
    question_type = Column(Enum(QuestionTypeEnum), nullable=False)

    # Relations
    survey = relationship("Survey", foreign_keys=[survey_id])

    def __repr__(self):
        return f"<SurveyQuestion(id={self.id}, survey_id={self.survey_id}, type={self.question_type})>"

class SurveyAnswer(Base):
    __tablename__ = "survey_answers"

    id = Column(Integer, primary_key=True, index=True)
    response_id = Column(Integer, ForeignKey("survey_responses.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("survey_questions.id"), nullable=False)
    answer = Column(Text, nullable=True)
    score = Column(Numeric(5, 2), nullable=True)  # optional numeric score

    # Relations
    response = relationship("SurveyResponse", foreign_keys=[response_id])
    question = relationship("SurveyQuestion", foreign_keys=[question_id])

    def __repr__(self):
        return f"<SurveyAnswer(id={self.id}, response_id={self.response_id}, question_id={self.question_id})>"


class DocumentType(Base):
    __tablename__ = "document_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<DocumentType(id={self.id}, name={self.name})>"


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<DocumentTemplate(id={self.id}, name={self.name})>"


class DocumentStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    FINAL = "final"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("document_templates.id"), nullable=True)
    document_type = Column(String(100), nullable=True)  # ex: attestation, contrat, congé, absence
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    generated_by_ai = Column(Boolean, default=False, nullable=False)
    status = Column(Enum(DocumentStatusEnum), default=DocumentStatusEnum.DRAFT, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    file_url = Column(String(500), nullable=True)
    is_sent = Column(Boolean, default=False, nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])
    template = relationship("DocumentTemplate", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Document(id={self.id}, employee_id={self.employee_id}, title={self.title})>"


class Formation(Base):
    __tablename__ = "formations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    target_department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    target_department = relationship("Department")

    @property
    def target_department_name(self):
        return self.target_department.name if self.target_department else None

    def __repr__(self):
        return f"<Formation(id={self.id}, title={self.title})>"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    contract_type = Column(String(100), nullable=False)  # CDI, CDD, Stage, etc.
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    position = Column(String(255), nullable=False)
    salary = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Contract(id={self.id}, user_id={self.user_id}, position={self.position})>"


class FormationEnrollment(Base):
    __tablename__ = "formation_enrollments"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    formation_id = Column(Integer, ForeignKey("formations.id"), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])
    formation = relationship("Formation", foreign_keys=[formation_id])

    __table_args__ = (
        UniqueConstraint("employee_id", "formation_id", name="uq_employee_formation_enrollment"),
    )

    def __repr__(self):
        return f"<FormationEnrollment(id={self.id}, employee_id={self.employee_id}, formation_id={self.formation_id})>"

class KpiSnapshot(Base):
    __tablename__ = "kpi_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    snapshot_date = Column(Date, nullable=False)
    headcount = Column(Integer, nullable=False)
    turnover_rate = Column(Numeric(5, 2), nullable=True)
    absenteeism_rate = Column(Numeric(5, 2), nullable=True)
    engagement_score = Column(Numeric(5, 2), nullable=True)
    payroll_amount = Column(Numeric(12, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<KpiSnapshot(id={self.id}, date={self.snapshot_date})>"

class RiskScore(Base):
    __tablename__ = "risk_scores"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    turnover_risk = Column(Numeric(5, 2), nullable=True)
    burnout_risk = Column(Numeric(5, 2), nullable=True)
    engagement_risk = Column(Numeric(5, 2), nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])

    def __repr__(self):
        return f"<RiskScore(id={self.id}, employee_id={self.employee_id})>"

class RecommendationStatusEnum(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    risk_score_id = Column(Integer, ForeignKey("risk_scores.id"), nullable=False)
    recommendation = Column(Text, nullable=False)
    status = Column(Enum(RecommendationStatusEnum), default=RecommendationStatusEnum.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])
    risk_score = relationship("RiskScore", foreign_keys=[risk_score_id])

    def __repr__(self):
        return f"<Recommendation(id={self.id}, employee_id={self.employee_id}, status={self.status})>"

class AlertStatusEnum(str, enum.Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(String(100), nullable=False)
    severity = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(AlertStatusEnum), default=AlertStatusEnum.NEW, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])

    def __repr__(self):
        return f"<Alert(id={self.id}, employee_id={self.employee_id}, type={self.alert_type}, status={self.status})>"

class AlertHistory(Base):
    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    action = Column(Text, nullable=False)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    alert = relationship("Alert", foreign_keys=[alert_id])
    performer = relationship("User", foreign_keys=[performed_by])

    def __repr__(self):
        return f"<AlertHistory(id={self.id}, alert_id={self.alert_id}, action={self.action})>"

class TicketStatusEnum(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class HrTicket(Base):
    __tablename__ = "hr_tickets"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TicketStatusEnum), default=TicketStatusEnum.OPEN, nullable=False)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    employee = relationship("User", foreign_keys=[employee_id])
    assignee = relationship("User", foreign_keys=[assigned_to])

    def __repr__(self):
        return f"<HrTicket(id={self.id}, employee_id={self.employee_id}, status={self.status})>"

class ApprovalWorkflowStatusEnum(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(Integer, nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(ApprovalWorkflowStatusEnum), default=ApprovalWorkflowStatusEnum.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relations
    approver = relationship("User", foreign_keys=[approver_id])

    def __repr__(self):
        return f"<ApprovalWorkflow(id={self.id}, entity_type={self.entity_type}, entity_id={self.entity_id}, status={self.status})>"


class TaskPriorityEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatusEnum(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class ManagerTask(Base):
    __tablename__ = "manager_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    due_date = Column(Date, nullable=True)
    priority = Column(Enum(TaskPriorityEnum, name="taskpriorityenum"), default=TaskPriorityEnum.MEDIUM, nullable=False)
    status = Column(Enum(TaskStatusEnum, name="taskstatusenum"), default=TaskStatusEnum.TODO, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relations
    assignee = relationship("User", foreign_keys=[assigned_to])
    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<ManagerTask(id={self.id}, title={self.title}, status={self.status}, assigned_to={self.assigned_to})>"


class WorkflowConfig(Base):
    __tablename__ = "workflow_configs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), unique=True, nullable=False)  # 'leave' or 'absence'
    logic_type = Column(String(100), default='single_manager', nullable=False)  # 'auto', 'single_manager', 'single_rh', 'sequential'
    validator_role = Column(String(100), nullable=True)  # 'rh', 'direction', etc.
    validator_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relation
    validator_user = relationship("User", foreign_keys=[validator_user_id])

    def __repr__(self):
        return f"<WorkflowConfig(id={self.id}, entity_type={self.entity_type}, logic_type={self.logic_type})>"

