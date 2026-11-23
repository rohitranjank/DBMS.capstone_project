import hmac, re, time
from datetime import datetime
from functools import wraps
from secrets import token_hex
from flask import Blueprint, jsonify, request, session
from sqlalchemy import or_, func
from . import db
from .models import Student, Admin, Department, Complaint, ComplaintUpdate

bp = Blueprint("api", __name__, url_prefix="/api")
CATEGORIES = ["Classroom", "Laboratory", "Hostel", "Library", "Wi-Fi and Internet", "Electricity",
              "Water Supply", "Cleanliness", "Infrastructure", "Other"]
STATUSES = ["Pending", "In Progress", "Resolved", "Rejected"]
PRIORITIES = ["Low", "Medium", "High", "Urgent"]
# Allowed status changes (Resolved -> In Progress is a "reopen", Rejected -> Pending a re-review)
TRANSITIONS = {"Pending": {"In Progress", "Resolved", "Rejected"}, "In Progress": {"Pending", "Resolved", "Rejected"},
               "Resolved": {"In Progress"}, "Rejected": {"Pending"}}
BLOCKS = ["A Block", "B Block", "C Block", "D Block"]  # ground floor + floors 1-5, 22 classrooms per floor
HOSTELS = ["Boys Hostel", "Girls Hostel"]              # floors 1-6
BUILDINGS = BLOCKS + HOSTELS
FAILS = {}  # ip -> (count, last_time); in-memory login rate limit

def ok(data=None, status=200, **extra): return jsonify(success=True, data=data, **extra), status
def err(msg, status=400, fields=None): return jsonify(success=False, error=msg, fields=fields or {}), status

@bp.before_request
def csrf_check():
    if request.method in ("POST", "PATCH", "PUT", "DELETE"):
        sent, real = request.headers.get("X-CSRF-Token", ""), session.get("csrf", "")
        if not real or not hmac.compare_digest(sent, real): return err("Invalid CSRF token", 403)

@bp.errorhandler(413)
def too_big(e): return err("Request too large", 413)

def auth(*roles):
    def deco(f):
        @wraps(f)
        def w(*a, **k):
            if "uid" not in session: return err("Please log in", 401)
            if session["role"] not in roles: return err("You do not have access", 403)
            return f(*a, **k)
        return w
    return deco

def body(): return request.get_json(silent=True) or {}
def s(d, k): return str(d.get(k) or "").strip()

# ---------- auth ----------
@bp.get("/auth/csrf")
def csrf():
    session["csrf"] = session.get("csrf") or token_hex(16)
    return ok({"token": session["csrf"]})

def do_login(model, role):
    ip = request.remote_addr
    cnt, last = FAILS.get(ip, (0, 0))
    if time.time() - last > 300: cnt = 0
    if cnt >= 5: return err("Too many attempts. Try again in a few minutes.", 429)
    d = body()
    u = model.query.filter_by(email=s(d, "email").lower()).first()
    if not u or not u.check_password(str(d.get("password") or "")):
        FAILS[ip] = (cnt + 1, time.time())
        return err("Invalid email or password", 401)
    FAILS.pop(ip, None)
    token = session.get("csrf"); session.clear(); session["csrf"] = token
    session.permanent = True
    session.update(uid=u.student_id if role == "student" else u.admin_id, role=role)
    return ok(u.to_dict())

@bp.post("/auth/student/login")
def student_login(): return do_login(Student, "student")

@bp.post("/auth/admin/login")
def admin_login(): return do_login(Admin, "admin")

