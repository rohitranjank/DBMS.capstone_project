from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

def iso(d): return d.isoformat() + "Z" if d else None

class PasswordMixin:
    def set_password(self, p): self.password_hash = generate_password_hash(p)
    def check_password(self, p): return check_password_hash(self.password_hash, p)

class Student(db.Model, PasswordMixin):
    __tablename__ = "students"
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    academic_department = db.Column(db.String(100), nullable=False)
    year_of_study = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def to_dict(self):
        return dict(id=self.student_id, role="student", name=self.name, email=self.email,
                    academic_department=self.academic_department, year_of_study=self.year_of_study)

class Admin(db.Model, PasswordMixin):
    __tablename__ = "admins"
    admin_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def to_dict(self): return dict(id=self.admin_id, role="admin", name=self.name, email=self.email)

class Department(db.Model):
    __tablename__ = "departments"
    department_id = db.Column(db.Integer, primary_key=True)
    department_name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    def to_dict(self): return dict(id=self.department_id, name=self.department_name, description=self.description)

class Complaint(db.Model):
    __tablename__ = "complaints"
    complaint_id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.student_id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id", ondelete="SET NULL"), index=True)
    title = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(40), nullable=False, index=True)
    location = db.Column(db.String(150), nullable=False)  # e.g. "B Block, Floor 2, Room 215"
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending", index=True)
    priority = db.Column(db.String(10), nullable=False, default="Medium", index=True)
    assigned_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    resolution_details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    student = db.relationship("Student", backref="complaints")
    department = db.relationship("Department")
    updates = db.relationship("ComplaintUpdate", backref="complaint", order_by="ComplaintUpdate.update_id.desc()")
    def to_dict(self, detail=False):
        d = dict(id=self.complaint_id, reference=self.reference, title=self.title, category=self.category,
                 location=self.location, status=self.status, priority=self.priority,
                 department=self.department.department_name if self.department else None,
                 student_name=self.student.name, created_at=iso(self.created_at))
        if detail:
            d.update(description=self.description, department_id=self.department_id,
                     resolution_details=self.resolution_details, resolved_at=iso(self.resolved_at),
                     student_email=self.student.email, updated_at=iso(self.updated_at),
                     history=[u.to_dict() for u in self.updates])
        return d

class ComplaintUpdate(db.Model):
    __tablename__ = "complaint_updates"
    update_id = db.Column(db.Integer, primary_key=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey("complaints.complaint_id", ondelete="CASCADE"), nullable=False, index=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("admins.admin_id"), nullable=False)
    old_status = db.Column(db.String(20))
    new_status = db.Column(db.String(20))
    old_department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id", ondelete="SET NULL"))
    new_department_id = db.Column(db.Integer, db.ForeignKey("departments.department_id", ondelete="SET NULL"))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin = db.relationship("Admin")
    new_department = db.relationship("Department", foreign_keys=[new_department_id])
    def to_dict(self):
        return dict(id=self.update_id, admin=self.admin.name, old_status=self.old_status, new_status=self.new_status,
                    department=self.new_department.department_name if self.new_department else None,
                    remarks=self.remarks, created_at=iso(self.created_at))
