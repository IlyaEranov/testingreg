"use client";
import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import { UserProvider, useUser } from "@/lib/UserContext";
import { getNavForRole, canAccess, ROLE_LABELS } from "@/lib/roles";
import { notifications } from "@/lib/api";
import {
  LayoutDashboard, ArrowLeftRight, Warehouse, BarChart3,
  BookOpen, Users, Bell, User, LogOut, Menu, Settings, Truck, type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  LayoutDashboard, ArrowLeftRight, Warehouse, BarChart3, BookOpen, Users, Bell, User, Settings, Truck,
};

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useUser();
  const pathname = usePathname();
  const router = useRouter();
  const [notifCount, setNotifCount] = useState(0);

  useEffect(() => {
    notifications.count().then((r) => setNotifCount(r.count)).catch(() => {});
  }, [pathname]);

  // Guard: redirect if no access to current route
  useEffect(() => {
    if (user && !canAccess(user.role, pathname)) {
      router.replace("/dashboard");
    }
  }, [user, pathname, router]);

  if (!user) return null;

  const nav = getNavForRole(user.role);
  const sections = Array.from(new Set(nav.map((n) => n.section)));
  const initials = (user.last_name?.[0] || "") + (user.first_name?.[0] || "");

  return (
    <nav className="w-[270px] h-full bg-gradient-to-b from-brand-600 to-brand-700 text-brand-100 flex flex-col flex-shrink-0">
      <div className="px-6 py-6 border-b border-brand-400/30">
        <h2 className="text-lg font-semibold text-white">Регион Сервис</h2>
        <p className="text-xs opacity-70 mt-1">АИС сопровождения возвратов</p>
      </div>

      <div className="flex-1 px-4 py-5 space-y-1 overflow-y-auto">
        {sections.map((section) => (
          <div key={section}>
            <p className="text-[10px] uppercase tracking-widest text-brand-300/60 font-bold px-4 mt-4 mb-2">
              {section}
            </p>
            {nav.filter((n) => n.section === section).map((item) => {
              const Icon = ICONS[item.icon];
              const active = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onNavigate}
                  className={`flex items-center gap-3 px-4 py-2.5 rounded-2xl text-sm font-medium transition-colors ${
                    active
                      ? "bg-brand-500 text-white shadow-md"
                      : "text-brand-100 hover:bg-brand-500/50 hover:text-white"
                  }`}
                >
                  {Icon && <Icon className="w-5 h-5" />}
                  <span className="flex-1">{item.label}</span>
                  {item.href === "/notifications" && notifCount > 0 && (
                    <span className="bg-accent text-brand-700 text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {notifCount}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        ))}
      </div>

      <div className="px-5 py-4 border-t border-brand-400/30 flex items-center gap-3">
        <div className="w-10 h-10 bg-accent rounded-full flex items-center justify-center text-brand-700 font-bold text-sm flex-shrink-0">
          {initials}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold truncate">{user.last_name} {user.first_name?.[0]}.</p>
          <p className="text-[11px] opacity-70">{user.role_label || ROLE_LABELS[user.role]}</p>
        </div>
        <button
          onClick={logout}
          className="p-1.5 rounded-lg hover:bg-brand-500/50 transition"
          title="Выйти"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </nav>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const { loading, user } = useUser();
  const [menuOpen, setMenuOpen] = useState(false);
  const pathname = usePathname();

  // Close the drawer on route change
  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-brand-400 text-lg">Загрузка...</div>
      </div>
    );
  }
  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden lg:flex h-full">
        <Sidebar />
      </div>

      {/* Mobile drawer + overlay */}
      <div className={`lg:hidden fixed inset-0 z-40 ${menuOpen ? "" : "pointer-events-none"}`}>
        <div
          className={`absolute inset-0 bg-black/40 transition-opacity ${menuOpen ? "opacity-100" : "opacity-0"}`}
          onClick={() => setMenuOpen(false)}
        />
        <div
          className={`absolute left-0 top-0 h-full transition-transform duration-300 ${menuOpen ? "translate-x-0" : "-translate-x-full"}`}
        >
          <Sidebar onNavigate={() => setMenuOpen(false)} />
        </div>
      </div>

      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar */}
        <header className="lg:hidden flex items-center gap-3 bg-brand-600 text-white px-4 py-3 flex-shrink-0">
          <button
            onClick={() => setMenuOpen(true)}
            className="p-1.5 rounded-lg hover:bg-brand-500/50 transition"
            aria-label="Открыть меню"
          >
            <Menu className="w-6 h-6" />
          </button>
          <span className="font-semibold">Регион Сервис</span>
        </header>

        <main className="flex-1 overflow-y-auto bg-brand-50 p-4 sm:p-6 lg:p-8">{children}</main>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <UserProvider>
      <Shell>{children}</Shell>
    </UserProvider>
  );
}
