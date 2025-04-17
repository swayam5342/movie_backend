from typing import Generator
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc, case, cast, Float
from typing import Dict, List, Any
import json
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

@app.get("/movies/{title}")
def get_movie_title(title: str, db: Session = Depends(get_db)):
    existing_movie = db.query(Movie).filter(func.lower(Movie.title) == title.lower()).first()
    if existing_movie:
        return existing_movie


@app.post("/movies/")
def add_movie(title: str, db: Session = Depends(get_db)):
    existing_movie = db.query(Movie).filter(func.lower(Movie.title) == title.lower()).first()
    if existing_movie:
        return existing_movie

    movie_data = fetch_movie_details(title)
    if not movie_data:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    try:
        new_movie = Movie(**movie_data)
        db.add(new_movie)
        db.commit()
        db.refresh(new_movie)
        return new_movie
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Movie with this IMDb ID already exists.")

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


@app.get("/statistics/")
def get_statistics(db: Session = Depends(get_db)):
    """Get overall statistics about the movie collection"""
    total_movies = db.query(func.count(Movie.id)).scalar()
    watched_movies = db.query(func.count(Movie.id)).filter(Movie.watched == True).scalar()
    unwatched_movies = total_movies - watched_movies
    genres_data = []
    all_genres = set()
    movies = db.query(Movie).all()
    for movie in movies:
        if movie.genre: #type:ignore
            genres = [g.strip() for g in movie.genre.split(',')]
            all_genres.update(genres)
    for genre in all_genres:
        count = 0
        for movie in movies:
            if movie.genre and genre in movie.genre: #type:ignore
                count += 1
        genres_data.append({"name": genre, "count": count})
    genres_data.sort(key=lambda x: x["count"], reverse=True)
    movie_types = db.query(
        Movie.type, 
        func.count(Movie.id).label('count')
    ).group_by(Movie.type).all()
    
    types_data = [{"name": t[0] if t[0] else "Unknown", "count": t[1]} for t in movie_types]
    actors_data = []
    all_actors = set()
    for movie in movies:
        if movie.actors: #type:ignore
            actors = [a.strip() for a in movie.actors.split(',')]
            all_actors.update(actors)
    
    for actor in all_actors:
        count = 0
        for movie in movies:
            if movie.actors and actor in movie.actors: #type:ignore
                count += 1
        actors_data.append({"name": actor, "count": count})
    
    actors_data.sort(key=lambda x: x["count"], reverse=True)
    top_actors = actors_data[:10]
    ratings_data = {"Internet Movie Database": 0, "Rotten Tomatoes": 0, "Metacritic": 0}
    ratings_count = {"Internet Movie Database": 0, "Rotten Tomatoes": 0, "Metacritic": 0}
    
    for movie in movies:
        if movie.ratings: #type:ignore
            try:
                cleaned_ratings = movie.ratings.replace("'", "\"")
                ratings = json.loads(cleaned_ratings)
                
                for rating in ratings:
                    source = rating.get("Source")
                    value = rating.get("Value")
                    
                    if source in ratings_data:
                        if source == "Internet Movie Database":
                            try:
                                score = float(value.split('/')[0])
                                ratings_data[source] += score  #type:ignore
                                ratings_count[source] += 1
                            except (ValueError, IndexError):
                                pass
                        elif source == "Rotten Tomatoes":
                            try:
                                score = float(value.replace('%', ''))
                                ratings_data[source] += score  #type:ignore
                                ratings_count[source] += 1
                            except ValueError:
                                pass
                        elif source == "Metacritic":
                            try:
                                score = float(value.split('/')[0])
                                ratings_data[source] += score  #type:ignore
                                ratings_count[source] += 1
                            except (ValueError, IndexError):
                                pass
            except json.JSONDecodeError:
                continue
    avg_ratings = {}
    for source in ratings_data:
        if ratings_count[source] > 0:
            avg_ratings[source] = round(ratings_data[source] / ratings_count[source], 1)
        else:
            avg_ratings[source] = 0
    
    return {
        "total_movies": total_movies,
        "watched_movies": watched_movies,
        "unwatched_movies": unwatched_movies,
        "watched_percentage": round((watched_movies / total_movies * 100) if total_movies > 0 else 0, 1),
        "genres": genres_data,
        "types": types_data,
        "top_actors": top_actors,
        "avg_ratings": avg_ratings
    }

@app.get("/statistics/recent-activity/")
def get_recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    """Get recently added or watched movies"""
    recent_movies = db.query(Movie).order_by(desc(Movie.id)).limit(limit).all()
    return recent_movies