"""Seed the database with initial data (roles, statuses, demo users, etc.)."""
import asyncio
from sqlalchemy import select
from app.database import engine, async_session, Base
from app.models import *  # noqa: F403
from app.utils.security import get_password_hash
from app.services.notification_service import notify_employees


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        # ===== Roles =====
        existing = await db.execute(select(Role))
        if not existing.scalars().first():
            roles = [
                Role(id=1, name="admin", description="Администратор"),
                Role(id=2, name="manager", description="Менеджер"),
                Role(id=3, name="warehouse_staff", description="Складской сотрудник"),
                Role(id=4, name="director", description="Руководитель"),
            ]
            db.add_all(roles)
            await db.flush()

        # ===== Statuses =====
        existing = await db.execute(select(ReturnStatus))
        if not existing.scalars().first():
            statuses = [
                ReturnStatus(id=1, name="Создана", code="created", sort_order=1),
                ReturnStatus(id=2, name="На проверке склада", code="warehouse", sort_order=2),
                ReturnStatus(id=3, name="Ожидает решения", code="waiting", sort_order=3),
                ReturnStatus(id=4, name="Передана на экспертизу", code="expertise", sort_order=4),
                ReturnStatus(id=5, name="Экспертиза завершена", code="expertise_done", sort_order=5),
                ReturnStatus(id=6, name="Одобрена", code="approved", sort_order=6),
                ReturnStatus(id=7, name="Отклонена", code="rejected", sort_order=7),
                ReturnStatus(id=8, name="Документы сформированы", code="docs", sort_order=8),
                ReturnStatus(id=9, name="Ожидает фин. завершения", code="finance", sort_order=9),
                ReturnStatus(id=10, name="Завершена", code="done", sort_order=10),
            ]
            db.add_all(statuses)

        # ===== Reasons =====
        existing = await db.execute(select(ReturnReason))
        if not existing.scalars().first():
            reasons = [
                ReturnReason(id=1, name="Не подошёл по цвету/оттенку", description="Товар не подошёл по цвету"),
                ReturnReason(id=2, name="Излишки после ремонта", description="Неиспользованный материал"),
                ReturnReason(id=3, name="Производственный брак", description="Дефект, допущенный при производстве"),
                ReturnReason(id=4, name="Повреждение при транспортировке", description="Товар повреждён при доставке"),
                ReturnReason(id=5, name="Несоответствие заказу", description="Доставлен другой товар"),
                ReturnReason(id=6, name="Дефект покрытия", description="Царапины, сколы, отслоение"),
            ]
            db.add_all(reasons)

        # ===== Suppliers =====
        existing = await db.execute(select(Supplier))
        if not existing.scalars().first():
            suppliers = [
                Supplier(id=1, name="Kronostar", contact_person="Петров А.В.", phone="+7(495)111-22-33", email="supply@kronostar.ru"),
                Supplier(id=2, name="Tarkett", contact_person="Сидорова Е.Н.", phone="+7(495)222-33-44", email="returns@tarkett.com"),
                Supplier(id=3, name="Quick-Step", contact_person="Козлов Д.И.", phone="+7(495)333-44-55", email="info@quickstep.ru"),
                Supplier(id=4, name="Alpine Floor", contact_person="Миронов К.С.", phone="+7(495)444-55-66", email="quality@alpinefloor.ru"),
                Supplier(id=5, name="Egger", contact_person="Васильев О.Г.", phone="+7(495)555-66-77", email="claim@egger.com"),
            ]
            db.add_all(suppliers)

        # ===== Warehouses =====
        existing = await db.execute(select(Warehouse))
        if not existing.scalars().first():
            warehouses = [
                Warehouse(id=1, name="Основной склад", address="г. Краснодар, ул. Промышленная, 15"),
                Warehouse(id=2, name="Склад выставочный зал", address="г. Краснодар, ул. Красная, 120"),
                Warehouse(id=3, name="Склад брака", address="г. Краснодар, ул. Промышленная, 15, секция Б"),
            ]
            db.add_all(warehouses)

        # ===== App settings (адреса тестовых внешних сервисов по умолчанию) =====
        existing = await db.execute(select(AppSetting))
        if not existing.scalars().first():
            db.add_all([
                AppSetting(key="onec_api_url", value="http://host.docker.internal:8081"),
                AppSetting(key="onec_api_token", value=""),
                # Email — тестовый сервер Mailpit (SMTP 1025, веб http://localhost:8025)
                AppSetting(key="smtp_host", value="host.docker.internal"),
                AppSetting(key="smtp_port", value="1025"),
                AppSetting(key="smtp_user", value=""),
                AppSetting(key="smtp_password", value=""),
                AppSetting(key="smtp_from", value="no-reply@region-service.ru"),
                # SMS — тестовый приёмник в onec-mock
                AppSetting(key="sms_api_url", value="http://host.docker.internal:8081/sms"),
                AppSetting(key="sms_api_key", value=""),
                AppSetting(key="sms_sender", value="RegionService"),
            ])

        # ===== Users =====
        existing = await db.execute(select(User))
        if not existing.scalars().first():
            pwd = get_password_hash("password123")
            users = [
                User(id=1, email="admin@region-service.ru", hashed_password=pwd, last_name="Волкова", first_name="Ирина", patronymic="Николаевна", role_id=1),
                User(id=2, email="ivanov@region-service.ru", hashed_password=pwd, last_name="Иванов", first_name="Михаил", patronymic="Алексеевич", role_id=2),
                User(id=3, email="petrova@region-service.ru", hashed_password=pwd, last_name="Петрова", first_name="Анна", patronymic="Сергеевна", role_id=2),
                User(id=4, email="sidorov@region-service.ru", hashed_password=pwd, last_name="Сидоров", first_name="Дмитрий", patronymic="Юрьевич", role_id=3),
                User(id=5, email="morozov@region-service.ru", hashed_password=pwd, last_name="Морозов", first_name="Андрей", patronymic="Петрович", role_id=4),
            ]
            db.add_all(users)

        await db.flush()

        # ===== Demo returns =====
        existing = await db.execute(select(ReturnRequest))
        if not existing.scalars().first():
            await seed_returns(db)

        await db.commit()

        # Reset sequences so manual ids don't conflict with future inserts
        await reset_sequences(db)
        await db.commit()
        print("Database seeded successfully!")


