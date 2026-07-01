# YDAYS API - Backend FastAPI

API backend pour la gestion des utilisateurs avec authentification par rôles.

## 🚀 Installation

### Prérequis
- Python 3.10+
- PostgreSQL (optionnel, SQLite par défaut)

### Étapes d'installation

1. **Cloner le projet**
```bash
cd c:\ydays_back
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```
*Note: La dépendance `bcrypt` est verrouillée à la version `4.0.1` pour assurer la compatibilité avec `passlib`.*

4. **Créer le premier administrateur**
```bash
python create_admin.py
```

5. **Lancer l'application**
```bash
python main.py
```

ou avec uvicorn directement:
```bash
uvicorn main:app --reload
```

---

### 🐋 Alternative : Lancement rapide avec Docker Compose

Si vous préférez utiliser Docker, les services PostgreSQL et l'API sont configurés et prêts à l'emploi.

1. **Lancer les conteneurs (API et Base de données)**
```bash
docker compose up --build -d
```

2. **Créer l'administrateur dans le conteneur**
```bash
docker exec ydays_api python create_admin.py
```

L'API sera disponible sur: `http://localhost:8000`
La documentation Swagger est disponible sur: `http://localhost:8000/docs`

## 📚 Documentation API

### Documentation interactive
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔐 Authentification et Gestion des utilisateurs

### Rôles disponibles
- **admin**: Accès complet au système et création des utilisateurs
- **collaborateur**: Accès aux tâches et projets
- **direction**: Vue d'ensemble de l'entreprise
- **manager**: Gestion de l'équipe
- **rh**: Gestion des ressources humaines

### Flux de création d'utilisateurs

1. **Créer le premier administrateur** (une seule fois)
   ```bash
   python create_admin.py
   ```
   Cela crée un utilisateur admin avec:
   - Email: `admin@example.com`
   - Mot de passe: `admin123`

2. **L'admin se connecte** - `POST /api/auth/login`

3. **L'admin crée les autres utilisateurs** - `POST /api/users/` (avec authentification admin)
   - **Seul l'Admin** peut créer des utilisateurs
   - L'enregistrement public est désactivé

### Flux d'authentification complet

1. **Admin crée un utilisateur** - `POST /api/users/`
```json
{
  "nom": "Dupont",
  "prenom": "Jean",
  "email": "jean.dupont@example.com",
  "mots_de_passe": "password123",
  "role": "collaborateur"
}
```
> ⚠️ **Seul Admin** peut créer des utilisateurs

2. **Utilisateur se connecte** - `POST /api/auth/login`
```json
{
  "email": "jean.dupont@example.com",
  "mots_de_passe": "password123"
}
```

