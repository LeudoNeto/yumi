import { createContext, useContext, useEffect, useState } from "react";
import { shopApi, CUSTOMER_TOKEN_KEY } from "./api";
import { clearGuestOrders } from "./pages/store/orderStore.js";

const CustomerAuthContext = createContext(null);

export function CustomerAuthProvider({ children }) {
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadMe() {
    const token = localStorage.getItem(CUSTOMER_TOKEN_KEY);
    if (!token) {
      setCustomer(null);
      setLoading(false);
      return;
    }
    try {
      const { data } = await shopApi.get("/customer/auth/me");
      setCustomer(data);
    } catch {
      localStorage.removeItem(CUSTOMER_TOKEN_KEY);
      setCustomer(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadMe();
  }, []);

  async function login(email, password) {
    const { data } = await shopApi.post("/customer/auth/login", { email, password });
    localStorage.setItem(CUSTOMER_TOKEN_KEY, data.access_token);
    await loadMe();
  }

  async function register(payload) {
    const { data } = await shopApi.post("/customer/auth/register", payload);
    localStorage.setItem(CUSTOMER_TOKEN_KEY, data.access_token);
    await loadMe();
  }

  function logout() {
    localStorage.removeItem(CUSTOMER_TOKEN_KEY);
    clearGuestOrders(); // this device forgets the previous session's tracked orders
    setCustomer(null);
  }

  return (
    <CustomerAuthContext.Provider value={{ customer, loading, login, register, logout, reload: loadMe }}>
      {children}
    </CustomerAuthContext.Provider>
  );
}

export function useCustomerAuth() {
  return useContext(CustomerAuthContext);
}
