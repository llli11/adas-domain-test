from typing import Optional

from app.core.crud import CRUDBase
from app.models.contractor import (
    ContractorAssessmentRecord,
    ContractorAttendance,
    ContractorEvaluation,
    ContractorPerformance,
    ContractorProject,
    ContractorResignation,
    ContractorStaff,
    ContractorVehicleStatus,
    ContractorWorkLog,
)
from app.schemas.contractor import (
    ContractorProjectCreate,
    ContractorProjectUpdate,
)
from app.schemas.contractor import (
    ContractorAssessmentRecordCreate,
    ContractorAssessmentRecordUpdate,
    ContractorAttendanceCreate,
    ContractorAttendanceUpdate,
    ContractorEvaluationCreate,
    ContractorEvaluationUpdate,
    ContractorPerformanceCreate,
    ContractorPerformanceUpdate,
    ContractorResignationCreate,
    ContractorResignationUpdate,
    ContractorStaffCreate,
    ContractorStaffUpdate,
    ContractorVehicleStatusCreate,
    ContractorVehicleStatusUpdate,
    ContractorWorkLogCreate,
    ContractorWorkLogUpdate,
)


class ContractorStaffController(CRUDBase[ContractorStaff, ContractorStaffCreate, ContractorStaffUpdate]):
    def __init__(self):
        super().__init__(model=ContractorStaff)

    async def get(self, id: int) -> Optional[ContractorStaff]:
        return await self.model.get_or_none(id=id)


class ContractorAttendanceController(CRUDBase[ContractorAttendance, ContractorAttendanceCreate, ContractorAttendanceUpdate]):
    def __init__(self):
        super().__init__(model=ContractorAttendance)

    async def get(self, id: int) -> Optional[ContractorAttendance]:
        return await self.model.get_or_none(id=id)


class ContractorVehicleStatusController(CRUDBase[ContractorVehicleStatus, ContractorVehicleStatusCreate, ContractorVehicleStatusUpdate]):
    def __init__(self):
        super().__init__(model=ContractorVehicleStatus)

    async def get(self, id: int) -> Optional[ContractorVehicleStatus]:
        return await self.model.get_or_none(id=id)


class ContractorWorkLogController(CRUDBase[ContractorWorkLog, ContractorWorkLogCreate, ContractorWorkLogUpdate]):
    def __init__(self):
        super().__init__(model=ContractorWorkLog)

    async def get(self, id: int) -> Optional[ContractorWorkLog]:
        return await self.model.get_or_none(id=id)

    async def exists(self, staff_id: int, work_date: str) -> bool:
        return await self.model.filter(staff_id=staff_id, work_date=work_date).exists()


class ContractorAssessmentRecordController(CRUDBase[ContractorAssessmentRecord, ContractorAssessmentRecordCreate, ContractorAssessmentRecordUpdate]):
    def __init__(self):
        super().__init__(model=ContractorAssessmentRecord)

    async def get(self, id: int) -> Optional[ContractorAssessmentRecord]:
        return await self.model.get_or_none(id=id)


class ContractorEvaluationController(CRUDBase[ContractorEvaluation, ContractorEvaluationCreate, ContractorEvaluationUpdate]):
    def __init__(self):
        super().__init__(model=ContractorEvaluation)

    async def get(self, id: int) -> Optional[ContractorEvaluation]:
        return await self.model.get_or_none(id=id)


class ContractorPerformanceController(CRUDBase[ContractorPerformance, ContractorPerformanceCreate, ContractorPerformanceUpdate]):
    def __init__(self):
        super().__init__(model=ContractorPerformance)

    async def get(self, id: int) -> Optional[ContractorPerformance]:
        return await self.model.get_or_none(id=id)


class ContractorResignationController(CRUDBase[ContractorResignation, ContractorResignationCreate, ContractorResignationUpdate]):
    def __init__(self):
        super().__init__(model=ContractorResignation)

    async def get(self, id: int) -> Optional[ContractorResignation]:
        return await self.model.get_or_none(id=id)


contractor_staff_controller = ContractorStaffController()
contractor_attendance_controller = ContractorAttendanceController()
contractor_vehicle_status_controller = ContractorVehicleStatusController()
contractor_work_log_controller = ContractorWorkLogController()
contractor_assessment_record_controller = ContractorAssessmentRecordController()
contractor_evaluation_controller = ContractorEvaluationController()
contractor_performance_controller = ContractorPerformanceController()
contractor_resignation_controller = ContractorResignationController()


class ContractorProjectController(CRUDBase[ContractorProject, ContractorProjectCreate, ContractorProjectUpdate]):
    def __init__(self):
        super().__init__(model=ContractorProject)

    async def get(self, id: int):
        return await self.model.get_or_none(id=id)


contractor_project_controller = ContractorProjectController()
