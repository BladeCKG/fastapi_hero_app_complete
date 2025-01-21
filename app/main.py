from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select
from .database import engine
from .database import postgresql_url
from .model import Hero


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/heroes/")
def create_hero(hero: Hero):
    with Session(engine) as session:
        session.add(hero)
        session.commit()
        session.refresh(hero)
        return hero


@app.get("/heroes/")
def read_heroes():
    with Session(engine) as session:
        heroes = session.exec(select(Hero)).all()
        return heroes

@app.get("/")
async def read_root():
    return {"message": "Hello, World!"}

@app.get("/db_url")
async def read_root():
    return {"message": postgresql_url}