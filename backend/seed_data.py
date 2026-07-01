"""
Script de seed pour initialiser les données de base :
- Départements : Informatique, Finance
- Postes : Chef d'équipe, Agent
"""

from database.db import SessionLocal
from models.user import User  # nécessaire pour que SQLAlchemy résolve la relation Employee → User
from models.employees import Department, Position
from models.features import DocumentType, DocumentTemplate, LeaveType


def seed_departments(db):
    """Créer les départements par défaut s'ils n'existent pas"""
    departments = [
        {"name": "Informatique", "description": "Département des systèmes d'information et développement"},
        {"name": "Finance", "description": "Département comptabilité, contrôle de gestion et trésorerie"},
    ]
    created = 0
    for dept_data in departments:
        existing = db.query(Department).filter(Department.name == dept_data["name"]).first()
        if not existing:
            db.add(Department(**dept_data))
            created += 1
    db.commit()
    print(f"  ✓ Départements : {created} créé(s)")


def seed_positions(db):
    """Créer les postes par défaut s'ils n'existent pas"""
    positions = [
        {"title": "Chef d'équipe", "description": "Responsable d'une équipe opérationnelle"},
        {"title": "Agent", "description": "Agent d'exécution opérationnelle"},
    ]
    created = 0
    for pos_data in positions:
        existing = db.query(Position).filter(Position.title == pos_data["title"]).first()
        if not existing:
            db.add(Position(**pos_data))
            created += 1
    db.commit()
    print(f"  ✓ Postes : {created} créé(s)")


def seed_document_types(db):
    """Créer les types de document par défaut s'ils n'existent pas"""
    doc_types = [
        {"id": 1, "name": "attestation", "description": "Attestations diverses (travail, salaire, etc.)"},
        {"id": 2, "name": "contrat", "description": "Contrats de travail, CDI, CDD, avenants"},
        {"id": 3, "name": "congé", "description": "Documents liés aux demandes de congés"},
        {"id": 4, "name": "absence", "description": "Justificatifs d'absences"}
    ]
    created = 0
    for dt_data in doc_types:
        existing = db.query(DocumentType).filter(DocumentType.id == dt_data["id"]).first()
        if not existing:
            db.add(DocumentType(**dt_data))
            created += 1
    db.commit()
    print(f"  ✓ Types de documents : {created} créé(s)")


