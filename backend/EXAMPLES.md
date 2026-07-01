# YDAYS API - Exemples d'utilisation

## 📋 Table des matières
1. [Installation et Lancement](#installation-et-lancement)
2. [Authentification](#authentification)
3. [Dashboards](#dashboards)
4. [Gestion des utilisateurs](#gestion-des-utilisateurs)

---

## Installation et Lancement

### Option 1: Installation locale

```bash
# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Créer l'administrateur
python create_admin.py

# Lancer l'API
python main.py
```

L'API sera disponible sur: `http://localhost:8000`

### Option 2: Avec Docker

```bash
# Construire et lancer avec Docker Compose
docker-compose up -d

# Vérifier que tout fonctionne
curl http://localhost:8000/health
```

---

## Authentification

### 1. Créer un nouvel utilisateur (Admin/RH uniquement)

#### cURL
```bash
TOKEN="votre_token_admin_ici"

curl -X POST "http://localhost:8000/api/users/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "Dupont",
    "prenom": "Jean",
    "email": "jean.dupont@example.com",
    "mots_de_passe": "password123",
    "role": "collaborateur"
  }'
```

#### Python
```python
import requests

admin_token = "votre_token_admin_ici"
headers = {"Authorization": f"Bearer {admin_token}"}

response = requests.post(
    "http://localhost:8000/api/users/",
    json={
        "nom": "Dupont",
        "prenom": "Jean",
        "email": "jean.dupont@example.com",
        "mots_de_passe": "password123",
        "role": "collaborateur"
    },
    headers=headers
)

print(response.json())
```

### 2. Se connecter

#### cURL
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jean.dupont@example.com",
    "mots_de_passe": "password123"
  }'
```

#### Python
```python
import requests

response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={
        "email": "jean.dupont@example.com",
        "mots_de_passe": "password123"
    }
)

data = response.json()
access_token = data["access_token"]
print(f"Token reçu: {access_token}")
```

**Réponse:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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

---

## Dashboards

Après authentification, l'utilisateur est redirigé vers son dashboard selon son rôle.

### 1. Redirection automatique

#### cURL
```bash
TOKEN="votre_token_ici"

curl -X GET "http://localhost:8000/api/dashboard/home" \
  -H "Authorization: Bearer $TOKEN"
```

#### Python
```python
import requests

token = "votre_token_ici"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/api/dashboard/home",
    headers=headers
)

print(response.json())
```

**Réponse pour un collaborateur:**
```json
{
  "role": "collaborateur",
  "user_name": "Jean Dupont",
  "first_login": false,
  "message": "Bienvenue sur votre dashboard. Vous pouvez consulter vos tâches et projets."
}
```

### 2. Accès aux dashboards spécifiques

#### Dashboard Admin
```bash
curl -X GET "http://localhost:8000/api/dashboard/admin" \
  -H "Authorization: Bearer $TOKEN"
```

#### Dashboard Collaborateur
```bash
curl -X GET "http://localhost:8000/api/dashboard/collaborateur" \
  -H "Authorization: Bearer $TOKEN"
```

#### Dashboard Manager
```bash
curl -X GET "http://localhost:8000/api/dashboard/manager" \
  -H "Authorization: Bearer $TOKEN"
```

#### Dashboard RH
```bash
curl -X GET "http://localhost:8000/api/dashboard/rh" \
  -H "Authorization: Bearer $TOKEN"
```

#### Dashboard Direction
```bash
curl -X GET "http://localhost:8000/api/dashboard/direction" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Gestion des utilisateurs

### 1. Récupérer le profil de l'utilisateur connecté

#### cURL
```bash
TOKEN="votre_token_ici"

curl -X GET "http://localhost:8000/api/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

#### Python
```python
import requests

token = "votre_token_ici"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/api/users/me",
    headers=headers
)

print(response.json())
```

### 2. Modifier son profil

#### cURL
```bash
TOKEN="votre_token_ici"