**Réponse:**
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "role": "collaborateur",
    "is_active": true,
    "first_login": false,
    "created_at": "2024-01-15T10:30:00"
  }
}
```

3. **Utilisateur accède à son dashboard** - `GET /api/dashboard/home`
Ajouter le header:
```
Authorization: Bearer <access_token>
```

## 📍 Endpoints disponibles

### Authentification (`/api/auth`)
- `POST /api/auth/login` - Authentifier un utilisateur et recevoir un JWT token

### Dashboard (`/api/dashboard`)
- `GET /api/dashboard/home` - Redirection automatique au dashboard selon le rôle
- `GET /api/dashboard/admin` - Dashboard administrateur
- `GET /api/dashboard/collaborateur` - Dashboard collaborateur
- `GET /api/dashboard/direction` - Dashboard direction
- `GET /api/dashboard/manager` - Dashboard manager
- `GET /api/dashboard/rh` - Dashboard RH

### Utilisateurs (`/api/users`)
- `POST /api/users/` - Créer un nouvel utilisateur (**Admin seulement**)
- `GET /api/users/me` - Profil de l'utilisateur connecté (tous sauf RH)
- `PUT /api/users/me` - Modifier son profil (tous sauf RH)
- `PUT /api/users/me/change-password` - Modifier son propre mot de passe (Tous)
- `GET /api/users/` - Lister tous les utilisateurs (**Admin et RH** pour gestion des employés)
- `GET /api/users/{user_id}` - Obtenir les détails d'un utilisateur (**Admin et RH** pour gestion des employés)
- `PUT /api/users/{user_id}` - Modifier un utilisateur (**Admin et RH** pour gestion des employés)
- `DELETE /api/users/{user_id}` - Désactiver un utilisateur (**Admin seulement**)

### Congés (`/api/leaves`)
- `POST /api/leaves/` - Créer une demande de congé (Collaborateur, Manager)
- `GET /api/leaves/my-leaves` - Récupérer mes demandes de congé
- `GET /api/leaves/team` - Récupérer les demandes de son équipe (Manager)
- `PUT /api/leaves/{leave_id}` - Valider/Rejeter une demande (Manager, Admin)
- `PATCH /api/leaves/{leave_id}` - Modifier une demande de congé en attente (Collaborateur, Manager)
- `DELETE /api/leaves/{leave_id}` - Annuler/Supprimer une demande de congé en attente (Collaborateur, Manager)

### Documents (`/api/documents`)
- `GET /api/documents/my-documents` - Récupérer mes documents (Tous)
- `GET /api/documents/{document_id}` - Consulter un document spécifique (Propriétaire, RH, Admin)
- `GET /api/documents/{document_id}/download` - Télécharger un document au format PDF (Propriétaire, RH, Admin)
- `GET /api/documents/employee/{user_id}` - Consulter les documents d'un employé (RH, Admin)
- `GET /api/documents/all` - Consulter tous les documents (RH, Admin)
- `POST /api/documents/manual` - Création manuelle d'un document (RH, Admin)
- `POST /api/documents/generate` - Génération automatique d'un document via template et IA (RH, Admin)
- `PUT /api/documents/{document_id}/status` - Valider le statut d'un document (RH, Admin)
- `DELETE /api/documents/{document_id}` - Supprimer un document (Admin)

#### Modèles de documents (`/api/documents/templates`)
- `POST /api/documents/templates` - Créer un modèle (RH, Admin)
- `GET /api/documents/templates` - Lister les modèles (RH, Admin)
- `GET /api/documents/templates/{template_id}` - Voir un modèle (RH, Admin)
- `PUT /api/documents/templates/{template_id}` - Modifier un modèle (RH, Admin)
- `DELETE /api/documents/templates/{template_id}` - Supprimer un modèle (Admin)

#### Types de documents (`/api/documents/types`)
- `POST /api/documents/types` - Créer un type (RH, Admin)
- `GET /api/documents/types` - Lister les types (RH, Admin)

### Formations (`/api/formations`)
- `GET /api/formations/` - Récupérer toutes les formations
- `GET /api/formations/rh/all` - Récupérer toutes les formations (RH, Admin)
- `POST /api/formations/` - Créer une formation (RH, Admin)
- `PUT /api/formations/{formation_id}` - Modifier une formation (RH, Admin)
- `DELETE /api/formations/{formation_id}` - Supprimer une formation (Admin)

### Contrats (`/api/contracts`)
- `GET /api/contracts/my-contract` - Récupérer mon contrat
- `GET /api/contracts/` - Récupérer tous les contrats (RH, Admin)
- `GET /api/contracts/employee/{user_id}` - Récupérer le contrat d'un employé (RH, Admin)
- `POST /api/contracts/` - Créer un contrat (RH, Admin)
- `PUT /api/contracts/{contract_id}` - Modifier un contrat (RH, Admin)
- `DELETE /api/contracts/{contract_id}` - Supprimer un contrat (Admin)

## 🗄️ Structure de la base de données

### Table users
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    mots_de_passe VARCHAR(255) NOT NULL,
    role ENUM('admin', 'collaborateur', 'direction', 'manager', 'rh') DEFAULT 'collaborateur',
    is_active BOOLEAN DEFAULT TRUE,
    first_login BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 📁 Structure du projet

```
ydays_back/
├── main.py                 # Application FastAPI principale
├── requirements.txt        # Dépendances Python
├── .env                    # Variables d'environnement
├── database/
│   ├── __init__.py
│   └── db.py              # Configuration de la base de données
├── models/
│   ├── __init__.py
│   └── user.py            # Modèle SQLAlchemy User
├── schemas/
│   ├── __init__.py
│   └── user.py            # Schémas Pydantic
├── api/
│   ├── __init__.py
│   ├── auth.py            # Routes d'authentification
│   ├── dashboard.py       # Routes des dashboards
│   └── users.py           # Routes des utilisateurs
└── core/
    ├── __init__.py
    └── security.py        # Fonctions de sécurité (JWT, hachage)
```

## 🧪 Exemple d'utilisation avec cURL

### 1. Admin crée un utilisateur
```bash
ADMIN_TOKEN="votre_token_admin_ici"

curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -d '{
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "mots_de_passe": "password123",
    "role": "collaborateur"
  }'
```

### 2. Connexion
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jean.dupont@example.com",
    "mots_de_passe": "password123"
  }'
```

### 3. Accès au dashboard
```bash
curl -X GET "http://localhost:8000/api/dashboard/home" \
  -H "Authorization: Bearer <access_token>"
```

### 4. Profil utilisateur
```bash
curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer <access_token>"
```

## 🔒 Contrôle d'accès par rôle

### Permissions par endpoint

### Permissions par endpoint

