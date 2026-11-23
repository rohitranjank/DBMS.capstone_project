import pytest
from app import create_app, db
from app.models import Admin, Department

class Client:
    def __init__(self, app):
        self.c = app.test_client(); self.tok = self.c.get("/api/auth/csrf").json["data"]["token"]
    def req(self, m, url, **kw): return getattr(self.c, m)(url, headers={"X-CSRF-Token": self.tok}, **kw)
    def post(self, u, j=None): return self.req("post", u, json=j)
    def patch(self, u, j=None): return self.req("patch", u, json=j)
    def get(self, u, **kw): return self.c.get(u, **kw)

@pytest.fixture
def app():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": True, "SECRET_KEY": "t"})
    with app.app_context():
        db.create_all()
        a = Admin(name="Boss", email="admin@x.com"); a.set_password("AdminPass1")
        db.session.add_all([a, Department(department_name="IT Support")]); db.session.commit()
    return app

def student(app, email="a@x.com"):
    c = Client(app)
    r = c.post("/api/auth/student/register", dict(name="Ann", email=email, password="password1", academic_department="CS", year_of_study=2))
    assert r.status_code == 201 and "password" not in r.get_data(as_text=True)
    assert c.post("/api/auth/student/login", dict(email=email, password="password1")).status_code == 200
    return c

def admin(app):
    c = Client(app); assert c.post("/api/auth/admin/login", dict(email="admin@x.com", password="AdminPass1")).status_code == 200
    return c

COMPLAINT = dict(title="Broken fan", category="Classroom", building="A Block", floor="2", room="215", description="The fan is broken badly")

def test_register_duplicate_and_bad_login(app):
    student(app); c = Client(app)
    assert c.post("/api/auth/student/register", dict(name="Ann", email="a@x.com", password="password1", academic_department="CS", year_of_study=2)).status_code == 409
    assert c.post("/api/auth/student/login", dict(email="a@x.com", password="wrong")).status_code == 401

def test_csrf_required(app):
    assert app.test_client().post("/api/auth/logout").status_code == 403

def test_unauthenticated_and_role_rejected(app):
    assert Client(app).get("/api/complaints/my").status_code == 401
    assert student(app).get("/api/admin/complaints").status_code == 403

def test_submit_and_ownership(app):
    a, b = student(app), student(app, "b@x.com")
    r = a.post("/api/complaints", COMPLAINT); assert r.status_code == 201
    d = r.json["data"]; assert d["status"] == "Pending" and d["reference"].startswith("CMP-")
    assert d["location"] == "A Block, Floor 2, Room 215"
    assert a.get(f"/api/complaints/{d['id']}").status_code == 200
    assert b.get(f"/api/complaints/{d['id']}").status_code == 404
    assert b.get("/api/complaints/my").json["total"] == 0

def test_invalid_input(app):
    r = student(app).post("/api/complaints", dict(title="x", category="Nope"))
    assert r.status_code == 400 and "title" in r.json["fields"] and "building" in r.json["fields"]

def test_location_rules(app):
    s = student(app)
    base = dict(title="Broken thing", category="Hostel", description="Something is broken here")
    ok = lambda **k: s.post("/api/complaints", {**base, **k})
    assert ok(building="A Block", floor="0", room="022").json["data"]["location"] == "A Block, Ground Floor, Room 022"
    assert ok(building="B Block", floor="2", room="223").status_code == 400
    assert ok(building="C Block", floor="6", room="601").status_code == 400
    assert ok(building="D Block", floor="3", room="215").status_code == 400
    assert ok(building="Girls Hostel", floor="6").json["data"]["location"] == "Girls Hostel, Floor 6"
    assert ok(building="Boys Hostel", floor="7").status_code == 400
    assert ok(building="Other", location="Canteen").status_code == 201

def test_admin_workflow_history_and_filters(app):
    s, a = student(app), admin(app)
    cid = s.post("/api/complaints", COMPLAINT).json["data"]["id"]
    assert a.get("/api/admin/complaints?q=fan&status=Pending").json["total"] == 1
    assert a.get("/api/admin/complaints?building=A%20Block").json["total"] == 1
    assert a.get("/api/admin/complaints?building=B%20Block").json["total"] == 0
    assert a.get("/api/admin/complaints?status=Resolved").json["total"] == 0
    assert a.patch(f"/api/admin/complaints/{cid}", dict(status="In Progress", department_id=1, remarks="On it")).status_code == 200
    assert a.patch(f"/api/admin/complaints/{cid}", dict(status="Resolved")).status_code == 400
    assert a.patch(f"/api/admin/complaints/{cid}", dict(status="Resolved", remarks="Fixed", resolution_details="Fan replaced")).status_code == 200
    assert a.patch(f"/api/admin/complaints/{cid}", dict(status="Rejected", remarks="x")).status_code == 400
    hist = s.get(f"/api/complaints/{cid}/history").json["data"]
    assert [h["new_status"] for h in hist] == ["Resolved", "In Progress"]
    assert a.patch(f"/api/admin/complaints/{cid}", dict(status="In Progress", remarks="Recurred")).status_code == 200
    assert a.patch(f"/api/admin/complaints/{cid}", dict(department_id=99)).status_code == 400
    assert a.get("/api/admin/dashboard").json["data"]["counts"]["In Progress"] == 1

def test_logout(app):
    s = student(app); assert s.post("/api/auth/logout").status_code == 200
    assert s.get("/api/auth/me").status_code == 401

def test_change_password_and_add_admin(app):
    s = student(app)
    assert s.post("/api/auth/change-password", dict(current_password="bad", new_password="newpassword1")).status_code == 400
    assert s.post("/api/auth/change-password", dict(current_password="password1", new_password="newpassword1")).status_code == 200
    assert Client(app).post("/api/auth/student/login", dict(email="a@x.com", password="newpassword1")).status_code == 200
    assert s.post("/api/admin/admins", dict(name="X", email="n@x.com", password="password1")).status_code == 403
    a = admin(app)
    assert a.post("/api/admin/admins", dict(name="New Admin", email="n@x.com", password="password1")).status_code == 201
    assert a.post("/api/admin/admins", dict(name="New Admin", email="n@x.com", password="password1")).status_code == 409
