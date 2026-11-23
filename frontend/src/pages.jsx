import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import api, { errText, fieldErrors } from "./api";
import { useAuth } from "./App.jsx";
import { Alert, Field } from "./ui.jsx";

export const Landing = () => (
  <div className="landing"><header><span className="brand"><img className="logo" src="/krmu-logo.png" alt="K.R. Mangalam University logo" /><strong>K.R. Mangalam University: Campus Care</strong></span><Link to="/admin/login">Administrator login</Link></header>
    <div className="herobg"><section className="hero"><h2>Report a campus problem. Watch it get fixed.</h2>
      <p>Pick your block, floor and classroom, or your hostel and floor, and tell us what is wrong. Wi-Fi, water, electricity and cleanliness issues are covered too.</p>
      <div className="row"><Link className="btn" to="/login">Student login</Link><Link className="btn ghost" to="/register">Create account</Link></div></section></div>
    <section className="steps">{[["Submit", "Describe the problem and exactly where it is."], ["Assigned", "An administrator routes it to the right department."], ["Tracked", "Every status change and remark is recorded."], ["Resolved", "See the resolution details on your complaint."]].map(([t, d]) =>
      <div key={t} className="card"><h3>{t}</h3><p>{d}</p></div>)}</section></div>
);

export function Login({ role }) {
  const { user, setUser } = useAuth(), nav = useNavigate();
  const [f, setF] = useState({ email: "", password: "" }), [error, setError] = useState(""), [busy, setBusy] = useState(false);
  if (user) return <Navigate to={user.role === "admin" ? "/admin" : "/student"} replace />;
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError("");
    try { const r = await api.post(`/auth/${role}/login`, f); setUser(r.data.data); nav(role === "admin" ? "/admin" : "/student"); }
    catch (er) { setError(errText(er)); } finally { setBusy(false); }
  };
  return <div className="authbg"><form className="card auth" onSubmit={submit}><img className="logo big" src="/krmu-logo.png" alt="K.R. Mangalam University" /><h2>{role === "admin" ? "Administrator login" : "Student login"}</h2><Alert>{error}</Alert>
    <Field label="Email"><input type="email" required value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
    <Field label="Password"><input type="password" required value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></Field>
    <button className="btn" disabled={busy}>{busy ? "Logging in…" : "Log in"}</button>
    {role === "student" && <p className="muted">New here? <Link to="/register">Create an account</Link></p>}<Link to="/">Back to home</Link></form></div>;
}

export function Register() {
  const nav = useNavigate();
  const [f, setF] = useState({ name: "", email: "", password: "", academic_department: "", year_of_study: 1 });
  const [fe, setFe] = useState({}), [error, setError] = useState(""), [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError(""); setFe({});
    try { await api.post("/auth/student/register", f); nav("/login"); }
    catch (er) { setError(errText(er)); setFe(fieldErrors(er)); } finally { setBusy(false); }
  };
  return <div className="authbg"><form className="card auth" onSubmit={submit}><img className="logo big" src="/krmu-logo.png" alt="K.R. Mangalam University" /><h2>Create student account</h2><Alert>{error}</Alert>
    <Field label="Full name" error={fe.name}><input required value={f.name} onChange={set("name")} /></Field>
    <Field label="Email" error={fe.email}><input type="email" required value={f.email} onChange={set("email")} /></Field>
    <Field label="Password (8+ characters)" error={fe.password}><input type="password" required value={f.password} onChange={set("password")} /></Field>
    <Field label="Academic department" error={fe.academic_department}><input required value={f.academic_department} onChange={set("academic_department")} /></Field>
    <Field label="Year of study" error={fe.year_of_study}><select value={f.year_of_study} onChange={set("year_of_study")}>{[1,2,3,4,5,6].map((y) => <option key={y}>{y}</option>)}</select></Field>
    <button className="btn" disabled={busy}>{busy ? "Creating…" : "Create account"}</button><Link to="/login">Already registered? Log in</Link></form></div>;
}