curl -X PUT "http://localhost:8000/api/users/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "nom": "DupontModifié",
    "prenom": "Jean"
  }'
```

#### Python
```python
import requests

token = "votre_token_ici"
headers = {"Authorization": f"Bearer {token}"}

response = requests.put(
    "http://localhost:8000/api/users/me",
    json={
        "nom": "DupontModifié",
        "prenom": "Jean"
    },
    headers=headers
)

print(response.json())
```

### 3. Lister tous les utilisateurs (Admin et RH seulement)

#### cURL
```bash
TOKEN="token_admin_ou_rh"

curl -X GET "http://localhost:8000/api/users/" \
  -H "Authorization: Bearer $TOKEN"
```

#### Python
```python
import requests

token = "token_admin_ou_rh"
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    "http://localhost:8000/api/users/",
    headers=headers
)

print(response.json())
```

### 4. Obtenir les détails d'un utilisateur

#### cURL
```bash
TOKEN="votre_token_ici"
USER_ID=1

curl -X GET "http://localhost:8000/api/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### Python
```python
import requests

token = "votre_token_ici"
user_id = 1
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    f"http://localhost:8000/api/users/{user_id}",
    headers=headers
)

print(response.json())
```

### 5. Modifier un utilisateur (Admin et RH seulement)

#### cURL
```bash
TOKEN="token_admin_ou_rh"
USER_ID=1

curl -X PUT "http://localhost:8000/api/users/$USER_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "role": "manager",
    "is_active": true
  }'
```

#### Python
```python
import requests

token = "token_admin_ou_rh"
user_id = 1
headers = {"Authorization": f"Bearer {token}"}

response = requests.put(
    f"http://localhost:8000/api/users/{user_id}",
    json={
        "role": "manager",
        "is_active": True
    },
    headers=headers
)

print(response.json())
```

### 6. Désactiver un utilisateur (Admin seulement)

#### cURL
```bash
TOKEN="token_admin"
USER_ID=1

curl -X DELETE "http://localhost:8000/api/users/$USER_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### Python
```python
import requests

token = "token_admin"
user_id = 1
headers = {"Authorization": f"Bearer {token}"}

response = requests.delete(
    f"http://localhost:8000/api/users/{user_id}",
    headers=headers
)

print(f"Status: {response.status_code}")
```

---

## 🧪 Script de test complet

Exécuter le script de test:

```bash
# Assurez-vous que l'API est lancée
python main.py

# Dans un autre terminal
python test_api.py
```

---

## 📊 Flux d'authentification

```
┌─────────────┐
│   Utilisateur  │
└──────┬──────┘
       │
       ├─► 1. POST /auth/register (créer un compte)
       │        ↓
       │     ✓ Compte créé
       │
       ├─► 2. POST /auth/login (se connecter)
       │        ↓
       │     ✓ JWT Token reçu
       │
       ├─► 3. GET /dashboard/home (accès au dashboard)
       │    (+ Header: Authorization: Bearer <token>)
       │        ↓
       │     ✓ Redirection vers dashboard selon rôle
       │
       └─► 4. GET /users/me (profil utilisateur)
            (+ Header: Authorization: Bearer <token>)
                 ↓
              ✓ Profil récupéré
```

---

## 🔐 Sécurité

- Les mots de passe sont hashés avec bcrypt
- Les tokens JWT expirent après 30 minutes (configurable)
- Les endpoints sont protégés par rôle
- HTTPS recommandé en production

---

## 📝 Codes de réponse HTTP

| Code | Signification |
|------|---------------|
| 200 | Succès |
| 201 | Ressource créée |
| 204 | Succès (pas de contenu) |
| 400 | Mauvaise requête |
| 401 | Non authentifié |
| 403 | Non autorisé |
| 404 | Non trouvé |
| 500 | Erreur serveur |

---

## 📞 Support

Pour toute question, consultez la documentation Swagger:
`http://localhost:8000/docs`
