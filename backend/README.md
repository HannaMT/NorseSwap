# 🎓 CampusLoop — FastAPI Backend

**Learn Python backend development by building a real product.**

---

## Why FastAPI?

| Feature | Node.js/Express | FastAPI |
|---------|----------------|---------|
| Auto API docs | ❌ Manual (Swagger setup) | ✅ Auto-generated at `/docs` |
| Request validation | ❌ Manual (express-validator) | ✅ Automatic (Pydantic) |
| Type safety | ⚠️ TypeScript optional | ✅ Built-in Python types |
| Performance | Fast | Faster (async + Starlette) |
| Learning curve | Low | Low-Medium |
| AI/ML integration | Limited | Native (same language) |

---

## Project Structure

```
campusloop-fastapi/
├── run.py                    # Start the server (like `node src/index.js`)
├── requirements.txt          # Dependencies (like package.json)
├── .env.example              # Environment variables template
│
└── app/
    ├── main.py               # FastAPI app + middleware + router registration
    │
    ├── core/
    │   ├── config.py         # Settings loaded from .env (like dotenv in Node)
    │   ├── database.py       # DB connection + session (like Prisma client)
    │   ├── security.py       # JWT, bcrypt, .edu validation
    │   └── dependencies.py   # FastAPI dependency injection (like Express middleware)
    │
    ├── models/
    │   └── models.py         # SQLAlchemy DB models (like Prisma schema.prisma)
    │
    ├── schemas/
    │   └── schemas.py        # Pydantic request/response shapes (validation + serialization)
    │
    ├── routers/
    │   ├── auth.py           # POST /auth/register, /login, /verify-email, etc.
    │   ├── listings.py       # GET/POST/PATCH/DELETE /listings
    │   ├── rentals.py        # POST /rentals, /respond, /return
    │   ├── orders.py         # Marketplace buy/sell
    │   ├── services.py       # Service bookings
    │   ├── messages.py       # WebSocket + REST messaging
    │   ├── reviews.py        # Reviews & ratings
    │   ├── notifications.py  # In-app notifications
    │   ├── payments.py       # Stripe payment intents + Connect
    │   ├── reports.py        # Report listings
    │   └── users.py          # User profiles
    │
    └── utils/
        ├── email.py          # Send emails (fastapi-mail)
        └── cloudinary.py     # Upload images
```

---

## Quick Start

### 1. Install Python 3.11+
```bash
# macOS
brew install python@3.11

# Ubuntu/Debian
sudo apt install python3.11
```

### 2. Create a virtual environment
```bash
# LEARN: Virtual environments isolate Python packages per project
# It's like having a separate node_modules per project, but explicit
python3 -m venv venv

# Activate it (do this every time you open a terminal)
source venv/bin/activate     # Mac/Linux
.\venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Open .env and fill in your DATABASE_URL, JWT_SECRET, etc.
```

### 5. Set up PostgreSQL
```bash
# Create the database
createdb campusloop_db

# Run migrations (creates all tables)
# Option A: Let FastAPI create tables on startup (development only)
# Option B: Use Alembic for proper migrations (recommended)
alembic upgrade head
```

### 6. Start the server
```bash
python run.py
# OR
uvicorn app.main:app --reload
```

Visit **http://localhost:8000/docs** — your interactive API docs are ready! 🎉

---

## 🎓 Learning Path: Node.js → Python/FastAPI

### Concept Mapping

| Node.js / Express | Python / FastAPI |
|---|---|
| `package.json` | `requirements.txt` |
| `npm install` | `pip install -r requirements.txt` |
| `process.env.VAR` | `settings.VAR` (Pydantic BaseSettings) |
| `express()` | `FastAPI()` |
| `app.use(middleware)` | `app.add_middleware(...)` |
| `app.use('/route', router)` | `app.include_router(router)` |
| `req.body` | Function parameter with type hint |
| `res.json({...})` | `return {...}` |
| `res.status(201).json({...})` | `@router.post("", status_code=201)` |
| `async (req, res) => {}` | `async def route_name(...):` |
| `await db.findMany({...})` | `await db.execute(select(Model)...)` |
| `req.user` | `current_user: User = Depends(get_current_user)` |
| `next()` | `yield` in dependency |
| Prisma schema | SQLAlchemy models (`class User(Base):`) |
| Zod / express-validator | Pydantic (`class UserRegister(BaseModel):`) |
| bcryptjs | passlib (`pwd_context.hash(password)`) |
| jsonwebtoken | python-jose (`jwt.encode(payload, secret)`) |
| nodemailer | fastapi-mail |
| Socket.IO | Native WebSockets (`@router.websocket("/ws")`) |

