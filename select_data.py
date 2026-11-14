"""Задание №3 (средней сложности): Выбрать данные из таблицы."""

from pathlib import Path
import sqlite3
from typing import Any, Dict, List, Optional, Tuple


class StudentDatabase:
    """Менеджер базы данных SQLite для выборки записей о студентах."""

    def __init__(self, db_path: str = ":memory:") -> None:
        """Инициализирует подключение к базе данных и создаёт таблицу."""
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        """Создаёт таблицу students, если она ещё не существует."""
        query = """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            group_name TEXT NOT NULL,
            course INTEGER NOT NULL CHECK (course BETWEEN 1 AND 6),
            gpa REAL NOT NULL CHECK (gpa BETWEEN 0.0 AND 5.0)
        )
        """
        with self.connection:
            self.connection.execute(query)

    def seed_sample_data(
        self, records: List[Tuple[str, str, int, float]]
    ) -> int:
        """Заполняет таблицу начальным набором записей о студентах."""
        query = """
        INSERT INTO students (full_name, group_name, course, gpa)
        VALUES (?, ?, ?, ?)
        """
        with self.connection:
            cursor = self.connection.executemany(query, records)
            return cursor.rowcount

    def select_all(self) -> List[Dict[str, Any]]:
        """Возвращает все записи, отсортированные по среднему баллу."""
        query = """
        SELECT id, full_name, group_name, course, gpa
        FROM students
        ORDER BY gpa DESC, id ASC
        """
        cursor = self.connection.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def select_by_id(self, student_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает одну запись студента по его идентификатору."""
        query = """
        SELECT id, full_name, group_name, course, gpa
        FROM students
        WHERE id = ?
        """
        cursor = self.connection.execute(query, (student_id,))
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(row)

    def select_by_group(self, group_name: str) -> List[Dict[str, Any]]:
        """Возвращает список студентов указанной учебной группы."""
        query = """
        SELECT id, full_name, group_name, course, gpa
        FROM students
        WHERE group_name = ?
        ORDER BY full_name ASC
        """
        cursor = self.connection.execute(query, (group_name,))
        return [dict(row) for row in cursor.fetchall()]

    def select_by_min_gpa(self, min_gpa: float) -> List[Dict[str, Any]]:
        """Выбирает студентов со средним баллом не ниже заданного порога."""
        query = """
        SELECT id, full_name, group_name, course, gpa
        FROM students
        WHERE gpa >= ?
        ORDER BY gpa DESC
        """
        cursor = self.connection.execute(query, (min_gpa,))
        return [dict(row) for row in cursor.fetchall()]

    def select_group_statistics(self) -> List[Dict[str, Any]]:
        """Выполняет агрегированную выборку статистики по учебным группам."""
        query = """
        SELECT
            group_name,
            COUNT(*) AS student_count,
            ROUND(AVG(gpa), 2) AS avg_gpa,
            MAX(gpa) AS max_gpa,
            MIN(gpa) AS min_gpa
        FROM students
        GROUP BY group_name
        ORDER BY avg_gpa DESC
        """
        cursor = self.connection.execute(query)
        return [dict(row) for row in cursor.fetchall()]

    def close(self) -> None:
        """Закрывает соединение с базой данных."""
        self.connection.close()


def format_student_row(student: Dict[str, Any]) -> str:
    """Форматирует словарь с данными студента в читаемую строку."""
    return (
        f"  [ID {student['id']}] {student['full_name']} | "
        f"Группа: {student['group_name']} | "
        f"Курс: {student['course']} | "
        f"Средний балл: {student['gpa']:.2f}"
    )


def main() -> None:
    """Демонстрирует различные варианты выборки данных из таблицы SQLite."""
    db_file = Path("students_select_demo.db")
    if db_file.exists():
        db_file.unlink()

    db = StudentDatabase(str(db_file))
    try:
        sample_students: List[Tuple[str, str, int, float]] = [
            ("Берченёв Егор Константинович", "220042-11", 3, 4.95),
            ("Соколов Андрей Викторович", "220042-11", 3, 4.60),
            ("Морозова Анна Сергеевна", "220042-12", 3, 4.85),
            ("Волков Дмитрий Игоревич", "220042-11", 3, 4.20),
            ("Лебедева Мария Алексеевна", "220042-12", 3, 3.90),
        ]
        inserted = db.seed_sample_data(sample_students)
        print(f"Добавлено записей в таблицу students: {inserted}")

        print("\n1. Выборка всех записей (SELECT * ORDER BY gpa DESC):")
        all_students = db.select_all()
        assert len(all_students) == 5
        for item in all_students:
            print(format_student_row(item))

        print("\n2. Выборка записи по первичному ключу (WHERE id = 1):")
        first_student = db.select_by_id(1)
        assert first_student is not None
        print(format_student_row(first_student))

        print("\n3. Выборка студентов группы 220042-11:")
        group_students = db.select_by_group("220042-11")
        assert len(group_students) == 3
        for item in group_students:
            print(format_student_row(item))

        print("\n4. Выборка отличников со средним баллом >= 4.70:")
        honors = db.select_by_min_gpa(4.70)
        assert len(honors) == 2
        for item in honors:
            print(format_student_row(item))

        print("\n5. Агрегированная статистика по группам (GROUP BY):")
        stats = db.select_group_statistics()
        assert len(stats) == 2
        for group_stat in stats:
            print(
                f"  Группа {group_stat['group_name']}: "
                f"студентов={group_stat['student_count']}, "
                f"средний={group_stat['avg_gpa']:.2f}, "
                f"макс={group_stat['max_gpa']:.2f}, "
                f"мин={group_stat['min_gpa']:.2f}"
            )
    finally:
        db.close()
        if db_file.exists():
            db_file.unlink()


if __name__ == "__main__":
    main()
