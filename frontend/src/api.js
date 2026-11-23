import axios from "axios";
const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || (import.meta.env.DEV ? "http://localhost:5000/api" : "/api"), withCredentials: true });
let token = null;
// Fetch the CSRF token once, then send it on every state-changing request.
api.interceptors.request.use(async (c) => {
  if (["post", "patch", "put", "delete"].includes(c.method)) {
    if (!token) token = (await api.get("/auth/csrf")).data.data.token;
    c.headers["X-CSRF-Token"] = token;
  }
  return c;
});
export const resetCsrf = () => { token = null; };
export const errText = (e) => e.response?.data?.error || (e.request ? "Cannot reach the server. Is the backend running?" : "Something went wrong");
export const fieldErrors = (e) => e.response?.data?.fields || {};
export default api;
