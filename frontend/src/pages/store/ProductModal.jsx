import { useMemo, useState } from "react";
import Modal from "../../components/Modal.jsx";
import { formatBRL } from "../../lib";

export default function ProductModal({ item, onClose, onAdd }) {
  // selection: { [groupId]: { [optionId]: quantity } }
  const [selection, setSelection] = useState({});
  const [quantity, setQuantity] = useState(1);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState("");

  function groupCount(groupId) {
    const g = selection[groupId] || {};
    return Object.values(g).reduce((a, b) => a + b, 0);
  }

  function selectSingle(group, optionId) {
    setSelection((s) => ({ ...s, [group.id]: { [optionId]: 1 } }));
    setError("");
  }

  function toggleMulti(group, optionId) {
    setSelection((s) => {
      const cur = { ...(s[group.id] || {}) };
      if (cur[optionId]) {
        delete cur[optionId];
      } else {
        if (groupCount(group.id) >= group.max_select) return s; // at limit
        cur[optionId] = 1;
      }
      return { ...s, [group.id]: cur };
    });
    setError("");
  }

  function stepOption(group, optionId, delta) {
    setSelection((s) => {
      const cur = { ...(s[group.id] || {}) };
      const total = Object.values(cur).reduce((a, b) => a + b, 0);
      const next = (cur[optionId] || 0) + delta;
      if (delta > 0 && total >= group.max_select) return s;
      if (next <= 0) delete cur[optionId];
      else cur[optionId] = next;
      return { ...s, [group.id]: cur };
    });
    setError("");
  }

  const unitPrice = useMemo(() => {
    let price = item.base_price;
    for (const group of item.option_groups) {
      const sel = selection[group.id] || {};
      for (const opt of group.options) {
        const q = sel[opt.id] || 0;
        price += opt.price_delta * q;
      }
    }
    return price;
  }, [selection, item]);

  function validate() {
    for (const group of item.option_groups) {
      const count = groupCount(group.id);
      if (count < group.min_select)
        return `Escolha pelo menos ${group.min_select} em "${group.name}".`;
    }
    return "";
  }

  function add() {
    const err = validate();
    if (err) return setError(err);
    const selectedOptions = [];
    for (const group of item.option_groups) {
      const sel = selection[group.id] || {};
      for (const opt of group.options) {
        const q = sel[opt.id] || 0;
        if (q > 0) selectedOptions.push({ group, option: opt, quantity: q });
      }
    }
    onAdd({
      uid: `${item.id}-${Date.now()}`,
      item,
      quantity,
      selectedOptions,
      unitPrice,
      notes: notes.trim(),
    });
    onClose();
  }

  return (
    <Modal
      title={item.name}
      onClose={onClose}
      footer={
        <div className="product-foot">
          <div className="qty-stepper">
            <button onClick={() => setQuantity((q) => Math.max(1, q - 1))}>−</button>
            <span>{quantity}</span>
            <button onClick={() => setQuantity((q) => q + 1)}>+</button>
          </div>
          <button className="btn grow" onClick={add}>
            Adicionar · {formatBRL(unitPrice * quantity)}
          </button>
        </div>
      }
    >
      {item.image_url && <img src={item.image_url} alt="" className="product-img" />}
      {item.description && <p className="muted">{item.description}</p>}
      {error && <div className="alert error">{error}</div>}

      {item.option_groups.map((group) => {
        const single = group.max_select === 1 && !group.allow_repeat;
        const count = groupCount(group.id);
        return (
          <div key={group.id} className="opt-section">
            <div className="opt-section-head">
              <div>
                <strong>{group.name}</strong>
                <div className="text-sm muted">
                  {group.min_select > 0 ? "Obrigatório · " : "Opcional · "}
                  escolha até {group.max_select}
                  {group.allow_repeat ? " (pode repetir)" : ""}
                </div>
              </div>
              {group.required && (
                <span className={`badge ${count >= group.min_select ? "green" : "orange"}`}>
                  {count >= group.min_select ? "ok" : "obrigatório"}
                </span>
              )}
            </div>

            <div className="opt-options">
              {group.options.map((opt) => {
                const q = (selection[group.id] || {})[opt.id] || 0;
                const selected = q > 0;
                return (
                  <label key={opt.id} className={`opt-pick ${selected ? "selected" : ""}`}>
                    <div className="grow">
                      <span>{opt.name}</span>
                      {opt.price_delta > 0 && <span className="muted text-sm"> +{formatBRL(opt.price_delta)}</span>}
                    </div>
                    {group.allow_repeat ? (
                      <div className="qty-stepper sm">
                        <button type="button" onClick={() => stepOption(group, opt.id, -1)} disabled={q === 0}>−</button>
                        <span>{q}</span>
                        <button type="button" onClick={() => stepOption(group, opt.id, 1)}>+</button>
                      </div>
                    ) : single ? (
                      <input type="radio" name={`g-${group.id}`} checked={selected}
                        onChange={() => selectSingle(group, opt.id)} />
                    ) : (
                      <input type="checkbox" checked={selected}
                        onChange={() => toggleMulti(group, opt.id)} />
                    )}
                  </label>
                );
              })}
            </div>
          </div>
        );
      })}

      <div className="field mt16">
        <label>Observações</label>
        <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Ex.: sem cebola, ponto da carne..." />
      </div>
    </Modal>
  );
}
