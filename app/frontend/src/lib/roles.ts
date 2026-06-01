// Role-based navigation and permissions config

export type Role =
  | "admin"
  | "manager"
  | "warehouse_staff"
  | "director";

export const ROLE_LABELS: Record<string, string> = {
  admin: "Администратор",
  manager: "Менеджер",
  warehouse_staff: "Складской сотрудник",
  director: "Руководитель",
};

export interface NavItem {
  href: string;
  label: string;
  icon: string; // lucide icon name
  section: string;
}

// All possible nav items
const ALL_NAV: NavItem[] = [
  { href: "/dashboard", label: "Главная", icon: "LayoutDashboard", section: "Основное" },
  { href: "/returns", label: "Заявки на возврат", icon: "ArrowLeftRight", section: "Основное" },
  { href: "/warehouse", label: "Складская проверка", icon: "Warehouse", section: "Основное" },
  { href: "/reports", label: "Отчёты", icon: "BarChart3", section: "Аналитика" },
  { href: "/directories", label: "Справочники", icon: "BookOpen", section: "Настройки" },
  { href: "/users", label: "Пользователи", icon: "Users", section: "Настройки" },
  { href: "/notifications", label: "Уведомления", icon: "Bell", section: "Основное" },
  { href: "/profile", label: "Профиль", icon: "User", section: "Настройки" },
];

// Which routes each role can access
const ROLE_ROUTES: Record<Role, string[]> = {
  admin: ["/dashboard", "/returns", "/warehouse", "/reports", "/directories", "/users", "/notifications", "/profile"],
  manager: ["/dashboard", "/returns", "/reports", "/notifications", "/profile"],
  warehouse_staff: ["/dashboard", "/warehouse", "/returns", "/notifications", "/profile"],
  director: ["/dashboard", "/returns", "/reports", "/notifications", "/profile"],
};

export function getNavForRole(role: string): NavItem[] {
  const allowed = ROLE_ROUTES[role as Role] || ROLE_ROUTES.manager;
  return ALL_NAV.filter((item) => allowed.includes(item.href));
}

export function canAccess(role: string, href: string): boolean {
  const allowed = ROLE_ROUTES[role as Role] || ROLE_ROUTES.manager;
  // match by prefix (e.g. /returns/5 -> /returns)
  return allowed.some((r) => href === r || href.startsWith(r + "/"));
}

// Permission helpers for actions
export function canCreateReturn(role: string): boolean {
  return ["manager", "admin"].includes(role);
}

export function canDecide(role: string): boolean {
  return ["manager", "director", "admin"].includes(role);
}

export function canCheckWarehouse(role: string): boolean {
  return ["warehouse_staff", "admin"].includes(role);
}

export function canFinance(role: string): boolean {
  return ["manager", "admin"].includes(role);
}

export function canManageUsers(role: string): boolean {
  return role === "admin";
}
