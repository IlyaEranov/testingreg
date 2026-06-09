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
                Role(id=3, name="claims", description="Сотрудник претензионного отдела"),
                Role(id=4, name="director", description="Руководитель"),
                Role(id=5, name="logistics", description="Логистика"),
            ]
            db.add_all(roles)
            await db.flush()

        # ===== Statuses =====
        existing = await db.execute(select(ReturnStatus))
        if not existing.scalars().first():
            statuses = [
                ReturnStatus(id=1, name="Создана", code="created", sort_order=1),
                ReturnStatus(id=2, name="Ожидает данных покупателя", code="client_data", sort_order=2),
                ReturnStatus(id=3, name="Претензия отправлена заводу", code="claim_factory", sort_order=3),
                ReturnStatus(id=4, name="На рассмотрении завода", code="factory_review", sort_order=4),
                ReturnStatus(id=5, name="Заключение получено", code="factory_done", sort_order=5),
                ReturnStatus(id=6, name="Транспортировка на склад", code="in_transit", sort_order=6),
                ReturnStatus(id=7, name="Принят и сверён", code="received", sort_order=7),
                ReturnStatus(id=8, name="Отклонена", code="rejected", sort_order=8),
                ReturnStatus(id=9, name="Завершена", code="done", sort_order=9),
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
                # Сотрудник претензионного отдела
                User(id=4, email="sidorov@region-service.ru", hashed_password=pwd, last_name="Сидоров", first_name="Дмитрий", patronymic="Юрьевич", role_id=3),
                # Руководитель
                User(id=5, email="morozov@region-service.ru", hashed_password=pwd, last_name="Морозов", first_name="Андрей", patronymic="Петрович", role_id=4),
                # Логистика
                User(id=6, email="logist@region-service.ru", hashed_password=pwd, last_name="Орлов", first_name="Сергей", patronymic="Викторович", role_id=5),
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

    # Заявки на возврат. kind: defect — претензия по качеству (через завод),
    #                          quality — надлежащее качество (без завода).
    # claim — данные претензии/заключения завода; onec_docs — учётные документы из 1С.
    data = [
        # 1. Создана (брак) — проверяются условия
        dict(id=1, number="ВЗ-000001", client_id=1, return_type="Ненадлежащее качество", kind="defect", reason_id=3,
             status="created", manager_id=2, warehouse_id=1, date="2025-05-25",
             comment="Замковое соединение повреждено на нескольких досках",
             items=[("Ламинат Kronostar D2304 Дуб Натуральный", "D2304", 3, "уп.", "1450")],
             checks=[], docs=[], onec_docs=[], claim=None,
             history=[("2025-05-25 09:15", "Обращение зарегистрировано, проверяются условия возврата", 2, None, "created")]),
        # 2. Ожидает данных покупателя (брак)
        dict(id=2, number="ВЗ-000002", client_id=2, return_type="Ненадлежащее качество", kind="defect", reason_id=6,
             status="client_data", manager_id=3, warehouse_id=1, date="2025-05-24",
             comment="Дефект покрытия — царапины на декоративном слое",
             items=[("Ламинат Egger EPL 046 Дуб Шерман", "EPL046", 4, "уп.", "1890")],
             checks=[], docs=[], onec_docs=[], claim=None,
             history=[("2025-05-24 10:00", "Обращение зарегистрировано", 3, None, "created"),
                      ("2025-05-24 10:20", "Условия соблюдены, покупателю направлена форма для данных", 3, "created", "client_data")]),
        # 3. Претензия отправлена заводу (брак)
        dict(id=3, number="ВЗ-000003", client_id=3, return_type="Ненадлежащее качество", kind="defect", reason_id=3,
             status="claim_factory", manager_id=2, warehouse_id=1, date="2025-05-20",
             comment="Производственный брак — расслоение",
             items=[("Кварцвинил Alpine Floor ECO 11-1 Дуб Рустик", "ECO11-1", 6, "уп.", "2180")],
             checks=[], docs=[("claim_letter", "2025-05-21")], onec_docs=[],
             claim=dict(supplier_id=4, transfer="2025-05-21T11:00:00"),
             history=[("2025-05-20 14:00", "Обращение зарегистрировано", 2, None, "created"),
                      ("2025-05-20 14:30", "Условия соблюдены, запрошены данные покупателя", 2, "created", "client_data"),
                      ("2025-05-21 11:00", "Сформирована и направлена претензия заводу", 4, "client_data", "claim_factory")]),
        # 4. Заключение получено (брак подтверждён)
        dict(id=4, number="ВЗ-000004", client_id=4, return_type="Ненадлежащее качество", kind="defect", reason_id=6,
             status="factory_done", manager_id=3, warehouse_id=1, date="2025-05-12",
             comment="Отслоение верхнего слоя после укладки",
             items=[("Ламинат Egger PRO Classic EPL 150", "EPL150", 6, "уп.", "1750")],
             checks=[], docs=[("claim_letter", "2025-05-13")], onec_docs=[],
             claim=dict(supplier_id=5, transfer="2025-05-13T10:00:00", result="2025-05-19T16:00:00",
                        conclusion="defect_confirmed", details="Заводской брак подтверждён"),
             history=[("2025-05-12 09:00", "Обращение зарегистрировано", 3, None, "created"),
                      ("2025-05-12 09:30", "Запрошены данные покупателя", 3, "created", "client_data"),
                      ("2025-05-13 10:00", "Претензия направлена заводу", 4, "client_data", "claim_factory"),
                      ("2025-05-19 16:00", "Получено заключение завода: defect_confirmed", 4, "claim_factory", "factory_done")]),
        # 5. Транспортировка на склад (брак, ветка А)
        dict(id=5, number="ВЗ-000005", client_id=5, return_type="Ненадлежащее качество", kind="defect", reason_id=3,
             status="in_transit", manager_id=2, warehouse_id=1, date="2025-05-10",
             comment="Нарушение геометрии досок",
             items=[("Ламинат Kronostar Grunhof D2987", "D2987", 5, "уп.", "1290")],
             checks=[], docs=[("claim_letter", "2025-05-11"), ("route_sheet", "2025-05-17")], onec_docs=[],
             claim=dict(supplier_id=1, transfer="2025-05-11T10:00:00", result="2025-05-16T15:00:00",
                        conclusion="defect_confirmed", details="Заводской брак подтверждён"),
             history=[("2025-05-10 09:00", "Обращение зарегистрировано", 2, None, "created"),
                      ("2025-05-10 09:30", "Запрошены данные покупателя", 2, "created", "client_data"),
                      ("2025-05-11 10:00", "Претензия направлена заводу", 4, "client_data", "claim_factory"),
                      ("2025-05-16 15:00", "Получено заключение: брак подтверждён", 4, "claim_factory", "factory_done"),
                      ("2025-05-17 09:00", "Сформирован маршрутный лист, передано в логистику", 2, "factory_done", "in_transit")]),
        # 6. Принят и сверён (брак)
        dict(id=6, number="ВЗ-000006", client_id=6, return_type="Ненадлежащее качество", kind="defect", reason_id=6,
             status="received", manager_id=3, warehouse_id=1, date="2025-05-06",
             comment="Сколы на кромке",
             items=[("Паркетная доска Polarwood Дуб Меркурий", "PW-DM", 4, "уп.", "3450")],
             checks=[(0, 4, "Упаковка вскрыта", "Сколы на кромке 5 досок, заводской дефект", 4, "2025-05-15")],
             docs=[("claim_letter", "2025-05-07"), ("route_sheet", "2025-05-13"), ("inspection_act", "2025-05-15")], onec_docs=[],
             claim=dict(supplier_id=2, transfer="2025-05-07T10:00:00", result="2025-05-12T15:00:00",
                        conclusion="defect_confirmed", details="Заводской брак подтверждён"),
             history=[("2025-05-06 09:00", "Обращение зарегистрировано", 3, None, "created"),
                      ("2025-05-07 10:00", "Претензия направлена заводу", 4, "client_data", "claim_factory"),
                      ("2025-05-12 15:00", "Получено заключение: брак подтверждён", 4, "claim_factory", "factory_done"),
                      ("2025-05-13 09:00", "Маршрутный лист передан в логистику", 3, "factory_done", "in_transit"),
                      ("2025-05-15 12:00", "Товар принят и сверён, сформирован акт осмотра", 4, "in_transit", "received")]),
        # 7. Отклонена (брак не подтверждён — нарушение эксплуатации)
        dict(id=7, number="ВЗ-000007", client_id=7, return_type="Ненадлежащее качество", kind="defect", reason_id=3,
             status="rejected", manager_id=2, warehouse_id=1, date="2025-05-04",
             comment="Вздутие после контакта с водой",
             items=[("Ламинат Quick-Step Balance BACL40127", "BACL40127", 6, "уп.", "2650")],
             checks=[], docs=[("claim_letter", "2025-05-05"), ("rejection_notice", "2025-05-12")], onec_docs=[],
             claim=dict(supplier_id=3, transfer="2025-05-05T10:00:00", result="2025-05-11T15:00:00",
                        conclusion="misuse", details="Нарушение условий эксплуатации (контакт с водой)"),
             history=[("2025-05-04 09:00", "Обращение зарегистрировано", 2, None, "created"),
                      ("2025-05-05 10:00", "Претензия направлена заводу", 4, "client_data", "claim_factory"),
                      ("2025-05-11 15:00", "Заключение: нарушение эксплуатации", 4, "claim_factory", "factory_done"),
                      ("2025-05-12 09:00", "Возврат отклонён: нарушение условий эксплуатации", 5, "factory_done", "rejected")]),
        # 8. Завершена — списание (брак)
        dict(id=8, number="ВЗ-000008", client_id=8, return_type="Ненадлежащее качество", kind="defect", reason_id=3,
             status="done", outcome="write_off", manager_id=2, warehouse_id=1, date="2025-04-10",
             comment="Замки повреждены, заводской брак",
             items=[("Ламинат Kronostar D2304 Дуб Натуральный", "D2304", 3, "уп.", "1450")],
             checks=[(0, 3, "Упаковка вскрыта", "Сколы замкового соединения, заводской брак", 4, "2025-04-18")],
             docs=[("claim_letter", "2025-04-11"), ("route_sheet", "2025-04-16"), ("inspection_act", "2025-04-18")],
             onec_docs=[("write_off", "СП-00041", "2025-04-19"), ("reconciliation_act", "АС-00041", "2025-04-19")],
             claim=dict(supplier_id=1, transfer="2025-04-11T10:00:00", result="2025-04-15T15:00:00",
                        conclusion="defect_confirmed", details="Заводской брак подтверждён"),
             history=[("2025-04-10 09:00", "Обращение зарегистрировано", 2, None, "created"),
                      ("2025-04-11 10:00", "Претензия направлена заводу", 4, "client_data", "claim_factory"),
                      ("2025-04-15 15:00", "Заключение: брак подтверждён", 4, "claim_factory", "factory_done"),
                      ("2025-04-16 09:00", "Маршрутный лист передан в логистику", 2, "factory_done", "in_transit"),
                      ("2025-04-18 12:00", "Товар принят и сверён", 4, "in_transit", "received"),
                      ("2025-04-19 10:00", "Решение: списание; из 1С получен документ списания СП-00041, акт сверки АС-00041", 2, "received", "done")]),
        # 9. Транспортировка на склад (надлежащее качество, ветка Б — без завода)
        dict(id=9, number="ВЗ-000009", client_id=9, return_type="Надлежащее качество", kind="quality", reason_id=2,
             status="in_transit", manager_id=3, warehouse_id=2, date="2025-05-19",
             comment="Излишки после ремонта, упаковка не вскрыта",
             items=[("Кварцвинил Alpine Floor ECO 11-1 Дуб Рустик", "ECO11-1", 5, "уп.", "2180")],
             checks=[], docs=[("route_sheet", "2025-05-20")], onec_docs=[], claim=None,
             history=[("2025-05-19 09:00", "Обращение зарегистрировано", 3, None, "created"),
                      ("2025-05-19 09:30", "Условия соблюдены, запрошены данные покупателя", 3, "created", "client_data"),
                      ("2025-05-20 09:00", "Надлежащее качество: маршрутный лист передан в логистику", 4, "client_data", "in_transit")]),
        # 10. Завершена — корректировка / возврат в продажу (надлежащее качество)
        dict(id=10, number="ВЗ-000010", client_id=10, return_type="Надлежащее качество", kind="quality", reason_id=1,
             status="done", outcome="correction", manager_id=2, warehouse_id=1, date="2025-05-02",
             comment="Не подошёл оттенок, упаковка целая",
             items=[("Линолеум Tarkett Идиллия Нова Танго 3", "IDN-T3", 12, "м²", "890")],
             checks=[(0, 12, "Упаковка целая, товарный вид сохранён", "Дефектов не обнаружено", 4, "2025-05-05")],
             docs=[("route_sheet", "2025-05-03"), ("inspection_act", "2025-05-05")],
             onec_docs=[("correction", "КР-00018", "2025-05-06"), ("reconciliation_act", "АС-00018", "2025-05-06")],
             claim=None,
             history=[("2025-05-02 09:00", "Обращение зарегистрировано", 2, None, "created"),
                      ("2025-05-02 09:30", "Запрошены данные покупателя", 2, "created", "client_data"),
                      ("2025-05-03 09:00", "Маршрутный лист передан в логистику", 4, "client_data", "in_transit"),
                      ("2025-05-05 12:00", "Товар принят и сверён", 4, "in_transit", "received"),
                      ("2025-05-06 10:00", "Решение: корректировка, возврат в продажу; из 1С получен документ КР-00018, акт сверки АС-00018", 2, "received", "done")]),
    ]

    doc_titles = {
        "claim_letter": "Претензионное письмо заводу", "route_sheet": "Маршрутный лист",
        "inspection_act": "Акт осмотра / сверки товара", "rejection_notice": "Уведомление об отказе в возврате",
        "write_off": "Акт списания товара (1С)", "correction": "Корректировка / возврат в продажу (1С)",
        "reconciliation_act": "Акт сверки (1С)",
    }

    for d in data:
        total = sum(Decimal(p) * q for _, _, q, _, p in d["items"])
        rr = ReturnRequest(
            id=d["id"], number=d["number"], client_id=d["client_id"],
            return_type=d["return_type"], kind=d["kind"], outcome=d.get("outcome"),
            reason_id=d["reason_id"], status=d["status"],
            manager_id=d["manager_id"], warehouse_id=d["warehouse_id"],
            comment=d["comment"], total_amount=total, created_at=dt(d["date"] + "T09:00:00"),
            onec_synced=(d["status"] == "done"),
            onec_document_number=(d["onec_docs"][0][1] if d.get("onec_docs") else None),
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

        # Внутренние документы АИС
        for dtype, ddate in d["docs"]:
            db.add(Document(
                return_request_id=rr.id, document_type=dtype,
                file_name=f"{dtype}_{rr.number}.docx", file_path=f"documents/{dtype}_{rr.number}.docx",
                generated_by="system", created_at=dt(ddate + "T10:00:00"),
            ))
        # Учётные документы, подтянутые из 1С
        for dtype, dnumber, ddate in d.get("onec_docs", []):
            db.add(Document(
                return_request_id=rr.id, document_type=dtype,
                file_name=f"{doc_titles.get(dtype, dtype)} {dnumber}", file_path="",
                generated_by="1С", created_at=dt(ddate + "T10:00:00"),
            ))

        for hdate, action, uid, old_s, new_s in d["history"]:
            db.add(ActionHistory(
                return_request_id=rr.id, user_id=uid, action=action,
                old_status=old_s, new_status=new_s, created_at=dt(hdate.replace(" ", "T")),
            ))

        # Претензия / заключение завода
        if d.get("claim"):
            c = d["claim"]
            db.add(SupplierExamination(
                return_request_id=rr.id, supplier_id=c["supplier_id"],
                transfer_date=dt(c["transfer"]) if c.get("transfer") else None,
                result_date=dt(c["result"]) if c.get("result") else None,
                conclusion=c.get("conclusion"), details=c.get("details"),
            ))

        # Демо-уведомления сотрудникам по текущему этапу заявки
        await notify_employees(db, rr, d["status"])

    await db.flush()


if __name__ == "__main__":
    asyncio.run(seed())
