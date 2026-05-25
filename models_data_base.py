from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(length=200), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    created_at = Column(DateTime, nullable=False)
    children = relationship("Department", back_populates="parent", cascade="all, delete-orphan")
    parent = relationship("Department", back_populates="children", remote_side=id)
    employees = relationship("Employee", back_populates="department", cascade="all, delete-orphan")

class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"))
    full_name = Column(String(length=200), nullable=False)
    position = Column(String(length=200), nullable=False)
    hired_at = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False)

    department = relationship("Department", back_populates="employees")