# Insert, Delete and Modify Data

## Insert Data

With `db.add` you can insert Date into the Database

```python
from fastapi_framework.database import db

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    obj: MyModel = MyModel(x=1)
    await db.add(obj)
```

## Delete Data

With `db.delete` you can delete Data from your Database

```python
from fastapi_framework.database import db, select

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    model: MyModel = await select(MyModel).filter_by(x=1)
    await db.delete(model)
```

## Modify Data

You can modify Data in your Database by change the Model Class Attribute

```python
from fastapi_framework.database import db, select

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    model: MyModel = await select(MyModel).filter_by(x=1)
    model.x = 1
```
