import requests

base_url = "http://localhost:8000"
email = "jean@example.com"
password = "YDAYS2026!"

def run_tests():
    print("--- DEBUT DE L'AUDIT COMPLET COLLABORATEUR ---")
    
    # 1. AUTHENTIFICATION
    print("\n1. Test d'Authentification...")
    resp = requests.post(f"{base_url}/api/auth/login", json={"email": email, "mots_de_passe": password})
    if resp.status_code != 200:
        print(f"[ECHEC] AUTH: {resp.text}")
        return
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    print(f"[OK] Authentification reussie pour {email}")
    
    # 2. PROFIL UTILISATEUR
    print("\n2. Test Profil Utilisateur...")
    resp = requests.get(f"{base_url}/api/users/me", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Profil recupere: {resp.json().get('prenom')} {resp.json().get('nom')}")
    else:
        print(f"[ECHEC] Profil: {resp.status_code} - {resp.text}")
        
    # 3. ANNONCES / DASHBOARD
    print("\n3. Test Annonces Entreprise...")
    resp = requests.get(f"{base_url}/api/announcements", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Annonces recuperees ({len(resp.json())} annonces trouvees)")
    else:
        print(f"[ECHEC] Annonces: {resp.status_code} - {resp.text}")

    # 4. SOLDES DE CONGES
    print("\n4. Test Soldes de Conges...")
    resp = requests.get(f"{base_url}/api/leaves/balances/me", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Soldes recuperes ({len(resp.json())} types de conges trouves)")
    else:
        print(f"[ECHEC] Soldes: {resp.status_code} - {resp.text}")

    # 5. HISTORIQUE DES CONGES
    print("\n5. Test Historique des Conges...")
    resp = requests.get(f"{base_url}/api/leaves/my-leaves", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Historique des conges recupere ({len(resp.json())} demandes trouvees)")
    else:
        print(f"[ECHEC] Historique Conges: {resp.status_code} - {resp.text}")

    # 6. DOCUMENTS
    print("\n6. Test Documents Personnels...")
    resp = requests.get(f"{base_url}/api/documents/my", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Documents recuperes ({len(resp.json())} documents trouves)")
    else:
        print(f"[ECHEC] Documents: {resp.status_code} - {resp.text}")

    # 7. FORMATIONS
    print("\n7. Test Formations (Catalogue)...")
    resp = requests.get(f"{base_url}/api/formations", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Catalogue de formations recupere ({len(resp.json())} formations trouvees)")
    else:
        print(f"[ECHEC] Formations: {resp.status_code} - {resp.text}")

    # 8. TACHES / TO-DO
    print("\n8. Test Taches Assignees (My Tasks)...")
    resp = requests.get(f"{base_url}/api/my-tasks", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Taches recuperees ({len(resp.json())} taches assignees)")
    else:
        print(f"[ECHEC] Taches: {resp.status_code} - {resp.text}")

    # 9. NOTIFICATIONS
    print("\n9. Test Notifications...")
    resp = requests.get(f"{base_url}/api/notifications", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Notifications recuperees ({len(resp.json())} trouvees)")
    else:
        print(f"[ECHEC] Notifications: {resp.status_code} - {resp.text}")

    # 10. FEUILLES DE TEMPS (TIMESHEET)
    print("\n10. Test Feuilles de Temps...")
    resp = requests.get(f"{base_url}/api/timesheet/my-timesheets", headers=headers)
    if resp.status_code == 200:
        print(f"[OK] Feuilles de temps recuperees ({len(resp.json())} trouvees)")
    else:
        print(f"[ECHEC] Feuilles de Temps: {resp.status_code} - {resp.text}")
        
    print("\n--- FIN DE L'AUDIT ---")

if __name__ == "__main__":
    run_tests()
