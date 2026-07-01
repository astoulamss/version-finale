from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database.db import get_db
from models.user import User, RoleEnum
from models.features import Contract
from schemas.features import ContractCreate, ContractResponse
from core.security import get_current_user, require_role
from typing import List
import datetime

def get_contract_html(contract, user, db: Session):
    from models.employees import Employee, Department
    
    profile = db.query(Employee).filter(Employee.user_id == user.id).first()
    departement = "Informatique"
    if profile and profile.department_id:
        dept = db.query(Department).filter(Department.id == profile.department_id).first()
        if dept:
            departement = dept.name
            
    def format_date(d):
        if not d: return "[Indéterminée]"
        if isinstance(d, str):
            try:
                d = datetime.datetime.strptime(d, "%Y-%m-%d").date()
            except:
                return d
        months = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
        return f"{d.day} {months[d.month - 1]} {d.year}"
        
    date_jour = format_date(datetime.date.today())
    start_date = format_date(contract.start_date)
    
    contract_type = (contract.contract_type or "CDI").upper()
    if contract_type == "CDI":
        type_desc = "INDÉTERMINÉE"
    elif contract_type == "CDD":
        type_desc = "DÉTERMINÉE"
    else:
        type_desc = contract_type
        
    ref = f"{datetime.date.today().strftime('%d%m%Y')}-{user.id}{contract.id}"

    user_prenom = (user.prenom or '').upper()
    user_nom = (user.nom or '').upper()
    full_name = f"{user_prenom} {user_nom}".strip()
    adresse_salarie = profile.adresse if profile and profile.adresse else "[adresse à compléter]"
    
    text = f"""
NEXCORE RH
PARIS SUR-SEINE 9280

CONTRAT DE TRAVAIL À DURÉE {type_desc} ({contract_type})

DATE : {date_jour}
OBJET : CONTRAT DE TRAVAIL POUR {full_name}

ENTRE LES SOUSSIGNÉS :

NEXCORE RH, société immatriculée au Registre du Commerce et des Sociétés sous le numéro [à compléter], dont le siège social est situé au Paris Sur-Seine 9280, représentée par son représentant légal, Monsieur AKMEL JEAN,
Ci-après dénommée " l'Employeur ",

ET :
Monsieur/Madame {full_name}, demeurant {adresse_salarie},
Ci-après dénommé(e) " le Salarié ",

IL A ÉTÉ CONVENU ET ARRÊTÉ CE QUI SUIT :

1. ENGAGEMENT
L'Employeur engage le Salarié en qualité d'{contract.position} au sein du département {departement}, sous contrat à durée {type_desc.lower()} ({contract_type}), à compter du {start_date}.

2. FONCTIONS ET ATTRIBUTIONS
Le Salarié exercera les fonctions d'{contract.position} au sein du département {departement}. Ses missions principales consisteront à :
- Participer au développement et aux activités de l'entreprise.
- Collaborer avec les autres membres de l'équipe pour garantir le bon fonctionnement des activités.
- Exécuter les tâches inhérentes à son poste.
Le Salarié s'engage à exercer ses fonctions avec diligence et professionnalisme, conformément aux directives de son supérieur hiérarchique.

3. LIEU DE TRAVAIL
Le lieu principal de travail est situé à Paris, France. Toutefois, l'Employeur se réserve le droit de modifier ce lieu en fonction des nécessités de service, sous réserve d'un préavis raisonnable et dans le respect des dispositions légales en vigueur.

4. DURÉE DU TRAVAIL
La durée hebdomadaire de travail est fixée à 35 heures, réparties selon les horaires en vigueur dans l'entreprise.

5. RÉMUNÉRATION
Le Salarié percevra une rémunération brute de {contract.salary or '[Non spécifiée]'}, versée à la fin de chaque mois civil. Cette rémunération pourra être révisée annuellement en fonction des performances du Salarié et des résultats de l'entreprise.

6. PÉRIODE D'ESSAI
Le présent contrat est conclu avec une période d'essai de trois mois, durant laquelle chacune des parties pourra y mettre fin sans préavis ni indemnité, sous réserve du respect des dispositions légales.

7. AVANTAGES
Le Salarié bénéficiera des avantages suivants, conformément à la politique interne de l'entreprise :
- Mutuelle santé collective.
- Tickets restaurant.

8. CONGÉS PAYÉS
Le Salarié bénéficiera de congés payés conformément aux dispositions légales en vigueur, soit 2,5 jours ouvrables par mois de travail effectif.

9. CONFIDENTIALITÉ
Le Salarié s'engage à respecter une obligation de confidentialité concernant toutes les informations, données ou documents auxquels il pourrait avoir accès dans le cadre de ses fonctions. Cette obligation perdurera après la cessation du présent contrat.

10. PROPRIÉTÉ INTELLECTUELLE
Tous les travaux, inventions, créations ou innovations réalisés par le Salarié dans le cadre de ses fonctions appartiennent à l'Employeur. Le Salarié s'engage à céder à l'Employeur l'intégralité des droits de propriété intellectuelle relatifs à ces créations.

11. NON-CONCURRENCE
Pendant la durée du contrat, le Salarié s'interdit d'exercer toute activité professionnelle concurrente à celle de l'Employeur, sauf accord écrit préalable de ce dernier.

12. RUPTURE DU CONTRAT
En dehors de la période d'essai, la rupture du contrat devra respecter les dispositions légales en vigueur, notamment en matière de préavis et d'indemnités.

13. DROIT APPLICABLE ET LITIGES
Le présent contrat est régi par le droit français. Tout litige relatif à son interprétation ou à son exécution sera soumis aux juridictions compétentes de Paris.

Fait à Paris, le {date_jour}

Pour la Direction Générale :
AKMEL JEAN
Représentant Légal

Bénéficiaire :
{full_name}
(Signature précédée de la mention "Lu et approuvé")
"""
    return text

