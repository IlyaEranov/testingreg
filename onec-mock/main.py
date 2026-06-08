"""
Тестовая 1С:Предприятие (эмулятор REST-сервиса).

Самостоятельный сервис, имитирующий HTTP-сервис учётной системы 1С.
Принимает те же запросы, что отправляет АИС сопровождения возвратов
(onec_service.py), «создаёт» соответствующие учётные документы и
показывает их в веб-интерфейсе в стиле печатных форм 1С.

Запуск:   uvicorn main:app --host 0.0.0.0 --port 8081
Интерфейс: http://localhost:8081
"""
import itertools
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI(title="Тестовая 1С:Предприятие (эмулятор)")

# Хранилище принятых документов (в памяти)
DOCS: list[dict] = []
SMS: list[dict] = []
_counter = itertools.count(1)

ORG = {
    "name": 'Общество с ограниченной ответственностью "Регион Сервис"',
    "inn": "0273075647 / 027301001",
    "address": "450027, Башкортостан Респ., Уфимский р-н, Уфа г., Индустриальное ш., дом № 92, корпус а",
}


def _num() -> str:
    return f"РС-{next(_counter):06d}"


def _store(kind: str, title: str, payload: dict, summary: str = "") -> dict:
    doc = {
        "id": len(DOCS) + 1,
        "kind": kind,
        "title": title,
        "number": _num(),
        "date": datetime.now().strftime("%d.%m.%Y"),
        "received_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "payload": payload,
        "summary": summary,
    }
    DOCS.insert(0, doc)
    return doc


def _resp(doc: dict) -> dict:
    return {
        "success": True,
        "documentType": doc["payload"].get("documentType", doc["kind"]),
        "documentNumber": doc["number"],
        "date": doc["date"],
        "message": f"Документ «{doc['title']}» создан в 1С",
    }


# ===================== ПРИЁМ ЗАПРОСОВ ОТ АИС =====================
# Маршруты регистрируются и с префиксом /api, и без него —
# чтобы работать при любом значении ONEC_API_URL.

async def _create_return(request: Request):
    p = await request.json()
    s = f'Контрагент: {p.get("client","")}; позиций: {len(p.get("items",[]))}; сумма: {p.get("totalAmount",0)} руб.'
    return _resp(_store("return", "Возврат товаров от покупателя", p, s))


async def _write_off(request: Request):
    p = await request.json()
    s = f'По возврату {p.get("returnNumber","")}; причина: {p.get("reason","")}; позиций: {len(p.get("items",[]))}'
    return _resp(_store("writeoff", "Акт о списании товаров (ТОРГ-16)", p, s))


async def _refund(request: Request):
    p = await request.json()
    s = f'Контрагент: {p.get("client","")}; сумма: {p.get("amount",0)} руб.'
    return _resp(_store("refund", "Возврат денежных средств покупателю", p, s))


async def _update_stock(request: Request):
    p = await request.json()
    s = f'Склад: {p.get("warehouse","")}; позиций: {len(p.get("items",[]))}'
    return _resp(_store("stock", "Корректировка складских остатков", p, s))


for path in ("/returns", "/api/returns"):
    app.add_api_route(path, _create_return, methods=["POST"])
for path in ("/write-off", "/api/write-off"):
    app.add_api_route(path, _write_off, methods=["POST"])
for path in ("/refund", "/api/refund"):
    app.add_api_route(path, _refund, methods=["POST"])
for path in ("/stock", "/api/stock"):
    app.add_api_route(path, _update_stock, methods=["PUT"])


# ===================== ТЕСТОВЫЙ SMS-ШЛЮЗ =====================

async def _receive_sms(request: Request):
    p = await request.json()
    SMS.insert(0, {
        "id": len(SMS) + 1,
        "phone": p.get("phone", ""),
        "text": p.get("text", ""),
        "sender": p.get("sender", ""),
        "received_at": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
    })
    return {"success": True, "status": "OK", "message": "SMS принято тестовым шлюзом"}


for path in ("/sms", "/api/sms"):
    app.add_api_route(path, _receive_sms, methods=["POST"])


@app.get("/health")
async def health():
    return {"status": "ok", "documents": len(DOCS), "sms": len(SMS)}


