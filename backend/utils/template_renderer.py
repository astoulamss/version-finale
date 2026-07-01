import re
from datetime import date


def render_template(content: str, variables: dict) -> str:
    """
    Remplace les variables {{nom_variable}} dans le contenu du template
    par les valeurs correspondantes du dictionnaire.
    Si une variable n'est pas trouvée, elle est conservée telle quelle.
    """
    def replacer(match):
        key = match.group(1).strip()
        value = variables.get(key)
        if value is None:
            return match.group(0)  # conserver le placeholder si non trouvé
        return str(value)

    return re.sub(r'\{\{(\w+)\}\}', replacer, content)


def build_employee_variables(user, employee=None, contract=None, extra_vars: dict = None) -> dict:
    """
    Construit le dictionnaire de variables pour le rendu d'un template.

    Variables disponibles :
    - first_name, last_name, current_date, company_name
    - position, department, hire_date, salary (si contract fourni)
    - manager_name (si employee avec manager fourni)
    - Toutes les clés de extra_vars (ex: start_date, end_date, duration)
    """
    variables = {
        "first_name": user.prenom or "",
        "last_name": user.nom or "",
        "current_date": date.today().strftime("%d/%m/%Y"),
        "company_name": "YDAYS",
    }

    if employee:
        if employee.position:
            variables["position"] = employee.position.title
        if employee.department:
            variables["department"] = employee.department.name
        if employee.manager:
            mgr = employee.manager
            variables["manager_name"] = f"{mgr.prenom} {mgr.nom}"

    if contract:
        variables.setdefault("position", contract.position or "")
        variables["salary"] = contract.salary or ""
        if contract.start_date:
            variables["hire_date"] = contract.start_date.strftime("%d/%m/%Y")

    if extra_vars:
        variables.update(extra_vars)

    return variables
