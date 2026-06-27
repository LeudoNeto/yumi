import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { formatBRL } from "../lib";

export default function PixView({ payload, amount }) {
  const [qr, setQr] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!payload) return;
    QRCode.toDataURL(payload, { margin: 1, width: 240 })
      .then(setQr)
      .catch(() => setQr(null));
  }, [payload]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(payload);
    } catch {
      // fallback for non-secure contexts
      const ta = document.createElement("textarea");
      ta.value = payload;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="pix-view">
      <div className="badge green">💠 Pague com PIX</div>
      {amount != null && <div className="price" style={{ fontSize: 22 }}>{formatBRL(amount)}</div>}
      {qr && <img src={qr} alt="QR Code PIX" className="pix-qr" />}
      <p className="text-sm muted">Escaneie o QR Code ou use o PIX Copia e Cola:</p>
      <div className="pix-code">{payload}</div>
      <button className="btn block" onClick={copy}>{copied ? "✓ Copiado!" : "Copiar código PIX"}</button>
    </div>
  );
}
