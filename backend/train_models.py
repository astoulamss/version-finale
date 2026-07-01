"""
train_models.py — Version Production NexCore RH
Améliorations implémentées :
  - StratifiedKFold pour la CV (respect de l'équilibre des classes)
  - CV sur X_train uniquement (pas de data leakage)
  - Fonction générique train_model() (refactoring)
  - Seuils métier RH (LOW / MEDIUM / HIGH RISK)
  - predict_proba() pour les probabilités réelles
  - Feature importance avec avertissement sur les biais OHE
"""

import pandas as pd
import joblib
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import accuracy_score, classification_report

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION DES SEUILS METIER RH
# ─────────────────────────────────────────────────────────────────────────────
RISK_THRESHOLDS = {
    "LOW":    0.30,   # < 30%  → Pas d'alerte
    "MEDIUM": 0.55,   # 30-55% → Surveillance recommandée
    "HIGH":   0.75,   # > 75%  → Action RH requise
}

def classify_risk(probability: float) -> str:
    """Convertit une probabilite brute en niveau de risque metier RH."""
    if probability >= RISK_THRESHOLDS["HIGH"]:
        return "HIGH RISK   => Action RH urgente requise"
    elif probability >= RISK_THRESHOLDS["MEDIUM"]:
        return "MEDIUM RISK => Surveillance recommandee"
    else:
        return "LOW RISK    => Pas d'alerte"


# ─────────────────────────────────────────────────────────────────────────────
# PIPELINE DE PREPARATION DES DONNEES
# ─────────────────────────────────────────────────────────────────────────────
def build_preprocessor(numeric_features, categorical_features):
    return ColumnTransformer(transformers=[
        ('num', StandardScaler(), numeric_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical_features)
    ])


# ─────────────────────────────────────────────────────────────────────────────
# FONCTION GENERIQUE D'ENTRAINEMENT (refactoring pro)
# ─────────────────────────────────────────────────────────────────────────────
def build_model(preprocessor):
    """Construit un Pipeline RandomForest avec gestion du déséquilibre."""
    return Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=42
        ))
    ])


def train_model(preprocessor, X_train, y_train):
    """Entraîne et retourne un modèle générique."""
    model = build_model(preprocessor)
    model.fit(X_train, y_train)
    return model


def evaluate_model(model, X_train, y_train, X_test, y_test, label, target_names, preprocessor):
    """Évalue un modèle avec métriques complètes et cross-validation correcte."""
    print("\n" + "=" * 60)
    print(f"MODELE : {label}")
    print("=" * 60)

    # Prédictions sur le test set
    preds = model.predict(X_test)
    probas = model.predict_proba(X_test)[:, 1]  # probabilité classe positive

    acc = accuracy_score(y_test, preds)
    print(f"Accuracy : {acc*100:.1f}%\n")
    print(classification_report(y_test, preds, zero_division=0, target_names=target_names))

    # --- Validation croisée CORRECTE ---
    # CV sur X_train uniquement (pas de data leakage)
    # StratifiedKFold pour préserver la proportion des classes dans chaque fold
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_model = build_model(preprocessor)
    cv_scores = cross_val_score(cv_model, X_train, y_train, cv=cv, scoring="f1")
    print(f"Cross-Validation StratifiedKFold (5 folds sur Train) :")
    print(f"  F1 moyen = {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")

    # --- Démonstration des seuils métier RH (sur 5 exemples du test) ---
    print(f"\nExemples de predictions avec seuils metier RH (5 premiers du test set) :")
    for i, (prob, actual) in enumerate(zip(probas[:5], y_test.values[:5])):
        risk_level = classify_risk(prob)
        print(f"  Employe #{i+1}: Proba={prob:.2%} | Reel={'OUI' if actual==1 else 'NON':3s} | {risk_level}")

    return model


