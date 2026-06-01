"use client";
import { useState, useEffect } from "react";
import { auth } from "@/lib/api";
import { useUser } from "@/lib/UserContext";
import { ROLE_LABELS } from "@/lib/roles";

export default function ProfilePage() {
  const { user, refresh } = useUser();
  const [profile, setProfile] = useState({ last_name: "", first_name: "", patronymic: "", phone: "" });
  const [pwd, setPwd] = useState({ old: "", new1: "", new2: "" });
  const [msg, setMsg] = useState<{ text: string; ok: boolean } | null>(null);
  const [pwdMsg, setPwdMsg] = useState<{ text: string; ok: boolean } | null>(null);

  useEffect(() => {
    if (user) {
      setProfile({
        last_name: user.last_name || "",
        first_name: user.first_name || "",
        patronymic: user.patronymic || "",
        phone: user.phone || "",
      });
    }
  }, [user]);

  async function saveProfile(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    try {
      await auth.updateProfile(profile);
      await refresh();
      setMsg({ text: "Данные профиля сохранены", ok: true });
    } catch (err: any) { setMsg({ text: err.message, ok: false }); }
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setPwdMsg(null);
    if (pwd.new1 !== pwd.new2) { setPwdMsg({ text: "Пароли не совпадают", ok: false }); return; }
    if (pwd.new1.length < 4) { setPwdMsg({ text: "Пароль слишком короткий (мин. 4)", ok: false }); return; }
    try {
      await auth.changePassword(pwd.old, pwd.new1);
      setPwd({ old: "", new1: "", new2: "" });
      setPwdMsg({ text: "Пароль успешно изменён", ok: true });
    } catch (err: any) { setPwdMsg({ text: err.message, ok: false }); }
  }

  if (!user) return null;
  const initials = (user.last_name?.[0] || "") + (user.first_name?.[0] || "");

  return (
    <div className="max-w-3xl">
      <h1 className="text-2xl font-bold text-brand-700 mb-6">Профиль</h1>

      {/* Header card */}
      <div className="bg-white rounded-xl3 border border-brand-100 p-6 mb-6 flex items-center gap-4">
        <div className="w-16 h-16 bg-accent rounded-full flex items-center justify-center text-brand-700 font-bold text-xl">{initials}</div>
        <div>
          <h2 className="text-lg font-bold text-brand-700">{user.last_name} {user.first_name} {user.patronymic}</h2>
          <p className="text-sm text-gray-500">{user.email}</p>
          <span className="inline-block mt-1 px-3 py-0.5 rounded-full text-xs font-semibold bg-brand-100 text-brand-600">{user.role_label || ROLE_LABELS[user.role]}</span>
        </div>
      </div>

      {/* Edit profile */}
      <form onSubmit={saveProfile} className="bg-white rounded-xl3 border border-brand-100 p-6 mb-6">
        <h3 className="text-sm font-bold text-brand-600 mb-4">Личные данные</h3>
        <div className="grid grid-cols-2 gap-4 mb-4">
          <PInput label="Фамилия" value={profile.last_name} onChange={(v) => setProfile({ ...profile, last_name: v })} />
          <PInput label="Имя" value={profile.first_name} onChange={(v) => setProfile({ ...profile, first_name: v })} />
          <PInput label="Отчество" value={profile.patronymic} onChange={(v) => setProfile({ ...profile, patronymic: v })} />
          <PInput label="Телефон" value={profile.phone} onChange={(v) => setProfile({ ...profile, phone: v })} />
        </div>
        {msg && <div className={`text-sm mb-3 ${msg.ok ? "text-green-600" : "text-red-600"}`}>{msg.text}</div>}
        <button type="submit" className="px-5 py-2 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition">Сохранить</button>
      </form>

      {/* Change password */}
      <form onSubmit={changePassword} className="bg-white rounded-xl3 border border-brand-100 p-6">
        <h3 className="text-sm font-bold text-brand-600 mb-4">Смена пароля</h3>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <PInput label="Текущий пароль" type="password" value={pwd.old} onChange={(v) => setPwd({ ...pwd, old: v })} />
          <PInput label="Новый пароль" type="password" value={pwd.new1} onChange={(v) => setPwd({ ...pwd, new1: v })} />
          <PInput label="Повтор пароля" type="password" value={pwd.new2} onChange={(v) => setPwd({ ...pwd, new2: v })} />
        </div>
        {pwdMsg && <div className={`text-sm mb-3 ${pwdMsg.ok ? "text-green-600" : "text-red-600"}`}>{pwdMsg.text}</div>}
        <button type="submit" className="px-5 py-2 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition">Изменить пароль</button>
      </form>
    </div>
  );
}

function PInput({ label, value, onChange, type = "text" }: any) {
  return (
    <div>
      <label className="block text-xs font-semibold text-brand-600 mb-1">{label}</label>
      <input type={type} value={value} onChange={(e) => onChange(e.target.value)} className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none focus:border-brand-500" />
    </div>
  );
}
