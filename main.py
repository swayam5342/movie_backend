from typing import Generator
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
from typing import Any
from dotenv import load_dotenv
load_dotenv()
DATABASE_URL = "sqlite:///./movies_data.db"
OMDB_API_KEY: str | None = os.getenv("OMDB_API_KEY")
OMDB_API_URL = "http://www.omdbapi.com/"

if not OMDB_API_KEY:
    raise ValueError("OMDB_API_KEY is missing! Make sure to set it in the .env file.")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Movie(Base):
    __tablename__ = "movies"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    poster_url = Column(String, nullable=True)
    type = Column(String, nullable=True)
    imdb_id = Column(String, unique=True, nullable=True)
    watched = Column(Boolean, default=False)
    genre = Column(String, nullable=True)
    actors = Column(String, nullable=True)
    ratings = Column(String, nullable=True)

Base.metadata.create_all(bind=engine)
app = FastAPI()

origins: list[str] = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db() -> Generator[Session, Any, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def fetch_movie_details(title: str):
    params = {"apikey": OMDB_API_KEY, "t": title}
    response = requests.get(OMDB_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            return {
                "title": data.get("Title"),
                "description": data.get("Plot", "No description available"),
                "poster_url": data.get("Poster", None),
                "type": data.get("Type", "Unknown"),
                "imdb_id": data.get("imdbID", None),
                "genre": data.get("Genre", ""),
                "actors": data.get("Actors", ""),  
                "ratings": str(data.get("Ratings", []))  
            }
    return None

def fetch_movie_details_imdb(imdb_id: str):
    params = {"apikey": OMDB_API_KEY, "i": imdb_id}
    response = requests.get(OMDB_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            return {
                "title": data.get("Title"),
                "description": data.get("Plot", "No description available"),
                "poster_url": data.get("Poster", None),
                "type": data.get("Type", "Unknown"),
                "imdb_id": data.get("imdbID", None),
                "genre": data.get("Genre", ""),
                "actors": data.get("Actors", ""),
                "ratings": str(data.get("Ratings", []))
            }
    return None



@app.get("/movies/")
def get_movies(db: Session = Depends(get_db)):
    """Retrieve all movies"""
    return db.query(Movie).all()

@app.get("/movies/rating/{id}")
def get_rating(id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"movie_id": id, "title": movie.title, "rating": movie.ratings}


@app.post("/movies/")
def add_movie(title: str, db: Session = Depends(get_db)):
    existing_movie = db.query(Movie).filter(Movie.title == title).first()
    if existing_movie:
        return existing_movie

    movie_data = fetch_movie_details(title)
    if not movie_data:
        raise HTTPException(status_code=404, detail="Movie not found")

    new_movie = Movie(**movie_data)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie

@app.post("/imdb/movies/")
def add_movie_imdb(imdb_id: str, db: Session = Depends(get_db)):
    existing_movie = db.query(Movie).filter(Movie.imdb_id == imdb_id).first()
    if existing_movie:
        return existing_movie

    movie_data = fetch_movie_details_imdb(imdb_id)
    if not movie_data:
        raise HTTPException(status_code=404, detail="Movie not found")

    new_movie = Movie(**movie_data)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie

@app.put("/movies/{movie_id}/watched")
def mark_watched(movie_id: int, db: Session = Depends(get_db)):
    """Toggle movie watched status"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    movie.watched = not movie.watched #type:ignore
    db.commit()
    db.refresh(movie)
    return movie

@app.delete("/movies/{movie_id}/")
def delete_movie(movie_id: int, db: Session = Depends(get_db)):
    """Delete a movie"""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    db.delete(movie)
    db.commit()
    return {"message": "Movie deleted successfully", "id": movie_id}