def print_feature_importance(model, numeric_features, categorical_features):
    """Affiche l'importance des features avec avertissement sur les biais."""
    print("\n--- Top 5 variables (ATTENTION : biais possible avec OHE) ---")
    print("    Note : SHAP serait plus fiable pour l'explicabilite finale.")
    rf = model.named_steps['classifier']
    ohe_cats = model.named_steps['preprocessor'].named_transformers_['cat'].get_feature_names_out(categorical_features)
    all_features = numeric_features + list(ohe_cats)
    importances = pd.Series(rf.feature_importances_, index=all_features)
    top5 = importances.sort_values(ascending=False).head(5)
    for feat, score in top5.items():
        print(f"  {feat:40s} {score:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def train_and_save_models(data_path="c:/ydays_back/employees_ml_dataset.csv"):
    print("=" * 60)
    print("CHARGEMENT ET PREPARATION DES DONNEES")
    print("=" * 60)
    df = pd.read_csv(data_path)

    # Anti-discrimination : retrait age, genre et ID
    columns_to_drop = ["employee_id", "age", "gender"]
    print(f"Colonnes supprimees (anti-discrimination) : {columns_to_drop}")

    X_base = df.drop(columns=columns_to_drop + ["target_turnover", "target_burnout", "target_disengagement"])
    Y = df[["target_turnover", "target_burnout", "target_disengagement"]]

    print(f"\nDistribution des cibles dans le dataset complet :")
    for col in Y.columns:
        pos = Y[col].sum()
        print(f"  {col}: {pos} positifs ({pos/len(Y)*100:.1f}%)")

    # Split unique et coherent (garantit l'alignement des 3 targets)
    X_train, X_test, Y_train, Y_test = train_test_split(
        X_base, Y, test_size=0.2, random_state=42, stratify=Y["target_turnover"]
    )
    print(f"\nTrain : {len(X_train)} lignes | Test : {len(X_test)} lignes")

    # Features
    categorical_features = ["department", "job_role", "overtime"]
    numeric_features = [col for col in X_base.columns if col not in categorical_features]
    preprocessor = build_preprocessor(numeric_features, categorical_features)

    # ── Modele 1 : TURNOVER ───────────────────────────────────────
    y_turnover_train = Y_train["target_turnover"]
    y_turnover_test  = Y_test["target_turnover"]
    model_turnover = train_model(preprocessor, X_train, y_turnover_train)
    model_turnover = evaluate_model(
        model_turnover, X_train, y_turnover_train, X_test, y_turnover_test,
        "TURNOVER (DEMISSION)", ["Reste (0)", "Demissionne (1)"], preprocessor
    )
    print_feature_importance(model_turnover, numeric_features, categorical_features)
    joblib.dump(model_turnover, "c:/ydays_back/model_turnover.pkl")
    print("[OK] model_turnover.pkl sauvegarde")

    # ── Modele 2 : BURNOUT ────────────────────────────────────────
    y_burnout_train = Y_train["target_burnout"]
    y_burnout_test  = Y_test["target_burnout"]
    model_burnout = train_model(preprocessor, X_train, y_burnout_train)
    model_burnout = evaluate_model(
        model_burnout, X_train, y_burnout_train, X_test, y_burnout_test,
        "BURNOUT (EPUISEMENT)", ["Pas de Burnout (0)", "Burnout (1)"], preprocessor
    )
    print_feature_importance(model_burnout, numeric_features, categorical_features)
    joblib.dump(model_burnout, "c:/ydays_back/model_burnout.pkl")
    print("[OK] model_burnout.pkl sauvegarde")

    # ── Modele 3 : DISENGAGEMENT ──────────────────────────────────
    y_diseng_train = Y_train["target_disengagement"]
    y_diseng_test  = Y_test["target_disengagement"]
    model_disengagement = train_model(preprocessor, X_train, y_diseng_train)
    model_disengagement = evaluate_model(
        model_disengagement, X_train, y_diseng_train, X_test, y_diseng_test,
        "DISENGAGEMENT (QUIET QUITTING)", ["Engage (0)", "Desengagement (1)"], preprocessor
    )
    print_feature_importance(model_disengagement, numeric_features, categorical_features)
    joblib.dump(model_disengagement, "c:/ydays_back/model_disengagement.pkl")
    print("[OK] model_disengagement.pkl sauvegarde")

    print("\n" + "=" * 60)
    print("Tout est pret ! Les 3 cerveaux sont crees et sauvegardes.")
    print("Seuils metier RH configures :")
    print(f"  LOW    : proba < {RISK_THRESHOLDS['LOW']*100:.0f}%")
    print(f"  MEDIUM : proba {RISK_THRESHOLDS['LOW']*100:.0f}% - {RISK_THRESHOLDS['HIGH']*100:.0f}%")
    print(f"  HIGH   : proba >= {RISK_THRESHOLDS['HIGH']*100:.0f}%")
    print("=" * 60)


if __name__ == "__main__":
    train_and_save_models()
