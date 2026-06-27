import { useRef, useState } from "react";
import Modal from "./Modal.jsx";
import api, { apiError } from "../api";
import { formatBRL } from "../lib";
import { MoneyInput } from "./Inputs.jsx";

function blankGroup() {
  return { name: "", min_select: 0, max_select: 1, allow_repeat: false, options: [blankOption()] };
}
function blankOption() {
  return { name: "", price_delta: 0 };
}

export default function ItemEditor({ categoryId, item, onClose, onSaved }) {
  const isEdit = !!item;
  const [form, setForm] = useState(() => ({
    name: item?.name || "",
    description: item?.description || "",
    base_price: item?.base_price ?? "",
    is_available: item?.is_available ?? true,
    image_url: item?.image_url || null,
    option_groups: (item?.option_groups || []).map((g) => ({
      name: g.name,
      min_select: g.min_select,
      max_select: g.max_select,
      allow_repeat: g.allow_repeat,
      options: g.options.map((o) => ({ name: o.name, price_delta: o.price_delta })),
    })),
  }));
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(item?.image_url || null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const fileInput = useRef();

  function set(key, value) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  // ---- option group helpers ----
  function addGroup() {
    set("option_groups", [...form.option_groups, blankGroup()]);
  }
  function updateGroup(gi, key, value) {
    set("option_groups", form.option_groups.map((g, i) => (i === gi ? { ...g, [key]: value } : g)));
  }
  function removeGroup(gi) {
    set("option_groups", form.option_groups.filter((_, i) => i !== gi));
  }
  function addOption(gi) {
    set("option_groups", form.option_groups.map((g, i) =>
      i === gi ? { ...g, options: [...g.options, blankOption()] } : g));
  }
  function updateOption(gi, oi, key, value) {
    set("option_groups", form.option_groups.map((g, i) =>
      i === gi ? { ...g, options: g.options.map((o, j) => (j === oi ? { ...o, [key]: value } : o)) } : g));
  }
  function removeOption(gi, oi) {
    set("option_groups", form.option_groups.map((g, i) =>
      i === gi ? { ...g, options: g.options.filter((_, j) => j !== oi) } : g));
  }

  function onPickImage(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
  }

  async function save(e) {
    e.preventDefault();
    setError("");
    // basic validation
    for (const g of form.option_groups) {
      if (!g.name.trim()) return setError("Dê um nome a todas as seções de opções.");
      const opts = g.options.filter((o) => o.name.trim());
      if (opts.length === 0) return setError(`A seção "${g.name}" precisa de pelo menos uma opção.`);
      if (Number(g.max_select) < Number(g.min_select))
        return setError(`Em "${g.name}", o máximo não pode ser menor que o mínimo.`);
    }
    setBusy(true);
    try {
      const payload = {
        name: form.name,
        description: form.description,
        base_price: Number(form.base_price) || 0,
        is_available: form.is_available,
        option_groups: form.option_groups.map((g, gi) => ({
          name: g.name,
          min_select: Number(g.min_select) || 0,
          max_select: Math.max(Number(g.max_select) || 1, 1),
          allow_repeat: g.allow_repeat,
          sort_order: gi,
          options: g.options
            .filter((o) => o.name.trim())
            .map((o, oi) => ({ name: o.name, price_delta: Number(o.price_delta) || 0, sort_order: oi })),
        })),
      };
      let saved;
      if (isEdit) {
        ({ data: saved } = await api.patch(`/menu/items/${item.id}`, payload));
      } else {
        ({ data: saved } = await api.post(`/menu/categories/${categoryId}/items`, payload));
      }
      if (imageFile) {
        const fd = new FormData();
        fd.append("file", imageFile);
        ({ data: saved } = await api.post(`/menu/items/${saved.id}/image`, fd));
      }
      onSaved(saved);
      onClose();
    } catch (err) {
      setError(apiError(err));
      setBusy(false);
    }
  }

  return (
    <Modal
      wide
      title={isEdit ? "Editar item" : "Novo item"}
      onClose={onClose}
      footer={
        <>
          <button className="btn ghost" onClick={onClose} type="button">Cancelar</button>
          <button className="btn" onClick={save} disabled={busy}>{busy ? "Salvando..." : "Salvar item"}</button>
        </>
      }
    >
      {error && <div className="alert error">{error}</div>}
      <form onSubmit={save}>
        <div className="item-edit-top">
          <div className="item-image-pick" onClick={() => fileInput.current.click()}>
            {imagePreview ? <img src={imagePreview} alt="" /> : <span>📷<br />Foto</span>}
            <input ref={fileInput} type="file" accept="image/*" hidden onChange={onPickImage} />
          </div>
          <div className="grow">
            <div className="field"><label>Nome do item</label>
              <input value={form.name} onChange={(e) => set("name", e.target.value)} required autoFocus /></div>
            <div className="field"><label>Preço base</label>
              <MoneyInput allowEmpty value={form.base_price}
                onChange={(v) => set("base_price", v)} placeholder="R$ 0,00" required /></div>
          </div>
        </div>
        <div className="field"><label>Descrição</label>
          <textarea value={form.description} onChange={(e) => set("description", e.target.value)} /></div>
        <label className="checkbox"><input type="checkbox" checked={form.is_available}
          onChange={(e) => set("is_available", e.target.checked)} /> Disponível para venda</label>

        <div className="between mt24">
          <h4 style={{ margin: 0 }}>Seções de opções</h4>
          <button type="button" className="btn ghost sm" onClick={addGroup}>+ Adicionar seção</button>
        </div>
        <p className="hint">Ex.: tamanho, sabor, adicionais. Defina quantas opções o cliente pode escolher.</p>

        <div className="stack" style={{ gap: 14 }}>
          {form.option_groups.map((g, gi) => (
            <div key={gi} className="opt-group">
              <div className="row">
                <div className="field" style={{ flex: 2 }}><label>Nome da seção</label>
                  <input value={g.name} onChange={(e) => updateGroup(gi, "name", e.target.value)}
                    placeholder="Ex.: Escolha o tamanho" /></div>
                <div className="field"><label>Mínimo</label>
                  <input type="number" min="0" value={g.min_select}
                    onChange={(e) => updateGroup(gi, "min_select", e.target.value)} /></div>
                <div className="field"><label>Máximo</label>
                  <input type="number" min="1" value={g.max_select}
                    onChange={(e) => updateGroup(gi, "max_select", e.target.value)} /></div>
              </div>
              <div className="between">
                <label className="checkbox"><input type="checkbox" checked={g.allow_repeat}
                  onChange={(e) => updateGroup(gi, "allow_repeat", e.target.checked)} />
                  Permitir escolher a mesma opção mais de uma vez</label>
                <button type="button" className="btn danger sm" onClick={() => removeGroup(gi)}>Remover seção</button>
              </div>

              <div className="opt-list">
                {g.options.map((o, oi) => (
                  <div key={oi} className="opt-row">
                    <input value={o.name} placeholder="Nome da opção"
                      onChange={(e) => updateOption(gi, oi, "name", e.target.value)} />
                    <div className="opt-price">
                      <span>+</span>
                      <MoneyInput value={o.price_delta}
                        onChange={(v) => updateOption(gi, oi, "price_delta", v)} />
                    </div>
                    <button type="button" className="opt-remove" onClick={() => removeOption(gi, oi)}>✕</button>
                  </div>
                ))}
                <button type="button" className="btn ghost sm" onClick={() => addOption(gi)}>+ Opção</button>
              </div>
            </div>
          ))}
          {form.option_groups.length === 0 && (
            <p className="muted text-sm">Nenhuma seção. Itens simples (ex.: bebidas) podem ficar sem opções.</p>
          )}
        </div>
      </form>
    </Modal>
  );
}