# ===================== ВЕБ-ИНТЕРФЕЙС =====================

def _rub_words(amount: float) -> str:
    rub = int(amount)
    kop = int(round((amount - rub) * 100))
    return f"{rub} руб. {kop:02d} коп."


def _items_rows(items: list[dict]) -> str:
    rows = ""
    total = 0.0
    for i, it in enumerate(items, 1):
        name = it.get("productName") or it.get("product_name") or "—"
        art = it.get("article", "")
        qty = it.get("quantity", "")
        price = float(it.get("price", 0) or 0)
        s = price * float(qty or 0)
        total += s
        rows += (f"<tr><td class='c'>{i}</td><td>{art}</td><td>{name}</td>"
                 f"<td class='c'>{qty} шт</td><td class='r'>{price:,.2f}</td>"
                 f"<td class='r'>{s:,.2f}</td></tr>".replace(",", " "))
    return rows, total


def _render_doc(doc: dict) -> str:
    p = doc["payload"]
    items = p.get("items", [])
    rows, total = _items_rows(items)
    if doc["kind"] == "refund":
        total = float(p.get("amount", 0) or 0)

    items_block = ""
    if items:
        items_block = f"""
        <table class="items">
          <tr><th>№</th><th>Артикул</th><th>Товар</th><th>Количество</th><th>Цена</th><th>Сумма</th></tr>
          {rows}
          <tr class="total"><td colspan="5" class="r">Итого:</td><td class="r">{total:,.2f}</td></tr>
        </table>
        <p>Всего наименований {len(items)}, на сумму {total:,.2f} руб.</p>
        <p><b>Сумма прописью:</b> {_rub_words(total)}</p>
        """.replace(",", " ")

    extra = ""
    if doc["kind"] == "return":
        extra = f"<p><b>Контрагент (покупатель):</b> {p.get('client','')}</p>"
    elif doc["kind"] == "writeoff":
        extra = f"<p><b>Основание:</b> возврат № {p.get('returnNumber','')}; причина списания: {p.get('reason','')}</p>"
    elif doc["kind"] == "refund":
        extra = (f"<p><b>Контрагент (получатель):</b> {p.get('client','')}</p>"
                 f"<p><b>Сумма к возврату:</b> {total:,.2f} руб. ({_rub_words(total)})</p>".replace(",", " "))
    elif doc["kind"] == "stock":
        wh = p.get("warehouse", "")
        srows = "".join(
            f"<tr><td>{it.get('article','')}</td><td class='c'>{it.get('quantity','')}</td>"
            f"<td>{it.get('operation','')}</td></tr>" for it in items)
        extra = (f"<p><b>Склад:</b> {wh}</p>"
                 f"<table class='items'><tr><th>Артикул</th><th>Кол-во</th><th>Операция</th></tr>{srows}</table>")
        items_block = ""

    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<title>{doc['title']} № {doc['number']}</title>
<style>{_CSS}</style></head><body>
<a class="back" href="/">← к списку документов</a>
<div class="page">
  <h1>{doc['title']} № {doc['number']} от {doc['date']} г.</h1>
  <table class="head">
    <tr><td class="lbl">Организация:</td><td><b>{ORG['name']}</b></td></tr>
    <tr><td class="lbl">ИНН / КПП:</td><td>{ORG['inn']}</td></tr>
    <tr><td class="lbl">Адрес:</td><td>{ORG['address']}</td></tr>
  </table>
  {extra}
  {items_block}
  <div class="sign">
    <div class="line">Отпустил</div>
    <div class="line">Получил</div>
  </div>
  <p class="note">Документ сформирован в учётной системе 1С:Предприятие по данным,
  переданным из АИС сопровождения возврата товаров (получено {doc['received_at']}).</p>
