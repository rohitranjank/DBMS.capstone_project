import { Link } from "react-router-dom";
export const STATUSES = ["Pending", "In Progress", "Resolved", "Rejected"];
export const PRIORITIES = ["Low", "Medium", "High", "Urgent"];
export const CATEGORIES = ["Classroom","Laboratory","Hostel","Library","Wi-Fi and Internet","Electricity","Water Supply","Cleanliness","Infrastructure","Other"];
export const BLOCKS = ["A Block", "B Block", "C Block", "D Block"], HOSTELS = ["Boys Hostel", "Girls Hostel"];
export const BUILDINGS = [...BLOCKS, ...HOSTELS];
export const blockFloors = [0, 1, 2, 3, 4, 5].map((n) => ({ v: String(n), t: n === 0 ? "Ground floor" : `Floor ${n}` }));
export const hostelFloors = [1, 2, 3, 4, 5, 6].map((n) => ({ v: String(n), t: `Floor ${n}` }));
export const roomsFor = (f) => Array.from({ length: 22 }, (_, i) => String(Number(f) * 100 + i + 1).padStart(3, "0"));
const slug = (s) => s.toLowerCase().replace(/\s+/g, "-");
export const Badge = ({ v }) => <span className={`badge b-${slug(v)}`}>{v}</span>;
export const fmt = (d) => (d ? new Date(d).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "-");
export const Spinner = () => <p className="muted" role="status">Loading…</p>;
export const Alert = ({ kind = "error", children }) => (children ? <div className={`alert ${kind}`} role="alert">{children}</div> : null);
export const Empty = ({ children }) => <div className="empty">{children}</div>;
export const Stat = ({ label, value }) => <div className="card stat"><span>{label}</span><strong>{value ?? 0}</strong></div>;
export const Pager = ({ page, pages, onPage }) => pages > 1 && (
  <div className="pager"><button className="btn ghost" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
    <span>Page {page} of {pages}</span><button className="btn ghost" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</button></div>);
export const Field = ({ label, error, children }) => <label className="field"><span>{label}</span>{children}{error && <small className="err">{error}</small>}</label>;
export function ComplaintTable({ rows, base, admin }) {
  return <div className="scroll"><table><thead><tr><th>Reference</th><th>Title</th>{admin && <th>Student</th>}<th>Location</th><th>Category</th><th>Department</th><th>Priority</th><th>Status</th><th>Submitted</th></tr></thead>
    <tbody>{rows.map((c) => <tr key={c.id}><td><Link to={`${base}/${c.id}`}>{c.reference}</Link></td><td>{c.title}</td>{admin && <td>{c.student_name}</td>}
      <td>{c.location}</td><td>{c.category}</td><td>{c.department || "Unassigned"}</td><td><Badge v={c.priority} /></td><td><Badge v={c.status} /></td><td>{fmt(c.created_at)}</td></tr>)}</tbody></table></div>;
}
