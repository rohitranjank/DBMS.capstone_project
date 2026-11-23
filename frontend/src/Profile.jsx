import { useState } from "react";
import api, { errText, fieldErrors } from "./api";
import { useAuth } from "./App.jsx";
import { Alert, Field } from "./ui.jsx";

function Form({ title, url, fields, done, button }) {
  const init = Object.fromEntries(fields.map(([k]) => [k, ""]));
  const [f, setF] = useState(init), [fe, setFe] = useState({}), [error, setError] = useState(""), [msg, setMsg] = useState(""), [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault(); setBusy(true); setError(""); setMsg(""); setFe({});
    try { await api.post(url, f); setMsg(done); setF(init); } catch (er) { setError(errText(er)); setFe(fieldErrors(er)); } finally { setBusy(false); }
  };
  return <form className="card" onSubmit={submit}><h3>{title}</h3><Alert>{error}</Alert><Alert kind="success">{msg}</Alert>
    {fields.map(([k, label, type]) => <Field key={k} label={label} error={fe[k]}><input type={type} required value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} /></Field>)}
    <button className="btn" disabled={busy}>{busy ? "Saving…" : button}</button></form>;
}

export default function Profile() {
  const { user } = useAuth();
  return <><h2>Profile</h2><div className="card"><p><strong>{user.name}</strong><br />{user.email}</p>
    {user.role === "student" && <p className="muted">{user.academic_department}, year {user.year_of_study}</p>}</div>
    <Form title="Change password" url="/auth/change-password" done="Password changed." button="Change password"
      fields={[["current_password", "Current password", "password"], ["new_password", "New password (8+ characters)", "password"]]} />
    {user.role === "admin" && <Form title="Add another administrator" url="/admin/admins" done="Administrator added." button="Add administrator"
      fields={[["name", "Name", "text"], ["email", "Email", "email"], ["password", "Temporary password (8+ characters)", "password"]]} />}</>;
}
