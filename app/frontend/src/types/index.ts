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
  kind?: string;
  outcome?: string;
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
  | "client_data"
  | "claim_factory"
  | "factory_review"
  | "factory_done"
  | "in_transit"
  | "received"
  | "rejected"
  | "done";

export const STATUS_LABELS: Record<StatusCode, string> = {
  created: "Создана",
  client_data: "Ожидает данных покупателя",
  claim_factory: "Претензия отправлена заводу",
  factory_review: "На рассмотрении завода",
  factory_done: "Заключение получено",
  in_transit: "Транспортировка на склад",
  received: "Принят и сверён",
  rejected: "Отклонена",
  done: "Завершена",
};

export const STATUS_COLORS: Record<StatusCode, string> = {
  created: "bg-blue-100 text-blue-800",
  client_data: "bg-sky-100 text-sky-800",
  claim_factory: "bg-orange-100 text-orange-800",
  factory_review: "bg-amber-100 text-amber-800",
  factory_done: "bg-pink-100 text-pink-800",
  in_transit: "bg-yellow-100 text-yellow-800",
  received: "bg-purple-100 text-purple-800",
  rejected: "bg-red-100 text-red-800",
  done: "bg-emerald-100 text-emerald-800",
};

// Итог обработки возврата
export const OUTCOME_LABELS: Record<string, string> = {
  write_off: "Списание",
  correction: "Корректировка / возврат в продажу",
};

// Ветка обработки
export const KIND_LABELS: Record<string, string> = {
  defect: "Претензия по качеству (брак)",
  quality: "Надлежащее качество",
};
