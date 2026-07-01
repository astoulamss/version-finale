# YDAYS 2026 - Plateforme IA RH

Prototype mobile Expo + React Native d'une application RH intelligente pour collaborateurs. Le projet ne contient pas de backend : toutes les donnees, reponses IA et workflows sont simules cote frontend pour concentrer le developpement sur l'experience mobile.

## Fonctionnalites implementees

- Flow d'authentification mobile : splash, connexion, OTP, premiere connexion et verification profil.
- Dashboard collaborateur : profil, assistant IA central, stats RH, actions rapides, documents recents, onboarding et notifications.
- Assistant IA RH conversationnel : messages collaborateur/IA, suggestions, input vocal simule, upload simule, clarification, refus confidentialite, escalade RH, erreur reseau et typing state.
- Documents RH automatises : categories, generation en 4 etapes, pre-remplissage IA, edition, detection de champs manquants, timeline de validation et historique.
- Onboarding J1-J30 : progression, semaines 1 a 4, taches, detail tache, ressources, contacts, alertes retard, recommandations IA et preview succes J30.
- Centre de notifications : filtres, priorites, badges non lus et action "marquer comme lu".
- Profil & parametres : profil RH, langue, dark mode, notifications, biometrie, securite et confidentialite IA.
- Design system mobile : cartes, boutons, chips, badges, bottom navigation, modals, dropdown, skeleton loading, empty states, error states et mode clair/sombre.

## Stack

- Expo SDK 54
- React Native 0.81
- React 19.1
- TypeScript
- Vitest pour la logique IA locale

## Lancer le prototype

```powershell
npm install
npm start
```

`npm start` lance Expo en mode LAN. Pour tester sur telephone, installez **Expo Go**, mettez le telephone sur le meme Wi-Fi que l'ordinateur, puis ouvrez :

```text
exp://192.168.8.228:8081
```

Important : `http://127.0.0.1:8081` est le serveur Metro. Ce n'est pas une page web de l'application, donc l'interface mobile ne s'affiche pas dans le navigateur.

Si le telephone ne se connecte pas en LAN, utilisez le tunnel Expo :

```powershell
npm run start:tunnel
```

Pour un simulateur Android/iOS :

```powershell
npm run android
npm run ios
```

Pour limiter Expo a la machine locale :

```powershell
npm run start:local
```

## Validation

```powershell
npm run typecheck
npm run build
npm test
npx expo-doctor
npm audit --audit-level=moderate
```

## Architecture

- `src/App.tsx` : interface mobile complete, navigation, ecrans, modals et composants UI reutilisables.
- `src/data/hrData.ts` : donnees collaborateur, documents, onboarding, notifications et permissions IA.
- `src/lib/aiEngine.ts` : logique IA locale, generation de reponses, permissions, escalade RH, documents et onboarding.
- `src/types.ts` : types produit partages.

## Limites assumees

- Aucun backend, aucune authentification reelle et aucune persistance distante.
- Les actions vocales, upload, biometrie, haptique, telechargement et synchronisation RH sont simulees dans le frontend.
- Les donnees RH sont fictives et servent a rendre les parcours developpables.
