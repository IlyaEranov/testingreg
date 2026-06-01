"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { access_token } = await auth.login(email, password);
      localStorage.setItem("token", access_token);
      router.push("/returns");
    } catch (err: any) {
      setError(err.message || "Ошибка входа");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-600 via-brand-500 to-brand-400 p-6">
      {/* Dot pattern */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage:
            "radial-gradient(rgba(255,255,255,0.08) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      <div className="w-full max-w-md bg-white rounded-[32px] shadow-2xl overflow-hidden relative z-10">
        {/* Accent bar */}
        <div className="h-2 bg-gradient-to-r from-brand-500 via-brand-400 to-accent" />

        <div className="p-8">
          {/* Brand */}
          <div className="text-center mb-8">
            <div className="w-14 h-14 bg-brand-50 rounded-2xl inline-flex items-center justify-center mb-4 shadow-sm">
              <svg className="w-8 h-8 text-brand-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
            </div>
            <h1 className="text-2xl font-semibold text-brand-700">Регион Сервис</h1>
            <p className="text-sm text-gray-500 mt-1">Система сопровождения возвратов товаров</p>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="mb-5">
              <label className="block text-sm font-semibold text-brand-600 mb-1.5">
                Электронная почта
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="ivanov@region-service.ru"
                required
                className="w-full px-4 py-3 bg-brand-50 border border-brand-200 rounded-xl focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition"
              />
            </div>

            <div className="mb-6">
              <label className="block text-sm font-semibold text-brand-600 mb-1.5">
                Пароль
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="w-full px-4 py-3 bg-brand-50 border border-brand-200 rounded-xl focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 outline-none transition"
              />
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 text-red-700 text-sm rounded-xl">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-brand-500 text-white font-semibold rounded-xl hover:bg-brand-600 transition disabled:opacity-50"
            >
              {loading ? "Вход..." : "Войти"}
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-brand-100 text-center text-xs text-gray-400">
            <span className="font-medium text-brand-400">Только авторизованный доступ</span>
            <br />
            Для получения учётных данных обратитесь к администратору
          </div>
        </div>
      </div>
    </div>
  );
}