| Endpoint | Admin | Collaborateur | Direction | Manager | RH |
|----------|-------|---------------|-----------|---------|----| 
| POST /api/users/ (créer) | ✅ | ❌ | ❌ | ❌ | ❌ |
| GET /api/users/me | ✅ | ✅ | ✅ | ✅ | ❌ |
| PUT /api/users/me | ✅ | ❌ | ❌ | ❌ | ❌ |
| PUT /api/users/me/change-password | ✅ | ✅ | ✅ | ✅ | ✅ |
| GET /api/users/ (liste) | ✅ | ❌ | ❌ | ❌ | ✅ |
| GET /api/users/{id} | ✅ | ❌ | ❌ | ❌ | ✅ |
| PUT /api/users/{id} (modifier) | ✅ | ❌ | ❌ | ❌ | ❌ |
| DELETE /api/users/{id} | ✅ | ❌ | ❌ | ❌ | ❌ |
| /dashboard/admin | ✅ | ❌ | ❌ | ❌ | ❌ |
| /dashboard/collaborateur | ❌ | ✅ | ❌ | ❌ | ❌ |
| /dashboard/direction | ❌ | ❌ | ✅ | ❌ | ❌ |
| /dashboard/manager | ❌ | ❌ | ❌ | ✅ | ❌ |
| /dashboard/rh | ❌ | ❌ | ❌ | ❌ | ✅ |
| POST /api/leaves/ | ✅ | ✅ | ❌ | ✅ | ❌ |
| GET /api/leaves/my-leaves | ✅ | ✅ | ❌ | ✅ | ❌ |
| GET /api/leaves/team | ✅ | ❌ | ❌ | ✅ | ❌ |
| PUT /api/leaves/{id} (valider) | ✅ | ❌ | ❌ | ✅ | ❌ |
| PATCH /api/leaves/{id} (modifier) | ❌ | ✅† | ❌ | ✅† | ❌ |
| DELETE /api/leaves/{id} (annuler) | ❌ | ✅† | ❌ | ✅† | ❌ |
| GET /api/documents/my-documents | ✅ | ✅ | ✅ | ✅ | ❌ |
| GET /api/documents/{id}/download | ✅ | ✅ | ✅ | ✅ | ✅ |
| GET /api/documents/employee/{id} | ✅ | ❌ | ❌ | ❌ | ✅ |
| GET /api/documents/all | ✅ | ❌ | ❌ | ❌ | ✅ |
| POST /api/documents/manual | ✅ | ❌ | ❌ | ❌ | ✅ |
| POST /api/documents/generate | ✅ | ❌ | ❌ | ❌ | ✅ |
| PUT /api/documents/{id}/status | ✅ | ❌ | ❌ | ❌ | ✅ |
| GET /api/formations/ | ✅ | ✅ | ✅ | ✅ | ❌ |
| POST /api/formations/ | ✅ | ❌ | ❌ | ❌ | ✅ |
| GET /api/contracts/my-contract | ✅ | ✅ | ✅ | ✅ | ❌ |
| GET /api/contracts/ | ✅ | ❌ | ❌ | ❌ | ✅ |
| POST /api/contracts/ | ✅ | ❌ | ❌ | ❌ | ✅ |

### Rôles et responsabilités

**Admin** 🔑
- Création des utilisateurs
- Gestion complète (création, modification, suppression)
- Accès à tous les endpoints

**RH** 👥
- Consultation des profils des employés (ne peut plus les modifier)
- Accès à la liste complète des utilisateurs (collaborateurs uniquement)
- **NE PEUT PAS** créer de compte
- **NE PEUT PAS** modifier son propre profil ni celui des autres employés
- **NE PEUT PAS** supprimer des utilisateurs

**Autres rôles** (Collaborateur, Manager, Direction) 💼
- Consultation de leur propre profil uniquement (la modification est réservée à l'Admin)
- Accès à leurs dashboards respectifs

## 📝 Variables d'attributs User

- **id**: Identifiant unique (Integer, Primary Key)
- **nom**: Nom de famille (String, 100 caractères)
- **prenom**: Prénom (String, 100 caractères)
- **email**: Email unique (String, 255 caractères)
- **mots_de_passe**: Mot de passe hashé (String, 255 caractères)
- **role**: Rôle de l'utilisateur (Enum: admin, collaborateur, direction, manager, rh)
- **is_active**: Activation de compte (Boolean, défaut: True)
- **first_login**: Premier login (Boolean, défaut: True)
- **created_at**: Date de création (DateTime, défaut: now)

## 🆕 Nouvelles Fonctionnalités (v1.1.0)

### Gestion des Congés
Les employés et managers peuvent demander des congés, les managers peuvent approuver/rejeter les demandes.

### Gestion des Documents
Les RH et Admins peuvent gérer les documents des employés (contrats, bulletins, certificats, etc.)

### Gestion des Formations
Les RH peuvent créer et gérer les formations disponibles dans l'entreprise.

### Gestion des Contrats
Les RH gèrent les contrats des employés (CDI, CDD, Stages, etc.)

**Pour plus de détails sur ces fonctionnalités, voir [FEATURES.md](FEATURES.md)**

## 🚨 Erreurs courants

### 401 Unauthorized
- Token invalide ou expiré
- Header Authorization manquant ou mal formé

### 403 Forbidden
- L'utilisateur n'a pas les permissions requises
- Le compte est désactivé

### 404 Not Found
- Ressource non trouvée

## 📦 Production

Avant de déployer en production:

1. Changer la `SECRET_KEY` dans `.env`
2. Modifier `allow_origins` dans `main.py` avec vos domaines
3. Configurer une vraie base de données PostgreSQL
4. Mettre à jour `DATABASE_URL` dans `.env`
5. Désactiver `reload=True` dans uvicorn
6. Configurer HTTPS/SSL

## 👨‍💻 Support

Pour toute question ou problème, veuillez ouvrir une issue sur le projet.

## 📄 Licence

Projet YDAYS - Tous droits réservés
