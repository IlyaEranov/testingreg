"use client";
import { useEffect, useState, useRef } from "react";
import { reports as api } from "@/lib/api";
import { Chart, registerables } from "chart.js";

Chart.register(...registerables);

export default function ReportsPage() {
  const [summary, setSummary] = useState<any>(null);
  const [byReason, setByReason] = useState<any[]>([]);
  const [byMonth, setByMonth] = useState<any[]>([]);
  const [bySupplier, setBySupplier] = useState<any[]>([]);
  const barRef = useRef<HTMLCanvasElement>(null);
  const pieRef = useRef<HTMLCanvasElement>(null);
  const chartInstances = useRef<any[]>([]);

  useEffect(() => { loadAll(); }, []);

  async function loadAll() {
    try {
      const [s, r, m, sup] = await Promise.all([
        api.summary(), api.byReason(), api.byMonth(), api.bySupplier(),
      ]);
      setSummary(s);
      setByReason(r);
      setByMonth(m);
      setBySupplier(sup);
      renderCharts(m, r);
    } catch (e) { console.error(e); }
  }

  function renderCharts(months: any[], reasons: any[]) {
    chartInstances.current.forEach((c) => c?.destroy());
    chartInstances.current = [];

    if (barRef.current) {
      const ctx = barRef.current.getContext("2d")!;
      chartInstances.current.push(
        new Chart(ctx, {
          type: "bar",
          data: {
            labels: months.map((m) => m.month),
            datasets: [{ label: "Заявок", data: months.map((m) => m.count), backgroundColor: "#407368", borderRadius: 8 }],
          },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
        })
      );
    }

    if (pieRef.current) {
      const ctx = pieRef.current.getContext("2d")!;
      const colors = ["#407368", "#c7bc9a", "#7ab8a8", "#e8a87c", "#d4a5a5", "#5f9b8c"];
      chartInstances.current.push(
        new Chart(ctx, {
          type: "pie",
          data: {
            labels: reasons.map((r) => r.reason),
            datasets: [{ data: reasons.map((r) => r.count), backgroundColor: colors, borderWidth: 2, borderColor: "#fff" }],
          },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: "right", labels: { font: { size: 11 } } } } },
        })
      );
    }
  }

  const fmt = (n: number) => new Intl.NumberFormat("ru-RU").format(n);

  return (
    <div>
      <h1 className="text-2xl font-bold text-brand-700 mb-6">Отчёты</h1>

      {/* Stats */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[
            { label: "Всего заявок", value: summary.total, accent: "border-l-brand-500" },
            { label: "В работе", value: summary.active, accent: "border-l-amber-400" },
            { label: "Завершено", value: summary.done, accent: "border-l-green-400" },
            { label: "Сумма возвратов", value: `${fmt(summary.total_amount)} ₽`, accent: "border-l-brand-400" },
          ].map((s, i) => (
            <div key={i} className={`bg-white rounded-xl3 p-5 border border-brand-100 border-l-4 ${s.accent}`}>
              <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider">{s.label}</div>
              <div className="text-2xl font-bold text-brand-700 mt-1">{s.value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 mb-6">
        <div className="bg-white rounded-xl3 border border-brand-100 p-5">
          <h3 className="text-sm font-bold text-brand-600 mb-3">Динамика по месяцам</h3>
          <div className="h-[260px]"><canvas ref={barRef} /></div>
        </div>
        <div className="bg-white rounded-xl3 border border-brand-100 p-5">
          <h3 className="text-sm font-bold text-brand-600 mb-3">По причинам возврата</h3>
          <div className="h-[260px]"><canvas ref={pieRef} /></div>
        </div>
      </div>

      {/* Supplier table */}
      <div className="bg-white rounded-xl3 border border-brand-100 overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-brand-100">
          <h3 className="text-sm font-bold text-brand-600">Статистика по поставщикам</h3>
        </div>
        <div className="overflow-x-auto">
        <table className="w-full text-sm min-w-[480px]">
          <thead><tr className="bg-brand-50">
            <th className="text-left px-5 py-3 font-bold text-brand-600">Поставщик</th>
            <th className="text-left px-5 py-3 font-bold text-brand-600">Экспертиз</th>
            <th className="text-left px-5 py-3 font-bold text-brand-600">Подтв. брак</th>
          </tr></thead>
          <tbody>
            {bySupplier.length === 0 ? (
              <tr><td colSpan={3} className="text-center py-8 text-brand-300">Нет данных</td></tr>
            ) : bySupplier.map((s, i) => (
              <tr key={i} className="border-t border-brand-50">
                <td className="px-5 py-3 font-semibold">{s.supplier}</td>
                <td className="px-5 py-3">{s.examinations}</td>
                <td className="px-5 py-3">{s.defects_confirmed}</td>
              </tr>
            ))}
          </tbody>
        </table>
        </div>
      </div>
    </div>
  );
}
