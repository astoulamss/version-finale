# 🎯 YDAYS API - Features Documentation

Documentation complète de tous les nouveaux endpoints de l'API YDAYS, incluant les fonctionnalités pour chaque rôle.

## 📋 Table of Contents

1. [Congés (Leaves)](#congés-leaves)
2. [Documents](#documents)
3. [Formations](#formations)
4. [Contrats](#contrats)
5. [Permissions par Rôle](#permissions-par-rôle)
6. [Exemples d'utilisation](#exemples-dutilisation)

---

## 🏖️ Congés (Leaves)

### Endpoints

#### POST `/api/leaves/` - Créer une demande de congé
**Rôles autorisés**: Collaborateur, Manager

**Corps de la requête:**
```json
{
  "start_date": "2024-02-01",
  "end_date": "2024-02-05",
  "leave_type": "vacation",
  "reason": "Vacances d'hiver"
}
```

**Types de congés disponibles:**
- `vacation`: Congés payés
- `sick`: Congé maladie
- `maternity`: Congé maternité
- `personal`: Congé personnel
- `unpaid`: Congé sans solde

**Réponse:**
```json
{
  "id": 1,
  "employee_id": 2,
  "start_date": "2024-02-01",
  "end_date": "2024-02-05",
  "leave_type": "vacation",
  "status": "pending",
  "reason": "Vacances d'hiver",
  "created_at": "2024-01-20T10:30:00"
}
```

---

#### GET `/api/leaves/my-leaves` - Récupérer mes demandes de congé
**Rôles autorisés**: Collaborateur, Manager

**Réponse:**
```json
[
  {
    "id": 1,
    "employee_id": 2,
    "start_date": "2024-02-01",
    "end_date": "2024-02-05",
    "leave_type": "vacation",
    "status": "pending",
    "reason": "Vacances d'hiver",
    "created_at": "2024-01-20T10:30:00"
  }
]
```

---

#### GET `/api/leaves/team` - Récupérer les demandes de congé de l'équipe
**Rôles autorisés**: Manager

**Réponse:**
Liste de tous les congés en attente que le manager peut valider.

---

#### PUT `/api/leaves/{leave_id}` - Valider/Rejeter une demande de congé
**Rôles autorisés**: Manager, Admin

**Corps de la requête:**
```json
{
  "status": "approved",
  "reason": "Approuvé"
}
```

**Statuts disponibles:**
- `pending`: En attente
- `approved`: Approuvé
- `rejected`: Rejeté
- `cancelled`: Annulé

---

#### DELETE `/api/leaves/{leave_id}` - Annuler une demande de congé
**Rôles autorisés**: Collaborateur, Manager

**Conditions:**
- Seules les demandes en attente peuvent être annulées
- L'utilisateur ne peut annuler que ses propres demandes

---

## 📄 Documents

### Endpoints

#### GET `/api/documents/my-documents` - Récupérer mes documents
**Rôles autorisés**: Collaborateur, Manager, Direction, Admin

**Note**: RH ne peut pas accéder aux documents personnels

**Réponse:**
```json
[
  {
    "id": 1,
    "user_id": 2,
    "title": "Contrat de travail",
    "document_type": "contract",
    "file_path": "/documents/contrat_2024.pdf",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

#### GET `/api/documents/employee/{user_id}` - Récupérer les documents d'un employé
**Rôles autorisés**: RH, Admin

**Réponse:**
Liste de tous les documents de l'employé spécifié.

---

#### POST `/api/documents/` - Télécharger un document
**Rôles autorisés**: Admin, RH

**Corps de la requête:**
```json
{
  "title": "Certificat de travail",
  "document_type": "certificate",
  "file_path": "/documents/certificat_2024.pdf"
}
```

**Types de documents:**
- `contract`: Contrat
- `payslip`: Bulletins de salaire
- `certificate`: Certificat de travail
- `training`: Document de formation
- `other`: Autre

---

#### DELETE `/api/documents/{document_id}` - Supprimer un document
**Rôles autorisés**: Admin

---

## 🎓 Formations

### Endpoints

#### GET `/api/formations/` - Récupérer toutes les formations
**Rôles autorisés**: Collaborateur, Manager, Direction, Admin

**Note**: RH ne peut pas accéder aux formations

**Réponse:**
```json
[
  {
    "id": 1,
    "title": "Formation Python avancée",
    "description": "Apprenez Python avancé",
    "start_date": "2024-03-01",
    "end_date": "2024-03-05",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

---

#### GET `/api/formations/rh/all` - Récupérer toutes les formations (RH)
**Rôles autorisés**: RH, Admin

Endpoint dédié pour RH avec accès complet aux formations.

---

#### POST `/api/formations/` - Créer une formation
**Rôles autorisés**: RH, Admin

**Corps de la requête:**
```json
{
  "title": "Formation Python avancée",
  "description": "Apprenez Python avancé",
  "start_date": "2024-03-01",
  "end_date": "2024-03-05"
}
```

---

#### PUT `/api/formations/{formation_id}` - Modifier une formation
**Rôles autorisés**: RH, Admin

---

#### DELETE `/api/formations/{formation_id}` - Supprimer une formation
**Rôles autorisés**: Admin

---

## 📋 Contrats

### Endpoints

#### GET `/api/contracts/my-contract` - Récupérer mon contrat
**Rôles autorisés**: Collaborateur, Manager, Direction, Admin

**Note**: RH ne peut pas accéder aux contrats personnels

**Réponse:**
```json
{
  "id": 1,
  "user_id": 2,
  "contract_type": "CDI",
  "start_date": "2024-01-01",
  "end_date": null,
  "position": "Développeur Python",
  "salary": "35000€",
  "created_at": "2024-01-15T10:30:00"
}
```

---

#### GET `/api/contracts/` - Récupérer tous les contrats
**Rôles autorisés**: RH, Admin

---

#### GET `/api/contracts/employee/{user_id}` - Récupérer le contrat d'un employé
**Rôles autorisés**: RH, Admin

---

#### POST `/api/contracts/` - Créer un contrat
**Rôles autorisés**: RH, Admin

**Corps de la requête:**
```json
{
  "contract_type": "CDI",
  "start_date": "2024-02-01",
  "end_date": null,
  "position": "Développeur Python",
  "salary": "35000€"
}
```

**Types de contrats:**
- `CDI`: Contrat à durée indéterminée
- `CDD`: Contrat à durée déterminée
- `Stage`: Stage
- `Alternance`: Contrat d'alternance
- `Freelance`: Travail en freelance

**Note**: Un utilisateur ne peut avoir qu'un seul contrat actif

---

#### PUT `/api/contracts/{contract_id}` - Modifier un contrat
**Rôles autorisés**: RH, Admin

---

#### DELETE `/api/contracts/{contract_id}` - Supprimer un contrat
**Rôles autorisés**: Admin

---

## 🔐 Permissions par Rôle

### Tableau récapitulatif

| Feature | Admin | Collaborateur | Direction | Manager | RH |
|---------|-------|---------------|-----------|---------|-----|
| **Congés** |
| Créer | ❌ | ✅ | ❌ | ✅ | ❌ |
| Voir les siens | ❌ | ✅ | ❌ | ✅ | ❌ |
| Valider/Rejeter | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Documents** |
| Voir les siens | ✅ | ✅ | ✅ | ✅ | ❌ |
| Voir ceux des employés | ✅ | ❌ | ❌ | ❌ | ✅ |
| Télécharger | ✅ | ❌ | ❌ | ❌ | ✅ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Formations** |
| Voir toutes | ✅ | ✅ | ✅ | ✅ | ❌ |
| Créer | ✅ | ❌ | ❌ | ❌ | ✅ |
| Modifier | ✅ | ❌ | ❌ | ❌ | ✅ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Contrats** |
| Voir le sien | ✅ | ✅ | ✅ | ✅ | ❌ |
| Voir tous | ✅ | ❌ | ❌ | ❌ | ✅ |
| Créer | ✅ | ❌ | ❌ | ❌ | ✅ |
| Modifier | ✅ | ❌ | ❌ | ❌ | ✅ |
| Supprimer | ✅ | ❌ | ❌ | ❌ | ❌ |

---

## 💡 Exemples d'utilisation

### Exemple 1: Créer et valider une demande de congé

**Étape 1: L'employé crée une demande de congé**
```bash
curl -X POST "http://localhost:8000/api/leaves/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer EMPLOYEE_TOKEN" \
  -d '{
    "start_date": "2024-02-01",
    "end_date": "2024-02-05",
    "leave_type": "vacation",
    "reason": "Vacances"
  }'
```

**Étape 2: Le manager récupère les demandes de son équipe**
```bash
curl -X GET "http://localhost:8000/api/leaves/team" \
  -H "Authorization: Bearer MANAGER_TOKEN"
```

**Étape 3: Le manager valide la demande**
```bash
curl -X PUT "http://localhost:8000/api/leaves/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer MANAGER_TOKEN" \
  -d '{
    "status": "approved",
    "reason": "Approuvé"
  }'
```

---

### Exemple 2: Gestion des documents RH

**Étape 1: RH télécharge un document pour un employé**
```bash
curl -X POST "http://localhost:8000/api/documents/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer RH_TOKEN" \
  -d '{
    "title": "Certificat de travail",
    "document_type": "certificate",
    "file_path": "/documents/certificat_2024.pdf"
  }'
```

**Étape 2: RH voir les documents d'un employé**
```bash
curl -X GET "http://localhost:8000/api/documents/employee/2" \
  -H "Authorization: Bearer RH_TOKEN"
```

---

### Exemple 3: Création d'un contrat

**Étape 1: RH crée un contrat pour un nouvel employé**
```bash
curl -X POST "http://localhost:8000/api/contracts/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer RH_TOKEN" \
  -d '{
    "user_id": 5,
    "contract_type": "CDI",
    "start_date": "2024-02-01",
    "end_date": null,
    "position": "Développeur Python",
    "salary": "35000€"
  }'
```

**Étape 2: L'employé consulte son contrat**
```bash
curl -X GET "http://localhost:8000/api/contracts/my-contract" \
  -H "Authorization: Bearer EMPLOYEE_TOKEN"
```

---

## 📊 Cas d'usage par rôle

### Employé (Collaborateur)
- ✅ Consulter ses informations personnelles
- ✅ Demander des congés
- ✅ Consulter ses documents
- ✅ Consulter son contrat
- ✅ Consulter les formations disponibles

### Manager
- ✅ Tout ce que fait un employé
- ✅ Valider/Rejeter les congés de son équipe
- ✅ Valider les congés maladie
- ✅ Voir les indicateurs de son équipe

### RH
- ✅ Gérer les employés (consultation et modification des profils)
- ✅ Créer et gérer les contrats
- ✅ Télécharger les documents pour les employés
- ✅ Créer et gérer les formations
- ✅ Gérer l'onboarding/offboarding

### Direction
- ✅ Accès à tous les dashboards stratégiques
- ✅ Consulter les KPI globaux
- ✅ Voir les prévisions RH
- ✅ Accéder aux analyses prédictives

### Admin
- ✅ Accès complet à tous les endpoints
- ✅ Créer des utilisateurs
- ✅ Gérer les rôles et permissions
- ✅ Auditer les actions du système

---

## 🔒 Notes de sécurité

1. **Authentification JWT**: Tous les endpoints (sauf login) nécessitent un token JWT valide
2. **Expiration du token**: 30 minutes par défaut
3. **Validation des dates**: Les dates doivent être valides (start_date < end_date)
4. **Permissions strictes**: Chaque action est validée selon le rôle de l'utilisateur
5. **Données sensibles**: Les contrats et salaires sont protégés par RBAC

---

## 📝 Conventions API

### Headers requis
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

### Codes de statut HTTP
- `200 OK`: Requête réussie
- `201 Created`: Ressource créée
- `400 Bad Request`: Données invalides
- `401 Unauthorized`: Token manquant ou invalide
- `403 Forbidden`: Permissions insuffisantes
- `404 Not Found`: Ressource non trouvée
- `500 Internal Server Error`: Erreur serveur

---

## ✉️ Support

Pour toute question sur ces fonctionnalités, veuillez contacter l'équipe de développement.