async def reset_sequences(db):
    """Sync PostgreSQL sequences with max(id) after manual id inserts."""
    from sqlalchemy import text
    tables = [
        "roles", "return_statuses", "return_reasons", "suppliers",
        "warehouses", "users", "clients", "return_requests",
        "return_items", "warehouse_checks", "supplier_examinations",
        "documents", "action_history", "notifications",
    ]
    for table in tables:
        await db.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM {table}), 1), true)"
        ))


async def seed_returns(db):
    """Create demo return requests with items, checks, docs and history."""
    from datetime import datetime, timezone
    from decimal import Decimal

    def dt(s):
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)

    # Clients
    clients_data = [
        (1, "Кузнецов Алексей Игоревич", "+7(918)100-20-30"),
        (2, 'ООО "СтройМастер"', "+7(918)200-30-40"),
        (3, "Смирнова Ольга Викторовна", "+7(918)300-40-50"),
        (4, "Попов Виталий Андреевич", "+7(918)400-50-60"),
        (5, "ИП Григорьев С.В.", "+7(918)500-60-70"),
        (6, "Новикова Мария Дмитриевна", "+7(918)600-70-80"),
        (7, 'ООО "Домострой"', "+7(918)700-80-90"),
        (8, "Фёдоров Павел Николаевич", "+7(918)800-90-10"),
        (9, "Белова Наталья Олеговна", "+7(918)900-10-20"),
        (10, "Краснов Олег Сергеевич", "+7(918)010-20-30"),
    ]
    for cid, name, phone in clients_data:
        db.add(Client(id=cid, name=name, phone=phone))
    await db.flush()

    # Return requests: (id, num, client_id, type, reason_id, status, mgr, wh, date, comment, items, checks, docs, history)
    data = [
        dict(id=1, number="ВЗ-000001", client_id=1, return_type="Ненадлежащее качество", reason_id=3,
             status="done", manager_id=2, warehouse_id=1, date="2025-04-10",
             comment="Замковое соединение повреждено на нескольких досках",
             items=[("Ламинат Kronostar D2304 Дуб Натуральный", "D2304", 3, "уп.", "1450"),
                    ("Подложка 3мм", "PL-003", 2, "рул.", "680")],
             checks=[(0, 3, "Повреждена упаковка", "Сколы замкового соединения на 2 досках", 3, "2025-04-11")],
             docs=[("application", "2025-04-10"), ("route_sheet", "2025-04-10"), ("inspection_act", "2025-04-11"),
                   ("return_act", "2025-04-14"), ("refund_act", "2025-04-15")],
             history=[("2025-04-10 09:15", "Заявка создана", 2, None, "created"),
                      ("2025-04-10 09:16", "Документы сформированы: заявление, маршрутный лист", None, "created", "created"),
                      ("2025-04-10 09:20", "Статус → На проверке склада", 2, "created", "warehouse"),
                      ("2025-04-11 14:30", "Складская проверка завершена", 3, "warehouse", "waiting"),
                      ("2025-04-12 10:00", "Возврат одобрен", 5, "waiting", "approved"),
                      ("2025-04-15 16:00", "Финансовое завершение, данные переданы в 1С", 4, "finance", "done")]),
        dict(id=2, number="ВЗ-000002", client_id=2, return_type="Надлежащее качество", reason_id=2,
             status="finance", manager_id=3, warehouse_id=1, date="2025-05-02",
             comment="Остаток после укладки, упаковка не вскрыта",
             items=[("Кварцвинил Alpine Floor ECO 11-1 Дуб Рустик", "ECO11-1", 5, "уп.", "2180")],
             checks=[(0, 5, "Упаковка целая, товарный вид сохранён", "Дефектов не обнаружено", 3, "2025-05-03")],
             docs=[("application", "2025-05-02"), ("route_sheet", "2025-05-02"), ("inspection_act", "2025-05-03"),
                   ("return_act", "2025-05-05")],
             history=[("2025-05-02 11:30", "Заявка создана", 3, None, "created"),
                      ("2025-05-02 11:31", "Статус → На проверке склада", 3, "created", "warehouse"),
                      ("2025-05-03 10:15", "Складская проверка завершена", 3, "warehouse", "waiting"),
                      ("2025-05-04 09:00", "Возврат одобрен", 5, "waiting", "approved"),
                      ("2025-05-05 14:01", "Статус → Ожидает финансового завершения", None, "docs", "finance")]),
        dict(id=3, number="ВЗ-000003", client_id=3, return_type="Ненадлежащее качество", reason_id=6,
             status="expertise", manager_id=2, warehouse_id=1, date="2025-05-10",
             comment="Отслоение верхнего слоя ламината после 2 недель эксплуатации",
             items=[("Ламинат Egger EPL 046 Дуб Шерман", "EPL046", 8, "уп.", "1890")],
             checks=[(0, 8, "Упаковка вскрыта, часть досок уложена", "Отслоение верхнего слоя на 12 досках, предположительно заводской брак", 3, "2025-05-11")],
             docs=[("application", "2025-05-10"), ("route_sheet", "2025-05-10"), ("inspection_act", "2025-05-11"),
                   ("transfer_act", "2025-05-13")],
             history=[("2025-05-10 14:00", "Заявка создана", 2, None, "created"),
                      ("2025-05-11 11:00", "Складская проверка завершена, признаки брака", 3, "warehouse", "waiting"),
                      ("2025-05-12 09:30", "Решение: передать на экспертизу поставщику", 2, "waiting", "expertise"),
                      ("2025-05-13 10:00", "Товар передан поставщику Egger", 2, "expertise", "expertise")]),
        dict(id=4, number="ВЗ-000004", client_id=4, return_type="Надлежащее качество", reason_id=1,
             status="warehouse", manager_id=3, warehouse_id=2, date="2025-05-20",
             comment="Цвет не совпадает с образцом в магазине",
             items=[("Линолеум Tarkett Идиллия Нова Танго 3", "IDN-T3", 12, "м²", "890"),
                    ("Плинтус ПВХ 80мм Дуб Серый", "PL-80-DG", 8, "шт.", "340")],
             checks=[], docs=[("application", "2025-05-20"), ("route_sheet", "2025-05-20")],
             history=[("2025-05-20 16:00", "Заявка создана", 3, None, "created"),
                      ("2025-05-20 16:05", "Статус → На проверке склада", 3, "created", "warehouse")]),
        dict(id=5, number="ВЗ-000005", client_id=5, return_type="Ненадлежащее качество", reason_id=4,
             status="warehouse", manager_id=2, warehouse_id=1, date="2025-05-22",
             comment="Несколько упаковок деформированы при доставке",
             items=[("Паркетная доска Polarwood Дуб Меркурий", "PW-DM", 4, "уп.", "3450")],
             checks=[], docs=[("application", "2025-05-22"), ("route_sheet", "2025-05-22")],
             history=[("2025-05-22 10:30", "Заявка создана", 2, None, "created"),
                      ("2025-05-22 10:35", "Статус → На проверке склада", 2, "created", "warehouse")]),
        dict(id=6, number="ВЗ-000006", client_id=6, return_type="Надлежащее качество", reason_id=2,
             status="created", manager_id=2, warehouse_id=1, date="2025-05-25", comment="",
             items=[("Подложка Tuplex 3мм", "TPX-3", 3, "рул.", "1200"),
                    ("Порог алюминиевый 40мм Серебро", "PR-40-S", 2, "шт.", "560")],
             checks=[], docs=[],
             history=[("2025-05-25 09:00", "Заявка создана", 2, None, "created")]),
        dict(id=7, number="ВЗ-000007", client_id=7, return_type="Ненадлежащее качество", reason_id=5,
             status="waiting", manager_id=3, warehouse_id=1, date="2025-05-18",
             comment="Доставлена коллекция Тоскана вместо Венеция",
             items=[("Ламинат Kronostar Венеция K005", "K005", 10, "уп.", "1350")],
             checks=[(0, 10, "Упаковка целая", "Артикул не соответствует заказу: K007 вместо K005", 3, "2025-05-19")],
             docs=[("application", "2025-05-18"), ("route_sheet", "2025-05-18"), ("inspection_act", "2025-05-19")],
             history=[("2025-05-18 13:00", "Заявка создана", 3, None, "created"),
                      ("2025-05-19 15:00", "Складская проверка завершена", 3, "warehouse", "waiting")]),
        dict(id=8, number="ВЗ-000008", client_id=8, return_type="Надлежащее качество", reason_id=1,
             status="rejected", manager_id=2, warehouse_id=2, date="2025-05-08",
             comment="Покупатель вскрыл упаковку и уложил часть материала",
             items=[("Кварцвинил Quick-Step Balance BACL40127", "BACL40127", 6, "уп.", "2650")],
             checks=[(0, 6, "3 упаковки вскрыты, плитка уложена и демонтирована", "Следы клея, товарный вид утрачен", 3, "2025-05-09")],
             docs=[("application", "2025-05-08"), ("route_sheet", "2025-05-08"), ("inspection_act", "2025-05-09"),
                   ("rejection_notice", "2025-05-10")],
             history=[("2025-05-08 11:00", "Заявка создана", 2, None, "created"),
                      ("2025-05-09 14:00", "Складская проверка: товарный вид утрачен", 3, "warehouse", "waiting"),
                      ("2025-05-10 09:00", "Возврат отклонён: нарушение условий возврата", 5, "waiting", "rejected")]),
        dict(id=9, number="ВЗ-000009", client_id=9, return_type="Ненадлежащее качество", reason_id=3,
             status="expertise_done", manager_id=3, warehouse_id=1, date="2025-05-05",
             comment="Нарушение геометрии досок",
             items=[("Ламинат Egger PRO Classic EPL 150", "EPL150", 6, "уп.", "1750")],
             checks=[(0, 6, "Упаковка частично вскрыта", "Выгнутые доски, щели при стыковке. Вероятный заводской брак", 3, "2025-05-06")],
             docs=[("application", "2025-05-05"), ("route_sheet", "2025-05-05"), ("inspection_act", "2025-05-06"),
                   ("transfer_act", "2025-05-08")],
             history=[("2025-05-05 15:00", "Заявка создана", 3, None, "created"),
                      ("2025-05-08 11:00", "Товар передан поставщику Egger", 3, "waiting", "expertise"),
                      ("2025-05-20 16:00", "Получено заключение: заводской брак подтверждён", 3, "expertise", "expertise_done")]),
        dict(id=10, number="ВЗ-000010", client_id=10, return_type="Ненадлежащее качество", reason_id=6,
             status="approved", manager_id=2, warehouse_id=1, date="2025-05-15",
             comment="Царапины на поверхности при вскрытии упаковки",
             items=[("Ламинат Kronostar Grunhof D2987", "D2987", 2, "уп.", "1290")],
             checks=[(0, 2, "Упаковка вскрыта", "Глубокие царапины на декоративном слое 4 досок, заводской дефект", 3, "2025-05-16")],
             docs=[("application", "2025-05-15"), ("route_sheet", "2025-05-15"), ("inspection_act", "2025-05-16"),
                   ("return_act", "2025-05-18")],
             history=[("2025-05-15 10:00", "Заявка создана", 2, None, "created"),
                      ("2025-05-16 11:00", "Складская проверка завершена", 3, "warehouse", "waiting"),
                      ("2025-05-17 09:00", "Возврат одобрен", 5, "waiting", "approved")]),
    ]

    # Статус заявки → событие для демо-уведомлений сотрудникам
    STATUS_EVENT = {
        "created": "created", "warehouse": "warehouse", "waiting": "waiting",
        "expertise": "expertise", "expertise_done": "expertise_done",
        "approved": "approved", "rejected": "rejected",
        "finance": "approved", "done": "done",
    }

    for d in data:
        total = sum(Decimal(p) * q for _, _, q, _, p in d["items"])
        rr = ReturnRequest(
            id=d["id"], number=d["number"], client_id=d["client_id"],
            return_type=d["return_type"], reason_id=d["reason_id"], status=d["status"],
            manager_id=d["manager_id"], warehouse_id=d["warehouse_id"],
            comment=d["comment"], total_amount=total, created_at=dt(d["date"] + "T09:00:00"),
        )
        db.add(rr)
        await db.flush()

        item_ids = []
        for name, art, qty, unit, price in d["items"]:
            it = ReturnItem(return_request_id=rr.id, product_name=name, article=art,
                            quantity=qty, unit=unit, price=Decimal(price))
            db.add(it)
            await db.flush()
            item_ids.append(it.id)

        for item_idx, qf, cond, defect, insp, cdate in d["checks"]:
            db.add(WarehouseCheck(
                return_item_id=item_ids[item_idx], quantity_fact=qf,
                packaging_condition=cond, defect_description=defect,
                inspector_id=insp, checked_at=dt(cdate + "T12:00:00"),
            ))

        doc_names = {
            "application": "Заявление на возврат товара", "route_sheet": "Маршрутный лист",
            "inspection_act": "Акт осмотра товара", "transfer_act": "Акт передачи товара поставщику",
            "return_act": "Акт возврата товара покупателю", "refund_act": "Акт возврата денежных средств",
            "rejection_notice": "Уведомление об отказе в возврате",
        }
        for dtype, ddate in d["docs"]:
            db.add(Document(
                return_request_id=rr.id, document_type=dtype,
                file_name=f"{dtype}_{rr.number}.docx", file_path=f"documents/{dtype}_{rr.number}.docx",
                generated_by="system", created_at=dt(ddate + "T10:00:00"),
            ))

        for hdate, action, uid, old_s, new_s in d["history"]:
            db.add(ActionHistory(
                return_request_id=rr.id, user_id=uid, action=action,
                old_status=old_s, new_status=new_s, created_at=dt(hdate.replace(" ", "T")),
            ))

        # Демо-уведомления сотрудникам по текущему этапу заявки
        ev = STATUS_EVENT.get(d["status"])
        if ev:
            await notify_employees(db, rr, ev)

    # Examinations for expertise returns
    db.add(SupplierExamination(return_request_id=3, supplier_id=5,
                               transfer_date=dt("2025-05-13T10:00:00"), details="Передан на экспертизу"))
    db.add(SupplierExamination(return_request_id=9, supplier_id=5,
                               transfer_date=dt("2025-05-08T11:00:00"), result_date=dt("2025-05-20T16:00:00"),
                               conclusion="defect_confirmed", details="Заводской брак подтверждён"))
    await db.flush()


if __name__ == "__main__":
    asyncio.run(seed())
