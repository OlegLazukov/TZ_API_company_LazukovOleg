🏢 Company Departments API
API для управления отделами и сотрудниками компании
На базе FastAPI, SQLAlchemy, PostgreSQL.
Быстрый старт через Docker Compose 🚀

📄 Описание проекта
Данный сервис предназначен для хранения и управления иерархией департаментов (отделов) компании, а также персоналом в этих отделах.

⚙️ Функционал
Создание/редактирование департаментов с вложенной структурой ("дерево").
Добавление сотрудников в отделы.
Получение информации о департаменте (с сотрудниками и дочерними отделами).
Удаление департаментов (с каскадным удалением или переназначением сотрудников).
Изменение связей между отделами (поддержка вложенности).
Миграции через alembic.
🧩 Структура моделей
Модель	Атрибуты
Department	id, name, parent_id(родительский отдел), created_at, children (дочерние), employees (сотрудники)
Employee	id, department_id, full_name, position, hired_at, created_at, department (ссылка на отдел)
🚀 Быстрый старт
git clone https://your-git-url/project.git
cd pythonProject1
cp .env.example .env   # Создай свой .env файл по примеру!
docker-compose up --build
⏳ После запуска сервис будет доступен по адресу:
http://localhost:8000/docs — Swagger UI
Настроено тестирование для end-point: 
- Создание/редактирование департаментов;
- Удаление департаментов;
Запустить тесты при помощи команды --asyncio-mode=auto.
 
⚒️ Переменные окружения (.env)
Пример .env:

POSTGRES_DB=company
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
DATABASE_URL=postgresql://postgres:yourpassword@db:5432/company
📝 Основные ручки API
Метод	URL	Назначение
POST	/departments/	Создать департамент
PATCH	/departments/{department_id}	Изменить департамент
DELETE	/departments/{id}?mode=...	Удалить департамент: каскадом или пересчет
GET	/departments/{id}	Получить инфо об отделе (+ дерево вложений)
POST	/departments/{id}/employees/	Добавить сотрудника в департамент
Открыть OpenAPI документацию: http://localhost:8000/docs

🐳 Запуск с миграциями
Предварительно сгенерируй миграции:

alembic revision --autogenerate -m "init"
alembic upgrade head
⭐️ Или запускай alembic из контейнера:

docker-compose exec web alembic upgrade head
(Если нужно заполнить БД дампом — положи dump.sql рядом с docker-compose.yml)

👤 Пример тела запроса
➕ Создать департамент
POST /departments/
{
  "name": "IT",
  "parent_id": null
}
➕ Добавить сотрудника
POST /departments/{id}/employees/
{
  "full_name": "Ivan Ivanov",
  "position": "Engineer",
  "hired_at": "2024-01-01"
}
🔁 Удаление департамента
Каскадно (с удалением всех вложенных и сотрудников):
DELETE /departments/{id}?mode=cascade
Передать сотрудников в другой отдел:
DELETE /departments/{id}?mode=reassign&reassign_to_department_id={new_id}
📚 Зависимости
Python 3.10+
FastAPI
SQLAlchemy
Alembic
pydantic
PostgreSQL
