def generate_recommendations(features: dict, turnover_proba: float, burnout_proba: float, disengagement_proba: float) -> list:
    """
    Système Expert générant des recommandations RH actionnables
    basées sur les probabilités de risque et les features exactes de l'employé.
    """
    recommendations = []
    
    # Transformation en pourcentages
    t_risk = turnover_proba * 100
    b_risk = burnout_proba * 100
    d_risk = disengagement_proba * 100
    
    # --- RÈGLES POUR LE TURNOVER (DÉMISSION) ---
    if t_risk >= 55:
        if features.get("monthly_salary", 0) < 3000:
            recommendations.append({
                "type": "turnover",
                "severity": "high" if t_risk >= 75 else "medium",
                "title": "Révision salariale conseillée",
                "description": "Le salaire actuel est inférieur à la moyenne cible. Une revalorisation salariale pourrait réduire considérablement le risque de départ."
            })
        if features.get("distance_from_home_km", 0) > 20:
            recommendations.append({
                "type": "turnover",
                "severity": "high" if t_risk >= 75 else "medium",
                "title": "Aménagements de Télétravail",
                "description": "Le trajet quotidien est long (>20km). Proposer des jours de télétravail supplémentaires ou des horaires flexibles."
            })
            
    # --- RÈGLES POUR LE BURNOUT ---
    if b_risk >= 55:
        if features.get("overtime") == "Yes":
            recommendations.append({
                "type": "burnout",
                "severity": "high" if b_risk >= 75 else "medium",
                "title": "Alerte Surcharge de Travail",
                "description": "L'employé accumule les heures supplémentaires. Il est urgent d'alléger sa charge ou d'imposer des jours de récupération."
            })
        if features.get("sick_leave_days_last_year", 0) > 10:
            recommendations.append({
                "type": "burnout",
                "severity": "high" if b_risk >= 75 else "medium",
                "title": "Suivi Santé / Médecine du travail",
                "description": "Le taux d'absence maladie est déjà élevé. Planifiez un point préventif avec la médecine du travail ou un suivi bien-être."
            })
            
    # --- RÈGLES POUR LE DÉSENGAGEMENT ---
    if d_risk >= 55:
        if features.get("training_times_last_year", 0) < 2:
            recommendations.append({
                "type": "disengagement",
                "severity": "high" if d_risk >= 75 else "medium",
                "title": "Plan de Formation",
                "description": "Aucune formation récente. Proposez un parcours de montée en compétences pour relancer l'intérêt intellectuel et la motivation."
            })
        if features.get("tenure_in_years", 0) > 3 and features.get("performance_rating", 0) >= 3:
            recommendations.append({
                "type": "disengagement",
                "severity": "high" if d_risk >= 75 else "medium",
                "title": "Perspectives d'Évolution",
                "description": "Employé ancien et performant mais potentiellement ennuyé. Envisagez une promotion ou un changement de missions transverses."
            })

    # Si aucun risque majeur n'a déclenché de recommandation
    if not recommendations and (t_risk >= 55 or b_risk >= 55 or d_risk >= 55):
        recommendations.append({
            "type": "general",
            "severity": "medium",
            "title": "Entretien de Suivi",
            "description": "Des signaux faibles sont détectés. Planifiez un point informel ('One-on-One') pour comprendre les attentes de l'employé."
        })
        
    if not recommendations:
        recommendations.append({
            "type": "success",
            "severity": "low",
            "title": "Indicateurs au Vert",
            "description": "Aucun risque majeur détecté. Continuez à maintenir les bonnes pratiques de management actuelles."
        })

    return recommendations
