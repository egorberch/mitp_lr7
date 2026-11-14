"""Создание таблиц подразделений и сотрудников (ревизия 0001)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Создаёт базовые таблицы departments и employees."""
    op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("budget", sa.Float(), nullable=False, server_default="0.0"),
    )
    op.create_table(
        "employees",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("position", sa.String(length=100), nullable=False),
        sa.Column("salary", sa.Float(), nullable=False),
        sa.Column(
            "department_id",
            sa.Integer(),
            sa.ForeignKey("departments.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Удаляет таблицы employees и departments при откате."""
    op.drop_table("employees")
    op.drop_table("departments")
