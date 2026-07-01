# Force UTF-8 encoding before any PostgreSQL connection
import os
import sys
os.environ['PYTHONUTF8'] = '1'
os.environ['PGCLIENTENCODING'] = 'UTF8'
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Hot-reload test comment triggered by audit
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from core.cache import init_redis, close_redis
from core.scheduler import start_scheduler, stop_scheduler
from database.db import Base, engine, SessionLocal
from api import auth, dashboard, users, leaves, documents, formations, contracts, employees, absences, history, notifications, chatbot, onboarding, offboarding, surveys, tickets, analytics_hr, alerts, manager_tasks, my_tasks, timesheet, performance_review, ml_predict, audit, knowledge_admin, workflows, announcements, system_alerts as system_alerts_api, team_risks
from ai.routers import ai as ai_router
from models import user, features, employees as employees_models, absences as absences_models, history as history_models, notification as notification_models, chatbot as chatbot_models, ml_features, audit_log, knowledge_document, system_alerts, announcement as announcement_models
from models.system_alerts import SystemAlert, SystemAlertStatusEnum
import traceback
# Créer les tables dans la base de données
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Connection to database failed. Tables not created: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    redis_client = await init_redis()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")
    start_scheduler()
    yield
    # Arrêt
    stop_scheduler()
    await close_redis()

# Créer l'application FastAPI
app = FastAPI(
    title="YDAYS API",
    description="API pour la gestion des utilisateurs avec authentification par rôles",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log exception in system_alerts
    db = SessionLocal()
    try:
        error_type = type(exc).__name__
        details = f"Path: {request.url.path}\nMethod: {request.method}\nDetails: {str(exc)}\nTraceback: {traceback.format_exc()[-1000:]}"
        
        alert = SystemAlert(
            title=f"Erreur Interne ({error_type})",
            description=details,
            severity="CRITICAL",
            status=SystemAlertStatusEnum.NEW
        )
        db.add(alert)
        db.commit()
    except Exception as db_exc:
        print(f"Failed to save system alert: {db_exc}")
    finally:
        db.close()
        
    return JSONResponse(
        status_code=500,
        content={"message": "Une erreur critique s'est produite sur le serveur. Les administrateurs ont été notifiés."}
    )

# Inclure les routes
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(leaves.router)
app.include_router(documents.router)
app.include_router(formations.router)
app.include_router(contracts.router)
app.include_router(employees.router)
app.include_router(absences.router)
app.include_router(history.router)
app.include_router(notifications.router)
app.include_router(chatbot.router)
app.include_router(onboarding.router)
app.include_router(offboarding.router)
app.include_router(surveys.router)
app.include_router(tickets.router)
app.include_router(analytics_hr.router)
app.include_router(alerts.router)
app.include_router(team_risks.router)
app.include_router(manager_tasks.router)
app.include_router(my_tasks.router)
app.include_router(timesheet.router)
app.include_router(performance_review.router)
app.include_router(ml_predict.router)
app.include_router(ai_router.router)
app.include_router(audit.router)
app.include_router(announcements.router)
app.include_router(knowledge_admin.router)
app.include_router(workflows.router)
app.include_router(system_alerts_api.router)

@app.get("/", tags=["Root"])
def read_root():
    """
    Endpoint racine pour vérifier que l'API fonctionne
    """
    return {
        "message": "Bienvenue sur l'API YDAYS",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """
    Vérifier l'état de l'API
    """
    return {
        "status": "ok",
        "message": "L'API est en bon état"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
