import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth.jsx";

import Home from "./pages/Home.jsx";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import AdminLayout from "./pages/admin/AdminLayout.jsx";
import Settings from "./pages/admin/Settings.jsx";
import MenuEditor from "./pages/admin/MenuEditor.jsx";
import Orders from "./pages/admin/Orders.jsx";
import Storefront from "./pages/store/Storefront.jsx";
import CustomerOrders from "./pages/store/CustomerOrders.jsx";

function Protected({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="spinner" />;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route
        path="/admin"
        element={
          <Protected>
            <AdminLayout />
          </Protected>
        }
      >
        <Route index element={<Navigate to="orders" replace />} />
        <Route path="orders" element={<Orders />} />
        <Route path="menu" element={<MenuEditor />} />
        <Route path="settings" element={<Settings />} />
      </Route>

      {/* public storefront — single dynamic segment, must stay last */}
      <Route path="/:empresaUrl/pedidos" element={<CustomerOrders />} />
      <Route path="/:empresaUrl" element={<Storefront />} />

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