</div></body></html>"""


@app.get("/", response_class=HTMLResponse)
async def index():
    if not DOCS:
        body = ("<p class='empty'>Документы ещё не поступали.<br>"
                "Выполните в АИС финансовое завершение возврата — документ появится здесь.</p>")
    else:
        rows = "".join(
            f"<tr><td>{d['number']}</td><td>{d['title']}</td>"
            f"<td>{d['date']}</td><td>{d['summary']}</td>"
            f"<td><a href='/doc/{d['id']}'>открыть</a></td></tr>"
            for d in DOCS)
        body = f"""<table class="items">
          <tr><th>Номер</th><th>Документ</th><th>Дата</th><th>Сведения</th><th></th></tr>
          {rows}</table>"""
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<title>Тестовые внешние сервисы</title><meta http-equiv="refresh" content="10">
<style>{_CSS}</style></head><body>
<div class="page">
  <div class="brand">Тестовые внешние сервисы <span>— эмуляторы для АИС</span></div>
  <div class="nav"><a href="/">Документы 1С ({len(DOCS)})</a> <a href="/sms">SMS ({len(SMS)})</a></div>
  <h1>Документы, принятые из АИС (1С:Предприятие)</h1>
  <p class="muted">Организация: {ORG['name']}. Страница обновляется автоматически.</p>
  {body}
</div></body></html>"""


@app.get("/sms", response_class=HTMLResponse)
async def sms_list():
    if not SMS:
        body = "<p class='empty'>SMS ещё не поступали.</p>"
    else:
        rows = "".join(
            f"<tr><td>{m['received_at']}</td><td>{m['sender']}</td>"
            f"<td>{m['phone']}</td><td>{m['text']}</td></tr>" for m in SMS)
        body = f"""<table class="items">
          <tr><th>Время</th><th>Отправитель</th><th>Телефон</th><th>Текст</th></tr>
          {rows}</table>"""
    return f"""<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">
<title>Тестовый SMS-шлюз</title><meta http-equiv="refresh" content="10">
<style>{_CSS}</style></head><body>
<div class="page">
  <div class="brand">Тестовые внешние сервисы <span>— эмуляторы для АИС</span></div>
  <div class="nav"><a href="/">Документы 1С ({len(DOCS)})</a> <a href="/sms">SMS ({len(SMS)})</a></div>
  <h1>SMS, принятые шлюзом</h1>
  <p class="muted">Имитация SMS-провайдера. Страница обновляется автоматически.</p>
  {body}
</div></body></html>"""


def _doc_by_id(doc_id: int):
    for d in DOCS:
        if d["id"] == doc_id:
            return d
    return None


@app.get("/doc/{doc_id}", response_class=HTMLResponse)
async def view_doc(doc_id: int):
    d = _doc_by_id(doc_id)
    if not d:
        return HTMLResponse("<p>Документ не найден. <a href='/'>назад</a></p>", status_code=404)
    return _render_doc(d)


_CSS = """
* { box-sizing: border-box; }
body { font-family: 'Times New Roman', serif; background:#eef0f3; margin:0; padding:30px; color:#111; }
.page { background:#fff; max-width:900px; margin:0 auto; padding:36px 44px; box-shadow:0 6px 24px rgba(0,0,0,.12); }
.brand { font-family:'Segoe UI',sans-serif; font-weight:700; color:#c00; font-size:18px; margin-bottom:8px; }
.brand span { color:#888; font-weight:400; font-size:14px; }
h1 { font-size:18px; margin:6px 0 18px; }
.muted { color:#777; font-size:13px; }
table.head { border-collapse:collapse; margin-bottom:14px; font-size:14px; }
table.head td { padding:2px 8px; vertical-align:top; }
table.head .lbl { color:#555; white-space:nowrap; }
table.items { width:100%; border-collapse:collapse; margin:14px 0; font-size:14px; }
table.items th, table.items td { border:1px solid #333; padding:5px 8px; }
table.items th { background:#f0f0f0; }
.items .c { text-align:center; } .items .r { text-align:right; }
.items .total td { font-weight:bold; background:#fafafa; }
.sign { display:flex; gap:60px; margin-top:50px; }
.sign .line { flex:1; border-top:1px solid #000; padding-top:4px; font-size:12px; color:#444; text-align:center; }
.note { margin-top:26px; font-size:11px; color:#888; font-style:italic; }
.empty { text-align:center; color:#888; padding:40px; }
.nav { font-family:'Segoe UI',sans-serif; margin:8px 0 4px; }
.nav a { display:inline-block; margin-right:16px; font-size:14px; font-weight:600; text-decoration:none; }
a { color:#06c; } a.back { font-family:'Segoe UI',sans-serif; font-size:13px; display:inline-block; margin-bottom:12px; }
"""
