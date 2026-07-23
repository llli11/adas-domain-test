from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.tool import Tool, ToolBorrow, ToolInventory, ToolInventoryDetail, ToolRequirement
from app.schemas.tool import (
    ToolCreate,
    ToolUpdate,
    ToolBorrowCreate,
    ToolBorrowUpdate,
    ToolInventoryCreate,
    ToolInventoryUpdate,
    ToolInventoryDetailCreate,
    ToolRequirementCreate,
    ToolRequirementUpdate,
)


class ToolController(CRUDBase[Tool, ToolCreate, ToolUpdate]):
    def __init__(self):
        super().__init__(model=Tool)

    async def search_tools(
        self,
        tool_code: str = None,
        tool_name: str = None,
        tool_type: str = None,
        status: str = None,
        current_user: str = None,
    ):
        q = Q()
        if tool_code:
            q &= Q(tool_code__contains=tool_code)
        if tool_name:
            q &= Q(tool_name__contains=tool_name)
        if tool_type:
            q &= Q(tool_type__contains=tool_type)
        if status:
            q &= Q(status=status)
        if current_user:
            q &= Q(current_user__contains=current_user)
        return await self.model.filter(q).order_by("-id")


tool_controller = ToolController()


class ToolBorrowController(CRUDBase[ToolBorrow, ToolBorrowCreate, ToolBorrowUpdate]):
    def __init__(self):
        super().__init__(model=ToolBorrow)

    async def search_borrows(
        self,
        tool_code: str = None,
        tool_name: str = None,
        borrower_name: str = None,
        status: str = None,
        approve_status: str = None,
    ):
        q = Q()
        if tool_code:
            q &= Q(tool_code__contains=tool_code)
        if tool_name:
            q &= Q(tool_name__contains=tool_name)
        if borrower_name:
            q &= Q(borrower_name__contains=borrower_name)
        if status:
            q &= Q(status=status)
        if approve_status:
            q &= Q(approve_status=approve_status)
        return await self.model.filter(q).order_by("-id")


tool_borrow_controller = ToolBorrowController()


class ToolInventoryController(CRUDBase[ToolInventory, ToolInventoryCreate, ToolInventoryUpdate]):
    def __init__(self):
        super().__init__(model=ToolInventory)

    async def search_inventories(
        self,
        task_code: str = None,
        task_name: str = None,
        status: str = None,
    ):
        q = Q()
        if task_code:
            q &= Q(task_code__contains=task_code)
        if task_name:
            q &= Q(task_name__contains=task_name)
        if status:
            q &= Q(status=status)
        return await self.model.filter(q).order_by("-id")


tool_inventory_controller = ToolInventoryController()


class ToolInventoryDetailController(CRUDBase[ToolInventoryDetail, ToolInventoryDetailCreate, ToolInventoryDetailCreate]):
    def __init__(self):
        super().__init__(model=ToolInventoryDetail)

    async def get_details_by_inventory(self, inventory_id: int):
        return await self.model.filter(inventory_id=inventory_id).order_by("id")


tool_inventory_detail_controller = ToolInventoryDetailController()


class ToolRequirementController(CRUDBase[ToolRequirement, ToolRequirementCreate, ToolRequirementUpdate]):
    def __init__(self):
        super().__init__(model=ToolRequirement)

    async def search_requirements(
        self,
        tool_name: str = None,
        tool_type: str = None,
        requester_name: str = None,
        status: str = None,
    ):
        q = Q()
        if tool_name:
            q &= Q(tool_name__contains=tool_name)
        if tool_type:
            q &= Q(tool_type__contains=tool_type)
        if requester_name:
            q &= Q(requester_name__contains=requester_name)
        if status:
            q &= Q(status=status)
        return await self.model.filter(q).order_by("-id")


tool_requirement_controller = ToolRequirementController()