def seed_document_templates(db):
    """Créer les modèles de documents par défaut s'ils n'existent pas"""
    templates = [
        {
            "name": "Attestation de travail",
            "content": "1. INFORMATIONS DE L'EMPLOYÉ\nNom complet : {{first_name}} {{last_name}}\nPoste Occupé : {{position}}\nDépartement : {{department}}\nType de contrat : CDI\nDate d'entrée : {{hire_date}}\n\n2. ATTRIBUTION & VALIDATION\nNous certifions par la présente que {{first_name}} {{last_name}}, occupant le poste de {{position}} au sein du département {{department}}, travaille au sein de notre entreprise depuis le {{hire_date}}.\n\nLe présent certificat est délivré à la demande de l'intéressé(e) pour servir et valoir ce que de droit.\n\nFait à Casablanca, le {{current_date}}\n\nBénéficiaire : {{first_name}} {{last_name}}\nPour la Direction Générale : Le Directeur des RH [Cachet SmartRH SARL]",
            "description": "Modèle d'attestation de travail standard"
        },
        {
            "name": "Autorisation de congé",
            "content": "1. INFORMATIONS DE L'EMPLOYÉ\nNom complet : {{first_name}} {{last_name}}\nPoste Occupé : {{position}}\nDépartement : {{department}}\nType de contrat : CDI\n\n2. DÉTAILS DE LA PÉRIODE DE CONGÉ\nType de congé : {{leave_type}}\nStatut Demande : Approuvé\nDate de début : {{start_date}}\nDate de fin : {{end_date}}\nNombre de jours : {{duration}} jours\n\n3. ATTRIBUTION & VALIDATION\nNous certifions par la présente que {{first_name}} {{last_name}}, occupant le poste de {{position}} au sein du département {{department}}, a bénéficié d'un congé de type {{leave_type}} du {{start_date}} au {{end_date}}, soit un total de {{duration}} jours.\n\nLe présent certificat est délivré à la demande de l'intéressé(e) pour servir et valoir ce que de droit auprès de toute autorité administrative de gestion de compétences.\n\nFait à Casablanca, le {{current_date}}\n\nBénéficiaire : {{first_name}} {{last_name}}\nPour la Direction Générale : Le Directeur des RH [Cachet SmartRH SARL]",
            "description": "Modèle d'autorisation de congé validée par le manager"
        },
        {
            "name": "Contrat de travail",
            "content": "1. INFORMATIONS DU SALARIÉ\nNom complet : {{first_name}} {{last_name}}\nPoste Occupé : {{position}}\nSalaire Mensuel : {{salary}}\n\n2. CONDITIONS D'ENGAGEMENT\nDate d'embauche : {{hire_date}}\nType de contrat : CDI\n\n3. ATTRIBUTION & VALIDATION\nCe contrat est établi selon les règles et la législation du travail en vigueur. Les deux parties s'engagent à en respecter les termes.\n\nFait à Casablanca, le {{current_date}}\n\nBénéficiaire : {{first_name}} {{last_name}}\nPour la Direction Générale : Le Directeur des RH [Cachet SmartRH SARL]",
            "description": "Modèle simplifié de contrat de travail"
        },
        {
            "name": "Justificatif d'absence",
            "content": "1. INFORMATIONS DE L'EMPLOYÉ\nNom complet : {{first_name}} {{last_name}}\nPoste Occupé : {{position}}\nDépartement : {{department}}\n\n2. DÉTAILS DE L'ABSENCE\nDate de début : {{start_date}}\nDate de fin : {{end_date}}\nRaison de l'absence : {{reason}}\n\n3. ATTRIBUTION & VALIDATION\nLe présent document atteste que l'absence de {{first_name}} {{last_name}} du {{start_date}} au {{end_date}} est justifiée pour le motif suivant : {{reason}}.\n\nFait à Casablanca, le {{current_date}}\n\nBénéficiaire : {{first_name}} {{last_name}}\nPour la Direction Générale : Le Directeur des RH [Cachet SmartRH SARL]",
            "description": "Modèle de justificatif pour absence déclarée"
        }
    ]
    created = 0
    for t_data in templates:
        existing = db.query(DocumentTemplate).filter(DocumentTemplate.name == t_data["name"]).first()
        if not existing:
            db.add(DocumentTemplate(**t_data))
            created += 1
    db.commit()
    print(f"  [OK] Modèles de documents : {created} créé(s)")


def seed_leave_types(db):
    """Créer les types de congés par défaut s'ils n'existent pas"""
    leave_types = [
        {"name": "Congé Payé", "max_days": 25, "description": "Congé annuel payé réglementaire."},
        {"name": "Arrêt Maladie", "max_days": 30, "description": "Absence autorisée pour motif médical."},
        {"name": "Maternité / Paternité", "max_days": 120, "description": "Congé de maternité ou de paternité légal."},
        {"name": "Congé Personnel", "max_days": 10, "description": "Congé exceptionnel pour convenance personnelle."},
        {"name": "Congé Sans Solde", "max_days": 90, "description": "Congé sans rémunération pour divers motifs."},
    ]
    created = 0
    for lt_data in leave_types:
        existing = db.query(LeaveType).filter(LeaveType.name == lt_data["name"]).first()
        if not existing:
            db.add(LeaveType(**lt_data))
            created += 1
    db.commit()
    print(f"  ✓ Catégories de congés : {created} créé(s)")


def run_seed():
    """Exécuter toutes les seeds"""
    print("[SEED] Initialisation des données de base...")
    db = SessionLocal()
    try:
        seed_departments(db)
        seed_positions(db)
        seed_document_types(db)
        seed_document_templates(db)
        seed_leave_types(db)
        print("[SEED] Seed terminé avec succès !")
    except Exception as e:
        db.rollback()
        print(f"❌ Erreur lors du seed : {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()

