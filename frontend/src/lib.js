export function formatBRL(value) {
  return (Number(value) || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export const WEEKDAYS = [
  "Segunda-feira",
  "Terça-feira",
  "Quarta-feira",
  "Quinta-feira",
  "Sexta-feira",
  "Sábado",
  "Domingo",
];

export const WEEKDAYS_SHORT = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"];

export const ORDER_TYPE_LABELS = {
  delivery: "Entrega",
  pickup: "Retirar no local",
  dine_in: "Consumir no local",
};

export const PAYMENT_LABELS = {
  pix: "PIX",
  cash: "Pagar na entrega",
};

export const STATUS_LABELS = {
  pending: "Pendente",
  confirmed: "Confirmado",
  preparing: "Em preparo",
  ready: "Pronto",
  delivering: "Saiu para entrega",
  completed: "Concluído",
  cancelled: "Cancelado",
};

export const STATUS_FLOW = [
  "pending",
  "confirmed",
  "preparing",
  "ready",
  "delivering",
  "completed",
];

// The progress flow depends on the fulfillment type: only delivery orders pass
// through "delivering" (you don't "deliver" a pickup / dine-in order).
export function statusFlowFor(orderType) {
  return orderType === "delivery"
    ? ["pending", "confirmed", "preparing", "ready", "delivering", "completed"]
    : ["pending", "confirmed", "preparing", "ready", "completed"];
}

export function nextStatusFor(orderType, status) {
  const flow = statusFlowFor(orderType);
  const i = flow.indexOf(status);
  return i >= 0 && i < flow.length - 1 ? flow[i + 1] : null;
}

// resolve uploaded image paths (served by the backend under /uploads)
export function mediaUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return path; // vite proxies /uploads -> backend
}
