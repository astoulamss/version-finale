from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List

from database.db import get_db
from models.user import User, RoleEnum
from models.features import HrTicket, TicketStatusEnum
from schemas.tickets import TicketCreate, TicketResponse, TicketUpdateStatus, TicketAssign
from core.security import get_current_user, require_role
from utils.notifications import notify_role

router = APIRouter(prefix="/api/tickets", tags=["Tickets RH"])

@router.get("", response_model=List[TicketResponse])
def get_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupérer les tickets.
    - Un RH ou Admin verra tous les tickets.
    - Un employé classique ne verra que les siens.
    """
    query = db.query(HrTicket).options(
        joinedload(HrTicket.employee),
        joinedload(HrTicket.assignee)
    )
    
    if current_user.role not in [RoleEnum.RH, RoleEnum.ADMIN]:
        if current_user.role == RoleEnum.MANAGER:
            from models.employees import Employee
            managed = db.query(Employee).filter(Employee.manager_id == current_user.id).all()
            team_user_ids = [current_user.id] + [e.user_id for e in managed]
            query = query.filter(HrTicket.employee_id.in_(team_user_ids))
        else:
            query = query.filter(HrTicket.employee_id == current_user.id)
        
    # Trier du plus récent au plus ancien
    tickets = query.order_by(HrTicket.created_at.desc()).all()
    return tickets

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def create_ticket(
    ticket: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Créer un nouveau ticket RH.
    """
    target_id = current_user.id
    if ticket.target_employee_id and current_user.role == RoleEnum.MANAGER:
        from models.employees import Employee
        emp = db.query(Employee).filter(Employee.user_id == ticket.target_employee_id).first()
        if emp and emp.manager_id == current_user.id:
            target_id = ticket.target_employee_id

    new_ticket = HrTicket(
        subject=ticket.subject,
        description=ticket.description,
        employee_id=target_id,
        status=TicketStatusEnum.OPEN
    )
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)

    # Notifier les RH
    msg = f"Nouvelle demande RH (Ticket) créée par {current_user.prenom} {current_user.nom} : {new_ticket.subject}"
    notify_role(db, RoleEnum.RH, msg)

    return new_ticket

@router.post("/{ticket_id}/remind")
def remind_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Relancer les RH pour un ticket.
    """
    ticket = db.query(HrTicket).filter(HrTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
    # Check permissions
    has_permission = False
    if ticket.employee_id == current_user.id:
        has_permission = True
    elif current_user.role == RoleEnum.MANAGER:
        from models.employees import Employee
        emp = db.query(Employee).filter(Employee.user_id == ticket.employee_id).first()
        if emp and emp.manager_id == current_user.id:
            has_permission = True
            
    if not has_permission:
        raise HTTPException(status_code=403, detail="Vous n'êtes pas autorisé à relancer ce ticket")
        
    msg = f"Relance : Le ticket #{ticket.id} '{ticket.subject}' nécessite votre attention. (Relancé par {current_user.prenom} {current_user.nom})"
    notify_role(db, RoleEnum.RH, msg)
    
    return {"message": "Relance envoyée avec succès"}

@router.put("/{ticket_id}/status", response_model=TicketResponse)
def update_ticket_status(
    ticket_id: int,
    status_update: TicketUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """
    Mettre à jour le statut d'un ticket (Réservé aux RH/Admin).
    """
    ticket = db.query(HrTicket).filter(HrTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
    ticket.status = status_update.status
    db.commit()
    db.refresh(ticket)
    return ticket

@router.put("/{ticket_id}/assign", response_model=TicketResponse)
def assign_ticket(
    ticket_id: int,
    assign_update: TicketAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """
    Assigner un ticket à un membre de l'équipe RH.
    """
    ticket = db.query(HrTicket).filter(HrTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
        
    # Vérifier que l'assigné existe et est RH/Admin (optionnel, mais recommandé)
    assignee = db.query(User).filter(User.id == assign_update.assigned_to).first()
    if not assignee or assignee.role not in [RoleEnum.RH, RoleEnum.ADMIN]:
        raise HTTPException(status_code=400, detail="L'utilisateur assigné n'est pas valide ou n'a pas les droits RH")

    ticket.assigned_to = assign_update.assigned_to
    db.commit()
    db.refresh(ticket)
    return ticket