### Python Syntax Cheatsheet for JS Developers

```python
# Variables — no let/const/var needed
name = "Alice"
age = 21

# Functions
def greet(name: str) -> str:        # type hints are optional but helpful
    return f"Hello, {name}!"        # f-strings = template literals

# Async functions
async def fetch_user(user_id: str):
    result = await db.execute(...)  # await works the same as JS
    return result

# Lists (like arrays)
tags = ["textbooks", "cs", "mit"]
tags.append("algorithms")           # .push() equivalent

# Dicts (like objects)
user = {"id": "123", "name": "Alice"}
user["email"] = "alice@mit.edu"     # add a key

# None = null/undefined
avatar: Optional[str] = None        # can be a string or None

# Type checking
if isinstance(value, str):          # like typeof in JS
    print("It's a string")

# List comprehension (common Python pattern — no equivalent in JS)
prices = [item.price for item in items if item.price > 10]
# Same as: items.filter(i => i.price > 10).map(i => i.price)

# f-strings (template literals)
message = f"Hello {user.first_name}, your total is ${total:.2f}"

# Unpacking (like destructuring)
first, *rest = [1, 2, 3, 4]         # first = 1, rest = [2, 3, 4]

# Error handling
try:
    result = risky_operation()
except ValueError as e:
    print(f"Value error: {e}")
except Exception as e:
    raise HTTPException(500, "Something went wrong")
finally:
    cleanup()
```

---

## API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication
All protected routes require: `Authorization: Bearer <access_token>`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | — | Register with .edu email |
| GET | `/auth/verify-email/{token}` | — | Verify email |
| POST | `/auth/login` | — | Login → returns JWT |
| POST | `/auth/refresh` | — | Refresh access token |
| POST | `/auth/forgot-password` | — | Request password reset |
| POST | `/auth/reset-password` | — | Reset password |
| GET | `/auth/me` | ✅ | Get current user |

### Listings
| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/listings` | Optional | Browse (filterable) |
| GET | `/listings/{id}` | Optional | Listing detail |
| GET | `/listings/me` | ✅ Verified | My listings |
| POST | `/listings` | ✅ Verified | Create listing + images |
| PATCH | `/listings/{id}` | ✅ Owner | Update listing |
| DELETE | `/listings/{id}` | ✅ Owner | Soft delete |
| POST | `/listings/{id}/save` | ✅ | Toggle save |

**Query filters:** `type`, `category`, `university`, `search`, `min_price`, `max_price`, `page`, `sort_by`

### Rentals, Orders, Services, Messages, etc.
See full docs at **http://localhost:8000/docs** when running.

### WebSocket (Real-time Messaging)
```javascript
// Client connection
const ws = new WebSocket("ws://localhost:8000/api/v1/messages/ws?token=YOUR_JWT");

// Send a message
ws.send(JSON.stringify({
  type: "send_message",
  conversation_id: "conv-123",
  content: "Hey, is the bike still available?"
}));

// Events you receive:
// { type: "new_message", message: {...} }
// { type: "typing_start", user_id: "...", name: "Alice" }
// { type: "typing_stop", ... }
```

---

## Database Migrations with Alembic

```bash
# LEARN: Alembic is Python's equivalent of Prisma migrations

# Create a new migration after changing models
alembic revision --autogenerate -m "add avatar_url to users"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# See migration history
alembic history
```

---

## Deployment

### Recommended Stack
- **API**: Railway or Render (supports Python natively)
- **Database**: Supabase or Neon (managed PostgreSQL)
- **Images**: Cloudinary (already integrated)

### Dockerfile (ready for production)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Next Steps to Learn

1. **Read `app/routers/auth.py`** — start here, every concept is explained inline
2. **Read `app/core/dependencies.py`** — understand dependency injection
3. **Read `app/models/models.py`** — understand SQLAlchemy vs Prisma
4. **Read `app/schemas/schemas.py`** — understand Pydantic validation
5. **Visit `/docs`** — test every endpoint interactively
6. **Add Alembic** — set up proper database migrations
7. **Add Redis** — scale the WebSocket manager for multiple servers
8. **Add pytest** — write tests for each router
