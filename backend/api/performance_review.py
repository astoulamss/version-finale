from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from models.ml_features import PerformanceReview
from models.user import User, RoleEnum
from schemas.ml_features import PerformanceReviewCreate, PerformanceReviewResponse
from core.security import get_current_user
from typing import List

router = APIRouter(
    prefix="/api/performance-reviews",
    tags=["Performance Reviews"],
)

@router.post("/", response_model=PerformanceReviewResponse)
def create_review(
    review_data: PerformanceReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [RoleEnum.RH, RoleEnum.MANAGER]:
        raise HTTPException(status_code=403, detail="Non autorisé à créer un entretien.")
        
    new_review = PerformanceReview(
        employee_id=review_data.employee_id,
        evaluator_id=current_user.id,
        review_date=review_data.review_date,
        performance_rating=review_data.performance_rating,
        comments=review_data.comments
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

@router.get("/", response_model=List[PerformanceReviewResponse])
def get_all_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [RoleEnum.RH, RoleEnum.MANAGER, RoleEnum.DIRECTION]:
        raise HTTPException(status_code=403, detail="Non autorisé.")
        
    query = db.query(PerformanceReview)
    
    if current_user.role == RoleEnum.MANAGER:
        from models.employees import Employee
        manager_profile = db.query(Employee).filter(Employee.user_id == current_user.id).first()
        
        if manager_profile and manager_profile.department_id:
            query = query.join(Employee, PerformanceReview.employee_id == Employee.id).filter(
                Employee.department_id == manager_profile.department_id
            )
        else:
            # Fallback to direct subordinates if no department is set
            query = query.join(Employee, PerformanceReview.employee_id == Employee.id).filter(
                Employee.manager_id == current_user.id
            )
            
    return query.order_by(PerformanceReview.review_date.desc()).all()
