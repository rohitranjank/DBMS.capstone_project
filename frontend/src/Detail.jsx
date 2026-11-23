import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import api, { errText, fieldErrors } from "./api";
import { Alert, Badge, Field, fmt, PRIORITIES, Spinner, STATUSES } from "./ui.jsx";

export default function Detail({ admin }) {
  const { id } = useParams(), [c, setC] = useState(null), [deps, setDeps] = useState([]), [error, setError] = useState("");
  const [f, setF] = useState({}), [fe, setFe] = useState({}), [msg, setMsg] = useState(""), [busy, setBusy] = useState(false);
  const load = () => api.get(`/complaints/${id}`).then((r) => { setC(r.data.data); setF({ status: r.data.data.status, priority: r.data.data.priority, department_id: r.data.data.department_id || "", remarks: "", resolution_details: "" }); }).catch((e) => setError(errText(e)));
  useEffect(() => { load(); if (admin) api.get("/admin/departments").then((r) => setDeps(r.data.data)); }, [id]);
  const save = async (e) => {
    e.preventDefault(); setBusy(true); setError(""); setFe({}); setMsg("");
    try { await api.patch(`/admin/complaints/${id}`, f); setMsg("Complaint updated."); await load(); }
    catch (er) { setError(errText(er)); setFe(fieldErrors(er)); } finally { setBusy(false); }
  };
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  if (!c) return error ? <Alert>{error}</Alert> : <Spinner />;
  return <><h2>{c.reference}: {c.title}</h2><div className="card"><p><Badge v={c.status} /> <Badge v={c.priority} /></p><p>{c.description}</p>
    <dl><dt>Category</dt><dd>{c.category}</dd><dt>Location</dt><dd>{c.location}</dd><dt>Department</dt><dd>{c.department || "Unassigned"}</dd><dt>Submitted</dt><dd>{fmt(c.created_at)}</dd>
      {admin && <><dt>Student</dt><dd>{c.student_name} ({c.student_email})</dd></>}{c.resolution_details && <><dt>Resolution</dt><dd>{c.resolution_details}</dd></>}</dl></div>
    {admin && <form className="card" onSubmit={save}><h3>Update complaint</h3><Alert>{error}</Alert><Alert kind="success">{msg}</Alert>
      <div className="grid3"><Field label="Status" error={fe.status}><select value={f.status} onChange={set("status")}>{STATUSES.map((s) => <option key={s}>{s}</option>)}</select></Field>
        <Field label="Priority" error={fe.priority}><select value={f.priority} onChange={set("priority")}>{PRIORITIES.map((s) => <option key={s}>{s}</option>)}</select></Field>
        <Field label="Department" error={fe.department_id}><select value={f.department_id} onChange={set("department_id")}><option value="">Unassigned</option>{deps.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}</select></Field></div>
      <Field label="Remarks" error={fe.remarks}><textarea rows={2} value={f.remarks} onChange={set("remarks")} /></Field>
      <Field label="Resolution details" error={fe.resolution_details}><textarea rows={2} value={f.resolution_details} onChange={set("resolution_details")} /></Field>
      <button className="btn" disabled={busy}>{busy ? "Saving…" : "Save changes"}</button></form>}
    <h3>History</h3>{c.history.length ? <ul className="timeline">{c.history.map((h) => <li key={h.id}><strong>{h.old_status} to {h.new_status}</strong> by {h.admin}{h.department && ` (${h.department})`}<br />{h.remarks}<br /><small>{fmt(h.created_at)}</small></li>)}</ul> : <p className="muted">No updates yet.</p>}</>;
}
