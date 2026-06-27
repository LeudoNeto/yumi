import axios from "axios";

export const ADMIN_TOKEN_KEY = "yumi_token";
export const CUSTOMER_TOKEN_KEY = "yumi_customer_token";

// ----- Admin API -----
const api = axios.create({ baseURL: "/api" });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem(ADMIN_TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem(ADMIN_TOKEN_KEY)) {
      localStorage.removeItem(ADMIN_TOKEN_KEY);
    }
    return Promise.reject(err);
  }
);

// ----- Customer / storefront API -----
// Attaches the customer token when present. Public endpoints ignore it; order
// creation uses it (optional) to link the order to the logged-in customer.
export const shopApi = axios.create({ baseURL: "/api" });

shopApi.interceptors.request.use((config) => {
  const token = localStorage.getItem(CUSTOMER_TOKEN_KEY);
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

shopApi.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && localStorage.getItem(CUSTOMER_TOKEN_KEY)) {
      localStorage.removeItem(CUSTOMER_TOKEN_KEY);
    }
    return Promise.reject(err);
  }
);

// helper to turn an axios error into a readable message
export function apiError(err, fallback = "Algo deu errado. Tente novamente.") {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return detail[0].msg;
  return fallback;
}

export default api;
