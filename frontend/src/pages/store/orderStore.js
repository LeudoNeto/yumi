// Tracks order ids placed from this device per store, so the customer can follow
// them in "Meus pedidos" even without an account (guest checkout).
const key = (slug) => `yumi_orders_${slug}`;

export function rememberGuestOrder(slug, orderId) {
  try {
    const ids = getGuestOrderIds(slug);
    if (!ids.includes(orderId)) {
      ids.unshift(orderId);
      localStorage.setItem(key(slug), JSON.stringify(ids.slice(0, 50)));
    }
  } catch {
    /* ignore storage errors */
  }
}

export function getGuestOrderIds(slug) {
  try {
    return JSON.parse(localStorage.getItem(key(slug)) || "[]");
  } catch {
    return [];
  }
}

// Drop all device-tracked order ids — called on logout so this device stops
// surfacing orders from a previous session/account.
export function clearGuestOrders() {
  try {
    Object.keys(localStorage)
      .filter((k) => k.startsWith("yumi_orders_"))
      .forEach((k) => localStorage.removeItem(k));
  } catch {
    /* ignore storage errors */
  }
}
