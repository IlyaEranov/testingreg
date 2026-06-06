"use client";
import { useEffect, useState } from "react";
import { users as api } from "@/lib/api";
import { useUser } from "@/lib/UserContext";
import { ROLE_LABELS } from "@/lib/roles";
import { Plus, X, Lock, Unlock } from "lucide-react";

export default function UsersPage() {
  const { user } = useUser();
  const [data, setData] = useState<any[]>([]);
  const [roles, setRoles] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState<any | null>(null);

  const isAdmin = user?.role === "admin";

  function load() {
    setLoading(true);
    api.list().then(setData).catch(console.error).finally(() => setLoading(false));
  }
  useEffect(() => {
    load();
    api.roles().then(setRoles).catch(() => {});
  }, []);

  function openNew() {
    setModal({ email: "", password: "", last_name: "", first_name: "", patronymic: "", phone: "", role_id: 2 });
  }

  async function save() {
    try {
      await api.create(modal);
      setModal(null);
      load();
    } catch (e: any) { alert(e.message); }
  }

  async function toggleActive(u: any) {
    try {
      await api.update(u.id, { is_active: !u.is_active });
      load();
    } catch (e: any) { alert(e.message); }
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-brand-700">Пользователи</h1>
        {isAdmin && (
          <button onClick={openNew} className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white rounded-2xl font-semibold text-sm hover:bg-brand-600 transition shadow-md">
            <Plus className="w-4 h-4" /> Добавить
          </button>
        )}
      </div>

      <div className="bg-white rounded-xl3 border border-brand-100 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[640px]">
          <thead>
            <tr className="bg-brand-50">
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">ID</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">ФИО</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Email</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Роль</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Статус</th>
              {isAdmin && <th className="text-right px-5 py-3.5 font-bold text-brand-600">Действия</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="text-center py-10 text-brand-300">Загрузка...</td></tr>
            ) : (
              data.map((u) => (
                <tr key={u.id} className="border-t border-brand-50 hover:bg-brand-50/50">
                  <td className="px-5 py-3">{u.id}</td>
                  <td className="px-5 py-3 font-semibold">{u.last_name} {u.first_name} {u.patronymic || ""}</td>
                  <td className="px-5 py-3">{u.email}</td>
                  <td className="px-5 py-3"><span className="px-3 py-1 rounded-full text-xs font-semibold bg-brand-100 text-brand-600">{ROLE_LABELS[u.role_name] || u.role_name}</span></td>
                  <td className="px-5 py-3"><span className={`px-3 py-1 rounded-full text-xs font-semibold ${u.is_active ? "bg-green-100 text-green-800" : "bg-red-100 text-red-800"}`}>{u.is_active ? "Активен" : "Заблокирован"}</span></td>
                  {isAdmin && (
                    <td className="px-5 py-3 text-right">
                      <button onClick={() => toggleActive(u)} className="p-1.5 rounded-lg hover:bg-brand-100 transition" title={u.is_active ? "Заблокировать" : "Разблокировать"}>
                        {u.is_active ? <Lock className="w-4 h-4 text-red-500" /> : <Unlock className="w-4 h-4 text-green-600" />}
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
        </div>
      </div>

      {modal && (
        <div className="fixed inset-0 bg-brand-700/50 backdrop-blur-sm z-50 flex items-start justify-center p-3 sm:p-6 pt-6 sm:pt-12 overflow-y-auto"
          onClick={(e) => { if (e.target === e.currentTarget) setModal(null); }}>
          <div className="bg-white rounded-[28px] w-full max-w-lg shadow-2xl">
            <div className="flex items-center justify-between px-7 py-5 border-b border-brand-100 bg-brand-50 rounded-t-[28px]">
              <h2 className="text-lg font-bold text-brand-700">Новый пользователь</h2>
              <button onClick={() => setModal(null)} className="text-brand-300 hover:text-brand-500"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5 sm:p-7 grid grid-cols-1 sm:grid-cols-2 gap-4">
              <UInput label="Фамилия" value={modal.last_name} onChange={(v) => setModal({ ...modal, last_name: v })} />
              <UInput label="Имя" value={modal.first_name} onChange={(v) => setModal({ ...modal, first_name: v })} />
              <UInput label="Отчество" value={modal.patronymic} onChange={(v) => setModal({ ...modal, patronymic: v })} />
              <UInput label="Телефон" value={modal.phone} onChange={(v) => setModal({ ...modal, phone: v })} />
              <UInput label="Email" value={modal.email} onChange={(v) => setModal({ ...modal, email: v })} />
              <UInput label="Пароль" value={modal.password} onChange={(v) => setModal({ ...modal, password: v })} />
              <div className="col-span-2">
                <label className="block text-xs font-semibold text-brand-600 mb-1">Роль</label>
                <select value={modal.role_id} onChange={(e) => setModal({ ...modal, role_id: Number(e.target.value) })} className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none">
                  {roles.map((r) => <option key={r.id} value={r.id}>{ROLE_LABELS[r.name] || r.name}</option>)}
                </select>
              </div>
              <div className="col-span-2 flex gap-3 justify-end pt-2">
                <button onClick={() => setModal(null)} className="px-5 py-2 bg-brand-100 text-brand-600 rounded-xl font-semibold text-sm">Отмена</button>
                <button onClick={save} className="px-5 py-2 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition">Создать</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function UInput({ label, value, onChange }: any) {
  return (
    <div>
      <label className="block text-xs font-semibold text-brand-600 mb-1">{label}</label>
      <input value={value || ""} onChange={(e) => onChange(e.target.value)} className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none focus:border-brand-500" />
    </div>
  );
}
