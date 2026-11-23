"""Regenerates ../database/schema.sql from the SQLAlchemy models (MySQL dialect)."""
import os
from sqlalchemy.dialects import mysql
from sqlalchemy.schema import CreateTable, CreateIndex
from app import create_app, db
import app.models
out = ["CREATE DATABASE IF NOT EXISTS campus_complaints CHARACTER SET utf8mb4;", "USE campus_complaints;", ""]
d = mysql.dialect()
for t in db.metadata.sorted_tables:
    out.append(str(CreateTable(t).compile(dialect=d)).strip() + ";")
    out += [str(CreateIndex(i).compile(dialect=d)) + ";" for i in sorted(t.indexes, key=lambda i: i.name)]
out += ["", "INSERT IGNORE INTO departments (department_name) VALUES ('IT Support'),('Electrical Maintenance'),('Civil Maintenance'),('Hostel Administration'),('Library Administration'),('Housekeeping'),('General Administration');"]
os.makedirs("../database", exist_ok=True); open("../database/schema.sql", "w").write("\n".join(out) + "\n")
