## Берченёв Егор Константинович, группа 220042-11, вариант 3, лабораторная №7

## "Работа с различными СУБД в Python"

## Задания варианта 3:

Средней сложности:
- №3 - Выбрать данные из таблицы (`select_data.py`)
- №5 - Удалить запись (`delete_record.py`)
- №9 - Экспорт данных в CSV (`export_to_csv.py`)

Повышенной сложности:
- №3 - Миграции Alembic (`alembic_migrations.py`, `alembic.ini`, `migrations/`)
- №7 - FastAPI + SQLAlchemy (REST) (`fastapi_sqlalchemy_rest.py`)

## Инструкция по запуску:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python select_data.py
python delete_record.py
python export_to_csv.py
python alembic_migrations.py
python fastapi_sqlalchemy_rest.py
```

Для запуска REST API сервера в интерактивном режиме (Swagger UI доступен по адресу `http://127.0.0.1:8000/docs`):

```
python fastapi_sqlalchemy_rest.py --serve
```

Все скрипты оформлены по PEP8 и проверены FLAKE8 (`python -m flake8 .`).
