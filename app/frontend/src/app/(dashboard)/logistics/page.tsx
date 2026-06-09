"use client";
import { useEffect, useState } from "react";
import { returns as api } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";
import { Download, FileText, Truck } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export default function LogisticsPage() {
  const [list, setList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState<any | null>(null);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try {
      // Бэкенд для роли «Логистика» возвращает только заявки в перевозке
      setList(await api.list({ status: "in_transit" }));
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function open(id: number) {
    try { setDetail(await api.get(id)); } catch (e: any) { alert(e.message); }
  }

  function downloadDoc(docId: number) {
    const token = localStorage.getItem("token");
    fetch(`${API_BASE}/documents/download/${docId}`, { headers: { Authorization: `Bearer ${token}` } })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url; a.download = "route_sheet.docx"; a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => alert("Ошибка скачивания"));
  }

  const fmt = (n: number) => new Intl.NumberFormat("ru-RU").format(n);
  const routeSheet = detail?.documents?.find((d: any) => d.document_type === "route_sheet");

  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <Truck className="w-6 h-6 text-brand-600" />
        <h1 className="text-2xl font-bold text-brand-700">К перевозке</h1>
      </div>
      <p className="text-sm text-gray-500 mb-6">Заявки, по которым сформирован маршрутный лист — товар нужно доставить на склад</p>

      <div className="bg-white rounded-xl3 border border-brand-100 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[600px]">
            <thead>
              <tr className="bg-brand-50">
                <th className="text-left px-5 py-3.5 font-bold text-brand-600">№ заявки</th>
                <th className="text-left px-5 py-3.5 font-bold text-brand-600">Клиент</th>
                <th className="text-left px-5 py-3.5 font-bold text-brand-600">Склад приёмки</th>
                <th className="text-left px-5 py-3.5 font-bold text-brand-600">Статус</th>
                <th className="text-left px-5 py-3.5 font-bold text-brand-600">Действия</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="text-center py-10 text-brand-300">Загрузка...</td></tr>
              ) : list.length === 0 ? (
                <tr><td colSpan={5} className="text-center py-10 text-brand-300">Нет заявок к перевозке</td></tr>
              ) : (
                list.map((r) => (
                  <tr key={r.id} className="border-t border-brand-50 hover:bg-brand-50/50">
                    <td className="px-5 py-3 font-semibold">{r.number}</td>
                    <td className="px-5 py-3">{r.client_name}</td>
                    <td className="px-5 py-3 text-xs">{r.warehouse_name}</td>
                    <td className="px-5 py-3"><StatusBadge status={r.status} /></td>
                    <td className="px-5 py-3">
                      <button onClick={() => open(r.id)} className="px-4 py-1.5 bg-brand-500 text-white rounded-xl text-xs font-semibold hover:bg-brand-600 transition">
                        Маршрутный лист
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Маршрутный лист */}
      {detail && (
        <div className="fixed inset-0 bg-brand-700/50 backdrop-blur-sm z-50 flex items-start justify-center p-3 sm:p-6 pt-6 sm:pt-12 overflow-y-auto"
          onClick={(e) => { if (e.target === e.currentTarget) setDetail(null); }}>
          <div className="bg-white rounded-[28px] w-full max-w-2xl shadow-2xl">
            <div className="flex items-center justify-between px-7 py-5 border-b border-brand-100 bg-brand-50 rounded-t-[28px]">
              <h2 className="text-lg font-bold text-brand-700">Перевозка — {detail.number}</h2>
              <button onClick={() => setDetail(null)} className="text-brand-300 hover:text-brand-500 text-2xl">&times;</button>
            </div>
            <div className="p-7 space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
                <div><span className="text-xs text-gray-400 font-semibold">Откуда забрать (покупатель)</span><div className="mt-1 font-medium text-brand-700">{detail.client_name}</div></div>
                <div><span className="text-xs text-gray-400 font-semibold">Телефон</span><div className="mt-1 font-medium text-brand-700">{detail.client_phone || "—"}</div></div>
                <div><span className="text-xs text-gray-400 font-semibold">Куда везти (склад)</span><div className="mt-1 font-medium text-brand-700">{detail.warehouse_name}</div></div>
                <div><span className="text-xs text-gray-400 font-semibold">Позиций</span><div className="mt-1 font-medium text-brand-700">{detail.items?.length || 0}</div></div>
              </div>

              <div className="space-y-2">
                {detail.items?.map((it: any) => (
                  <div key={it.id} className="bg-brand-50 rounded-xl p-3 border border-brand-100 text-sm">
                    <span className="font-semibold text-brand-700">{it.product_name}</span>
                    <span className="text-xs text-gray-500 ml-2">{it.quantity} {it.unit} • арт. {it.article}</span>
                  </div>
                ))}
              </div>

              <div className="border-t border-brand-100 pt-4">
                {routeSheet ? (
                  <button onClick={() => downloadDoc(routeSheet.id)} className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white rounded-2xl font-semibold text-sm hover:bg-brand-600 transition">
                    <Download className="w-4 h-4" /> Скачать маршрутный лист
                  </button>
                ) : (
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <FileText className="w-4 h-4" /> Маршрутный лист ещё не сформирован
                  </div>
                )}
                <p className="text-xs text-gray-400 mt-3">Приёмку и сверку товара на складе выполняет сотрудник претензионного отдела.</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
