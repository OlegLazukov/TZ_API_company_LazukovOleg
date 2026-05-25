from datetime import datetime

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend import app
from database import Base
from models_data_base import Department, Employee

DATABASE_URL = "postgresql://postgres:1039Gau41`*din@localhost:5432/company"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

@pytest.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app)) as client:
        yield client



@pytest.mark.asyncio
async def test_create_department(async_client, db_session):
    new_department_data = {
        "name": "Finance",
        "parent_id": None
    }

    response = await async_client.post("http://localhost:8000/departments/", json=new_department_data)

    assert response.status_code == 200
    assert response.json()["name"] == new_department_data["name"]

    db_department = db_session.query(Department).filter_by(name="Finance").first()
    assert db_department is not None


@pytest.mark.asyncio
async def test_delete_department_cascade(async_client, db_session):
    department = db_session.query(Department).first()
    assert department is not None

    response = await async_client.delete(f"http://localhost:8000/departments/{department.id}?mode=cascade&department_id={department.id}")
    print(response.json())
    assert response.status_code == 200
    assert response.json()["detail"] == "Department deleted"

    db_department = db_session.query(Department).filter_by(id=department.id).first()
    assert db_department is None


@pytest.mark.asyncio
async def test_delete_department_reassign(async_client, db_session):
    old_department = db_session.query(Department).first()
    if not old_department:
        old_department = Department(name="Old Department")
        db_session.add(old_department)
        db_session.commit()

    new_department = db_session.query(Department).filter(Department.id != old_department.id).first()
    if not new_department:
        new_department = Department(name="New Department")
        db_session.add(new_department)
        db_session.commit()


    employee = Employee(full_name="Employee 1", position="Developer", department_id=old_department.id, created_at=datetime.now())
    db_session.add(employee)
    db_session.commit()

    assert old_department is not None
    assert new_department is not None

    response = await async_client.delete(
        f"http://localhost:8000/departments/{old_department.id}?mode=reassign&reassign_to_department_id={new_department.id}&department_id={old_department.id}"
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json()["detail"] == "Department deleted and employees reassigned"

    employees = db_session.query(Employee).filter_by(department_id=old_department.id).all()
    for employee in employees:
        assert employee.department_id == new_department.id

    db_department = db_session.query(Department).filter_by(id=old_department.id).first()
    assert db_department is None