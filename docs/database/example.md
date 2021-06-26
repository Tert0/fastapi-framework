# Example

```python
from fastapi_framework.database import db, select
from fastapi import FastAPI, HTTPException
from sqlalchemy import Integer, Column, String
from typing import Union

app = FastAPI()


class User(db.Base):
    __tablename__ = "users"
    id: Union[Column, int] = Column(Integer, primary_key=True)
    name: Union[Column, str] = Column(String(255))

    @staticmethod
    async def create(name: str) -> "User":
        row = User(name=name)
        await db.add(row)
        return row


@app.get("/users")
async def get_users():
    return await db.all(select(User))


@app.get("/users/{name}")
async def get_users(name: str):
    return await db.all(select(User).filter_by(name=name))


@app.post("/users/{name}")
async def add_user(name: str) -> User:
    if await db.exists(select(User).filter_by(name=name)):
        raise HTTPException(409, "Username already used")
    user = await User.create(name)
    await db.commit()
    return user

```