import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Column, Integer, String, ForeignKey
from fastapi import FastAPI, HTTPException, Body, Depends
from pydantic import BaseModel

load_dotenv()

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
#db = SessionLocal()

# Базовый класс для моделей
Base = declarative_base()

class Clubs(Base):
    __tablename__ = "football_club"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

class Players(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True)
    id_club = Column(Integer, ForeignKey("football_club.id")) # Внешний ключ
    name = Column(String, index=True)
    surname = Column(String, index=True)

class Goals(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    id_players = Column(Integer, ForeignKey("players.id")) # Внешний ключ
    goal = Column(String, index=True)

# Создание таблицы (если она еще не существует)
Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

 # для данных при создании/обновлении клуба
class ClubUpdate(BaseModel):
    name: str

@app.get("/clubs")
async def read_items(db: Session = Depends(get_db)):
    items = db.query(Clubs).all()

    # Преобразуем результаты в список словарей для JSON
    result = []
    for item in items:
        result.append({
            "ID": item.id,
            "Name": item.name
        })

    return result

@app.get("/players")
async def read_items(db: Session = Depends(get_db)):
    items = db.query(Players).all()

    # Преобразуем результаты в список словарей для JSON
    result = []
    for item in items:
        result.append({
            "ID": item.id,
            "ID club": item.id_club,
            "Name": item.name,
            "Surname": item.surname
        })

    return result


@app.get("/goal")
async def read_items(db: Session = Depends(get_db)):
    items = db.query(Goals).all()

    # Преобразуем результаты в список словарей для JSON
    result = []
    for item in items:
        result.append({
            "ID": item.id,
            "ID player": item.id_players,
            "Goal": item.goal
        })

    return result

@app.put("/clubs/{id}")
async def update_club(id: int, club_update: ClubUpdate, db: Session = Depends(get_db)):
    try:
        club = db.query(Clubs).filter(Clubs.id == id).first()
        if club is None:
            raise HTTPException(status_code=404, detail="Club not found")

        # Обновляем все поля клуба данными из club_update
        club.name = club_update.name

        db.commit()
        db.refresh(club) # Обновляем объект club из базы данных, чтобы получить последние изменения
        return club
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clubs/{id}")
async def delete_club(id: int, db: Session = Depends(get_db)):
    try:
        club = db.query(Clubs).filter(Clubs.id == id).first()
        if club is None:
            raise HTTPException(status_code=404, detail="Club not found")

        # 1. Удаляем Goals, связанные с Players, которые связаны с клубом
        player_ids = [player.id for player in db.query(Players).filter(Players.id_club == id).all()]
        for player_id in player_ids:
            db.query(Goals).filter(Goals.id_players == player_id).delete(synchronize_session=False)

        # 2. Удаляем Players, связанные с клубом
        db.query(Players).filter(Players.id_club == id).delete(synchronize_session=False)

        # удаляем клуб
        db.delete(club)
        db.commit()
        return {"message": f"Club with id {id} deleted successfully"}
    except Exception as e:
        db.rollback()  # Важно откатить транзакцию при ошибке
        raise HTTPException(status_code=500, detail=str(e))  # Вернуть сообщение об ошибке

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
