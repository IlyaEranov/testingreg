"use client";
import { useEffect, useState } from "react";
import { settings as api } from "@/lib/api";
import { Plug, Save } from "lucide-react";

export default function SettingsPage() {
  const [form, setForm] = useState({ onec_api_url: "", onec_api_token: "" });
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get()
      .then((d) => setForm({ onec_api_url: d.onec_api_url || "", onec_api_token: d.onec_api_token || "" }))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function save() {
    setSaved(false);
    try {
      await api.update(form);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e: any) { alert(e.message); }
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-brand-700 mb-2">Интеграция с 1С:Предприятие</h1>
      <p className="text-sm text-gray-500 mb-6">
        Адрес REST-сервиса 1С, в который система передаёт данные о завершённых возвратах
        (создание документа возврата, обновление остатков). Изменения применяются сразу.
      </p>

      <div className="bg-white rounded-xl3 border border-brand-100 shadow-sm p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-brand-50 flex items-center justify-center">
            <Plug className="w-5 h-5 text-brand-500" />
          </div>
          <div>
            <div className="font-semibold text-brand-700">Параметры подключения</div>
            <div className="text-xs text-gray-400">Доступно только администратору</div>
          </div>
        </div>

        {loading ? (
          <div className="text-brand-300 py-8 text-center">Загрузка...</div>
        ) : (
          <>
            <div className="mb-5">
              <label className="block text-xs font-semibold text-brand-600 mb-1">Адрес сервиса 1С (URL)</label>
              <input
                value={form.onec_api_url}
                onChange={(e) => setForm({ ...form, onec_api_url: e.target.value })}
                placeholder="http://host.docker.internal:8081"
                className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none focus:border-brand-500 font-mono"
              />
              <p className="text-[11px] text-gray-400 mt-1">
                Например, адрес опубликованного HTTP-сервиса 1С или тестового сервиса.
              </p>
            </div>

            <div className="mb-6">
              <label className="block text-xs font-semibold text-brand-600 mb-1">Токен авторизации (необязательно)</label>
              <input
                value={form.onec_api_token}
                onChange={(e) => setForm({ ...form, onec_api_token: e.target.value })}
                placeholder="Bearer-токен, если требуется"
                className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none focus:border-brand-500 font-mono"
              />
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={save}
                className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition"
              >
                <Save className="w-4 h-4" /> Сохранить
              </button>
              {saved && <span className="text-sm text-green-600 font-semibold">Сохранено ✓</span>}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
