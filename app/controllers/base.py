from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from tortoise.models import Model
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, id: Any) -> Optional[ModelType]:
        return await self.model.filter(id=id).first()

    async def list(self) -> List[ModelType]:
        return await self.model.all()

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        obj_in_data = dict(obj_in)
        return await self.model.create(**obj_in_data)

    async def update(self, id: Any, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> Optional[ModelType]:
        db_obj = await self.get(id=id)
        if db_obj:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            await db_obj.update_from_dict(update_data)
            await db_obj.save()
        return db_obj

    async def remove(self, id: Any) -> bool:
        deleted_count = await self.model.filter(id=id).delete()
        return deleted_count > 0