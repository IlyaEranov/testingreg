"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { dashboard } from "@/lib/api";
import { useUser } from "@/lib/UserContext";
import { canCreateReturn } from "@/lib/roles";
import StatusBadge from "@/components/ui/StatusBadge";
import { Plus } from "lucide-react";

const ACCENT_BORDER: Record<string, string> = {
  brand: "border-l-brand-500",
  amber: "border-l-amber-400",
  green: "border-l-green-400",
  purple: "border-l-purple-400",
  orange: "border-l-orange-400",
};

export default function DashboardPage() {
  const router = useRouter();
  const { user } = useUser();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    dashboard.get().then(setData).catch(console.error).finally(() => setLoading(false));
  }, []);

  const fmt = (n: number) => new Intl.NumberFormat("ru-RU").format(n);

  if (loading || !data) {
    return <div className="text-brand-400">Загрузка...</div>;
  }

  const greeting = (() => {
    const h = new Date().getHours();
    if (h < 6) return "Доброй ночи";
    if (h < 12) return "Доброе утро";
    if (h < 18) return "Добрый день";
    return "Добрый вечер";
  })();

  return (
    <div>
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-brand-700">
            {greeting}, {user?.first_name}!
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Рабочее место: {data.role_label} • {new Date().toLocaleDateString("ru-RU")}
          </p>
        </div>
        {user && canCreateReturn(user.role) && (
          <button
            onClick={() => router.push("/returns?new=1")}
            className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white rounded-2xl font-semibold text-sm hover:bg-brand-600 transition shadow-md"
          >
            <Plus className="w-4 h-4" /> Новая заявка
          </button>
        )}
      </div>

      {/* Widgets */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-7">
        {data.widgets.map((w: any, i: number) => (
          <div
            key={i}
            className={`bg-white rounded-xl3 p-5 border border-brand-100 border-l-4 ${
              ACCENT_BORDER[w.accent] || "border-l-brand-500"
            } shadow-sm`}
          >
            <div className="text-xs text-gray-400 font-semibold uppercase tracking-wider">
              {w.label}
            </div>
            <div className="text-2xl font-bold text-brand-700 mt-1">
              {w.is_money ? `${fmt(w.value)} ₽` : w.value}
            </div>
          </div>
        ))}
      </div>

      {/* Queue */}
      <div className="bg-white rounded-xl3 border border-brand-100 overflow-hidden shadow-sm">
        <div className="px-5 py-4 border-b border-brand-100 flex items-center justify-between">
          <h3 className="text-sm font-bold text-brand-600">{data.queue_title}</h3>
          <span className="text-xs text-gray-400">{data.queue.length} заявок</span>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-brand-50">
              <th className="text-left px-5 py-3 font-bold text-brand-600">№</th>
              <th className="text-left px-5 py-3 font-bold text-brand-600">Клиент</th>
              <th className="text-left px-5 py-3 font-bold text-brand-600">Тип</th>
              <th className="text-left px-5 py-3 font-bold text-brand-600">Сумма</th>
              <th className="text-left px-5 py-3 font-bold text-brand-600">Статус</th>
            </tr>
          </thead>
          <tbody>
            {data.queue.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-center py-10 text-brand-300">
                  Нет заявок, требующих внимания
                </td>
              </tr>
            ) : (
              data.queue.map((r: any) => (
                <tr
                  key={r.id}
                  onClick={() => router.push(`/returns?open=${r.id}`)}
                  className="border-t border-brand-50 hover:bg-brand-50/50 cursor-pointer transition"
                >
                  <td className="px-5 py-3 font-semibold">{r.number}</td>
                  <td className="px-5 py-3">{r.client_name}</td>
                  <td className="px-5 py-3 text-xs">{r.return_type}</td>
                  <td className="px-5 py-3">{fmt(r.total_amount)} ₽</td>
                  <td className="px-5 py-3">
                    <StatusBadge status={r.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
