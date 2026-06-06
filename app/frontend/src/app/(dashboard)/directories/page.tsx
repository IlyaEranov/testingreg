"use client";
import { useEffect, useState } from "react";
import { directories as api } from "@/lib/api";
import { useUser } from "@/lib/UserContext";
import { Plus, X, Pencil } from "lucide-react";

type Tab = "reasons" | "suppliers" | "warehouses";

export default function DirectoriesPage() {
  const { user } = useUser();
  const [tab, setTab] = useState<Tab>("reasons");
  const [reasons, setReasons] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [modal, setModal] = useState<{ type: Tab; item: any } | null>(null);

  const canEdit = user && ["admin", "manager"].includes(user.role);

  function loadAll() {
    api.reasons().then(setReasons).catch(() => {});
    api.suppliers().then(setSuppliers).catch(() => {});
    api.warehouses().then(setWarehouses).catch(() => {});
  }
  useEffect(loadAll, []);

  const tabs: { key: Tab; label: string }[] = [
    { key: "reasons", label: "Причины возврата" },
    { key: "suppliers", label: "Поставщики" },
    { key: "warehouses", label: "Склады" },
  ];

  function openNew() {
    if (tab === "reasons") setModal({ type: "reasons", item: { name: "", description: "", is_active: true } });
    if (tab === "suppliers") setModal({ type: "suppliers", item: { name: "", contact_person: "", phone: "", email: "", address: "" } });
    if (tab === "warehouses") setModal({ type: "warehouses", item: { name: "", address: "", is_active: true } });
  }

  async function save() {
    if (!modal) return;
    const { type, item } = modal;
    try {
      if (type === "reasons") {
        item.id ? await api.updateReason(item.id, item) : await api.createReason(item);
      } else if (type === "suppliers") {
        item.id ? await api.updateSupplier(item.id, item) : await api.createSupplier(item);
      } else {
        await api.createWarehouse(item);
      }
      setModal(null);
      loadAll();
    } catch (e: any) { alert(e.message); }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-brand-700">Справочники</h1>
        {canEdit && (
          <button onClick={openNew} className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white rounded-2xl font-semibold text-sm hover:bg-brand-600 transition shadow-md">
            <Plus className="w-4 h-4" /> Добавить
          </button>
        )}
      </div>

      <div className="flex gap-1 border-b-2 border-brand-100 mb-5">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={`px-5 py-2.5 text-sm font-semibold rounded-t-xl transition -mb-[2px] ${tab === t.key ? "text-brand-600 border-b-2 border-brand-500 bg-brand-50" : "text-gray-400 hover:text-brand-500"}`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Reasons */}
      {tab === "reasons" && (
        <Table headers={["ID", "Наименование", "Описание", "Активна", ""]}>
          {reasons.map((r) => (
            <tr key={r.id} className="border-t border-brand-50">
              <td className="px-5 py-3">{r.id}</td>
              <td className="px-5 py-3 font-semibold">{r.name}</td>
              <td className="px-5 py-3 text-xs text-gray-500">{r.description}</td>
              <td className="px-5 py-3"><Active v={r.is_active} /></td>
              <td className="px-5 py-3 text-right">{canEdit && <EditBtn onClick={() => setModal({ type: "reasons", item: { ...r } })} />}</td>
            </tr>
          ))}
        </Table>
      )}

      {/* Suppliers */}
      {tab === "suppliers" && (
        <Table headers={["ID", "Наименование", "Контакт", "Телефон", "Email", ""]}>
          {suppliers.map((s) => (
            <tr key={s.id} className="border-t border-brand-50">
              <td className="px-5 py-3">{s.id}</td>
              <td className="px-5 py-3 font-semibold">{s.name}</td>
              <td className="px-5 py-3">{s.contact_person}</td>
              <td className="px-5 py-3">{s.phone}</td>
              <td className="px-5 py-3">{s.email}</td>
              <td className="px-5 py-3 text-right">{canEdit && <EditBtn onClick={() => setModal({ type: "suppliers", item: { ...s } })} />}</td>
            </tr>
          ))}
        </Table>
      )}

      {/* Warehouses */}
      {tab === "warehouses" && (
        <Table headers={["ID", "Наименование", "Адрес", "Активен"]}>
          {warehouses.map((w) => (
            <tr key={w.id} className="border-t border-brand-50">
              <td className="px-5 py-3">{w.id}</td>
              <td className="px-5 py-3 font-semibold">{w.name}</td>
              <td className="px-5 py-3">{w.address}</td>
              <td className="px-5 py-3"><Active v={w.is_active} /></td>
            </tr>
          ))}
        </Table>
      )}

      {/* Modal */}
      {modal && (
        <div className="fixed inset-0 bg-brand-700/50 backdrop-blur-sm z-50 flex items-start justify-center p-3 sm:p-6 pt-6 sm:pt-16 overflow-y-auto"
          onClick={(e) => { if (e.target === e.currentTarget) setModal(null); }}>
          <div className="bg-white rounded-[28px] w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between px-7 py-5 border-b border-brand-100 bg-brand-50 rounded-t-[28px]">
              <h2 className="text-lg font-bold text-brand-700">{modal.item.id ? "Редактирование" : "Новая запись"}</h2>
              <button onClick={() => setModal(null)} className="text-brand-300 hover:text-brand-500"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-7 space-y-4">
              {modal.type === "reasons" && (
                <>
                  <ModalInput label="Наименование" value={modal.item.name} onChange={(v) => setModal({ ...modal, item: { ...modal.item, name: v } })} />
                  <ModalInput label="Описание" value={modal.item.description} onChange={(v) => setModal({ ...modal, item: { ...modal.item, description: v } })} />
                  <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={modal.item.is_active} onChange={(e) => setModal({ ...modal, item: { ...modal.item, is_active: e.target.checked } })} /> Активна</label>
                </>
              )}
              {modal.type === "suppliers" && (
                <>
                  <ModalInput label="Наименование" value={modal.item.name} onChange={(v) => setModal({ ...modal, item: { ...modal.item, name: v } })} />
                  <ModalInput label="Контактное лицо" value={modal.item.contact_person} onChange={(v) => setModal({ ...modal, item: { ...modal.item, contact_person: v } })} />
                  <ModalInput label="Телефон" value={modal.item.phone} onChange={(v) => setModal({ ...modal, item: { ...modal.item, phone: v } })} />
                  <ModalInput label="Email" value={modal.item.email} onChange={(v) => setModal({ ...modal, item: { ...modal.item, email: v } })} />
                  <ModalInput label="Адрес" value={modal.item.address} onChange={(v) => setModal({ ...modal, item: { ...modal.item, address: v } })} />
                </>
              )}
              {modal.type === "warehouses" && (
                <>
                  <ModalInput label="Наименование" value={modal.item.name} onChange={(v) => setModal({ ...modal, item: { ...modal.item, name: v } })} />
                  <ModalInput label="Адрес" value={modal.item.address} onChange={(v) => setModal({ ...modal, item: { ...modal.item, address: v } })} />
                </>
              )}
              <div className="flex gap-3 justify-end pt-2">
                <button onClick={() => setModal(null)} className="px-5 py-2 bg-brand-100 text-brand-600 rounded-xl font-semibold text-sm">Отмена</button>
                <button onClick={save} className="px-5 py-2 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition">Сохранить</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Table({ headers, children }: { headers: string[]; children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl3 border border-brand-100 overflow-hidden">
      <div className="overflow-x-auto">
      <table className="w-full text-sm min-w-[520px]">
        <thead><tr className="bg-brand-50">{headers.map((h, i) => <th key={i} className="text-left px-5 py-3 font-bold text-brand-600">{h}</th>)}</tr></thead>
        <tbody>{children}</tbody>
      </table>
      </div>
    </div>
  );
}
function Active({ v }: { v: boolean }) {
  return <span className={`px-3 py-1 rounded-full text-xs font-semibold ${v ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>{v ? "Да" : "Нет"}</span>;
}
function EditBtn({ onClick }: { onClick: () => void }) {
  return <button onClick={onClick} className="p-1.5 rounded-lg hover:bg-brand-100 transition"><Pencil className="w-4 h-4 text-brand-500" /></button>;
}
function ModalInput({ label, value, onChange }: any) {
  return (
    <div>
      <label className="block text-xs font-semibold text-brand-600 mb-1">{label}</label>
      <input value={value || ""} onChange={(e) => onChange(e.target.value)} className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none focus:border-brand-500" />
    </div>
  );
}
