from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database import get_db, MovieModel
from database.models import CountryModel, GenreModel, ActorModel, LanguageModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieDetailSchema, MovieUpdateSchema,
)

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_movies(
        page: int = Query(1, ge=1),
        per_page: int = Query(10, ge=1, le=100),
        db: AsyncSession = Depends(get_db)
):
    offset = (page - 1) * per_page
    query = select(MovieModel).order_by(MovieModel.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_query = await db.execute(select(func.count()).select_from(MovieModel))
    total_items = total_query.scalar()
    total_pages = (total_items + per_page - 1) // per_page

    prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": movies,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items
    }


@router.post("/movies/", status_code=201, response_model=MovieDetailSchema)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db)):
    movie_dict = movie.dict()
    country_code = movie_dict.pop("country")
    genre_names = movie_dict.pop("genres")
    actor_names = movie_dict.pop("actors")
    language_names = movie_dict.pop("languages")

    result = await db.execute(select(CountryModel).where(CountryModel.code == country_code))
    country = result.scalar_one_or_none()
    if not country:
        country = CountryModel(code=country_code)
        db.add(country)
        await db.flush()
    movie_dict["country_id"] = country.id

    new_movie = MovieModel(**movie_dict)

    genres = []
    for name in genre_names:
        result = await db.execute(select(GenreModel).where(GenreModel.name == name))
        genre = result.scalar_one_or_none()
        if not genre:
            genre = GenreModel(name=name)
            db.add(genre)
            await db.flush()
        genres.append(genre)

    actors = []
    for name in actor_names:
        result = await db.execute(select(ActorModel).where(ActorModel.name == name))
        actor = result.scalar_one_or_none()
        if not actor:
            actor = ActorModel(name=name)
            db.add(actor)
            await db.flush()
        actors.append(actor)

    languages = []
    for name in language_names:
        result = await db.execute(select(LanguageModel).where(LanguageModel.name == name))
        language = result.scalar_one_or_none()
        if not language:
            language = LanguageModel(name=name)
            db.add(language)
            await db.flush()
        languages.append(language)

    new_movie.genres = genres
    new_movie.actors = actors
    new_movie.languages = languages

    try:
        db.add(new_movie)
        await db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"A movie with the name '{new_movie.name}' "
                   f"and release date '{new_movie.date}' already exists."
        )

    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .filter(MovieModel.id == new_movie.id)
    )
    movie_with_relations = result.scalars().first()

    return movie_with_relations


@router.get("/movies/{movie_id}/", response_model=MovieDetailSchema)
async def get_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .filter(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    return movie


@router.delete("/movies/{movie_id}/", status_code=204)
async def delete_movie(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    await db.delete(movie)
    await db.commit()


@router.patch("/movies/{movie_id}/")
async def update_movie(
        movie_id: int,
        updated_data: MovieUpdateSchema,
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(MovieModel)
        .options(
            joinedload(MovieModel.country),
            joinedload(MovieModel.genres),
            joinedload(MovieModel.actors),
            joinedload(MovieModel.languages),
        )
        .filter(MovieModel.id == movie_id)
    )
    movie = result.scalars().first()

    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    movie_dict = updated_data.dict(exclude_unset=True)
    country_code = movie_dict.pop("country", None)
    genre_names = movie_dict.pop("genres", None)
    actor_names = movie_dict.pop("actors", None)
    language_names = movie_dict.pop("languages", None)

    if country_code:
        result = await db.execute(select(CountryModel).where(CountryModel.code == country_code))
        country = result.scalar_one_or_none()
        if not country:
            country = CountryModel(code=country_code)
            db.add(country)
            await db.flush()
        movie_dict["country_id"] = country.id

    if genre_names:
        genres = []
        for name in genre_names:
            result = await db.execute(select(GenreModel).where(GenreModel.name == name))
            genre = result.scalar_one_or_none()
            if not genre:
                genre = GenreModel(name=name)
                db.add(genre)
                await db.flush()
            genres.append(genre)
            movie.genres = genres

    if actor_names:
        actors = []
        for name in actor_names:
            result = await db.execute(select(ActorModel).where(ActorModel.name == name))
            actor = result.scalar_one_or_none()
            if not actor:
                actor = ActorModel(name=name)
                db.add(actor)
                await db.flush()
            actors.append(actor)
            movie.actors = actors

    if language_names:
        languages = []
        for name in language_names:
            result = await db.execute(select(LanguageModel).where(LanguageModel.name == name))
            language = result.scalar_one_or_none()
            if not language:
                language = LanguageModel(name=name)
                db.add(language)
                await db.flush()
            languages.append(language)
            movie.languages = languages

    for key, value in movie_dict.items():
        setattr(movie, key, value)

    await db.commit()
    await db.refresh(movie)
    return {"detail": "Movie updated successfully."}
