import sys
import os
sys.path.append(os.getcwd())

from database.db import SessionLocal, engine, Base
import models.user  # ensure User is registered
import models.employees  # ensure Employee is registered
import models.features  # ensure Formation is registered
from models.features import Formation
import datetime

db = SessionLocal()
try:
    if db.query(Formation).count() == 0:
        f1 = Formation(
            title='Sécurité au travail (Obligatoire)',
            description='Formation obligatoire sur les normes de sécurité en entreprise.',
            start_date=datetime.date(2026, 7, 1),
            end_date=datetime.date(2026, 7, 15)
        )
        f2 = Formation(
            title='Leadership & Management',
            description='Améliorez vos compétences en gestion d\'équipe.',
            start_date=datetime.date(2026, 8, 1),
            end_date=datetime.date(2026, 8, 5)
        )
        f3 = Formation(
            title='React Native Avancé',
            description='Maîtrisez le développement mobile avec React Native et Expo.',
            start_date=datetime.date(2026, 9, 10),
            end_date=datetime.date(2026, 9, 13)
        )
        db.add_all([f1, f2, f3])
        db.commit()
        print('Seed formations inserted.')
    else:
        print('Formations already exist.')
finally:
    db.close()
