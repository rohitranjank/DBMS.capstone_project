import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errText } from "./api";
import { Alert, BUILDINGS, CATEGORIES, ComplaintTable, Empty, Field, Pager, PRIORITIES, Spinner, STATUSES, Stat } from "./ui.jsx";

export function AdminDashboard() {
  const [d, setD] = useState(null), [error, setError] = useState("");
  useEffect(() => { api.get("/admin/dashboard").then((r) => setD(r.data.data)).catch((e) => setError(errText(e))); }, []);
  if (error) return <Alert>{error}</Alert>;
  if (!d) return <Spinner />;
  const max = Math.max(1, ...d.categories.map((c) => c.count));
  return <><div className="bar"><h2>Dashboard</h2><Link className="btn" to="/admin/complaints">Manage complaints</Link></div>
    <div className="grid">{["Total", ...STATUSES].map((k) => <Stat key={k} label={k} value={d.counts[k]} />)}</div>
    <div className="card"><h3>Complaints by category</h3>{d.categories.map((c) => <div className="barrow" key={c.name}><span>{c.name}</span><div><i style={{ width: `${(c.count / max) * 100}%` }} /></div><b>{c.count}</b></div>)}</div>
    <h3>Recent complaints</h3>{d.recent.length ? <ComplaintTable rows={d.recent} base="/admin/complaints" admin /> : <Empty>No complaints yet.</Empty>}</>;
}

export function AdminComplaints() {
  const blank = { q: "", status: "", category: "", priority: "", building: "", department_id: "", date_from: "", date_to: "", page: 1 };
  const [p, setP] = useState(blank), [r, setR] = useState(null), [deps, setDeps] = useState([]), [error, setError] = useState("");
  useEffect(() => { api.get("/admin/departments").then((x) => setDeps(x.data.data)).catch(() => {}); }, []);
  useEffect(() => { setError(""); api.get("/admin/complaints", { params: p }).then((x) => setR(x.data)).catch((e) => setError(errText(e))); }, [p]);
  const set = (k) => (e) => setP({ ...p, [k]: e.target.value, page: 1 });
  const sel = (k, label, opts) => <select aria-label={label} value={p[k]} onChange={set(k)}><option value="">{label}</option>{opts.map((o) => <option key={o.v ?? o} value={o.v ?? o}>{o.t ?? o}</option>)}</select>;
  return <><h2>Manage complaints</h2><div className="filters"><input placeholder="Search reference, title, student, room" aria-label="Search" value={p.q} onChange={set("q")} />
    {sel("status", "All statuses", STATUSES)}{sel("category", "All categories", CATEGORIES)}{sel("priority", "All priorities", PRIORITIES)}{sel("building", "All buildings", BUILDINGS)}
    {sel("department_id", "All departments", deps.map((d) => ({ v: d.id, t: d.name })))}
    <input type="date" aria-label="From date" value={p.date_from} onChange={set("date_from")} /><input type="date" aria-label="To date" value={p.date_to} onChange={set("date_to")} />
    <button className="btn ghost" onClick={() => setP(blank)}>Clear filters</button></div>
    <Alert>{error}</Alert>{!r ? <Spinner /> : r.data.length ? <><ComplaintTable rows={r.data} base="/admin/complaints" admin /><Pager page={r.page} pages={r.pages} onPage={(page) => setP({ ...p, page })} /></> : <Empty>No complaints match these filters.</Empty>}</>;
}

export function Departments() {
  const [list, setList] = useState([]), [name, setName] = useState(""), [error, setError] = useState("");
  const load = () => api.get("/admin/departments").then((r) => setList(r.data.data)).catch((e) => setError(errText(e)));
  useEffect(() => { load(); }, []);
  const add = async (e) => { e.preventDefault(); setError(""); try { await api.post("/admin/departments", { name }); setName(""); load(); } catch (er) { setError(errText(er)); } };
  return <><h2>Departments</h2><Alert>{error}</Alert><form className="card row" onSubmit={add}><Field label="New department"><input required value={name} onChange={(e) => setName(e.target.value)} /></Field><button className="btn">Add department</button></form>
    <ul className="plain">{list.map((d) => <li className="card" key={d.id}>{d.name}</li>)}</ul></>;
}
