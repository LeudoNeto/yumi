import { useEffect, useRef } from "react";

export default function Modal({ title, onClose, children, footer, wide }) {
  // Só fecha quando o clique COMEÇA no backdrop. Sem isso, selecionar texto num
  // input e soltar o mouse fora do modal dispara o "click" no backdrop e fecha.
  const pressedOnBackdrop = useRef(false);

  useEffect(() => {
    function onKey(e) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [onClose]);

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        pressedOnBackdrop.current = e.target === e.currentTarget;
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && pressedOnBackdrop.current) onClose();
      }}
    >
      <div className={`modal ${wide ? "wide" : ""}`}>
        <header className="modal-head">
          <h3>{title}</h3>
          <button className="modal-close" onClick={onClose} aria-label="Fechar">✕</button>
        </header>
        <div className="modal-body">{children}</div>
        {footer && <footer className="modal-foot">{footer}</footer>}
      </div>
    </div>
  );
}
