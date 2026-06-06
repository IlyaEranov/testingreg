"use client";
import { useEffect, useState } from "react";
import { warehouse as api, returns as returnsApi } from "@/lib/api";
import StatusBadge from "@/components/ui/StatusBadge";
import type { ReturnRequest } from "@/types";

export default function WarehousePage() {
  const [pending, setPending] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingId, setCheckingId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ReturnRequest | null>(null);
  const [checkData, setCheckData] = useState<any[]>([]);

  useEffect(() => { loadPending(); }, []);

  async function loadPending() {
    setLoading(true);
    try {
      const res = await api.pending();
      setPending(res);
    } catch (e) { console.error(e); }
    setLoading(false);
  }

  async function startCheck(id: number) {
    try {
      const d = await returnsApi.get(id);
      setDetail(d);
      setCheckData(
        (d.items || []).map((item: any) => ({
          return_item_id: item.id,
          quantity_fact: item.quantity,
          packaging_condition: "Упаковка целая",
          defect_description: "",
        }))
      );
      setCheckingId(id);
    } catch (e: any) { alert(e.message); }
  }

  async function submitCheck(e: React.FormEvent) {
    e.preventDefault();
    if (!checkingId) return;
    try {
      await api.submitCheck(checkingId, checkData);
      setCheckingId(null);
      setDetail(null);
      loadPending();
    } catch (e: any) { alert(e.message); }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-brand-700 mb-2">Складская проверка</h1>
      <p className="text-sm text-gray-500 mb-6">Заявки, ожидающие проверки товара на складе</p>

      <div className="bg-white rounded-xl3 border border-brand-100 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[600px]">
          <thead>
            <tr className="bg-brand-50">
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">№ заявки</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Клиент</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Дата</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Сумма</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Действия</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5} className="text-center py-10 text-brand-300">Загрузка...</td></tr>
            ) : pending.length === 0 ? (
              <tr><td colSpan={5} className="text-center py-10 text-brand-300">Нет заявок на проверку</td></tr>
            ) : (
              pending.map((r) => (
                <tr key={r.id} className="border-t border-brand-50 hover:bg-brand-50/50">
                  <td className="px-5 py-3 font-semibold">{r.number}</td>
                  <td className="px-5 py-3">{r.client_name}</td>
                  <td className="px-5 py-3">{r.created_at?.slice(0, 10)}</td>
                  <td className="px-5 py-3">{new Intl.NumberFormat("ru-RU").format(r.total_amount)} ₽</td>
                  <td className="px-5 py-3">
                    <button
                      onClick={() => startCheck(r.id)}
                      className="px-4 py-1.5 bg-brand-500 text-white rounded-xl text-xs font-semibold hover:bg-brand-600 transition"
                    >
                      Провести проверку
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        </div>
      </div>

      {/* Check modal */}
      {checkingId && detail && (
        <div className="fixed inset-0 bg-brand-700/50 backdrop-blur-sm z-50 flex items-start justify-center p-3 sm:p-6 pt-6 sm:pt-12 overflow-y-auto"
          onClick={(e) => { if (e.target === e.currentTarget) { setCheckingId(null); setDetail(null); } }}>
          <div className="bg-white rounded-[28px] w-full max-w-2xl shadow-2xl">
            <div className="flex items-center justify-between px-7 py-5 border-b border-brand-100 bg-brand-50 rounded-t-[28px]">
              <h2 className="text-lg font-bold text-brand-700">Складская проверка — {detail.number}</h2>
              <button onClick={() => { setCheckingId(null); setDetail(null); }} className="text-brand-300 hover:text-brand-500 text-2xl">&times;</button>
            </div>
            <form onSubmit={submitCheck} className="p-7">
              {(detail.items || []).map((item: any, i: number) => (
                <div key={item.id} className="bg-brand-50 rounded-2xl p-4 mb-4 border border-brand-100">
                  <div className="font-semibold text-brand-700 mb-3">{item.product_name} ({item.article})</div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-brand-600 mb-1">Факт. кол-во</label>
                      <input type="number" min="0" value={checkData[i]?.quantity_fact || 0}
                        onChange={(e) => { const d = [...checkData]; d[i].quantity_fact = Number(e.target.value); setCheckData(d); }}
                        className="w-full px-3 py-2 bg-white border border-brand-200 rounded-xl text-sm outline-none" />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold text-brand-600 mb-1">Состояние упаковки</label>
                      <select value={checkData[i]?.packaging_condition || ""}
                        onChange={(e) => { const d = [...checkData]; d[i].packaging_condition = e.target.value; setCheckData(d); }}
                        className="w-full px-3 py-2 bg-white border border-brand-200 rounded-xl text-sm outline-none">
                        <option>Упаковка целая</option>
                        <option>Упаковка повреждена</option>
                        <option>Упаковка вскрыта</option>
                        <option>Без упаковки</option>
                      </select>
                    </div>
                    <div className="col-span-2">
                      <label className="block text-xs font-semibold text-brand-600 mb-1">Описание дефекта</label>
                      <textarea rows={2} value={checkData[i]?.defect_description || ""}
                        onChange={(e) => { const d = [...checkData]; d[i].defect_description = e.target.value; setCheckData(d); }}
                        className="w-full px-3 py-2 bg-white border border-brand-200 rounded-xl text-sm outline-none resize-none"
                        placeholder="Опишите дефекты..." />
                    </div>
                  </div>
                </div>
              ))}
              <div className="flex gap-3 justify-end border-t border-brand-100 pt-5">
                <button type="button" onClick={() => { setCheckingId(null); setDetail(null); }}
                  className="px-5 py-2 bg-brand-100 text-brand-600 rounded-xl font-semibold text-sm">Отмена</button>
                <button type="submit" className="px-5 py-2 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition">
                  Сохранить результат
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
