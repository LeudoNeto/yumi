import { useEffect, useState } from "react";
import api, { apiError } from "../../api";
import { formatBRL } from "../../lib";
import Modal from "../../components/Modal.jsx";
import ItemEditor from "../../components/ItemEditor.jsx";

export default function MenuEditor() {
  const [categories, setCategories] = useState(null);
  const [error, setError] = useState("");
  const [catModal, setCatModal] = useState(null); // {id?, name, description}
  const [itemModal, setItemModal] = useState(null); // {categoryId, item}

  async function load() {
    try {
      const { data } = await api.get("/menu/categories");
      setCategories(data);
    } catch (err) {
      setError(apiError(err));
    }
  }
  useEffect(() => { load(); }, []);

  async function saveCategory(e) {
    e.preventDefault();
    try {
      const payload = { name: catModal.name, description: catModal.description || "", sort_order: catModal.sort_order ?? 0 };
      if (catModal.id) await api.patch(`/menu/categories/${catModal.id}`, payload);
      else await api.post("/menu/categories", payload);
      setCatModal(null);
      load();
    } catch (err) {
      setError(apiError(err));
    }
  }

  async function deleteCategory(cat) {
    if (!confirm(`Excluir a categoria "${cat.name}" e todos os seus itens?`)) return;
    await api.delete(`/menu/categories/${cat.id}`);
    load();
  }

  async function deleteItem(item) {
    if (!confirm(`Excluir o item "${item.name}"?`)) return;
    await api.delete(`/menu/items/${item.id}`);
    load();
  }

  if (!categories) return <div className="spinner" />;

  return (
    <div className="stack">
      <div className="between">
        <h2>Cardápio</h2>
        <button className="btn" onClick={() => setCatModal({ name: "", description: "" })}>+ Nova categoria</button>
      </div>
      {error && <div className="alert error">{error}</div>}

      {categories.length === 0 && (
        <div className="card pad empty">
          <p>Seu cardápio está vazio.</p>
          <button className="btn" onClick={() => setCatModal({ name: "", description: "" })}>Criar primeira categoria</button>
        </div>
      )}

      {categories.map((cat) => (
        <section key={cat.id} className="card pad">
          <div className="between">
            <div>
              <h3 style={{ margin: 0 }}>{cat.name}</h3>
              {cat.description && <span className="muted text-sm">{cat.description}</span>}
            </div>
            <div className="center gap8">
              <button className="btn ghost sm" onClick={() => setCatModal(cat)}>Editar</button>
              <button className="btn danger sm" onClick={() => deleteCategory(cat)}>Excluir</button>
            </div>
          </div>

          <div className="menu-items mt16">
            {cat.items.map((item) => (
              <div key={item.id} className="menu-item-row">
                <div className="menu-item-thumb">
                  {item.image_url ? <img src={item.image_url} alt="" /> : <span>🍽️</span>}
                </div>
                <div className="grow">
                  <div className="center gap8">
                    <strong>{item.name}</strong>
                    {!item.is_available && <span className="badge gray">Indisponível</span>}
                    {item.option_groups.length > 0 && (
                      <span className="badge orange">{item.option_groups.length} seção(ões)</span>
                    )}
                  </div>
                  {item.description && <div className="muted text-sm">{item.description}</div>}
                  <div className="price text-sm mt8">{formatBRL(item.base_price)}</div>
                </div>
                <div className="center gap8">
                  <button className="btn ghost sm" onClick={() => setItemModal({ categoryId: cat.id, item })}>Editar</button>
                  <button className="btn danger sm" onClick={() => deleteItem(item)}>✕</button>
                </div>
              </div>
            ))}
            <button className="btn ghost block mt8" onClick={() => setItemModal({ categoryId: cat.id, item: null })}>
              + Adicionar item em {cat.name}
            </button>
          </div>
        </section>
      ))}

      {catModal && (
        <Modal title={catModal.id ? "Editar categoria" : "Nova categoria"} onClose={() => setCatModal(null)}
          footer={
            <>
              <button className="btn ghost" onClick={() => setCatModal(null)}>Cancelar</button>
              <button className="btn" onClick={saveCategory}>Salvar</button>
            </>
          }>
          <form onSubmit={saveCategory}>
            <div className="field"><label>Nome</label>
              <input value={catModal.name} autoFocus required
                onChange={(e) => setCatModal({ ...catModal, name: e.target.value })} /></div>
            <div className="field"><label>Descrição (opcional)</label>
              <input value={catModal.description || ""}
                onChange={(e) => setCatModal({ ...catModal, description: e.target.value })} /></div>
          </form>
        </Modal>
      )}

      {itemModal && (
        <ItemEditor
          categoryId={itemModal.categoryId}
          item={itemModal.item}
          onClose={() => setItemModal(null)}
          onSaved={() => { setItemModal(null); load(); }}
        />
      )}
    </div>
  );
}
