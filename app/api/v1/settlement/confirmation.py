"""费用确认：当月产生费用的试验单汇总 + 责任人确认"""
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Query, Body
from tortoise.expressions import Q

from app.models.expense import DailyRecord, TestOrder, MonthlySettlement, SupplierRate
from app.schemas.base import Success

router = APIRouter(tags=["费用管理"])


@router.get("/query", summary="当月费用确认查询")
async def query_cost_confirmation(
    year_month: str = Query(..., description="月份(YYYY-MM)"),
    responsible_person: str = Query(None, description="责任人筛选"),
):
    # 费用确认从2026-07开始，之前不支持
    if year_month < "2026-07":
        return Success(data=[], msg="费用确认从2026-07开始，之前不支持")
    y, m = int(year_month[:4]), int(year_month[5:7])
    month_start = date(y, m, 1)
    month_end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)

    # 查当月非驳回 DailyRecord
    records = await DailyRecord.filter(
        Q(record_date__gte=str(month_start)) & Q(record_date__lt=str(month_end))
        & ~Q(approval_status="驳回")
    ).prefetch_related("test_order")

    # 按 test_order_id 分组
    grouped = {}
    for r in records:
        tid = r.test_order_id
        if not tid:
            continue
        if tid not in grouped:
            grouped[tid] = {
                "test_order_id": tid,
                "test_order_no": r.test_order.test_order_no if r.test_order else "",
                "responsible_person": r.test_order.responsible_person if r.test_order else "",
                "engineer_hours": 0.0,
                "driver_hours": 0.0,
                "advance_total": 0.0,
                "total_amount": 0.0,
                "engineer_suppliers": set(),
                "driver_suppliers": set(),
            }
        g = grouped[tid]
        hours = float(r.normal_hours or 0) + float(r.overtime_hours or 0)
        if r.person_type == "驾驶员":
            g["driver_hours"] += hours
            if r.supplier:
                g["driver_suppliers"].add(r.supplier)
        else:
            g["engineer_hours"] += hours
            if r.supplier:
                g["engineer_suppliers"].add(r.supplier)
        g["advance_total"] += float(r.advance_payment or 0)
        g["total_amount"] += float(r.total_amount or 0)

    # 取单价（从 SupplierRate 表，按供应商取当月生效的单价）
    sr_list = await SupplierRate.all()
    rates_by_supplier = {}
    for sr in sr_list:
        rates_by_supplier.setdefault(sr.name, []).append(sr)

    def _get_unit_price(supplier_name, target_unit):
        """取单价，target_unit='hour'(元/时) 或 'day'(元/天)"""
        rates = rates_by_supplier.get(supplier_name, [])
        for r in rates:
            ef = r.effective_from
            et = r.effective_to
            if (ef is None or month_start >= ef) and (et is None or month_start <= et):
                if r.unit == target_unit:
                    return float(r.local_rate)
                if r.unit == "hour" and target_unit == "day":
                    return float(r.local_rate) * 8
                if r.unit == "day" and target_unit == "hour":
                    return float(r.local_rate) / 8
        return 0

    # 查已有的确认状态
    settlements = await MonthlySettlement.filter(year_month=year_month).all()
    settlement_map = {s.test_order_id: s for s in settlements}

    data = []
    for tid, g in grouped.items():
        # 工程师单价（元/时）、驾驶员单价（元/天）
        engineer_price = 0
        if g["engineer_suppliers"]:
            engineer_price = _get_unit_price(list(g["engineer_suppliers"])[0], "hour")
        driver_price = 0
        if g["driver_suppliers"]:
            driver_price = _get_unit_price(list(g["driver_suppliers"])[0], "day")

        # 确认状态
        s = settlement_map.get(tid)
        confirm_status = s.status if s else "待审核"
        settlement_id = s.id if s else None

        data.append({
            "test_order_id": tid,
            "test_order_no": g["test_order_no"],
            "responsible_person": g["responsible_person"],
            "engineer_hours": round(g["engineer_hours"], 1),
            "driver_hours": round(g["driver_hours"], 1),
            "advance_total": round(g["advance_total"], 2),
            "engineer_price": round(engineer_price, 2),
            "driver_price": round(driver_price, 2),
            "total_amount": round(g["total_amount"], 2),
            "confirm_status": confirm_status,
            "settlement_id": settlement_id,
            "year_month": year_month,
        })

    # 责任人筛选
    if responsible_person:
        data = [d for d in data if responsible_person in (d.get("responsible_person") or "")]

    data.sort(key=lambda x: x["test_order_no"])
    return Success(data=data)


@router.post("/update", summary="更新费用确认状态")
async def update_cost_confirmation(
    test_order_id: int = Query(...),
    year_month: str = Query(...),
    status: str = Query(..., description="待审核/已确认/更正"),
):
    # 汇总该月该试验单的费用（非驳回）
    y, m = int(year_month[:4]), int(year_month[5:7])
    month_start = date(y, m, 1)
    month_end = date(y + 1, 1, 1) if m == 12 else date(y, m + 1, 1)
    records = await DailyRecord.filter(
        Q(record_date__gte=str(month_start)) & Q(record_date__lt=str(month_end))
        & Q(test_order_id=test_order_id) & ~Q(approval_status="驳回")
    )
    total = sum(float(r.total_amount or 0) for r in records)

    exist = await MonthlySettlement.filter(
        test_order_id=test_order_id, year_month=year_month
    ).first()
    old_status = exist.status if exist else None
    if exist:
        exist.status = status
        exist.total_amount = total
        await exist.save()
    else:
        exist = await MonthlySettlement.create(
            test_order_id=test_order_id,
            year_month=year_month,
            status=status,
            total_amount=total,
        )

    # 已确认（首次确认，非重复确认）→ 累加 settlement_amount
    if status == "已确认" and old_status != "已确认":
        to = await TestOrder.filter(id=test_order_id).first()
        if to:
            old_val = float(to.settlement_amount or 0)
            await TestOrder.filter(id=test_order_id).update(settlement_amount=old_val + total)

    return Success(msg=f"状态已更新为{status}")
