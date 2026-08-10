"""定时任务调度器：每日凌晨2点自动同步飞书考勤数据"""
import asyncio
import datetime
from datetime import timedelta

from app.log import logger


class DailySyncScheduler:
    """轻量级每日定时同步调度器"""

    def __init__(self):
        self._task: asyncio.Task = None
        self._running = False

    async def _wait_until_next_2am(self):
        """等待到下一个凌晨2点"""
        now = datetime.datetime.now()
        next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)
        if now >= next_run:
            next_run += datetime.timedelta(days=1)
        wait_seconds = (next_run - now).total_seconds()
        logger.info(
            f"[Scheduler] 下一次飞书自动同步将在 {next_run.strftime('%Y-%m-%d %H:%M:%S')} 执行"
        )
        await asyncio.sleep(wait_seconds)

    async def _run_sync(self):
        """执行飞书自动同步：考勤数据 → 每日费用记录"""
        try:
            from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
            from app.api.v1.expense.expense import _auto_sync_daily
            from app.models.expense import Personnel

            logger.info("[Scheduler] === 开始凌晨2点飞书自动同步 ===")

            ten_days_ago = (datetime.datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
            config = EXPENSE_FEISHU_CONFIG

            # 第一步：从飞书考勤表同步考勤数据到本地
            personnel_records = await Personnel.all()
            token_to_test_order = {
                r.personnel_record_id: r.test_order_no
                for r in personnel_records if r.personnel_record_id and r.test_order_no
            }
            person_to_test_order = {}
            project_to_test_order = {}
            for r in personnel_records:
                if r.person_name and r.test_order_no:
                    entries = person_to_test_order.setdefault(r.person_name, [])
                    entries.append({
                        "test_order_no": r.test_order_no,
                        "start_date": None,
                        "end_date": None,
                    })
                if r.vehicle_project_text and r.test_order_no:
                    project_entries = project_to_test_order.setdefault(r.vehicle_project_text, [])
                    project_entries.append({
                        "test_order_no": r.test_order_no,
                        "start_date": None,
                        "end_date": None,
                    })

            # 同步工程师考勤
            try:
                eng_result = await feishu_sync_service.sync_expense_from_feishu(
                    table_id=config["TABLE_IDS"]["ENGINEER"],
                    record_type="engineer",
                    date_start=ten_days_ago,
                    token_to_test_order=token_to_test_order,
                    person_to_test_order=person_to_test_order,
                    project_to_test_order=project_to_test_order,
                )
                logger.info(f"[Scheduler] 工程师考勤同步完成: {eng_result}")
            except Exception as e:
                logger.error(f"[Scheduler] 工程师考勤同步失败: {e}", exc_info=True)

            # 同步驾驶员考勤
            try:
                drv_result = await feishu_sync_service.sync_expense_from_feishu(
                    table_id=config["TABLE_IDS"]["DRIVER"],
                    record_type="driver",
                    date_start=ten_days_ago,
                    token_to_test_order=token_to_test_order,
                    person_to_test_order=person_to_test_order,
                    project_to_test_order=project_to_test_order,
                )
                logger.info(f"[Scheduler] 驾驶员考勤同步完成: {drv_result}")
            except Exception as e:
                logger.error(f"[Scheduler] 驾驶员考勤同步失败: {e}", exc_info=True)

            # 第二步：处理考勤数据 → 生成每日费用记录
            try:
                await _auto_sync_daily()
                logger.info("[Scheduler] 每日费用记录生成完成")
            except Exception as e:
                logger.error(f"[Scheduler] 每日费用记录生成失败: {e}", exc_info=True)

            logger.info("[Scheduler] === 凌晨2点飞书自动同步全部完成 ===")
        except Exception as e:
            logger.error(f"[Scheduler] 飞书自动同步整体失败: {e}", exc_info=True)

    async def start(self):
        """启动调度器（后台运行）"""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())
        logger.info("[Scheduler] 调度器已启动，将在每日凌晨2点自动同步飞书数据")

    async def _loop(self):
        """主循环：每天2点执行一次"""
        while self._running:
            try:
                await self._wait_until_next_2am()
                await self._run_sync()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Scheduler] 调度器循环异常: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def stop(self):
        """停止调度器"""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


# 全局调度器实例
daily_scheduler = DailySyncScheduler()
