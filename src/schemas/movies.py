import datetime

from pydantic import BaseModel, Field, validator
from typing import Optional
from decimal import Decimal
from datetime import timedelta

from database.models import MovieStatusEnum, CountryModel


class MovieListItemSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float
    overview: str

    class Config:
        from_attributes = True


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: Optional[str]
    next_page: Optional[str]
    total_pages: int
    total_items: int


class CountryResponseSchema(BaseModel):
    id: int
    code: str = Field(max_length=3)
    name: Optional[str]

    class Config:
        from_attributes = True


class GenreResponseSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)

    class Config:
        from_attributes = True


class ActorResponseSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)

    class Config:
        from_attributes = True


class LanguageResponseSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)

    class Config:
        from_attributes = True


class MovieDetailSchema(BaseModel):
    id: int
    name: str = Field(max_length=255)
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float = Field(ge=0)
    country: CountryResponseSchema
    genres: list[GenreResponseSchema]
    actors: list[ActorResponseSchema]
    languages: list[LanguageResponseSchema]

    class Config:
        from_attributes = True


class MovieCreateSchema(BaseModel):
    name: str = Field(max_length=255)
    date: datetime.date
    score: float = Field(ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: Decimal = Field(ge=0)
    revenue: float = Field(ge=0)

    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]

    @validator("date")
    def date_not_more_than_one_year(cls, v):
        if v > datetime.date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return v


class MovieUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    date: Optional[datetime.date] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    overview: Optional[str] = None
    status: Optional[MovieStatusEnum] = None
    budget: Optional[Decimal] = Field(None, ge=0)
    revenue: Optional[float] = Field(None, ge=0)

    country: Optional[str] = None
    genres: Optional[list[str]] = None
    actors: Optional[list[str]] = None
    languages: Optional[list[str]] = None

    @validator("date")
    def date_not_more_than_one_year(cls, v):
        if v > datetime.date.today() + timedelta(days=365):
            raise ValueError("Date cannot be more than one year in the future.")
        return v
