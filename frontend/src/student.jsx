import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errText, fieldErrors } from "./api";
import { useAuth } from "./App.jsx";
import { Alert, BLOCKS, HOSTELS, blockFloors, hostelFloors, roomsFor, CATEGORIES, ComplaintTable, Empty, Field, Pager, Spinner, STATUSES, Stat } from "./ui.jsx";

export function StudentDashboard() {
  const { user } = useAuth(), [d, setD] = useState(null), [error, setError] = useState("");
  useEffect(() => { api.get("/student/dashboard").then((r) => setD(r.data.data)).catch((e) => setError(errText(e))); }, []);
  if (error) return <Alert>{error}</Alert>;
  if (!d) return <Spinner />;
  return <><div className="bar"><h2>Welcome, {user.name}</h2><Link className="btn" to="/student/submit">Submit complaint</Link></div>
    <div className="grid">{[["Total", "Total"], ["Pending", "Pending"], ["In progress", "In Progress"], ["Resolved", "Resolved"]].map(([l, k]) => <Stat key={k} label={l} value={d.counts[k]} />)}</div>
    <h3>Recent complaints</h3>{d.recent.length ? <ComplaintTable rows={d.recent} base="/student/complaints" /> : <Empty>You have not submitted any complaints yet.</Empty>}</>;
}

// Building -> floor -> room dropdowns for K.R. Mangalam University; the server re-validates everything.
function LocationPicker({ f, setF, fe }) {
  const isBlock = BLOCKS.includes(f.building), isHostel = HOSTELS.includes(f.building);
  const pick = (k) => (e) => setF({ ...f, [k]: e.target.value, ...(k === "building" ? { floor: "", room: "", location: "" } : k === "floor" ? { room: "" } : {}) });
  const first = <option value="">Choose…</option>;
  return <>
    <Field label="Building" error={fe.building}><select required value={f.building} onChange={pick("building")}>{first}{[...BLOCKS, ...HOSTELS].map((b) => <option key={b}>{b}</option>)}<option>Other</option></select></Field>
    {(isBlock || isHostel) && <Field label="Floor" error={fe.floor}><select required value={f.floor} onChange={pick("floor")}>{first}{(isBlock ? blockFloors : hostelFloors).map((x) => <option key={x.v} value={x.v}>{x.t}</option>)}</select></Field>}
    {isBlock && f.floor !== "" && <Field label="Classroom" error={fe.room}><select required value={f.room} onChange={pick("room")}>{first}{roomsFor(f.floor).map((r) => <option key={r}>{r}</option>)}</select></Field>}
    {isHostel && <Field label="Room number (optional)" error={fe.room}><input maxLength={20} value={f.room} onChange={pick("room")} /></Field>}
    {f.building === "Other" && <Field label="Location" error={fe.location}><input required maxLength={150} value={f.location} onChange={pick("location")} placeholder="e.g. Library, canteen, parking" /></Field>}
  </>;
}

export function Submit() {
  const empty = { title: "", category: "", building: "", floor: "", room: "", location: "", description: "" };
  const [f, setF] = useState(empty), [fe, setFe] = useState({}), [error, setError] = useState(""), [ref, setRef] = useState(""), [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const submit = async (e) => {
    e.preventDefault(); if (busy) return; setBusy(true); setError(""); setFe({}); setRef("");
    try { const r = await api.post("/complaints", f); setRef(r.data.data.reference); setF(empty); }  // clear only on success
    catch (er) { setError(errText(er)); setFe(fieldErrors(er)); } finally { setBusy(false); }
  };
  return <form className="card" onSubmit={submit}><h2>Submit a complaint</h2><Alert>{error}</Alert>
    {ref && <Alert kind="success">Complaint submitted. Your reference is <strong>{ref}</strong>.</Alert>}
    <Field label="Title" error={fe.title}><input required maxLength={150} value={f.title} onChange={set("title")} /></Field>
    <Field label="Category" error={fe.category}><select required value={f.category} onChange={set("category")}><option value="">Choose…</option>{CATEGORIES.map((c) => <option key={c}>{c}</option>)}</select></Field>
    <LocationPicker f={f} setF={setF} fe={fe} />
    <Field label="Description" error={fe.description}><textarea required rows={5} maxLength={2000} value={f.description} onChange={set("description")} /></Field>
    <button className="btn" disabled={busy}>{busy ? "Submitting…" : "Submit complaint"}</button></form>;
}

export function MyComplaints() {
  const [p, setP] = useState({ q: "", status: "", category: "", page: 1 }), [r, setR] = useState(null), [error, setError] = useState("");
  useEffect(() => { setError(""); api.get("/complaints/my", { params: p }).then((x) => setR(x.data)).catch((e) => setError(errText(e))); }, [p]);
  const set = (k) => (e) => setP({ ...p, [k]: e.target.value, page: 1 });
  return <><h2>My complaints</h2><div className="filters"><input placeholder="Search title, reference or room" aria-label="Search" value={p.q} onChange={set("q")} />
    <select aria-label="Status" value={p.status} onChange={set("status")}><option value="">All statuses</option>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select>
    <select aria-label="Category" value={p.category} onChange={set("category")}><option value="">All categories</option>{CATEGORIES.map((s) => <option key={s}>{s}</option>)}</select></div>
    <Alert>{error}</Alert>{!r ? <Spinner /> : r.data.length ? <><ComplaintTable rows={r.data} base="/student/complaints" /><Pager page={r.page} pages={r.pages} onPage={(page) => setP({ ...p, page })} /></> : <Empty>No complaints match these filters.</Empty>}</>;
}
