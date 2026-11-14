"""Задание №7 (повышенная сложность): FastAPI + SQLAlchemy (REST)."""

import sys
from typing import Any, Dict, Generator, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Response, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Float, Integer, String, create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool

DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый декларативный класс моделей SQLAlchemy."""


class BookModel(Base):
    """ORM-модель книги в каталоге библиотеки."""

    __tablename__ = "books"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str] = mapped_column(String(150), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    in_stock: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    def __init__(
        self,
        title: str,
        author: str,
        year: int,
        price: float,
        in_stock: bool = True,
    ) -> None:
        """Инициализирует запись книги для сохранения в БД."""
        self.title = title
        self.author = author
        self.year = year
        self.price = price
        self.in_stock = in_stock


Base.metadata.create_all(bind=engine)


class BookCreate(BaseModel):
    """Схема Pydantic для создания новой книги."""

    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=150)
    year: int = Field(..., ge=1450, le=2100)
    price: float = Field(..., ge=0.0)
    in_stock: bool = True


class BookUpdate(BaseModel):
    """Схема Pydantic для частичного или полного обновления книги."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=150)
    year: Optional[int] = Field(None, ge=1450, le=2100)
    price: Optional[float] = Field(None, ge=0.0)
    in_stock: Optional[bool] = None


class BookResponse(BaseModel):
    """Схема Pydantic для возврата данных книги в ответах REST API."""

    id: int
    title: str
    author: str
    year: int
    price: float
    in_stock: bool


def serialize_book(book: BookModel) -> BookResponse:
    """Преобразует ORM-объект BookModel в схему ответа BookResponse."""
    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        year=book.year,
        price=book.price,
        in_stock=book.in_stock,
    )


def get_db() -> Generator[Session, None, None]:
    """Зависимость FastAPI, предоставляющая сессию БД на время запроса."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(
    title="Library Catalog REST API",
    description="REST API на базе FastAPI и SQLAlchemy ORM (ЛР №7, вариант 3)",
    version="1.0.0",
)


@app.post(
    "/api/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_book(
    payload: BookCreate, db: Session = Depends(get_db)
) -> BookResponse:
    """Создаёт новую книгу в базе данных."""
    book = BookModel(
        title=payload.title,
        author=payload.author,
        year=payload.year,
        price=payload.price,
        in_stock=payload.in_stock,
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return serialize_book(book)


@app.get("/api/books", response_model=List[BookResponse])
def list_books(
    author: Optional[str] = Query(None, description="Фильтр по автору"),
    in_stock: Optional[bool] = Query(None, description="Фильтр наличия"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> List[BookResponse]:
    """Возвращает список книг с поддержкой фильтрации и пагинации."""
    query = db.query(BookModel)
    if author is not None:
        query = query.filter(BookModel.author == author)
    if in_stock is not None:
        query = query.filter(BookModel.in_stock == in_stock)
    items = query.order_by(BookModel.id.asc()).offset(skip).limit(limit).all()
    return [serialize_book(item) for item in items]


@app.get("/api/books/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int, db: Session = Depends(get_db)
) -> BookResponse:
    """Возвращает книгу по её уникальному идентификатору."""
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID={book_id} не найдена",
        )
    return serialize_book(book)


@app.put("/api/books/{book_id}", response_model=BookResponse)
def update_book(
    book_id: int,
    payload: BookUpdate,
    db: Session = Depends(get_db),
) -> BookResponse:
    """Обновляет поля существующей книги по её идентификатору."""
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID={book_id} не найдена",
        )

    if payload.title is not None:
        book.title = payload.title
    if payload.author is not None:
        book.author = payload.author
    if payload.year is not None:
        book.year = payload.year
    if payload.price is not None:
        book.price = payload.price
    if payload.in_stock is not None:
        book.in_stock = payload.in_stock

    db.commit()
    db.refresh(book)
    return serialize_book(book)


@app.delete(
    "/api/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_book(
    book_id: int, db: Session = Depends(get_db)
) -> Response:
    """Удаляет книгу из базы данных по идентификатору."""
    book = db.query(BookModel).filter(BookModel.id == book_id).first()
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Книга с ID={book_id} не найдена",
        )
    db.delete(book)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def run_self_tests() -> None:
    """Выполняет комплексную самопроверку всех эндпоинтов REST API."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)
    print("Запуск демонстрации и самопроверки FastAPI + SQLAlchemy REST API:")

    book1_data: Dict[str, Any] = {
        "title": "Чистая архитектура",
        "author": "Роберт Мартин",
        "year": 2018,
        "price": 1450.0,
        "in_stock": True,
    }
    book2_data: Dict[str, Any] = {
        "title": "Изучаем Python",
        "author": "Марк Лутц",
        "year": 2019,
        "price": 2300.0,
        "in_stock": True,
    }

    resp1 = client.post("/api/books", json=book1_data)
    assert resp1.status_code == 201
    created1 = resp1.json()
    print(f"1. POST /api/books -> создана книга: {created1}")

    resp2 = client.post("/api/books", json=book2_data)
    assert resp2.status_code == 201

    resp_list = client.get("/api/books")
    assert resp_list.status_code == 200
    all_books = resp_list.json()
    assert len(all_books) == 2
    print(f"2. GET /api/books -> получено книг в каталоге: {len(all_books)}")

    book_id = created1["id"]
    resp_get = client.get(f"/api/books/{book_id}")
    assert resp_get.status_code == 200
    print(f"3. GET /api/books/{book_id} -> {resp_get.json()['title']}")

    resp_update = client.put(
        f"/api/books/{book_id}",
        json={"price": 1290.0, "in_stock": False},
    )
    assert resp_update.status_code == 200
    updated = resp_update.json()
    assert updated["price"] == 1290.0 and updated["in_stock"] is False
    print(
        f"4. PUT /api/books/{book_id} -> "
        f"новая цена={updated['price']}, в наличии={updated['in_stock']}"
    )

    resp_delete = client.delete(f"/api/books/{book_id}")
    assert resp_delete.status_code == 204
    print(f"5. DELETE /api/books/{book_id} -> статус 204 (успешно удалена)")

    resp_missing = client.get(f"/api/books/{book_id}")
    assert resp_missing.status_code == 404
    print(
        f"6. Проверка удалённой книги ID={book_id} -> "
        f"статус {resp_missing.status_code} ({resp_missing.json()['detail']})"
    )


def main() -> None:
    """Точка входа: запускает автотесты или интерактивный сервер uvicorn."""
    if "--serve" in sys.argv:
        import uvicorn

        uvicorn.run(app, host="127.0.0.1", port=8000)
    else:
        run_self_tests()


if __name__ == "__main__":
    main()
