export interface User {
  id: number;
  email: string;
  last_name: string;
  first_name: string;
  patronymic?: string;
  phone?: string;
  role: string;
  is_active: boolean;
}

export interface ReturnItem {
  id: number;
  product_name: string;
  article?: string;
  quantity: number;
  unit: string;
  price: number;
}

export interface WarehouseCheck {
  id: number;
  return_item_id: number;
  quantity_fact: number;
  packaging_condition: string;
  defect_description?: string;
  inspector_name?: string;
  checked_at: string;
}

export interface DocumentInfo {
  id: number;
  document_type: string;
  file_name: string;
  file_path: string;
  created_at: string;
}

export interface ActionHistoryEntry {
  id: number;
  action: string;
  old_status?: string;
  new_status?: string;
  details?: string;
  user_name?: string;
  created_at: string;
}

export interface Examination {
  id: number;
  supplier_id: number;
  supplier_name?: string;
  transfer_date?: string;
  result_date?: string;
  conclusion?: string;
  details?: string;
}

export interface ReturnRequest {
  id: number;
  number: string;
  client_name: string;
  client_phone?: string;
  client_email?: string;
  return_type: string;
  reason_name?: string;
  status: string;
  manager_name?: string;
  warehouse_name?: string;
  comment?: string;
  total_amount: number;
  created_at: string;
  updated_at?: string;
  items?: ReturnItem[];
  checks?: WarehouseCheck[];
  documents?: DocumentInfo[];
  history?: ActionHistoryEntry[];
  examination?: Examination;
}

export interface Reason {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface Supplier {
  id: number;
  name: string;
  contact_person?: string;
  phone?: string;
  email?: string;
  address?: string;
  is_active: boolean;
}

export interface Warehouse {
  id: number;
  name: string;
  address?: string;
  is_active: boolean;
}

export interface UserListItem {
  id: number;
  email: string;
  last_name: string;
  first_name: string;
  patronymic?: string;
  phone?: string;
  role_name?: string;
  is_active: boolean;
}

export type StatusCode =
  | "created"
  | "warehouse"
  | "waiting"
  | "expertise"
  | "expertise_done"
  | "approved"
  | "rejected"
  | "docs"
  | "finance"
  | "done";

export const STATUS_LABELS: Record<StatusCode, string> = {
  created: "Создана",
  warehouse: "На проверке склада",
  waiting: "Ожидает решения",
  expertise: "На экспертизе",
  expertise_done: "Экспертиза завершена",
  approved: "Одобрена",
  rejected: "Отклонена",
  docs: "Документы сформированы",
  finance: "Ожидает фин. завершения",
  done: "Завершена",
};

export const STATUS_COLORS: Record<StatusCode, string> = {
  created: "bg-blue-100 text-blue-800",
  warehouse: "bg-yellow-100 text-yellow-800",
  waiting: "bg-purple-100 text-purple-800",
  expertise: "bg-orange-100 text-orange-800",
  expertise_done: "bg-pink-100 text-pink-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  docs: "bg-brand-100 text-brand-600",
  finance: "bg-amber-100 text-amber-800",
  done: "bg-emerald-100 text-emerald-800",
};
