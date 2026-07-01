"""
Service d'envoi d'emails via SMTP (fastapi-mail)
"""

import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from dotenv import load_dotenv

load_dotenv()

# Configuration de la connexion SMTP lue depuis le .env
mail_username = os.getenv("MAIL_USERNAME", "")
mail_password = os.getenv("MAIL_PASSWORD", "")
use_credentials = bool(mail_username and mail_password)

conf = ConnectionConfig(
    MAIL_USERNAME=mail_username,
    MAIL_PASSWORD=mail_password,
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@ydays.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Ydays RH"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 1025)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "mailhog"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "False").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False").lower() == "true",
    USE_CREDENTIALS=use_credentials,
    VALIDATE_CERTS=False,
)

fm = FastMail(conf)


def _build_welcome_html(prenom: str, nom: str, email: str, password: str, role: str) -> str:
    """Génère le template HTML du mail de bienvenue."""
    role_labels = {
        "admin": "Administrateur",
        "collaborateur": "Collaborateur",
        "manager": "Manager",
        "rh": "Ressources Humaines",
        "direction": "Direction",
        "medecine_travail": "Médecine du Travail",
    }
    role_display = role_labels.get(role, role.capitalize())

    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Bienvenue sur Ydays</title>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f172a;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
                      border-radius:16px;border:1px solid #334155;
                      box-shadow:0 20px 60px rgba(0,0,0,0.5);overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%);
                       padding:40px 48px;text-align:center;">
              <div style="font-size:36px;font-weight:900;color:#ffffff;letter-spacing:-1px;">
                Ydays
              </div>
              <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:4px;letter-spacing:2px;text-transform:uppercase;">
                Plateforme RH
              </div>
            </td>
          </tr>

          <!-- Greeting -->
          <tr>
            <td style="padding:40px 48px 24px;">
              <h1 style="color:#f8fafc;font-size:24px;font-weight:700;margin:0 0 8px;">
                Bienvenue, {prenom} ! 👋
              </h1>
              <p style="color:#94a3b8;font-size:15px;line-height:1.6;margin:0;">
                Votre compte a été créé par l'administrateur Ydays.
                Voici vos identifiants de connexion :
              </p>
            </td>
          </tr>

          <!-- Credentials box -->
          <tr>
            <td style="padding:0 48px 32px;">
              <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;
                          padding:28px 32px;border-left:4px solid #6366f1;">
                <table width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding-bottom:16px;">
                      <div style="color:#64748b;font-size:11px;font-weight:600;
                                  text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
                        Rôle
                      </div>
                      <div style="color:#a78bfa;font-size:15px;font-weight:600;">
                        {role_display}
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding-bottom:16px;border-top:1px solid #334155;padding-top:16px;">
                      <div style="color:#64748b;font-size:11px;font-weight:600;
                                  text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
                        Adresse e-mail
                      </div>
                      <div style="color:#f8fafc;font-size:15px;font-family:monospace;">
                        {email}
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td style="border-top:1px solid #334155;padding-top:16px;">
                      <div style="color:#64748b;font-size:11px;font-weight:600;
                                  text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
                        Mot de passe temporaire
                      </div>
                      <div style="color:#f8fafc;font-size:18px;font-family:monospace;
                                  font-weight:700;letter-spacing:2px;
                                  background:#0f172a;border-radius:8px;
                                  padding:10px 16px;display:inline-block;margin-top:4px;">
                        {password}
                      </div>
                    </td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>

          <!-- Warning -->
          <tr>
            <td style="padding:0 48px 32px;">
              <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
                          border-radius:10px;padding:16px 20px;display:flex;align-items:flex-start;">
                <span style="font-size:18px;margin-right:10px;">⚠️</span>
                <span style="color:#fcd34d;font-size:13px;line-height:1.5;">
                  Pour votre sécurité, veuillez <strong>changer votre mot de passe</strong>
                  dès votre première connexion.
                </span>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#0f172a;padding:24px 48px;text-align:center;
                       border-top:1px solid #1e293b;">
              <p style="color:#475569;font-size:12px;margin:0;">
                Cet email a été envoyé automatiquement par la plateforme Ydays.<br/>
                Ne répondez pas à cet email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_welcome_email(prenom: str, nom: str, email: str, password: str, role: str) -> bool:
    """
    Envoie un email de bienvenue avec les identifiants de connexion.
    Retourne True si l'envoi a réussi, False sinon (sans bloquer la création).
    """
    try:
        html_content = _build_welcome_html(prenom, nom, email, password, role)

        message = MessageSchema(
            subject=f"Bienvenue sur Ydays – Vos identifiants de connexion",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html,
        )

        await fm.send_message(message)
        print(f"[EMAIL] ✅ Email de bienvenue envoyé à {email}")
        return True

    except Exception as e:
        # On log l'erreur mais on ne bloque pas la création de l'utilisateur
        print(f"[EMAIL] ❌ Échec de l'envoi à {email}: {e}")
        return False


