"""from typing import Union

from sqlalchemy import String, Column, Integer

from database import database_dependency


class PermissionsModel(database_dependency.db.Base):
    name: Union[str, Column] = Column(String(255), primary_key=True)
    default: Union[int, Column] = Column(Integer)


class PermissionConnectionModel(database_dependency.db.Base):
    pass
"""
