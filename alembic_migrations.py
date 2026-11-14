"""Задание №3 (повышенная сложность): Миграции Alembic."""

from pathlib import Path
from typing import List, Optional

from alembic import command
from alembic.config import Config
from sqlalchemy import Float, ForeignKey, Integer, String, create_engine
from sqlalchemy import inspect as sa_inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Базовый декларативный класс для ORM-моделей SQLAlchemy."""


class Department(Base):
    """ORM-модель подразделения компании."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
    )
    budget: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )

    employees: Mapped[List["Employee"]] = relationship(
        "Employee", back_populates="department", cascade="all, delete-orphan"
    )

    def __init__(self, name: str, budget: float = 0.0) -> None:
        """Инициализирует экземпляр подразделения."""
        self.name = name
        self.budget = budget


class Employee(Base):
    """ORM-модель сотрудника компании (с учётом миграции 0002)."""

    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    position: Mapped[str] = mapped_column(String(100), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    department_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(120), nullable=True, unique=True
    )
    hire_date: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )

    department: Mapped[Department] = relationship(
        "Department", back_populates="employees"
    )

    def __init__(
        self,
        full_name: str,
        position: str,
        salary: float,
        department_id: int,
        email: Optional[str] = None,
        hire_date: Optional[str] = None,
    ) -> None:
        """Инициализирует экземпляр сотрудника."""
        self.full_name = full_name
        self.position = position
        self.salary = salary
        self.department_id = department_id
        self.email = email
        self.hire_date = hire_date


def build_alembic_config(db_url: str) -> Config:
    """Создаёт объект конфигурации Alembic с привязкой к указанному URL БД."""
    base_dir = Path(__file__).resolve().parent
    ini_path = base_dir / "alembic.ini"
    alembic_cfg = Config(str(ini_path))
    alembic_cfg.set_main_option(
        "script_location", str(base_dir / "migrations")
    )
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    return alembic_cfg


def get_table_columns(engine: Engine, table_name: str) -> List[str]:
    """Возвращает список имён столбцов указанной таблицы в текущей схеме БД."""
    inspector = sa_inspect(engine)
    if table_name not in inspector.get_table_names():
        return []
    return [col["name"] for col in inspector.get_columns(table_name)]


def get_current_revision(engine: Engine) -> Optional[str]:
    """Считывает текущую ревизию из служебной таблицы alembic_version."""
    inspector = sa_inspect(engine)
    if "alembic_version" not in inspector.get_table_names():
        return None
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT version_num FROM alembic_version")
        ).fetchone()
        return str(row[0]) if row is not None else None


def main() -> None:
    """Демонстрирует применение и откат миграций базы данных через Alembic."""
    db_file = Path("company_migrations_demo.db")
    if db_file.exists():
        db_file.unlink()

    db_url = f"sqlite:///{db_file.as_posix()}"
    alembic_cfg = build_alembic_config(db_url)
    engine = create_engine(db_url)

    try:
        print("1. Применение первой миграции (upgrade -> 0001):")
        command.upgrade(alembic_cfg, "0001")
        rev_after_0001 = get_current_revision(engine)
        cols_0001 = get_table_columns(engine, "employees")
        print(f"   Текущая ревизия БД: {rev_after_0001}")
        print(f"   Столбцы таблицы employees: {cols_0001}")
        assert rev_after_0001 == "0001"
        assert "email" not in cols_0001

        print("\n2. Применение второй миграции (upgrade -> head / 0002):")
        command.upgrade(alembic_cfg, "head")
        rev_after_head = get_current_revision(engine)
        cols_0002 = get_table_columns(engine, "employees")
        print(f"   Текущая ревизия БД: {rev_after_head}")
        print(f"   Столбцы таблицы employees: {cols_0002}")
        assert rev_after_head == "0002"
        assert "email" in cols_0002 and "hire_date" in cols_0002

        print("\n3. Добавление записей через ORM SQLAlchemy после миграции:")
        with Session(engine) as session:
            dept = Department(name="Отдел разработки ПО", budget=3500000.0)
            session.add(dept)
            session.flush()

            emp = Employee(
                full_name="Берченёв Егор Константинович",
                position="Python Backend Developer",
                salary=180000.0,
                department_id=dept.id,
                email="egor.berchenev@example.com",
                hire_date="2026-09-01",
            )
            session.add(emp)
            session.commit()

            loaded = session.query(Employee).first()
            assert loaded is not None
            print(
                f"   Запись в БД: {loaded.full_name} ({loaded.position}), "
                f"email={loaded.email}, дата приёма={loaded.hire_date}"
            )

        print("\n4. Демонстрация отката миграции (downgrade -> 0001):")
        command.downgrade(alembic_cfg, "0001")
        cols_after_downgrade = get_table_columns(engine, "employees")
        print(f"   Текущая ревизия БД: {get_current_revision(engine)}")
        print(f"   Столбцы после отката: {cols_after_downgrade}")
        assert "email" not in cols_after_downgrade

        print("\n5. Повторный накат до актуальной версии (upgrade -> head):")
        command.upgrade(alembic_cfg, "head")
        assert get_current_revision(engine) == "0002"
        print(f"   Финальная ревизия БД: {get_current_revision(engine)}")
    finally:
        engine.dispose()
        if db_file.exists():
            db_file.unlink()


if __name__ == "__main__":
    main()
