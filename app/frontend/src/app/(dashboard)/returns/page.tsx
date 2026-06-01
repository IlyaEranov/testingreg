"use client";
import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { returns as api, directories, documents as docApi, notifications as notifApi } from "@/lib/api";
import { useUser } from "@/lib/UserContext";
import { canCreateReturn, canDecide, canFinance } from "@/lib/roles";
import StatusBadge from "@/components/ui/StatusBadge";
import { Plus, Search, Filter, X, Download, FileText, Bell } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

const DOC_TYPES: Record<string, string> = {
  application: "Заявление на возврат товара",
  route_sheet: "Маршрутный лист",
  inspection_act: "Акт осмотра товара",
  transfer_act: "Акт передачи товара поставщику",
  acceptance_act: "Акт приёмки товара от поставщика",
  return_act: "Акт возврата товара покупателю",
  refund_act: "Акт возврата денежных средств",
  rejection_notice: "Уведомление об отказе в возврате",
  write_off_act: "Акт списания товара",
};

function ReturnsInner() {
  const { user } = useUser();
  const searchParams = useSearchParams();
  const router = useRouter();

  const [data, setData] = useState<any[]>([]);
  const [reasons, setReasons] = useState<any[]>([]);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [selected, setSelected] = useState<any | null>(null);
  const [tab, setTab] = useState("info");
  const [filter, setFilter] = useState({ status: "", client: "" });
  const [notifs, setNotifs] = useState<any[]>([]);

  const [form, setForm] = useState<any>({
    client_name: "", client_phone: "", return_type: "Надлежащее качество",
    reason_id: 0, warehouse_id: 0, comment: "",
    items: [{ product_name: "", article: "", quantity: 1, unit: "шт.", price: 0 }],
  });

  // Examination form
  const [examSupplier, setExamSupplier] = useState(0);
  const [examDetails, setExamDetails] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (filter.status) params.status = filter.status;
      if (filter.client) params.client = filter.client;
      setData(await api.list(params));
    } catch (e) { console.error(e); }
    setLoading(false);
  }, [filter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    directories.reasons().then(setReasons).catch(() => {});
    directories.warehouses().then(setWarehouses).catch(() => {});
    directories.suppliers().then(setSuppliers).catch(() => {});
  }, []);

  // Handle query params (?new=1, ?open=ID)
  useEffect(() => {
    if (searchParams.get("new") && user && canCreateReturn(user.role)) {
      setShowCreate(true);
    }
    const openId = searchParams.get("open");
    if (openId) openDetail(Number(openId));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams, user]);

  async function openDetail(id: number) {
    try {
      const detail = await api.get(id);
      setSelected(detail);
      setTab("info");
      notifApi.forReturn(id).then(setNotifs).catch(() => setNotifs([]));
    } catch (err: any) { alert(err.message); }
  }

  async function refreshSelected(id: number) {
    const detail = await api.get(id);
    setSelected(detail);
    notifApi.forReturn(id).then(setNotifs).catch(() => {});
    loadData();
  }

  async function handleStatusChange(id: number, newStatus: string) {
    try {
      await api.changeStatus(id, newStatus);
      await refreshSelected(id);
    } catch (err: any) { alert(err.message); }
  }

  async function handleSendToExamination() {
    if (!selected || !examSupplier) { alert("Выберите поставщика"); return; }
    try {
      await api.sendToExamination(selected.id, examSupplier, examDetails);
      setExamSupplier(0); setExamDetails("");
      await refreshSelected(selected.id);
    } catch (err: any) { alert(err.message); }
  }

  async function handleExamResult(conclusion: string) {
    if (!selected) return;
    try {
      await api.submitExamResult(selected.id, conclusion, examDetails);
      setExamDetails("");
      await refreshSelected(selected.id);
    } catch (err: any) { alert(err.message); }
  }

  async function handleGenerateDoc(docType: string) {
    if (!selected) return;
    try {
      await docApi.generate(selected.id, docType);
      await refreshSelected(selected.id);
    } catch (err: any) { alert(err.message); }
  }

  function downloadDoc(docId: number) {
    const token = localStorage.getItem("token");
    fetch(`${API_BASE}/documents/download/${docId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "document.docx";
        a.click();
        URL.revokeObjectURL(url);
      })
      .catch(() => alert("Ошибка скачивания"));
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    try {
      const created = await api.create(form);
      setShowCreate(false);
      setForm({
        client_name: "", client_phone: "", return_type: "Надлежащее качество",
        reason_id: 0, warehouse_id: 0, comment: "",
        items: [{ product_name: "", article: "", quantity: 1, unit: "шт.", price: 0 }],
      });
      router.replace("/returns");
      await loadData();
      if (created?.id) openDetail(created.id);
    } catch (err: any) { alert(err.message); }
  }

  function addItem() {
    setForm({ ...form, items: [...form.items, { product_name: "", article: "", quantity: 1, unit: "шт.", price: 0 }] });
  }
  function updateItem(i: number, field: string, value: any) {
    const items = [...form.items];
    items[i][field] = value;
    setForm({ ...form, items });
  }
  function removeItem(i: number) {
    setForm({ ...form, items: form.items.filter((_: any, idx: number) => idx !== i) });
  }

  function resetFilters() {
    setFilter({ status: "", client: "" });
  }

  const fmt = (n: number) => new Intl.NumberFormat("ru-RU").format(n);
  const role = user?.role || "";

  // Determine available actions based on status + role
  function renderActions(r: any) {
    const actions: React.ReactNode[] = [];
    if (r.status === "created" && (role === "manager" || role === "admin")) {
      actions.push(<button key="wh" onClick={() => handleStatusChange(r.id, "warehouse")} className="btn-primary">Передать на склад</button>);
    }
    if (r.status === "waiting" && canDecide(role)) {
      actions.push(<button key="ap" onClick={() => handleStatusChange(r.id, "approved")} className="btn-green">Одобрить возврат</button>);
      actions.push(<button key="rj" onClick={() => handleStatusChange(r.id, "rejected")} className="btn-red">Отклонить</button>);
    }
    if (r.status === "expertise_done" && canDecide(role)) {
      actions.push(<button key="ap2" onClick={() => handleStatusChange(r.id, "approved")} className="btn-green">Одобрить возврат</button>);
      actions.push(<button key="rj2" onClick={() => handleStatusChange(r.id, "rejected")} className="btn-red">Отклонить</button>);
    }
    if (r.status === "finance" && canFinance(role)) {
      actions.push(<button key="fin" onClick={() => handleStatusChange(r.id, "done")} className="btn-primary">Подтвердить возврат средств (1С)</button>);
    }
    return actions;
  }

  const TABS = [
    { key: "info", label: "Информация" },
    { key: "items", label: "Товары" },
    { key: "check", label: "Проверка" },
    { key: "expertise", label: "Экспертиза" },
    { key: "docs", label: "Документы" },
    { key: "notifs", label: "Уведомления" },
    { key: "history", label: "История" },
  ];

  return (
    <div>
      <style jsx global>{`
        .btn-primary{padding:8px 20px;background:#407368;color:#fff;border-radius:12px;font-weight:600;font-size:13px}
        .btn-primary:hover{background:#2c5a4f}
        .btn-green{padding:8px 20px;background:#16a34a;color:#fff;border-radius:12px;font-weight:600;font-size:13px}
        .btn-green:hover{background:#15803d}
        .btn-red{padding:8px 20px;background:#fee2e2;color:#b91c1c;border-radius:12px;font-weight:600;font-size:13px}
        .btn-red:hover{background:#fecaca}
      `}</style>

      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <h1 className="text-2xl font-bold text-brand-700">Заявки на возврат</h1>
        {user && canCreateReturn(role) && (
          <button onClick={() => setShowCreate(true)} className="flex items-center gap-2 px-5 py-2.5 bg-brand-500 text-white rounded-2xl font-semibold text-sm hover:bg-brand-600 transition shadow-md">
            <Plus className="w-4 h-4" /> Новая заявка
          </button>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 bg-white p-4 rounded-xl3 border border-brand-100 mb-5">
        <div className="flex items-center gap-2 bg-brand-50 px-3 rounded-full border border-brand-200">
          <Filter className="w-4 h-4 text-brand-400" />
          <select value={filter.status} onChange={(e) => setFilter({ ...filter, status: e.target.value })} className="bg-transparent py-2 text-sm outline-none">
            <option value="">Все статусы</option>
            <option value="created">Создана</option>
            <option value="warehouse">На проверке</option>
            <option value="waiting">Ожидает решения</option>
            <option value="expertise">На экспертизе</option>
            <option value="expertise_done">Экспертиза завершена</option>
            <option value="approved">Одобрена</option>
            <option value="rejected">Отклонена</option>
            <option value="finance">Ожидает фин.</option>
            <option value="done">Завершена</option>
          </select>
        </div>
        <div className="flex items-center gap-2 bg-brand-50 px-3 rounded-full border border-brand-200 flex-1 min-w-[180px]">
          <Search className="w-4 h-4 text-brand-400" />
          <input type="text" placeholder="Поиск по клиенту..." value={filter.client} onChange={(e) => setFilter({ ...filter, client: e.target.value })} className="bg-transparent py-2 text-sm outline-none w-full" />
        </div>
        <button onClick={resetFilters} className="px-4 py-2 bg-brand-100 text-brand-600 rounded-full text-sm font-semibold">Сбросить</button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl3 border border-brand-100 overflow-hidden shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-brand-50">
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">№</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Клиент</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Дата</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Тип</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Сумма</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Статус</th>
              <th className="text-left px-5 py-3.5 font-bold text-brand-600">Менеджер</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-10 text-brand-300">Загрузка...</td></tr>
            ) : data.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-10 text-brand-300">Заявок не найдено</td></tr>
            ) : (
              data.map((r) => (
                <tr key={r.id} onClick={() => openDetail(r.id)} className="border-t border-brand-50 hover:bg-brand-50/50 cursor-pointer transition">
                  <td className="px-5 py-3 font-semibold">{r.number}</td>
                  <td className="px-5 py-3">{r.client_name}</td>
                  <td className="px-5 py-3">{r.created_at?.slice(0, 10)}</td>
                  <td className="px-5 py-3 text-xs">{r.return_type}</td>
                  <td className="px-5 py-3">{fmt(r.total_amount)} ₽</td>
                  <td className="px-5 py-3"><StatusBadge status={r.status} /></td>
                  <td className="px-5 py-3 text-xs text-gray-500">{r.manager_name}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Detail modal */}
      {selected && (
        <div className="fixed inset-0 bg-brand-700/50 backdrop-blur-sm z-50 flex items-start justify-center p-6 pt-10 overflow-y-auto"
          onClick={(e) => { if (e.target === e.currentTarget) { setSelected(null); router.replace("/returns"); } }}>
          <div className="bg-white rounded-[28px] w-full max-w-3xl shadow-2xl">
            <div className="flex items-center justify-between px-7 py-5 border-b border-brand-100 bg-brand-50 rounded-t-[28px]">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-bold text-brand-700">Заявка {selected.number}</h2>
                <StatusBadge status={selected.status} />
              </div>
              <button onClick={() => { setSelected(null); router.replace("/returns"); }} className="text-brand-300 hover:text-brand-500 text-2xl">&times;</button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 px-5 border-b border-brand-100 overflow-x-auto">
              {TABS.map((t) => (
                <button key={t.key} onClick={() => setTab(t.key)}
                  className={`px-4 py-3 text-sm font-semibold whitespace-nowrap border-b-2 -mb-[1px] transition ${tab === t.key ? "text-brand-600 border-brand-500" : "text-gray-400 border-transparent hover:text-brand-500"}`}>
                  {t.label}
                  {t.key === "docs" && selected.documents?.length > 0 && <span className="ml-1.5 text-[10px] bg-brand-100 text-brand-600 px-1.5 py-0.5 rounded-full">{selected.documents.length}</span>}
                </button>
              ))}
            </div>

            <div className="p-7">
              {/* INFO */}
              {tab === "info" && (
                <div className="grid grid-cols-2 gap-4">
                  <Field label="Клиент" value={selected.client_name} />
                  <Field label="Телефон" value={selected.client_phone || "—"} />
                  <Field label="Тип возврата" value={selected.return_type} />
                  <Field label="Причина" value={selected.reason_name} />
                  <Field label="Менеджер" value={selected.manager_name} />
                  <Field label="Склад" value={selected.warehouse_name} />
                  <Field label="Дата создания" value={selected.created_at?.slice(0, 10)} />
                  <div>
                    <span className="text-xs text-gray-400 font-semibold">Сумма</span>
                    <div className="mt-1 text-xl font-bold text-brand-600">{fmt(selected.total_amount)} ₽</div>
                  </div>
                  {selected.comment && <div className="col-span-2"><Field label="Комментарий" value={selected.comment} /></div>}
                </div>
              )}

              {/* ITEMS */}
              {tab === "items" && (
                <div className="space-y-2">
                  {selected.items?.map((item: any) => (
                    <div key={item.id} className="bg-brand-50 rounded-2xl p-4 border border-brand-100">
                      <div className="font-semibold text-brand-700">{item.product_name}</div>
                      <div className="flex gap-5 mt-1 text-xs text-gray-500 flex-wrap">
                        <span>Арт: {item.article}</span>
                        <span>Кол-во: {item.quantity} {item.unit}</span>
                        <span>Цена: {fmt(item.price)} ₽</span>
                        <span className="font-semibold">Сумма: {fmt(item.quantity * item.price)} ₽</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {/* CHECK */}
              {tab === "check" && (
                selected.checks?.length ? (
                  <div className="space-y-3">
                    {selected.checks.map((c: any) => (
                      <div key={c.id} className="bg-brand-50 rounded-2xl p-4 border border-brand-100">
                        <div className="grid grid-cols-2 gap-2 text-sm">
                          <div><span className="text-gray-400">Факт. кол-во:</span> <strong>{c.quantity_fact}</strong></div>
                          <div><span className="text-gray-400">Инспектор:</span> {c.inspector_name}</div>
                          <div><span className="text-gray-400">Упаковка:</span> {c.packaging_condition}</div>
                          <div><span className="text-gray-400">Дата:</span> {c.checked_at?.slice(0, 10)}</div>
                          <div className="col-span-2"><span className="text-gray-400">Дефект:</span> {c.defect_description}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <Empty text="Складская проверка ещё не проведена" />
              )}

              {/* EXPERTISE */}
              {tab === "expertise" && (
                <div>
                  {selected.examination ? (
                    <div className="bg-brand-50 rounded-2xl p-5 border border-brand-100 mb-4">
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <Field label="Поставщик" value={selected.examination.supplier_name} />
                        <Field label="Дата передачи" value={selected.examination.transfer_date?.slice(0, 10) || "—"} />
                        <Field label="Дата результата" value={selected.examination.result_date?.slice(0, 10) || "— (ожидается)"} />
                        <Field label="Заключение" value={
                          selected.examination.conclusion === "defect_confirmed" ? "Заводской брак подтверждён" :
                          selected.examination.conclusion === "defect_not_confirmed" ? "Брак не подтверждён" : "— (ожидается)"
                        } />
                        {selected.examination.details && <div className="col-span-2"><Field label="Детали" value={selected.examination.details} /></div>}
                      </div>
                    </div>
                  ) : selected.status === "waiting" && canDecide(role) ? (
                    <div className="bg-orange-50 rounded-2xl p-5 border border-orange-100">
                      <h4 className="font-semibold text-brand-700 mb-3">Передать товар поставщику на экспертизу</h4>
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        <select value={examSupplier} onChange={(e) => setExamSupplier(Number(e.target.value))} className="px-3 py-2 bg-white border border-brand-200 rounded-xl text-sm outline-none">
                          <option value={0}>Выберите поставщика...</option>
                          {suppliers.filter((s) => s.is_active).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                        </select>
                        <input value={examDetails} onChange={(e) => setExamDetails(e.target.value)} placeholder="Комментарий" className="px-3 py-2 bg-white border border-brand-200 rounded-xl text-sm outline-none" />
                      </div>
                      <button onClick={handleSendToExamination} className="btn-primary">Передать на экспертизу</button>
                    </div>
                  ) : <Empty text="Экспертиза не требуется или недоступна на текущем этапе" />}

                  {/* Submit result form */}
                  {selected.status === "expertise" && canDecide(role) && (
                    <div className="bg-pink-50 rounded-2xl p-5 border border-pink-100 mt-4">
                      <h4 className="font-semibold text-brand-700 mb-3">Внести результат экспертизы</h4>
                      <textarea value={examDetails} onChange={(e) => setExamDetails(e.target.value)} placeholder="Заключение поставщика..." rows={2} className="w-full px-3 py-2 bg-white border border-brand-200 rounded-xl text-sm outline-none mb-3 resize-none" />
                      <div className="flex gap-2">
                        <button onClick={() => handleExamResult("defect_confirmed")} className="btn-green">Брак подтверждён</button>
                        <button onClick={() => handleExamResult("defect_not_confirmed")} className="btn-red">Брак не подтверждён</button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* DOCS */}
              {tab === "docs" && (
                <div>
                  {selected.documents?.length ? (
                    <div className="space-y-2 mb-5">
                      {selected.documents.map((d: any) => (
                        <div key={d.id} className="flex items-center gap-3 bg-brand-50 rounded-xl p-3 border border-brand-100">
                          <div className="w-9 h-9 bg-brand-100 rounded-lg flex items-center justify-center"><FileText className="w-4 h-4 text-brand-500" /></div>
                          <div className="flex-1">
                            <div className="text-sm font-semibold text-brand-700">{DOC_TYPES[d.document_type] || d.document_type}</div>
                            <div className="text-xs text-gray-400">{d.created_at?.slice(0, 10)} • .docx</div>
                          </div>
                          <button onClick={() => downloadDoc(d.id)} className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-100 text-brand-600 rounded-lg text-xs font-semibold hover:bg-brand-200 transition">
                            <Download className="w-3.5 h-3.5" /> Скачать
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : <Empty text="Документы пока не сформированы" />}

                  {(role === "manager" || role === "admin") && (
                    <div className="border-t border-brand-100 pt-4">
                      <p className="text-xs text-gray-400 font-semibold mb-2">Сформировать документ вручную:</p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(DOC_TYPES).map(([code, name]) => (
                          <button key={code} onClick={() => handleGenerateDoc(code)} className="px-3 py-1.5 bg-brand-50 border border-brand-200 text-brand-600 rounded-lg text-xs font-medium hover:bg-brand-100 transition">+ {name}</button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* NOTIFICATIONS */}
              {tab === "notifs" && (
                notifs.length ? (
                  <div className="space-y-2">
                    {notifs.map((n) => (
                      <div key={n.id} className="flex gap-3 bg-brand-50 rounded-xl p-3 border border-brand-100">
                        <Bell className="w-4 h-4 text-brand-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <div className="text-sm text-brand-700">{n.message}</div>
                          <div className="text-xs text-gray-400 mt-1">
                            {n.channel.toUpperCase()} → {n.recipient_contact} • {n.created_at?.slice(0, 16).replace("T", " ")}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : <Empty text="Уведомлений по заявке нет" />
              )}

              {/* HISTORY */}
              {tab === "history" && (
                <div className="pl-6 border-l-2 border-brand-100 space-y-3">
                  {selected.history?.map((h: any) => (
                    <div key={h.id}>
                      <div className="text-[11px] text-gray-400 font-semibold">{h.created_at?.slice(0, 16).replace("T", " ")}</div>
                      <div className="text-sm">{h.action}</div>
                      <div className="text-[11px] text-gray-400">{h.user_name}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* ACTIONS */}
              {renderActions(selected).length > 0 && (
                <div className="flex gap-3 flex-wrap border-t border-brand-100 pt-5 mt-5">
                  {renderActions(selected)}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-brand-700/50 backdrop-blur-sm z-50 flex items-start justify-center p-6 pt-10 overflow-y-auto"
          onClick={(e) => { if (e.target === e.currentTarget) { setShowCreate(false); router.replace("/returns"); } }}>
          <div className="bg-white rounded-[28px] w-full max-w-2xl shadow-2xl">
            <div className="flex items-center justify-between px-7 py-5 border-b border-brand-100 bg-brand-50 rounded-t-[28px]">
              <h2 className="text-lg font-bold text-brand-700">Новая заявка на возврат</h2>
              <button onClick={() => { setShowCreate(false); router.replace("/returns"); }} className="text-brand-300 hover:text-brand-500 text-2xl">&times;</button>
            </div>
            <form onSubmit={handleCreate} className="p-7">
              <div className="grid grid-cols-2 gap-4 mb-5">
                <Input label="Клиент" required value={form.client_name} onChange={(v) => setForm({ ...form, client_name: v })} placeholder="ФИО / Организация" />
                <Input label="Телефон" value={form.client_phone} onChange={(v) => setForm({ ...form, client_phone: v })} placeholder="+7 (999) 123-45-67" />
                <div>
                  <label className="block text-xs font-semibold text-brand-600 mb-1">Тип возврата</label>
                  <select value={form.return_type} onChange={(e) => setForm({ ...form, return_type: e.target.value })} className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none">
                    <option>Надлежащее качество</option><option>Ненадлежащее качество</option><option>Производственный брак</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-brand-600 mb-1">Причина</label>
                  <select required value={form.reason_id} onChange={(e) => setForm({ ...form, reason_id: Number(e.target.value) })} className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none">
                    <option value={0}>Выберите...</option>
                    {reasons.filter((r) => r.is_active).map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-brand-600 mb-1">Склад</label>
                  <select required value={form.warehouse_id} onChange={(e) => setForm({ ...form, warehouse_id: Number(e.target.value) })} className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none">
                    <option value={0}>Выберите...</option>
                    {warehouses.filter((w) => w.is_active).map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
                  </select>
                </div>
                <Input label="Комментарий" value={form.comment} onChange={(v) => setForm({ ...form, comment: v })} />
              </div>

              <h3 className="text-sm font-bold text-brand-600 mb-3">Товарные позиции</h3>
              {form.items.map((item: any, i: number) => (
                <div key={i} className="grid grid-cols-[2fr_1fr_70px_1fr_auto] gap-2 mb-2 bg-brand-50 p-3 rounded-xl border border-brand-100">
                  <input required value={item.product_name} onChange={(e) => updateItem(i, "product_name", e.target.value)} className="px-2 py-2 bg-white border border-brand-200 rounded-lg text-sm outline-none" placeholder="Наименование" />
                  <input value={item.article} onChange={(e) => updateItem(i, "article", e.target.value)} className="px-2 py-2 bg-white border border-brand-200 rounded-lg text-sm outline-none" placeholder="Артикул" />
                  <input type="number" min="1" required value={item.quantity} onChange={(e) => updateItem(i, "quantity", Number(e.target.value))} className="px-2 py-2 bg-white border border-brand-200 rounded-lg text-sm outline-none" />
                  <input type="number" min="0" step="0.01" required value={item.price || ""} onChange={(e) => updateItem(i, "price", Number(e.target.value))} className="px-2 py-2 bg-white border border-brand-200 rounded-lg text-sm outline-none" placeholder="Цена" />
                  <button type="button" onClick={() => removeItem(i)} className="text-red-400 hover:text-red-600 p-1"><X className="w-4 h-4" /></button>
                </div>
              ))}
              <button type="button" onClick={addItem} className="text-sm text-brand-500 font-semibold mb-5 hover:text-brand-600">+ Добавить позицию</button>

              <div className="flex gap-3 justify-end border-t border-brand-100 pt-5">
                <button type="button" onClick={() => { setShowCreate(false); router.replace("/returns"); }} className="px-5 py-2 bg-brand-100 text-brand-600 rounded-xl font-semibold text-sm">Отмена</button>
                <button type="submit" className="px-5 py-2 bg-brand-500 text-white rounded-xl font-semibold text-sm hover:bg-brand-600 transition">Создать заявку</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value }: { label: string; value: any }) {
  return (
    <div>
      <span className="text-xs text-gray-400 font-semibold">{label}</span>
      <div className="mt-1 font-medium text-brand-700">{value || "—"}</div>
    </div>
  );
}

function Input({ label, value, onChange, placeholder, required }: any) {
  return (
    <div>
      <label className="block text-xs font-semibold text-brand-600 mb-1">{label}</label>
      <input required={required} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
        className="w-full px-3 py-2.5 bg-brand-50 border border-brand-200 rounded-xl text-sm outline-none focus:border-brand-500" />
    </div>
  );
}

function Empty({ text }: { text: string }) {
  return <div className="text-center py-10 text-brand-300 text-sm">{text}</div>;
}

export default function ReturnsPage() {
  return (
    <Suspense fallback={<div className="text-brand-400">Загрузка...</div>}>
      <ReturnsInner />
    </Suspense>
  );
}
