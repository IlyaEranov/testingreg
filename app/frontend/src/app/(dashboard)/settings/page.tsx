"use client";
import { useEffect, useState } from "react";
import { settings as api } from "@/lib/api";
import { Plug, Mail, MessageSquare, Save } from "lucide-react";

const EMPTY = {
  onec_api_url: "", onec_api_token: "",
  smtp_host: "", smtp_port: "", smtp_user: "", smtp_password: "", smtp_from: "",
  sms_api_url: "", sms_api_key: "", sms_sender: "",
};

export default function SettingsPage() {
  const [form, setForm] = useState<Record<string, string>>(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api.get()
      .then((d) => setForm({ ...EMPTY, ...d }))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  function set(k: string, v: string) { setForm({ ...form, [k]: v }); }

  async function save() {
    setSaved(false);
    try {
      await api.update(form);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e: any) { alert(e.message); }
  }

  if (loading) return <div className="text-brand-300 py-10 text-center">Загрузка...</div>;

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-bold text-brand-700 mb-2">Настройки интеграций</h1>
      <p className="text-sm text-gray-500 mb-6">
        Параметры внешних сервисов. Изменения применяются сразу. Доступно только администратору.
      </p>

      <Section icon={<Plug className="w-5 h-5 text-brand-500" />} title="1С:Предприятие"
        hint="Адрес REST-сервиса 1С для передачи данных о завершённых возвратах.">
        <Field label="Адрес сервиса 1С (URL)" value={form.onec_api_url} onChange={(v) => set("onec_api_url", v)} mono placeholder="http://host.docker.internal:8081" />
        <Field label="Токен авторизации (необязательно)" value={form.onec_api_token} onChange={(v) => set("onec_api_token", v)} mono />
      </Section>

      <Section icon={<Mail className="w-5 h-5 text-brand-500" />} title="Email (SMTP)"
        hint="Сервер исходящей почты для уведомлений покупателям по электронной почте.">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="SMTP-сервер" value={form.smtp_host} onChange={(v) => set("smtp_host", v)} mono placeholder="smtp.yandex.ru" />
          <Field label="Порт" value={form.smtp_port} onChange={(v) => set("smtp_port", v)} mono placeholder="587" />
          <Field label="Пользователь" value={form.smtp_user} onChange={(v) => set("smtp_user", v)} mono />
          <Field label="Пароль" value={form.smtp_password} onChange={(v) => set("smtp_password", v)} mono type="password" />
        </div>
        <Field label="Адрес отправителя (From)" value={form.smtp_from} onChange={(v) => set("smtp_from", v)} mono placeholder="no-reply@region-service.ru" />
      </Section>

      <Section icon={<MessageSquare className="w-5 h-5 text-brand-500" />} title="SMS-шлюз"
        hint="HTTP-API провайдера для отправки SMS-уведомлений покупателям.">
        <Field label="URL API шлюза" value={form.sms_api_url} onChange={(v) => set("sms_api_url", v)} mono placeholder="https://api.smsc.ru/..." />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Field label="Ключ / токен API" value={form.sms_api_key} onChange={(v) => set("sms_api_key", v)} mono />
          <Field label="Имя отправителя" value={form.sms_sender} onChange={(v) => set("sms_sender", v)} mono placeholder="RegionService" />
        </div>
      </Section>

      <div className="flex items-center gap-4">
        <button onClick={save} className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition">
          <Save className="w-4 h-4" /> Сохранить
        </button>
        {saved && <span className="text-sm text-green-600 font-semibold">Сохранено ✓</span>}
      </div>
    </div>
  );
}

function Section({ icon, title, hint, children }: any) {
  return (
    <div className="bg-white rounded-xl3 border border-brand-100 shadow-sm p-6 mb-5">
      <div className="flex items-center gap-3 mb-1">
        <div className="w-10 h-10 rounded-2xl bg-brand-50 flex items-center justify-center">{icon}</div>
        <div className="font-semibold text-brand-700">{title}</div>
      </div>
      <p className="text-[11px] text-gray-400 mb-4 ml-13">{hint}</p>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function Field({ label, value, onChange, mono, placeholder, type }: any) {
  return (
    <div>
      <label className="block text-xs font-semibold text-brand-600 mb-1">{label}</label>
      <input
        type={type || "text"}
        value={value || ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none focus:border-brand-500 ${mono ? "font-mono" : ""}`}
      />
    </div>
  );
}
