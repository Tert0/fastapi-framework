# Query

Function for Database Query are 
```python
from fastapi_framework.database import select, filter_by
```

## Select

```python
from fastapi_framework.database import db, select

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    query = select(MyModel) # Selects all from the MyModel table
```

## Filter By

`filter_by(Model, criteria)` is a shortcut for `select(Model).filer_by(criteria)`

```python
from fastapi_framework.database import db, select, filter_by

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    query = filter_by(MyModel, id=1) # Selects all from the MyModel table where id is 1
    # Same here:
    query = select(MyModel).filter_by(id=1)
```

## Execute Querys

### Get First Element

Returns the first Result for the Query.
Could be `None`

```python
from fastapi_framework.database import db, select

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    query = select(MyModel) # Your Query
    result: MyModel = await db.first(query)
```

### Get All Element
Returns all results for the query.
Could be `[]`
```python
from fastapi_framework.database import db, select

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    query = select(MyModel) # Your Query
    result: list[MyModel] = await db.all(query)
```

### Check Exists

Checks if data for this query exists

```python
from fastapi_framework.database import db, select

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    query = select(MyModel) # Your Query
    exists: bool = await db.exists(query)
```

### Count Results

Returns count of matching rows for the query

```python
from fastapi_framework.database import db, select

class MyModel(db.Base):
    # The Model Code
    pass

async def main():
    query = select(MyModel) # Your Query
    count: int = await db.count(query)
```