def _build_reset_password_html(prenom: str, nom: str, email: str, password: str) -> str:
    """Génère le template HTML du mail de réinitialisation de mot de passe."""
    return f"""
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Réinitialisation de votre mot de passe</title>
</head>
<body style="margin:0;padding:0;background-color:#0f172a;font-family:'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0f172a;padding:40px 20px;">
    <tr>
      <td align="center">
        <table width="600" cellpadding="0" cellspacing="0"
               style="background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);
                      border-radius:16px;border:1px solid #334155;
                      box-shadow:0 20px 60px rgba(0,0,0,0.5);overflow:hidden;">

          <!-- Header -->
          <tr>
            <td style="background:linear-gradient(135deg,#6366f1 0%,#8b5cf6 100%);
                       padding:40px 48px;text-align:center;">
              <div style="font-size:36px;font-weight:900;color:#ffffff;letter-spacing:-1px;">
                Ydays
              </div>
              <div style="font-size:13px;color:rgba(255,255,255,0.75);margin-top:4px;letter-spacing:2px;text-transform:uppercase;">
                Sécurité Compte
              </div>
            </td>
          </tr>

          <!-- Greeting -->
          <tr>
            <td style="padding:40px 48px 24px;">
              <h1 style="color:#f8fafc;font-size:24px;font-weight:700;margin:0 0 8px;">
                Bonjour, {prenom} ! 👋
              </h1>
              <p style="color:#94a3b8;font-size:15px;line-height:1.6;margin:0;">
                Votre mot de passe a été réinitialisé par l'administrateur Ydays.
                Voici vos nouveaux identifiants temporaires de connexion :
              </p>
            </td>
          </tr>

          <!-- Credentials box -->
          <tr>
            <td style="padding:0 48px 32px;">
              <div style="background:#1e293b;border:1px solid #334155;border-radius:12px;
                          padding:28px 32px;border-left:4px solid #f59e0b;">
                <table width="100%" cellpadding="0" cellspacing="0">
                  <tr>
                    <td style="padding-bottom:16px;">
                      <div style="color:#64748b;font-size:11px;font-weight:600;
                                  text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
                        Adresse e-mail
                      </div>
                      <div style="color:#f8fafc;font-size:15px;font-family:monospace;">
                        {email}
                      </div>
                    </td>
                  </tr>
                  <tr>
                    <td style="border-top:1px solid #334155;padding-top:16px;">
                      <div style="color:#64748b;font-size:11px;font-weight:600;
                                  text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;">
                        Nouveau mot de passe temporaire
                      </div>
                      <div style="color:#f8fafc;font-size:18px;font-family:monospace;
                                  font-weight:700;letter-spacing:2px;
                                  background:#0f172a;border-radius:8px;
                                  padding:10px 16px;display:inline-block;margin-top:4px;">
                        {password}
                      </div>
                    </td>
                  </tr>
                </table>
              </div>
            </td>
          </tr>

          <!-- Warning -->
          <tr>
            <td style="padding:0 48px 32px;">
              <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);
                          border-radius:10px;padding:16px 20px;display:flex;align-items:flex-start;">
                <span style="font-size:18px;margin-right:10px;">⚠️</span>
                <span style="color:#fcd34d;font-size:13px;line-height:1.5;">
                  Pour votre sécurité, vous devrez <strong>changer ce mot de passe temporaire</strong>
                  immédiatement lors de votre prochaine connexion.
                </span>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#0f172a;padding:24px 48px;text-align:center;
                       border-top:1px solid #1e293b;">
              <p style="color:#475569;font-size:12px;margin:0;">
                Cet email a été envoyé automatiquement par la plateforme Ydays.<br/>
                Ne répondez pas à cet email.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""


async def send_reset_password_email(prenom: str, nom: str, email: str, password: str) -> bool:
    """
    Envoie un email de réinitialisation avec le nouveau mot de passe temporaire.
    Retourne True si l'envoi a réussi, False sinon.
    """
    try:
        html_content = _build_reset_password_html(prenom, nom, email, password)

        message = MessageSchema(
            subject="Ydays – Réinitialisation de votre mot de passe",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html,
        )

        await fm.send_message(message)
        print(f"[EMAIL] ✅ Email de réinitialisation envoyé à {email}")
        return True

    except Exception as e:
        print(f"[EMAIL] ❌ Échec de l'envoi de réinitialisation à {email}: {e}")
        return False

