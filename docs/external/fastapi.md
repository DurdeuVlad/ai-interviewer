# FastAPI — Implementation Reference

Source: https://fastapi.tiangolo.com/ (tutorial/first-steps, tutorial/cors,
tutorial/dependencies)

## Minimal app

```python
# main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

Run it (with uv):

```bash
uv run fastapi dev            # dev server with auto-reload
uv run fastapi dev main.py    # explicit entry file
```

Or directly with uvicorn:

```bash
uv run uvicorn main:app --reload --port 8000
```

Docs are auto-generated at `/docs` (Swagger UI), `/redoc`, and the raw schema
at `/openapi.json`.

## Routing

Path operation decorators mirror HTTP verbs:

```python
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}

@app.post("/items/")
async def create_item(item: Item):
    return item
```

Path parameters (`{item_id}`) are declared as typed function args; query
parameters are any other plain function args with defaults. FastAPI
validates and converts types automatically (e.g. `item_id: int` rejects
non-numeric input with a 422).

Group related routes with `APIRouter` for larger apps:

```python
# routers/interviews.py
from fastapi import APIRouter

router = APIRouter(prefix="/interviews", tags=["interviews"])

@router.get("/")
async def list_interviews():
    ...

# main.py
from routers import interviews
app.include_router(interviews.router)
```

## Request/response models via Pydantic

```python
from pydantic import BaseModel

class InterviewCreate(BaseModel):
    topic: str
    num_questions: int = 5

class InterviewOut(BaseModel):
    id: int
    topic: str
    status: str

    class Config:
        from_attributes = True  # allows returning ORM objects directly

@app.post("/interviews/", response_model=InterviewOut)
async def create_interview(payload: InterviewCreate):
    ...
```

- The request body type (`InterviewCreate`) is inferred from the parameter
  annotation — FastAPI parses and validates JSON into it automatically.
- `response_model` filters/validates the returned object and drives the
  OpenAPI schema, independent of the actual object returned by the function
  (e.g. a SQLAlchemy model instance).

## Dependency injection

Dependencies are plain callables that FastAPI invokes and injects results
of, useful for shared logic like DB sessions or pagination params:

```python
from typing import Annotated
from fastapi import Depends

async def common_parameters(q: str | None = None, skip: int = 0, limit: int = 100):
    return {"q": q, "skip": skip, "limit": limit}

@app.get("/items/")
async def read_items(commons: Annotated[dict, Depends(common_parameters)]):
    return commons
```

Typical use for a DB session per-request:

```python
from sqlalchemy.orm import Session
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/interviews/{id}")
def get_interview(id: int, db: Annotated[Session, Depends(get_db)]):
    return db.get(Interview, id)
```

Pass the dependency itself (no parentheses) to `Depends()`. Dependencies can
be `async def` or regular `def` regardless of the caller's style.

## CORS (for a separate frontend origin, e.g. Vite dev server)

```python
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:5173",   # Vite dev server default port
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Note: if `allow_credentials=True`, you cannot use `"*"` for `allow_origins`
— origins must be listed explicitly.

## Recommended small-app layout

```
backend/
  pyproject.toml
  uv.lock
  app/
    main.py            # FastAPI() instance, include_router calls, CORS setup
    database.py         # engine/session setup (SQLAlchemy)
    models.py            # SQLAlchemy ORM models
    schemas.py           # Pydantic request/response models
    routers/
      interviews.py     # APIRouter for interview endpoints
    dependencies.py      # shared Depends() callables (e.g. get_db)
```

`uvicorn`/`fastapi dev` is pointed at `app.main:app`.
