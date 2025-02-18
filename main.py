import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy import Column, Integer, String, ForeignKey
from fastapi import FastAPI, HTTPException, Body, Depends
from pydantic import BaseModel
from typing import Optional

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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Базовый класс для моделей
Base = declarative_base()

class Clubs(Base):
    __tablename__ = "football_club"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True)

class Players(Base):
    __tablename__ = "players"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    id_club = Column(Integer, ForeignKey("football_club.id")) # Внешний ключ
    name = Column(String, index=True)
    surname = Column(String, index=True)

class Goals(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
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
class ClubCreate(BaseModel):
    name: str
class PlayerUpdate(BaseModel):
    id_club: Optional[int] = None
    name: Optional[str] = None
    surname: Optional[str] = None
class PlayerCreate(BaseModel):
    id_club: int
    name: str
    surname: str
class GoalUpdate(BaseModel):
    id_players: Optional[int] = None
    goal: Optional[int] = None
class GoalCreate(BaseModel):
    id_players: int
    goal: int

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
    logger.info("goal")
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

@app.post("/clubs")
async def create_club(club: ClubCreate, db: Session = Depends(get_db)):
    try:
        new_club = Clubs(name=club.name)  # id будет сгенерирован автоматически
        db.add(new_club)
        db.commit()
        db.refresh(new_club)
        return new_club
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/players")
async def create_player(player: PlayerCreate, db: Session = Depends(get_db)):
    try:
        new_player = Players(id_club=player.id_club, name=player.name, surname=player.surname)
        db.add(new_player)
        db.commit()
        db.refresh(new_player)
        return new_player
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/goal")
async def create_goal(goal: GoalCreate, db: Session = Depends(get_db)):
    try:
        new_goal = Goals(id_players=goal.id_players, goal=goal.goal)
        db.add(new_goal)
        db.commit()
        db.refresh(new_goal)
        return new_goal
        return new_goal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/clubs/{id}")
async def update_item(id: int, club_update: ClubCreate, db: Session = Depends(get_db)):
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

@app.put("/players/{id}")
async def update_player(id: int, player_update: PlayerUpdate, db: Session = Depends(get_db)): #Переменная теперь player_update: PlayerUpdate
    try:
        player = db.query(Players).filter(Players.id == id).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")

        # Обновляем поля, только если они есть в player_update
        if player_update.id_club is not None:
            player.id_club = player_update.id_club
        if player_update.name is not None:
            player.name = player_update.name
        if player_update.surname is not None:
            player.surname = player_update.surname

        db.commit()
        db.refresh(player)
        return player
    except Exception as e:
        db.rollback()
        logging.error(e)
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/goals/{id}")
async def update_goal(id: int, goal_update: GoalUpdate, db: Session = Depends(get_db)):
    try:
        goal = db.query(Goals).filter(Goals.id == id).first()
        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")

        # Обновляем поля, только если они указаны в goal_update
        if goal_update.id_players is not None:
            goal.id_players = goal_update.id_players
        if goal_update.goal is not None:
            goal.goal = goal_update.goal

        db.commit()
        db.refresh(goal)  # Обновляем объект goal после коммита
        return goal
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/clubs/{id}")
async def delete_club(id: int, db: Session = Depends(get_db)):
    print("Del")
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

@app.delete("/players/{id}")
async def delete_player(id: int, db: Session = Depends(get_db)):
    try:
        player = db.query(Players).filter(Players.id == id).first()
        if player is None:
            raise HTTPException(status_code=404, detail="Player not found")

        # 1. Удаляем Goals, связанные с Players, которые связаны с клубом
        db.query(Goals).filter(Goals.id_players == id).delete(synchronize_session=False)

        # удаляем игрока
        db.delete(player)
        db.commit()
        return {"message": f"Player with id {id} deleted successfully"}
    except Exception as e:
        db.rollback()  # Важно откатить транзакцию при ошибке
        raise HTTPException(status_code=500, detail=str(e))  # Вернуть сообщение об ошибке

@app.delete("/goals/{id}")
async def delete_goal(id: int, db: Session = Depends(get_db)):
    try:
        goal = db.query(Goals).filter(Goals.id == id).first()
        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")

        db.delete(goal)
        db.commit()
        return {"message": f"Goal with id {id} deleted successfully"}
    except Exception as e:
        db.rollback()
        logging.error(e)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
