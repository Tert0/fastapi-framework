# Models

The Tutorial for SQLAlchemy Models can befound [here](https://docs.sqlalchemy.org/en/14/tutorial/metadata.html#declaring-mapped-classes).

A Model class should inherit from `fastapi_framework.db.Base`

To create the Models Async in your Code you could 
add this async function to your models:

```python
from fastapi_framework import db


class MyModel(db.Base):
    # your model code
    @staticmethod
    async def create(param: int, param2: str) -> "MyModel":
        row = MyModel(param=param, param2=param2)
        await db.add(row)
        return row
```