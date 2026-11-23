"""Create tables, departments and the first admin. Safe to re-run (never deletes data).
Usage: python seed.py            (prompts for admin email/password)
       python seed.py --demo     (also adds a demo student + complaints)"""
import os, sys, getpass
from app import create_app, db
from app.models import *

DEPTS = ["IT Support", "Electrical Maintenance", "Civil Maintenance", "Hostel Administration",
         "Library Administration", "Housekeeping", "General Administration"]
app = create_app()
with app.app_context():
    db.create_all()
    for n in DEPTS:
        if not Department.query.filter_by(department_name=n).first(): db.session.add(Department(department_name=n))
    db.session.commit()
    email = (os.getenv("ADMIN_EMAIL") or input("Admin email: ")).strip().lower()
    if not Admin.query.filter_by(email=email).first():
        pw = os.getenv("ADMIN_PASSWORD") or getpass.getpass("Admin password (min 8 chars): ")
        if len(pw) < 8: sys.exit("Password too short")
        a = Admin(name="Administrator", email=email); a.set_password(pw)
        db.session.add(a); db.session.commit(); print("Admin created.")
    if "--demo" in sys.argv and not Student.query.filter_by(email="demo.student@example.com").first():
        st = Student(name="Demo Student", email="demo.student@example.com", academic_department="Computer Science", year_of_study=2)
        st.set_password("DemoPass123"); db.session.add(st); db.session.flush()
        for t, cat, loc in [("Projector not working", "Classroom", "A Block, Floor 2, Room 204"),
                            ("Wi-Fi drops in the evening", "Wi-Fi and Internet", "Boys Hostel, Floor 3"),
                            ("Tap leaking in washroom", "Water Supply", "C Block, Ground Floor, Room 011")]:
            c = Complaint(student_id=st.student_id, title=t, category=cat, location=loc, description="Demo complaint for presentation.")
            db.session.add(c); db.session.flush(); c.reference = f"CMP-DEMO-{c.complaint_id:05d}"
        db.session.commit(); print("Demo student: demo.student@example.com / DemoPass123")
