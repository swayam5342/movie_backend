# 🎬 Movie Recommendation Backend

This is the backend for the Movie Recommendation System, built using **FastAPI** and **MySQL**. It provides endpoints for managing movies, user authentication, ratings, and recommendations.

## 🚀 Features

- Movie Management (Add, Delete, Update, Retrieve)
    
- Mark Movies as Watched/Unwatched
    
- Fetch Movie Ratings
    
- Suggest Movies from Watchlist
    
- Filter Movies by Genre, Actor, and Title
    
- RESTful API with FastAPI
    

---

## 🛠️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/movie-recommendation-backend.git
cd movie-recommendation-backend
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate 
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure API Key 


Update `.env` with your API key from [OMDB](https://www.omdbapi.com/) credentials:

``` shell
OMDB_API_KEY = "your_api_key"
```

### 5️⃣ Start the Server

```bash
uvicorn main:app --reload
```

API will be available at: [http://localhost:8000](http://localhost:8000/)

---

## 🔥 API Endpoints

### 🎥 Movie Endpoints

| Method   | Endpoint               | Description                |
| -------- | ---------------------- | -------------------------- |
| `GET`    | `/movies/`             | Get all movies             |
| `POST`   | `/movies/`             | Add a new movie            |
| `POST`   | `/imbd/movies/`        | Add a movie using IMDB I'd |
| `DELETE` | `/movies/{id}/`        | Delete a movie             |
| `PUT`    | `/movies/{id}/watched` | Mark as watched/unwatched  |
| `GET`    | `/movies/rating/{id}`  | Get movie rating           |

---

## 🛠️ Tech Stack

- **FastAPI** - Backend Framework
    
- **SQLite** - Database
    
- **SQLAlchemy** - ORM
    
- **Uvicorn** - ASGI Server
    

---

## 📌 Contributing

Feel free to fork the project, submit issues, or open a pull request!


---

## 🎯 Author

Developed by **Swayam** ✨