router = APIRouter(prefix="/api/contracts", tags=["contracts"])




# Get my contract
@router.get("/my-contract", response_model=ContractResponse)
def get_my_contract(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current user's contract"""
    # RH cannot view personal contracts
    if current_user.role == RoleEnum.RH:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="RH cannot view personal contracts"
        )

    contract = db.query(Contract).filter(Contract.user_id == current_user.id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No contract found for this user"
        )

    return contract


# Get all contracts (RH only)
@router.get("/", response_model=List[ContractResponse])
def get_all_contracts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """Get all contracts (RH and Admin only)"""
    contracts = db.query(Contract).all()
    return contracts


# Get contract for an employee (RH only)
@router.get("/employee/{user_id}", response_model=ContractResponse)
def get_employee_contract(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """Get contract for a specific employee (RH and Admin only)"""
    contract = db.query(Contract).filter(Contract.user_id == user_id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No contract found for this employee"
        )

    return contract


# Create a contract (RH only)
@router.post("/employee/{user_id}", response_model=ContractResponse)
def create_contract(
    user_id: int,
    contract_data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """
    Create a new contract for an employee
    - Only RH and Admin can create contracts
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Validate dates
    if contract_data.end_date and contract_data.start_date > contract_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    # Check removed: Users can have multiple contracts over time (e.g., CDD then CDI)

    contract = Contract(
        user_id=user_id,
        contract_type=contract_data.contract_type,
        start_date=contract_data.start_date,
        end_date=contract_data.end_date,
        position=contract_data.position,
        salary=contract_data.salary
    )

    db.add(contract)
    db.commit()
    db.refresh(contract)

    # Automatically generate a Document for this contract
    from models.features import Document, DocumentStatusEnum
    import datetime

    content = get_contract_html(contract, user, db)

    document = Document(
        employee_id=user_id,
        document_type="contrat",
        title=f"Contrat {contract.contract_type} - {user.prenom} {user.nom}",
        content=content,
        status=DocumentStatusEnum.FINAL,
        created_by=current_user.id,
        generated_by_ai=False
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        from api.documents import _upload_doc_to_minio_helper
        _upload_doc_to_minio_helper(document, db)
    except Exception as e:
        print(f"Error generating PDF for contract: {e}")

    return contract


# Get contract by ID
@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific contract"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Check access permissions
    if current_user.role == RoleEnum.RH:
        return contract
    elif contract.user_id == current_user.id:
        return contract
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this contract"
        )


# Update contract (RH only)
@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_data: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH]))
):
    """Update a contract (RH and Admin only)"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    # Validate dates
    if contract_data.end_date and contract_data.start_date > contract_data.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Start date must be before end date"
        )

    contract.contract_type = contract_data.contract_type
    contract.start_date = contract_data.start_date
    contract.end_date = contract_data.end_date
    contract.position = contract_data.position
    contract.salary = contract_data.salary

    db.add(contract)
    db.commit()
    db.refresh(contract)

    return contract


# Delete contract (RH only)
@router.delete("/{contract_id}")
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """Delete a contract (Admin only)"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    db.delete(contract)
    db.commit()

    return {"message": "Contract deleted successfully"}


@router.post("/{contract_id}/generate-document")
def generate_contract_document(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.RH, RoleEnum.ADMIN]))
):
    """Generate a Document for an existing contract (useful for contracts created before automatic generation)"""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found"
        )

    user = db.query(User).filter(User.id == contract.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from models.features import Document, DocumentStatusEnum
    
    # Check if a document already exists for this contract
    # We'll just create a new one anyway to allow regeneration
    content = get_contract_html(contract, user, db)

    document = Document(
        employee_id=contract.user_id,
        document_type="contrat",
        title=f"Contrat {contract.contract_type} - {user.prenom} {user.nom}",
        content=content,
        status=DocumentStatusEnum.FINAL,
        created_by=current_user.id,
        generated_by_ai=False
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        from api.documents import _upload_doc_to_minio_helper
        _upload_doc_to_minio_helper(document, db)
    except Exception as e:
        print(f"Error generating PDF for contract: {e}")

    return {"message": "Document generated successfully", "document_id": document.id}
