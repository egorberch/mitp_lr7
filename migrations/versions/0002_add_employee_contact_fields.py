"""Добавление полей email и hire_date в таблицу employees (ревизия 0002)."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Добавляет колонки email и hire_date и создаёт индекс по email."""
    with op.batch_alter_table("employees") as batch_op:
        batch_op.add_column(
            sa.Column("email", sa.String(length=120), nullable=True)
        )
        batch_op.add_column(
            sa.Column("hire_date", sa.String(length=20), nullable=True)
        )
        batch_op.create_index("ix_employees_email", ["email"], unique=True)


def downgrade() -> None:
    """Удаляет индекс и добавленные колонки email и hire_date."""
    with op.batch_alter_table("employees") as batch_op:
        batch_op.drop_index("ix_employees_email")
        batch_op.drop_column("hire_date")
        batch_op.drop_column("email")
