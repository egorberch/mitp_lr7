"""Задание №5 (средней сложности): Удалить запись."""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


class TaskDatabase:
    """Менеджер базы данных SQLite с операциями удаления записей."""

    def __init__(self, db_path: str = ":memory:") -> None:
        """Открывает соединение с БД и инициализирует схему таблицы задач."""
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        """Создаёт таблицу tasks для хранения проектных задач."""
        query = """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            priority INTEGER NOT NULL CHECK (priority BETWEEN 1 AND 5),
            is_completed INTEGER NOT NULL DEFAULT 0
        )
        """
        with self.connection:
            self.connection.execute(query)

    def add_task(
        self,
        title: str,
        category: str,
        priority: int,
        is_completed: bool = False,
    ) -> Optional[int]:
        """Добавляет новую задачу и возвращает её идентификатор."""
        query = """
        INSERT INTO tasks (title, category, priority, is_completed)
        VALUES (?, ?, ?, ?)
        """
        with self.connection:
            cursor = self.connection.execute(
                query, (title, category, priority, int(is_completed))
            )
            return cursor.lastrowid

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Возвращает список всех текущих задач в таблице."""
        query = """
        SELECT id, title, category, priority, is_completed
        FROM tasks
        ORDER BY id ASC
        """
        cursor = self.connection.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def delete_by_id(self, task_id: int) -> bool:
        """Удаляет запись по идентификатору и возвращает статус успеха."""
        query = "DELETE FROM tasks WHERE id = ?"
        with self.connection:
            cursor = self.connection.execute(query, (task_id,))
            return cursor.rowcount > 0

    def delete_completed(self) -> int:
        """Удаляет выполненные задачи и возвращает их количество."""
        query = "DELETE FROM tasks WHERE is_completed = 1"
        with self.connection:
            cursor = self.connection.execute(query)
            return cursor.rowcount

    def delete_by_category(self, category: str) -> int:
        """Удаляет задачи указанной категории и возвращает их количество."""
        query = "DELETE FROM tasks WHERE category = ?"
        with self.connection:
            cursor = self.connection.execute(query, (category,))
            return cursor.rowcount

    def clear_all(self) -> int:
        """Очищает таблицу задач и возвращает число удалённых строк."""
        query = "DELETE FROM tasks"
        with self.connection:
            cursor = self.connection.execute(query)
            return cursor.rowcount

    def close(self) -> None:
        """Закрывает подключение к базе данных."""
        self.connection.close()


def print_tasks(title: str, tasks: List[Dict[str, Any]]) -> None:
    """Выводит отформатированный список задач в консоль."""
    print(f"\n{title} (всего: {len(tasks)}):")
    if not tasks:
        print("  [Таблица пуста]")
        return
    for task in tasks:
        status = "Выполнена" if task["is_completed"] else "В работе"
        print(
            f"  [ID {task['id']}] {task['title']} | "
            f"Категория: {task['category']} | "
            f"Приоритет: {task['priority']} | Статус: {status}"
        )


def main() -> None:
    """Демонстрирует одиночное, условное и пакетное удаление записей из БД."""
    db_file = Path("tasks_delete_demo.db")
    if db_file.exists():
        db_file.unlink()

    db = TaskDatabase(str(db_file))
    try:
        initial_tasks: List[Tuple[str, str, int, bool]] = [
            ("Настроить схему БД SQLite", "database", 5, True),
            ("Написать SQL-запросы выборки", "database", 4, True),
            ("Реализовать экспорт в CSV", "backend", 3, False),
            ("Настроить миграции Alembic", "devops", 5, False),
            ("Обновить устаревшие логи", "maintenance", 1, False),
        ]
        for title, category, priority, done in initial_tasks:
            db.add_task(title, category, priority, done)

        print_tasks("Исходное состояние таблицы tasks", db.get_all_tasks())

        deleted_single = db.delete_by_id(5)
        assert deleted_single is True
        print("\nУдаление записи с ID=5 выполнено:", deleted_single)

        deleted_missing = db.delete_by_id(999)
        assert deleted_missing is False
        print("Попытка удаления несуществующего ID=999:", deleted_missing)
        print_tasks("После удаления записи с ID=5", db.get_all_tasks())

        removed_done = db.delete_completed()
        assert removed_done == 2
        print(f"\nУдалено выполненных задач: {removed_done}")
        print_tasks(
            "После удаления выполненных задач", db.get_all_tasks()
        )

        removed_cat = db.delete_by_category("devops")
        assert removed_cat == 1
        print(f"\nУдалено задач категории 'devops': {removed_cat}")
        remaining = db.get_all_tasks()
        assert len(remaining) == 1
        print_tasks("Итоговое состояние таблицы tasks", remaining)
    finally:
        db.close()
        if db_file.exists():
            db_file.unlink()


if __name__ == "__main__":
    main()