@bp.post("/auth/student/register")
def register():
    d, f = body(), {}
    name, email, pw, dept = s(d, "name"), s(d, "email").lower(), str(d.get("password") or ""), s(d, "academic_department")
    try: year = int(d.get("year_of_study"))
    except (TypeError, ValueError): year = 0
    if not 2 <= len(name) <= 100: f["name"] = "Name must be 2-100 characters"
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 150: f["email"] = "Enter a valid email"
    if len(pw) < 8: f["password"] = "Password must be at least 8 characters"
    if not 2 <= len(dept) <= 100: f["academic_department"] = "Enter your department"
    if not 1 <= year <= 6: f["year_of_study"] = "Year must be 1-6"
    if f: return err("Please fix the highlighted fields", 400, f)
    if Student.query.filter_by(email=email).first(): return err("An account with this email already exists", 409, {"email": "Already registered"})
    st = Student(name=name, email=email, academic_department=dept, year_of_study=year)
    st.set_password(pw)
    db.session.add(st); db.session.commit()
    return ok(st.to_dict(), 201)

@bp.post("/auth/logout")
def logout():
    session.clear()
    return ok()

@bp.get("/auth/me")
def me():
    if "uid" not in session: return err("Not logged in", 401)
    u = db.session.get(Student if session["role"] == "student" else Admin, session["uid"])
    if not u: session.clear(); return err("Not logged in", 401)
    return ok(u.to_dict())

@bp.post("/auth/change-password")
@auth("student", "admin")
def change_password():
    d = body(); u = db.session.get(Student if session["role"] == "student" else Admin, session["uid"])
    new = str(d.get("new_password") or "")
    if not u.check_password(str(d.get("current_password") or "")):
        return err("Current password is incorrect", 400, {"current_password": "Incorrect password"})
    if len(new) < 8: return err("New password is too short", 400, {"new_password": "At least 8 characters"})
    u.set_password(new); db.session.commit()
    return ok()

