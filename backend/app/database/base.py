"""
Declarative base shared by every SQLAlchemy model.

Importing app.database.base.Base in each model file (instead of each
model creating its own base) is what lets Base.metadata.create_all()
in main.py see every table at once.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()