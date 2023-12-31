from fastapi import FastAPI
from filmes import get_json
from typing import List

from fastapi.middleware.cors import (
     CORSMiddleware
)
app = FastAPI()



# habilita CORS (permite que o Svelte acesse o fastapi)
# por padrao o svelte roda na porta 5173
origins = [
    "http://localhost",
    "http://localhost:5173",
    "http://localhost:5174",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
import crud, models, schemas
from database import SessionLocal, engine
models.Base.metadata.create_all(bind=engine)

# =====================================================
# USERS
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ============ CRUD USUARIO 
#Create User
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/", response_model=list[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/users/{user_id}", response_model=schemas.User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

#Delete User
@app.put("/users/{user_id}", response_model=schemas.User)
def soft_delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Defina o campo is_active como False
    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    
    return db_user

#Update User
@app.put("/users/", response_model=schemas.User)
async def update_user(
    user: schemas.User,
    db: Session = Depends(get_db)
    ):
    db_user = crud.get_user(db, user)
    if db_user is None:
        raise HTTPException(
            status_code=404,
            detail="user not found"
        )
    crud.update_user(user)
    return db_user



@app.get("/teste/{user_id}",response_model=schemas.User)
def movie():
    return ("test")

# =========== FAVORITAR FILME

@app.post("/favorite_movie/{user_id}", response_model=schemas.FavoriteMovie)
def favorite_movie(user_id: int, favorite_movie: schemas.FavoriteMovieCreate, db: Session = Depends(get_db)):
    user_favorite_movies = crud.get_favorite_movies(db, user_id=user_id)
    for movie in user_favorite_movies:
        if movie.movie_id == favorite_movie.movie_id:
            raise HTTPException(
            status_code=303,
            detail="Movie is alredy favorite"
        )
    return crud.create_favorite_movie(db=db, favorite_movie=favorite_movie, user_id=user_id)

@app.get("/favorite_movies/{user_id}", response_model=List[schemas.FavoriteMovie])
def get_favorite_movies(user_id: int, db: Session = Depends(get_db)):
    movies = crud.get_favorite_movies(db, user_id=user_id)
    return movies

@app.delete("/unfavorite_movie/{user_id}", response_model=schemas.FavoriteMovie)
def unfavorite_movie(user_id: int, favorite_movie: schemas.FavoriteMovieCreate, db: Session = Depends(get_db)):
    user_favorite_movies = crud.get_favorite_movies(db, user_id=user_id)
    for movie in user_favorite_movies:
        if movie.movie_id == favorite_movie.movie_id:
            return crud.delete_favorite_movie(db, movie.id)
    
    raise HTTPException(status_code=400, detail="Movie not found in favorites")

# ============ FAVORITAR ARTISTA

@app.post("/favorite_artist/{user_id}", response_model=schemas.FavoriteArtist)
def favorite_artist(user_id: int, favorite_artist: schemas.FavoriteArtistCreate, db: Session = Depends(get_db)):
    user_favorite_artist = crud.get_favorite_artist(db, user_id=user_id)
    for artist in user_favorite_artist:
        if artist.artist_id == favorite_artist.artist_id:
            raise HTTPException(
            status_code=303,
            detail="Artist is alredy favorite"
        )
    return crud.create_favorite_artist(db=db, favorite_artist=favorite_artist, user_id=user_id)


@app.get("/favorite_artist/{user_id}", response_model=List[schemas.FavoriteArtist])
def get_favorite_artist(user_id: int, db: Session = Depends(get_db)):
    artist = crud.get_favorite_artist(db, user_id=user_id)
    return artist

@app.delete("/unfavorite_artist/{user_id}", response_model=schemas.FavoriteArtist)
def unfavorite_artist(user_id: int, favorite_artist: schemas.FavoriteArtistCreate, db: Session = Depends(get_db)):
    user_favorite_artist = crud.get_favorite_artist(db, user_id=user_id)
    for artist in user_favorite_artist:
        if artist.artist_id == favorite_artist.artist_id:
            return crud.delete_favorite_artist(db, artist.id)
    
    raise HTTPException(status_code=400, detail="Artist not found in favorites")


# ========== PROCURAR FILME PELO ID

@app.get("/movie/{filme_id}")
async def get_filme_id(filme_id: int):
    data = get_json(f"https://api.themoviedb.org/3/movie/{filme_id}?language=en-US")
    movie = data
    results = {
        'id': movie['id'],
        'title': movie['title'],
        'image': f"http://image.tmdb.org/t/p/w185{movie['poster_path']}"
    }
    return results

# ============= PROCURAR ARTISTA PELO ID

@app.get("/artist/{artist_id}")
async def get_artist_id(artist_id: int):
    data = get_json(f"https://api.themoviedb.org/3/person/{artist_id}?language=en-US")
    artist = data
    results = {
        'id': artist['id'],
        'name': artist['name'],
        'biography': artist['biography'],
        'birthday': artist['birthday'],
        'popularity': artist['popularity'],
        'image': f"http://image.tmdb.org/t/p/w185{artist['profile_path']}"
    }
    return results

# ============= LISTAR ARTISTAS PELA POPULARIDADE

@app.get("/artistas")
async def get_artist(limit=3):
    data = get_json("https://api.themoviedb.org/3/person/popular?language=en-US")
    results = data['results']
    filtro = []
    for artist in results:
        filtro.append ({
            'id': artist['id'],
            'name': artist['name'],
            'image':f"http://image.tmdb.org/t/p/w185{artist['profile_path']}",
            'rank': artist['popularity']
        })
    filtro.sort(reverse= True, key=lambda artist:artist['rank'])
    return filtro

# ============= LISTAR FILMES

@app.get("/filmes")
async def filmes_populares(limit=3):
    data = get_json("https://api.themoviedb.org/3/discover/movie","?sort_by=vote_count.desc")
    results = data['results']
    filtro = []
    for movie in results:
        filtro.append({
            'id': movie['id'],
            'title': movie['original_title'],
            'image':f"http://image.tmdb.org/t/p/w185{movie['poster_path']}"
        })
    return filtro


# ================== BUSCA FILMES PELO NOME ========================
@app.get("/filme/{title}")
async def find_movie(title: str):
    data = get_json(f"https://api.themoviedb.org/3/search/movie?query={title}&language=en-US")
    results = data['results']
    filtro = []
    for movie in results:
        filtro.append({
            'id': movie['id'],
            'title': movie['title'],
            'image': f"http://image.tmdb.org/t/p/w185{movie['poster_path']}",
            'rank': movie['popularity']
        })
    filtro.sort(reverse= True, key=lambda movie:movie['rank'])
    return filtro

# ================== ATIVIDADE 02 ========================

@app.get("/artista/filmes")
async def find_movie_byartist(personId: int):
    data = get_json(f"https://api.themoviedb.org/3/person/{personId}/movie_credits?language=en-US")
    cast = data['cast']
    filtro = []
    for movie in cast:
        filtro.append({
            'id': movie['id'],
            'title': movie['title'],
            'rank': movie['popularity']
        })
    filtro.sort(reverse= True, key=lambda movie:movie['rank'])
    return filtro

#======================================================

# BUSCA ARTISTA PELO NOME EM ORDEM DESCRESCENTE DE POPULARIDADE
@app.get("/artista/{name}")
async def get_artista(name: str):
    data = get_json(
        f"https://api.themoviedb.org/3/search/person?query={name}&include_adult=false&language=en-US"
    )
    results = data['results']
    filtro = []
    for artist in results:
        filtro.append({
            'id': artist['id'],
            'name': artist['name'],
            'image': f"http://image.tmdb.org/t/p/w185{artist['profile_path']}",
            'rank': artist['popularity']
        })
    filtro.sort(reverse= True, key=lambda artist:artist['rank'])
    return filtro


