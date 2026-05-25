from fastapi import FastAPI, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from models_data_base import Base, Department, Employee
from database import SessionLocal, engine
from pydantic import BaseModel, constr
from datetime import datetime, date
from typing import Optional



app = FastAPI()
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DepartmentCreate(BaseModel):
    name: constr(min_length=1, max_length=200)
    parent_id: Optional[int] = None

    @classmethod
    def validate_name(cls, name: str):
        return name.strip()


class EmployeeCreate(BaseModel):
    full_name: constr(min_length=1, max_length=200)
    position: constr(min_length=1, max_length=200)
    hired_at: Optional[date] = None


@app.post("/departments/", response_model=DepartmentCreate)
def create_department(department: DepartmentCreate, db: Session = Depends(get_db)):
    department.name = department.name.strip()

    if department.parent_id:
        existing_department = db.query(Department).filter(
            department.name == Department.name,
            department.parent_id == Department.parent_id
        ).first()

        if existing_department:
            raise HTTPException(status_code=400, detail="Department name must be unique within the same parent")

    db_department = Department(**department.model_dump(), created_at=datetime.now())
    try:
        db.add(db_department)
        db.commit()
        db.refresh(db_department)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error during operation")
    return db_department


@app.post("/departments/{id}/employees/")
def create_employee(department_id: int, employee: EmployeeCreate, db: Session = Depends(get_db)):
    department = db.query(Department).filter(department_id == Department.id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    db_employee = Employee(**employee.model_dump(), department_id=department_id, created_at=datetime.now())
    try:
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error during operation")
    return db_employee


@app.get("/departments/{id}")
def get_department(department_id: int, depth: int = Query(1, le=5), include_employees: bool = True, db: Session = Depends(get_db)):
    department = db.query(Department).filter(department_id == Department.id).first()
    if not department:
        raise HTTPException(status_code=404, detail="Department not found")

    def get_children(department_child_id: int, current_depth: int):
        if current_depth == 0:
            return []
        children = db.query(Department).filter(department_child_id == Department.parent_id).all()
        return [{
            "department": dept.name,
            "id": dept.id,
            "children": get_children(dept.id, current_depth - 1)
        } for dept in children]

    department_data = {
        "department": department.name,
        "id": department.id,
        "employees": [emp.full_name for emp in department.employees] if include_employees else [],
        "children": get_children(department.id, depth)
    }
    return department_data


@app.patch("/departments/{department_id}")
def change_department(department_id: int, department: DepartmentCreate, db: Session = Depends(get_db)):
    db_department = db.query(Department).filter(department_id == Department.id).first()
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")

    if department.parent_id == department_id:
        raise HTTPException(status_code=400, detail="Cannot assign the department as its own parent")

    if department.parent_id:
        parent_ids = []
        current_parent_id = department.parent_id

        while current_parent_id:
            parent_department = db.query(Department).filter(current_parent_id == Department.id).first()
            if not parent_department:

                raise HTTPException(status_code=400, detail="Parent department does not exist")
            if parent_department.id == department_id:
                raise HTTPException(status_code=409, detail="Creating a cycle in hierarchy is not allowed")

            parent_ids.append(parent_department.id)
            current_parent_id = parent_department.parent_id
    db_department.name = department.name.strip()
    db_department.parent_id = department.parent_id
    try:
        db.commit()
        db.refresh(db_department)
    except Exception:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error during operation")
    return {"Update department": db_department}

@app.delete("/departments/{id}")
def delete_department(department_id: int, mode: str, reassign_to_department_id: Optional[int] = None,
                      db: Session = Depends(get_db)):
    db_department = db.query(Department).filter(department_id == Department.id).first()
    if not db_department:
        raise HTTPException(status_code=404, detail="Department not found")

    if mode == "cascade":
        try:
            db.delete(db_department)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error during operation")

        return {"detail": "Department deleted"}

    elif mode == "reassign":
        if not reassign_to_department_id:
            raise HTTPException(status_code=400, detail="Must provide reassign_to_department_id in reassign mode")
        employees = db.query(Employee).filter(department_id == Employee.department_id).all()
        if not employees:
            return {"detail": "No employees found in the department to reassign."}
        new_department = db.query(Department).filter(reassign_to_department_id == Department.id).first()

        if not new_department:
            raise HTTPException(status_code=404, detail="New department not found")

        for employee in employees:
            employee.department_id = reassign_to_department_id

        try:
            db.commit()
            db.delete(db_department)
            db.commit()
        except Exception:
            db.rollback()
            raise HTTPException(status_code=500, detail="Error during operation")

        return {"detail": "Department deleted and employees reassigned"}
    else:
        raise HTTPException(status_code=400, detail="Unsupported mode")