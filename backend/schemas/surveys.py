from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from models.features import QuestionTypeEnum

# --- Survey Questions ---

class SurveyQuestionBase(BaseModel):
    question: str
    question_type: QuestionTypeEnum

class SurveyQuestionCreate(SurveyQuestionBase):
    pass

class SurveyQuestionUpdate(BaseModel):
    question: Optional[str] = None
    question_type: Optional[QuestionTypeEnum] = None

class SurveyQuestionResponseSchema(SurveyQuestionBase):
    id: int
    survey_id: int

    class Config:
        from_attributes = True

# --- Surveys ---

class SurveyBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_published: Optional[bool] = False
    end_date: Optional[date] = None

class SurveyCreate(SurveyBase):
    pass

class SurveyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_published: Optional[bool] = None
    end_date: Optional[date] = None

class SurveyResponseSchema(SurveyBase):
    id: int
    created_at: datetime
    questions: List[SurveyQuestionResponseSchema] = []

    class Config:
        from_attributes = True

# --- Survey Answers ---

class SurveyAnswerBase(BaseModel):
    question_id: int
    answer: Optional[str] = None
    score: Optional[Decimal] = None

class SurveyAnswerCreate(SurveyAnswerBase):
    pass

class SurveyAnswerResponseSchema(SurveyAnswerBase):
    id: int
    response_id: int

    class Config:
        from_attributes = True

# --- Survey Responses (Submissions by employees) ---

class SurveyResponseCreate(BaseModel):
    answers: List[SurveyAnswerCreate]

class SurveyResponseResponseSchema(BaseModel):
    id: int
    survey_id: int
    employee_id: int
    submitted_at: datetime
    answers: List[SurveyAnswerResponseSchema] = []

    class Config:
        from_attributes = True