# ---------- helpers ----------
def page_of(q, fn=lambda c: c.to_dict()):
    try: page, per = max(int(request.args.get("page", 1)), 1), min(max(int(request.args.get("per_page", 10)), 1), 50)
    except ValueError: page, per = 1, 10
    total = q.order_by(None).count()
    items = q.order_by(Complaint.created_at.desc(), Complaint.complaint_id.desc()).offset((page - 1) * per).limit(per).all()
    return ok([fn(c) for c in items], total=total, page=page, pages=max(-(-total // per), 1))

def apply_filters(q, admin):
    a = request.args
    for col, key, allowed in ((Complaint.status, "status", STATUSES), (Complaint.category, "category", CATEGORIES),
                              (Complaint.priority, "priority", PRIORITIES)):
        if a.get(key) in allowed: q = q.filter(col == a[key])
    if a.get("department_id", "").isdigit(): q = q.filter(Complaint.department_id == int(a["department_id"]))
    if a.get("building") in BUILDINGS: q = q.filter(Complaint.location.startswith(a["building"]))
    term = a.get("q", "").strip()[:100]
    if term:
        like = f"%{term}%"
        conds = [Complaint.title.ilike(like), Complaint.reference.ilike(like), Complaint.location.ilike(like)]
        if admin: conds += [Student.name.ilike(like), Student.email.ilike(like)]
        q = q.filter(or_(*conds))
    for key, op in (("date_from", lambda c, d: c >= d), ("date_to", lambda c, d: c < d)):
        try: d = datetime.strptime(a[key], "%Y-%m-%d") if a.get(key) else None
        except ValueError: d = None
        if d:
            if key == "date_to": d = d.replace(hour=23, minute=59, second=59)
            q = q.filter(op(Complaint.created_at, d))
    return q

def counts(q):
    rows = dict(q.with_entities(Complaint.status, func.count()).group_by(Complaint.status).all())
    return {st: rows.get(st, 0) for st in STATUSES} | {"Total": sum(rows.values())}

def build_location(d):
    """K.R. Mangalam University locations, validated on the server. Returns (text, errors)."""
    b, fl, room = s(d, "building"), s(d, "floor"), s(d, "room")
    if b in BLOCKS:
        if fl not in {"0", "1", "2", "3", "4", "5"}: return "", {"floor": "Choose a floor"}
        if room not in {f"{int(fl) * 100 + n:03d}" for n in range(1, 23)}: return "", {"room": "Choose a classroom on this floor"}
        return f"{b}, {'Ground Floor' if fl == '0' else 'Floor ' + fl}, Room {room}", {}
    if b in HOSTELS:
        if fl not in {"1", "2", "3", "4", "5", "6"}: return "", {"floor": "Choose a floor (1-6)"}
        if len(room) > 20: return "", {"room": "Room number too long"}
        return f"{b}, Floor {fl}" + (f", Room {room}" if room else ""), {}
    if b == "Other":
        loc = s(d, "location")
        return (loc, {}) if 2 <= len(loc) <= 150 else ("", {"location": "Enter the location (2-150 characters)"})
    return "", {"building": "Choose a building"}

# ---------- student / complaints ----------
@bp.get("/student/dashboard")
@auth("student")
def student_dashboard():
    q = Complaint.query.filter_by(student_id=session["uid"])
    recent = q.order_by(Complaint.created_at.desc()).limit(5).all()
    return ok({"counts": counts(q), "recent": [c.to_dict() for c in recent]})

@bp.post("/complaints")
@auth("student")
def create_complaint():
    d, f = body(), {}
    title, desc, cat = s(d, "title"), s(d, "description"), s(d, "category")
    loc, lerr = build_location(d); f.update(lerr)
    if not 5 <= len(title) <= 150: f["title"] = "Title must be 5-150 characters"
    if cat not in CATEGORIES: f["category"] = "Choose a category"
    if not 10 <= len(desc) <= 2000: f["description"] = "Description must be 10-2000 characters"
    if f: return err("Please fix the highlighted fields", 400, f)
    c = Complaint(student_id=session["uid"], title=title, category=cat, location=loc, description=desc)
    db.session.add(c); db.session.flush()
    c.reference = f"CMP-{datetime.utcnow().year}-{c.complaint_id:05d}"
    db.session.commit()
    return ok(c.to_dict(), 201)

@bp.get("/complaints/my")
@auth("student")
def my_complaints():
    return page_of(apply_filters(Complaint.query.join(Student).filter(Complaint.student_id == session["uid"]), False))

def get_allowed(cid):
    c = db.session.get(Complaint, cid)
    # 404 (not 403) for other students' complaints so IDs cannot be probed
    if not c or (session["role"] == "student" and c.student_id != session["uid"]): return None
    return c

@bp.get("/complaints/<int:cid>")
@auth("student", "admin")
def complaint_detail(cid):
    c = get_allowed(cid)
    return ok(c.to_dict(True)) if c else err("Complaint not found", 404)

@bp.get("/complaints/<int:cid>/history")
@auth("student", "admin")
def complaint_history(cid):
    c = get_allowed(cid)
    return ok([u.to_dict() for u in c.updates]) if c else err("Complaint not found", 404)

# ---------- admin ----------
@bp.get("/admin/dashboard")
@auth("admin")
def admin_dashboard():
    q = Complaint.query
    cats = q.with_entities(Complaint.category, func.count()).group_by(Complaint.category).all()
    recent = q.order_by(Complaint.created_at.desc()).limit(5).all()
    return ok({"counts": counts(q), "categories": [{"name": n, "count": c} for n, c in cats],
               "recent": [c.to_dict() for c in recent]})

@bp.get("/admin/complaints")
@auth("admin")
def admin_complaints():
    return page_of(apply_filters(Complaint.query.join(Student), True))

@bp.get("/admin/complaints/<int:cid>")
@auth("admin")
def admin_complaint(cid):
    c = db.session.get(Complaint, cid)
    return ok(c.to_dict(True)) if c else err("Complaint not found", 404)

@bp.patch("/admin/complaints/<int:cid>")
@auth("admin")
def update_complaint(cid):
    c = db.session.get(Complaint, cid)
    if not c: return err("Complaint not found", 404)
    d, f = body(), {}
    new_status = s(d, "status") or c.status
    remarks, res = s(d, "remarks"), s(d, "resolution_details")
    new_dept = c.department_id
    if "department_id" in d and d["department_id"] not in (None, ""):
        try: new_dept = int(d["department_id"])
        except (TypeError, ValueError): f["department_id"] = "Invalid department"
        else:
            if not db.session.get(Department, new_dept): f["department_id"] = "Department does not exist"
    if new_status not in STATUSES: f["status"] = "Invalid status"
    elif new_status != c.status and new_status not in TRANSITIONS[c.status]:
        f["status"] = f"Cannot change {c.status} to {new_status}"
    prio = s(d, "priority") or c.priority
    if prio not in PRIORITIES: f["priority"] = "Invalid priority"
    changed_status = new_status != c.status
    if changed_status and new_status in ("Rejected", "Resolved") and not remarks: f["remarks"] = "Remarks are required"
    if changed_status and c.status == "Resolved" and not remarks: f["remarks"] = "Give a reason for reopening"
    if new_status == "Resolved" and not (res or c.resolution_details): f["resolution_details"] = "Resolution details are required"
    if len(remarks) > 1000 or len(res) > 2000: f["remarks"] = "Text too long"
    if f: return err("Update rejected", 400, f)
    changed_dept = new_dept != c.department_id
    if changed_status or changed_dept or remarks:
        db.session.add(ComplaintUpdate(complaint_id=c.complaint_id, admin_id=session["uid"], old_status=c.status,
                                       new_status=new_status, old_department_id=c.department_id,
                                       new_department_id=new_dept, remarks=remarks or None))
    if changed_dept: c.department_id, c.assigned_at = new_dept, datetime.utcnow()
    if new_status == "Resolved" and changed_status: c.resolved_at = datetime.utcnow()
    if c.status == "Resolved" and changed_status: c.resolved_at = None  # reopened; old resolution stays in history
    if res: c.resolution_details = res
    c.status, c.priority = new_status, prio
    db.session.commit()  # complaint change + history row commit together
    return ok(c.to_dict(True))

@bp.get("/admin/departments")
@auth("admin")
def list_departments():
    return ok([x.to_dict() for x in Department.query.order_by(Department.department_name)])

@bp.post("/admin/departments")
@auth("admin")
def add_department():
    d = body(); name = s(d, "name")
    if not 2 <= len(name) <= 100: return err("Name must be 2-100 characters", 400, {"name": "Invalid name"})
    if Department.query.filter_by(department_name=name).first(): return err("Department already exists", 409)
    x = Department(department_name=name, description=s(d, "description")[:255] or None)
    db.session.add(x); db.session.commit()
    return ok(x.to_dict(), 201)

@bp.patch("/admin/departments/<int:did>")
@auth("admin")
def edit_department(did):
    x = db.session.get(Department, did)
    if not x: return err("Department not found", 404)
    d = body(); name = s(d, "name") or x.department_name
    dup = Department.query.filter(Department.department_name == name, Department.department_id != did).first()
    if dup or not 2 <= len(name) <= 100: return err("Invalid or duplicate name", 409 if dup else 400)
    x.department_name = name
    if "description" in d: x.description = s(d, "description")[:255] or None
    db.session.commit()
    return ok(x.to_dict())

@bp.post("/admin/admins")
@auth("admin")
def add_admin():
    d = body(); name, email, pw = s(d, "name"), s(d, "email").lower(), str(d.get("password") or "")
    f = {}
    if not 2 <= len(name) <= 100: f["name"] = "Enter a name"
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email): f["email"] = "Enter a valid email"
    if len(pw) < 8: f["password"] = "At least 8 characters"
    if f: return err("Please fix the highlighted fields", 400, f)
    if Admin.query.filter_by(email=email).first(): return err("An admin with this email already exists", 409)
    a = Admin(name=name, email=email); a.set_password(pw)
    db.session.add(a); db.session.commit()
    return ok(a.to_dict(), 201)
