from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from typing import List

from database.db import get_db
from models.user import User, RoleEnum
from models.features import Survey, SurveyQuestion, SurveyResponse, SurveyAnswer, QuestionTypeEnum
from models.notification import Notification
from schemas.surveys import (
    SurveyCreate, SurveyUpdate, SurveyResponseSchema,
    SurveyQuestionCreate, SurveyQuestionUpdate, SurveyQuestionResponseSchema,
    SurveyResponseCreate, SurveyResponseResponseSchema
)
from core.security import require_role, get_current_user

router = APIRouter(prefix="/api/surveys", tags=["Surveys"])

# --- Helper function ---

def _build_survey_response(survey: Survey, db: Session) -> SurveyResponseSchema:
    questions = db.query(SurveyQuestion).filter(SurveyQuestion.survey_id == survey.id).all()
    resp = SurveyResponseSchema.model_validate(survey)
    resp.questions = [SurveyQuestionResponseSchema.model_validate(q) for q in questions]
    return resp

# --- Survey Management (RH / Admin) ---

@router.get("/", response_model=List[SurveyResponseSchema])
def list_surveys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List surveys. 
    RH and Admin see all surveys.
    Collaborators and Managers see only published surveys.
    """
    query = db.query(Survey)
    if current_user.role not in [RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.DIRECTION]:
        query = query.filter(Survey.is_published == True)
        query = query.filter((Survey.end_date == None) | (Survey.end_date >= date.today()))
        # Exclude surveys the user has already responded to
        query = query.filter(
            ~db.query(SurveyResponse).filter(
                SurveyResponse.survey_id == Survey.id,
                SurveyResponse.employee_id == current_user.id
            ).exists()
        )
        
    surveys = query.order_by(Survey.created_at.desc()).all()
    return [_build_survey_response(s, db) for s in surveys]

@router.post("/", response_model=SurveyResponseSchema)
def create_survey(
    payload: SurveyCreate,
    db: Session = Depends(get_db),
    user_data: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    survey = Survey(**payload.model_dump())
    db.add(survey)
    db.commit()
    db.refresh(survey)
    return _build_survey_response(survey, db)

@router.get("/{survey_id}", response_model=SurveyResponseSchema)
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    if current_user.role not in [RoleEnum.RH, RoleEnum.ADMIN] and not survey.is_published:
        raise HTTPException(status_code=403, detail="Not authorized to view unpublished survey")
        
    return _build_survey_response(survey, db)

@router.put("/{survey_id}", response_model=SurveyResponseSchema)
def update_survey(
    survey_id: int,
    payload: SurveyUpdate,
    db: Session = Depends(get_db),
    user_data: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(survey, key, value)
        
    db.commit()
    db.refresh(survey)
    return _build_survey_response(survey, db)

@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    user_data: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    # Delete related answers, responses, questions (if no cascade)
    db.query(SurveyAnswer).filter(SurveyAnswer.question_id.in_(
        db.query(SurveyQuestion.id).filter(SurveyQuestion.survey_id == survey_id)
    )).delete(synchronize_session=False)
    
    db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id).delete()
    db.query(SurveyQuestion).filter(SurveyQuestion.survey_id == survey_id).delete()
    db.delete(survey)
    db.commit()
    return None

# --- Survey Questions Management ---

@router.post("/{survey_id}/questions", response_model=SurveyQuestionResponseSchema)
def add_question(
    survey_id: int,
    payload: SurveyQuestionCreate,
    db: Session = Depends(get_db),
    user_data: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    question = SurveyQuestion(survey_id=survey_id, **payload.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question

@router.put("/questions/{question_id}", response_model=SurveyQuestionResponseSchema)
def update_question(
    question_id: int,
    payload: SurveyQuestionUpdate,
    db: Session = Depends(get_db),
    user_data: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    question = db.query(SurveyQuestion).filter(SurveyQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)
        
    db.commit()
    db.refresh(question)
    return question

@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    user_data: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    question = db.query(SurveyQuestion).filter(SurveyQuestion.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
        
    # Remove related answers first
    db.query(SurveyAnswer).filter(SurveyAnswer.question_id == question_id).delete()
    db.delete(question)
    db.commit()
    return None

# --- Survey Responses ---

@router.post("/{survey_id}/responses", response_model=SurveyResponseResponseSchema)
def submit_survey_response(
    survey_id: int,
    payload: SurveyResponseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey or not survey.is_published:
        raise HTTPException(status_code=404, detail="Survey not found or not published")
        
    if survey.end_date and survey.end_date < date.today():
        raise HTTPException(status_code=400, detail="Survey has expired")
        
    # Check if already submitted
    existing_resp = db.query(SurveyResponse).filter(
        SurveyResponse.survey_id == survey_id,
        SurveyResponse.employee_id == current_user.id
    ).first()
    
    if existing_resp:
        raise HTTPException(status_code=400, detail="You have already responded to this survey")
        
    response = SurveyResponse(survey_id=survey_id, employee_id=current_user.id)
    db.add(response)
    db.commit()
    db.refresh(response)
    
    for ans in payload.answers:
        # Simple validation: ensure question belongs to survey
        q = db.query(SurveyQuestion).filter(SurveyQuestion.id == ans.question_id, SurveyQuestion.survey_id == survey_id).first()
        if q:
            answer_record = SurveyAnswer(
                response_id=response.id,
                question_id=ans.question_id,
                answer=ans.answer,
                score=ans.score
            )
            db.add(answer_record)
            
    db.commit()
    db.refresh(response)
    
    # Notify RH
    rh_users = db.query(User).filter(User.role == RoleEnum.RH).all()
    for rh in rh_users:
        notif = Notification(
            user_id=rh.id,
            message=f"{current_user.prenom} {current_user.nom} a répondu à l'enquête '{survey.title}'."
        )
        db.add(notif)
    db.commit()
    
    return response

# --- Results ---

from models.employees import Employee

@router.get("/{survey_id}/results")
def get_survey_results(
    survey_id: int,
    db: Session = Depends(get_db),
    user_data: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN, RoleEnum.DIRECTION]))
):
    survey = db.query(Survey).filter(Survey.id == survey_id).first()
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")
        
    responses = db.query(SurveyResponse).filter(SurveyResponse.survey_id == survey_id).all()
    questions = db.query(SurveyQuestion).filter(SurveyQuestion.survey_id == survey_id).all()
    
    employees = db.query(Employee).all()
    user_dept_map = {e.user_id: (e.department.name if e.department else "Sans département") for e in employees}
    
    resp_dept_map = {r.id: user_dept_map.get(r.employee_id, "Sans département") for r in responses}
    
    dept_counts = {}
    for r in responses:
        d = user_dept_map.get(r.employee_id, "Sans département")
        dept_counts[d] = dept_counts.get(d, 0) + 1

    results = {
        "survey_id": survey.id,
        "title": survey.title,
        "total_responses": len(responses),
        "participants_by_department": dept_counts,
        "questions_summary": []
    }
    
    for q in questions:
        q_summary = {
            "question_id": q.id,
            "question": q.question,
            "type": q.question_type.value,
            "answers": []
        }
        
        answers = db.query(SurveyAnswer).filter(SurveyAnswer.question_id == q.id).all()
        
        if q.question_type in [QuestionTypeEnum.SINGLE_CHOICE, QuestionTypeEnum.MULTIPLE_CHOICE, QuestionTypeEnum.YES_NO]:
            from collections import Counter
            counts = Counter([a.answer for a in answers if a.answer])
            q_summary["distribution"] = dict(counts)
            
        elif q.question_type == QuestionTypeEnum.RATING:
            scores = [float(a.score) for a in answers if a.score is not None]
            q_summary["average"] = sum(scores) / len(scores) if scores else 0
            q_summary["total_ratings"] = len(scores)
            
        else: # FREE_TEXT
            q_summary["answers"] = [{"response_id": a.response_id, "text": a.answer, "department": resp_dept_map.get(a.response_id, "Sans département")} for a in answers if a.answer]
            
        results["questions_summary"].append(q_summary)
        
    return results
