"""Задание №9 (средней сложности): Экспорт данных в CSV."""

import csv
from pathlib import Path
import sqlite3
from typing import Dict, List, Tuple


class OrderCsvExporter:
    """Менеджер базы данных заказов с поддержкой экспорта выборок в CSV."""

    def __init__(self, db_path: str = ":memory:") -> None:
        """Создаёт подключение к БД SQLite и инициализирует таблицу."""
        self.db_path = db_path
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        """Создаёт таблицу orders для хранения данных о заказах."""
        query = """
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK (quantity > 0),
            unit_price REAL NOT NULL CHECK (unit_price >= 0.0),
            order_date TEXT NOT NULL
        )
        """
        with self.connection:
            self.connection.execute(query)

    def seed_orders(
        self, orders: List[Tuple[str, str, int, float, str]]
    ) -> int:
        """Заполняет таблицу orders демонстрационными данными."""
        query = """
        INSERT INTO orders (
            customer, product, quantity, unit_price, order_date
        )
        VALUES (?, ?, ?, ?, ?)
        """
        with self.connection:
            cursor = self.connection.executemany(query, orders)
            return cursor.rowcount

    def export_all_to_csv(
        self, csv_path: Path, delimiter: str = ","
    ) -> int:
        """Экспортирует все записи таблицы orders в CSV-файл."""
        query = """
        SELECT
            id,
            customer,
            product,
            quantity,
            unit_price,
            ROUND(quantity * unit_price, 2) AS total_price,
            order_date
        FROM orders
        ORDER BY id ASC
        """
        cursor = self.connection.execute(query)
        rows = cursor.fetchall()
        headers: List[str] = []
        if cursor.description is not None:
            headers = [str(column[0]) for column in cursor.description]

        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file, delimiter=delimiter)
            writer.writerow(headers)
            for row in rows:
                writer.writerow(list(row))

        return len(rows)

    def export_filtered_to_csv(
        self, csv_path: Path, min_total: float
    ) -> int:
        """Экспортирует заказы со стоимостью не ниже порога min_total."""
        query = """
        SELECT
            id,
            customer,
            product,
            quantity,
            unit_price,
            ROUND(quantity * unit_price, 2) AS total_price,
            order_date
        FROM orders
        WHERE quantity * unit_price >= ?
        ORDER BY total_price DESC
        """
        cursor = self.connection.execute(query, (min_total,))
        records = [dict(row) for row in cursor.fetchall()]
        fieldnames = [
            "id",
            "customer",
            "product",
            "quantity",
            "unit_price",
            "total_price",
            "order_date",
        ]

        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)

        return len(records)

    @staticmethod
    def read_csv_records(
        csv_path: Path, delimiter: str = ","
    ) -> List[Dict[str, str]]:
        """Читает экспортированный CSV-файл и возвращает список словарей."""
        with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            return list(reader)

    def close(self) -> None:
        """Закрывает подключение к базе данных."""
        self.connection.close()


def main() -> None:
    """Демонстрирует экспорт таблицы SQLite в CSV и проверку содержимого."""
    db_file = Path("orders_export_demo.db")
    full_csv = Path("orders_all.csv")
    filtered_csv = Path("orders_filtered.csv")

    exporter = OrderCsvExporter(str(db_file))
    try:
        sample_orders: List[Tuple[str, str, int, float, str]] = [
            (
                "ООО «ТехноПром»",
                "Серверная стойка 42U",
                2,
                48500.0,
                "2026-10-01",
            ),
            (
                "ИП Смирнов А.В.",
                "Коммутатор L3 24-port",
                3,
                21900.0,
                "2026-10-03",
            ),
            (
                "АО «Вектор»",
                "ИБП 3000VA Rack",
                1,
                34200.0,
                "2026-10-05",
            ),
            (
                "ООО «АльфаСофт»",
                "Патч-корд Cat6 (уп.)",
                10,
                1250.0,
                "2026-10-07",
            ),
        ]
        exporter.seed_orders(sample_orders)

        total_exported = exporter.export_all_to_csv(full_csv)
        assert total_exported == 4
        print(
            f"Экспортировано всех заказов в '{full_csv.name}': "
            f"{total_exported}"
        )

        loaded_all = exporter.read_csv_records(full_csv)
        assert len(loaded_all) == 4
        print("\nСодержимое полного CSV-файла:")
        for row in loaded_all:
            print(
                f"  #{row['id']} | {row['customer']} | {row['product']} | "
                f"{row['quantity']} шт. x {row['unit_price']} = "
                f"{row['total_price']} руб. ({row['order_date']})"
            )

        filtered_count = exporter.export_filtered_to_csv(
            filtered_csv, min_total=40000.0
        )
        assert filtered_count == 2
        print(
            f"\nЭкспортировано крупных заказов (>= 40 000 руб.) "
            f"в '{filtered_csv.name}': {filtered_count}"
        )

        loaded_filtered = exporter.read_csv_records(filtered_csv)
        for row in loaded_filtered:
            print(
                f"  #{row['id']} | {row['customer']} | "
                f"Итого: {row['total_price']} руб."
            )
    finally:
        exporter.close()
        for temp_path in (db_file, full_csv, filtered_csv):
            if temp_path.exists():
                temp_path.unlink()


if __name__ == "__main__":
    main()
