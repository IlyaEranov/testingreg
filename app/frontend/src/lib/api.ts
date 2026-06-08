const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: "Server error" }));
    throw new Error(error.detail || `Error ${res.status}`);
  }

  return res.json();
}

// Auth
export const auth = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<any>("/auth/me"),
  updateProfile: (data: any) =>
    request<any>("/auth/profile", { method: "PUT", body: JSON.stringify(data) }),
  changePassword: (oldPassword: string, newPassword: string) =>
    request<any>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
    }),
};

// Dashboard
export const dashboard = {
  get: () => request<any>("/dashboard/"),
};

// Returns
export const returns = {
  list: (params?: Record<string, string>) => {
    const qs = params
      ? "?" + new URLSearchParams(params).toString()
      : "";
    return request<any[]>(`/returns/${qs}`);
  },
  get: (id: number) => request<any>(`/returns/${id}`),
  create: (data: any) =>
    request<any>("/returns/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  changeStatus: (id: number, newStatus: string, comment?: string) =>
    request<any>(`/returns/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ new_status: newStatus, comment }),
    }),
  sendToExamination: (id: number, supplierId: number, details?: string) =>
    request<any>(`/returns/${id}/examination`, {
      method: "POST",
      body: JSON.stringify({ supplier_id: supplierId, details }),
    }),
  submitExamResult: (id: number, conclusion: string, details?: string) =>
    request<any>(`/returns/${id}/examination/result`, {
      method: "POST",
      body: JSON.stringify({ conclusion, details }),
    }),
};

// Warehouse
export const warehouse = {
  pending: () => request<any[]>("/warehouse/pending"),
  submitCheck: (returnId: number, checks: any[]) =>
    request<any>(`/warehouse/${returnId}/check`, {
      method: "POST",
      body: JSON.stringify(checks),
    }),
};

// Documents
export const documents = {
  list: (returnId: number) => request<any[]>(`/documents/${returnId}`),
  generate: (returnId: number, docType: string) =>
    request<any>(`/documents/${returnId}/generate?doc_type=${docType}`, {
      method: "POST",
    }),
  downloadUrl: (docId: number) => `${API_BASE}/documents/download/${docId}`,
};

// Directories
export const directories = {
  reasons: () => request<any[]>("/directories/reasons"),
  createReason: (data: any) =>
    request<any>("/directories/reasons", { method: "POST", body: JSON.stringify(data) }),
  updateReason: (id: number, data: any) =>
    request<any>(`/directories/reasons/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  suppliers: () => request<any[]>("/directories/suppliers"),
  createSupplier: (data: any) =>
    request<any>("/directories/suppliers", { method: "POST", body: JSON.stringify(data) }),
  updateSupplier: (id: number, data: any) =>
    request<any>(`/directories/suppliers/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  warehouses: () => request<any[]>("/directories/warehouses"),
  createWarehouse: (data: any) =>
    request<any>("/directories/warehouses", { method: "POST", body: JSON.stringify(data) }),
  statuses: () => request<any[]>("/directories/statuses"),
};

// Users
export const users = {
  list: () => request<any[]>("/users/"),
  create: (data: any) =>
    request<any>("/users/", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  update: (id: number, data: any) =>
    request<any>(`/users/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  roles: () => request<any[]>("/users/roles"),
};

// Notifications
export const notifications = {
  list: (limit = 50) => request<any[]>(`/notifications/?limit=${limit}`),
  count: () => request<{ count: number }>("/notifications/count"),
  forReturn: (returnId: number) => request<any[]>(`/notifications/return/${returnId}`),
};

// Settings (интеграция)
export const settings = {
  get: () => request<any>("/settings/"),
  update: (data: any) =>
    request<any>("/settings/", { method: "PUT", body: JSON.stringify(data) }),
};

// Reports
export const reports = {
  summary: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any>(`/reports/summary${qs}`);
  },
  byReason: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any[]>(`/reports/by-reason${qs}`);
  },
  byMonth: (params?: Record<string, string>) => {
    const qs = params ? "?" + new URLSearchParams(params).toString() : "";
    return request<any[]>(`/reports/by-month${qs}`);
  },
  bySupplier: () => request<any[]>("/reports/by-supplier"),
};
