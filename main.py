import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String
from fastapi import FastAPI, HTTPException


db_host = os.environ.get("DB_HOST")
db_port = os.environ.get("DB_PORT")
db_name = os.environ.get("DB_NAME")
db_user = os.environ.get("DB_USER")
db_password = os.environ.get("DB_PASSWORD")

# URL для подключения к PostgreSQL
DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

# Создаём движок SQLAlchemy
engine = create_engine(DATABASE_URL)

# Создаём фабрику сессий для взаимодействия с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Базовый класс для моделей
Base = declarative_base()

class Clubs(Base):
    __tablename__ = "football_club"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# Создание таблицы (если она еще не существует)
Base.metadata.create_all(bind=engine)

club = db.query(Clubs).all()

app = FastAPI()

@app.get("/")
def root():
    return club