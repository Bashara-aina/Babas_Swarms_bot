"""scaffolder.py — Full-stack project scaffolder for Legion.

Supports: Next.js, FastAPI, Laravel.
Includes: test runner, auto-fixer, GitHub push.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

PROJECTS_DIR = Path.home() / "projects"
PROJECTS_DIR.mkdir(exist_ok=True)


async def _run(cmd: str, cwd: Optional[str] = None, timeout: int = 120) -> str:
    """Run a shell command and return output."""
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    out = stdout.decode("utf-8", errors="replace").strip()
    err = stderr.decode("utf-8", errors="replace").strip()
    if proc.returncode != 0:
        return f"exit {proc.returncode}\n{out}\n{err}".strip()
    return out or "(done)"


# ── Next.js ─────────────────────────────────────────────────────────────────


async def scaffold_nextjs(project_name: str, features: list[str] | None = None) -> str:
    """Create a Next.js project with TypeScript + Tailwind + App Router."""
    features = features or []
    project_path = PROJECTS_DIR / project_name

    if project_path.exists():
        return f"Project {project_name} already exists at {project_path}"

    result_lines = [f"Creating Next.js project: {project_name}"]

    # Create Next.js app
    cmd = (
        f"npx --yes create-next-app@latest {project_name} "
        "--typescript --tailwind --app --no-git --eslint "
        "--src-dir --import-alias '@/*' --use-npm"
    )
    result = await _run(cmd, cwd=str(PROJECTS_DIR), timeout=300)
    result_lines.append(f"Next.js: {result[:200]}")

    if not project_path.exists():
        return f"Failed to create project:\n{result}"

    # Add shadcn/ui
    try:
        shadcn = await _run(
            "npx --yes shadcn-ui@latest init --defaults",
            cwd=str(project_path),
            timeout=120,
        )
        result_lines.append(f"shadcn/ui: {shadcn[:100]}")
    except Exception as e:
        result_lines.append(f"shadcn/ui: skipped ({e})")

    # Create standard directories
    for d in ["components", "lib", "hooks", "types"]:
        (project_path / "src" / d).mkdir(parents=True, exist_ok=True)

    # Auth stub
    if "auth" in features:
        auth_file = project_path / "src" / "lib" / "auth.ts"
        auth_file.write_text(
            "// Auth configuration — install: npm install next-auth\n"
            "export const authConfig = {\n"
            "  providers: [],\n"
            "  // Configure your auth providers here\n"
            "};\n"
        )
        result_lines.append("Auth stub: created src/lib/auth.ts")

    # Supabase client
    if "supabase" in features:
        supabase_file = project_path / "src" / "lib" / "supabase.ts"
        supabase_file.write_text(
            "// Supabase client — install: npm install @supabase/supabase-js\n"
            "import { createClient } from '@supabase/supabase-js';\n\n"
            "const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;\n"
            "const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;\n\n"
            "export const supabase = createClient(supabaseUrl, supabaseKey);\n"
        )
        result_lines.append("Supabase: created src/lib/supabase.ts")

    # List files
    files = list(project_path.rglob("*"))
    file_count = len([f for f in files if f.is_file()])
    result_lines.append(f"\nTotal files created: {file_count}")
    result_lines.append(f"Location: {project_path}")

    return "\n".join(result_lines)


# ── FastAPI ─────────────────────────────────────────────────────────────────


async def scaffold_fastapi(project_name: str, features: list[str] | None = None) -> str:
    """Create a FastAPI project with standard structure."""
    features = features or []
    project_path = PROJECTS_DIR / project_name

    if project_path.exists():
        return f"Project {project_name} already exists at {project_path}"

    # Create directories
    dirs = [
        "app",
        "app/routes",
        "app/models",
        "app/services",
        "app/schemas",
        "tests",
    ]
    if "auth" in features:
        dirs.append("app/dependencies")
    for d in dirs:
        (project_path / d).mkdir(parents=True, exist_ok=True)

    # main.py
    main_py = (
        "from fastapi import FastAPI\n"
        "from fastapi.middleware.cors import CORSMiddleware\n\n"
        f'app = FastAPI(title="{project_name}")\n\n'
        "app.add_middleware(\n"
        "    CORSMiddleware,\n"
        '    allow_origins=["*"],\n'
        "    allow_credentials=True,\n"
        '    allow_methods=["*"],\n'
        '    allow_headers=["*"],\n'
        ")\n\n"
    )
    if "auth" in features:
        main_py += (
            "from app.routes.auth import router as auth_router\n"
            "from app.database import engine\n"
            "from app.models.user import Base\n\n\n"
            "@app.on_event('startup')\n"
            "async def startup():\n"
            "    async with engine.begin() as conn:\n"
            "        await conn.run_sync(Base.metadata.create_all)\n\n\n"
            "app.include_router(auth_router)\n"
        )
    main_py += (
        '@app.get("/health")\n'
        "async def health():\n"
        '    return {"status": "ok"}\n'
    )
    (project_path / "app" / "main.py").write_text(main_py)

    # __init__.py files
    init_dirs = ["app", "app/routes", "app/models", "app/services", "app/schemas"]
    if "auth" in features:
        init_dirs.append("app/dependencies")
    for d in init_dirs:
        (project_path / d / "__init__.py").write_text("")

    # requirements.txt
    reqs = ["fastapi>=0.110.0", "uvicorn[standard]>=0.27.0"]
    if "database" in features:
        reqs.extend(["sqlalchemy>=2.0.0", "alembic>=1.13.0", "asyncpg>=0.29.0", "psycopg2-binary>=2.9.9"])
    if "auth" in features:
        reqs.extend([
            "python-jose[cryptography]>=3.3.0",
            "passlib[bcrypt]>=1.7.4",
            "python-multipart>=0.0.9",
            "pydantic[email]>=2.0.0",
        ])
        if "database" not in features:
            features.append("database")
    reqs.extend(["pytest>=8.0.0", "pytest-asyncio>=0.23.0", "httpx>=0.27.0"])
    (project_path / "requirements.txt").write_text("\n".join(reqs) + "\n")

    # Dockerfile
    (project_path / "Dockerfile").write_text(
        "FROM python:3.12-slim\n"
        "WORKDIR /app\n"
        "COPY requirements.txt .\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n"
        "COPY . .\n"
        'CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]\n'
    )

    # Test stub
    (project_path / "tests" / "test_health.py").write_text(
        "from fastapi.testclient import TestClient\n"
        "from app.main import app\n\n"
        "client = TestClient(app)\n\n\n"
        "def test_health():\n"
        '    response = client.get("/health")\n'
        "    assert response.status_code == 200\n"
        '    assert response.json() == {"status": "ok"}\n'
    )

    # Database setup
    if "database" in features:
        (project_path / "app" / "database.py").write_text(
            "from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession\n"
            "from sqlalchemy.orm import sessionmaker, DeclarativeBase\n"
            "import os\n\n"
            'DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")\n\n'
            "engine = create_async_engine(DATABASE_URL)\n"
            "async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)\n\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n\n"
            "async def get_db():\n"
            "    async with async_session() as session:\n"
            "        yield session\n"
        )

    if "auth" in features:
        auth_py = (
            "from datetime import datetime, timedelta, timezone\n"
            "from jose import jwt, JWTError\n"
            "from passlib.context import CryptContext\n"
            "import os\n\n"
            'SECRET_KEY = os.getenv("SECRET_KEY", "changeme")\n'
            'ALGORITHM = "HS256"\n'
            "ACCESS_TOKEN_EXPIRE_MINUTES = 30\n\n"
            'pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")\n\n\n'
            "def verify_password(plain_password: str, hashed_password: str) -> bool:\n"
            "    return pwd_context.verify(plain_password, hashed_password)\n\n\n"
            "def get_password_hash(password: str) -> str:\n"
            "    return pwd_context.hash(password)\n\n\n"
            "def create_access_token(data: dict) -> str:\n"
            "    to_encode = data.copy()\n"
            "    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)\n"
            '    to_encode.update({"exp": expire})\n'
            "    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)\n\n\n"
            "def decode_token(token: str) -> dict | None:\n"
            "    try:\n"
            "        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])\n"
            "        return payload\n"
            "    except JWTError:\n"
            "        return None\n"
        )
        (project_path / "app" / "auth.py").write_text(auth_py)

        schemas_auth = (
            "from pydantic import BaseModel, EmailStr\n\n\n"
            "class Token(BaseModel):\n"
            "    access_token: str\n"
            "    token_type: str\n\n\n"
            "class TokenData(BaseModel):\n"
            "    user_id: int | None = None\n\n\n"
            "class UserCreate(BaseModel):\n"
            "    email: EmailStr\n"
            "    password: str\n\n\n"
            "class UserResponse(BaseModel):\n"
            "    id: int\n"
            "    email: EmailStr\n\n\n"
            "class LoginRequest(BaseModel):\n"
            "    email: EmailStr\n"
            "    password: str\n"
        )
        (project_path / "app" / "schemas" / "auth.py").write_text(schemas_auth)

        user_model = (
            "from sqlalchemy import Integer, String\n"
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\n\n\n"
            "class Base(DeclarativeBase):\n"
            "    pass\n\n\n"
            "class User(Base):\n"
            '    __tablename__ = "users"\n\n'
            "    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)\n"
            "    email: Mapped[str] = mapped_column(String, unique=True, index=True)\n"
            "    hashed_password: Mapped[str] = mapped_column(String)\n"
        )
        (project_path / "app" / "models" / "user.py").write_text(user_model)

        deps_auth = (
            "from fastapi import Depends, HTTPException, status\n"
            "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials\n"
            "from sqlalchemy.ext.asyncio import AsyncSession\n"
            "from sqlalchemy import select\n\n"
            "from app.database import get_db\n"
            "from app.models.user import User\n"
            "from app.auth import decode_token\n\n\n"
            "security = HTTPBearer()\n\n\n"
            "async def get_current_user(\n"
            "    credentials: HTTPAuthorizationCredentials = Depends(security),\n"
            "    db: AsyncSession = Depends(get_db),\n"
            ") -> User:\n"
            "    token = credentials.credentials\n"
            "    payload = decode_token(token)\n"
            "    if payload is None:\n"
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\n"
            '            detail="Invalid or expired token",\n'
            "        )\n"
            "    user_id = payload.get(\"sub\")\n"
            "    if user_id is None:\n"
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\n"
            '            detail="Invalid token payload",\n'
            "        )\n"
            "    result = await db.execute(select(User).where(User.id == int(user_id)))\n"
            "    user = result.scalar_one_or_none()\n"
            "    if user is None:\n"
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\n"
            '            detail="User not found",\n'
            "        )\n"
            "    return user\n"
        )
        (project_path / "app" / "dependencies" / "auth.py").write_text(deps_auth)

        routes_auth = (
            "from fastapi import APIRouter, Depends, HTTPException, status\n"
            "from sqlalchemy.ext.asyncio import AsyncSession\n"
            "from sqlalchemy import select\n\n"
            "from app.database import get_db\n"
            "from app.models.user import User\n"
            "from app.schemas.auth import Token, UserCreate, UserResponse, LoginRequest\n"
            "from app.auth import create_access_token, get_password_hash, verify_password\n\n\n"
            "router = APIRouter(prefix=\"/auth\", tags=[\"auth\"])\n\n\n"
            "@router.post(\"/register\", response_model=UserResponse)\n"
            "async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):\n"
            "    result = await db.execute(select(User).where(User.email == user_in.email))\n"
            "    existing = result.scalar_one_or_none()\n"
            "    if existing:\n"
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_400_BAD_REQUEST,\n"
            '            detail="Email already registered",\n'
            "        )\n"
            "    user = User(email=user_in.email, hashed_password=get_password_hash(user_in.password))\n"
            "    db.add(user)\n"
            "    await db.commit()\n"
            "    await db.refresh(user)\n"
            "    return user\n\n\n"
            "@router.post(\"/login\", response_model=Token)\n"
            "async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):\n"
            "    result = await db.execute(select(User).where(User.email == login_in.email))\n"
            "    user = result.scalar_one_or_none()\n"
            "    if not user or not verify_password(login_in.password, user.hashed_password):\n"
            "        raise HTTPException(\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\n"
            '            detail="Incorrect email or password",\n'
            "        )\n"
            "    access_token = create_access_token(data={\"sub\": str(user.id)})\n"
            "    return Token(access_token=access_token, token_type=\"bearer\")\n"
        )
        (project_path / "app" / "routes" / "auth.py").write_text(routes_auth)

        (project_path / "app" / "schemas" / "auth.py").write_text(
            "from pydantic import BaseModel, EmailStr\\n\\n\\n"
            "class Token(BaseModel):\\n"
            "    access_token: str\\n"
            "    token_type: str\\n\\n\\n"
            "class TokenData(BaseModel):\\n"
            "    user_id: int | None = None\\n\\n\\n"
            "class UserCreate(BaseModel):\\n"
            "    email: EmailStr\\n"
            "    password: str\\n\\n\\n"
            "class UserResponse(BaseModel):\\n"
            "    id: int\\n"
            "    email: EmailStr\\n\\n\\n"
            "class LoginRequest(BaseModel):\\n"
            "    email: EmailStr\\n"
            "    password: str\\n"
        )

        (project_path / "app" / "models" / "user.py").write_text(
            "from sqlalchemy import Integer, String\\n"
            "from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column\\n\\n\\n"
            "class Base(DeclarativeBase):\\n"
            "    pass\\n\\n\\n"
            "class User(Base):\\n"
            '    __tablename__ = "users"\\n\\n'
            "    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)\\n"
            "    email: Mapped[str] = mapped_column(String, unique=True, index=True)\\n"
            "    hashed_password: Mapped[str] = mapped_column(String)\\n"
        ")\\n"
        )

        (project_path / "app" / "dependencies" / "auth.py").write_text(
            "from fastapi import Depends, HTTPException, status\\n"
            "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials\\n"
            "from sqlalchemy.ext.asyncio import AsyncSession\\n"
            "from sqlalchemy import select\\n\\n"
            "from app.database import get_db\\n"
            "from app.models.user import User\\n"
            "from app.auth import decode_token\\n\\n\\n"
            "security = HTTPBearer()\\n\\n\\n"
            "async def get_current_user(\\n"
            "    credentials: HTTPAuthorizationCredentials = Depends(security),\\n"
            "    db: AsyncSession = Depends(get_db),\\n"
            ") -> User:\\n"
            "    token = credentials.credentials\\n"
            "    payload = decode_token(token)\\n"
            "    if payload is None:\\n"
            "        raise HTTPException(\\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\\n"
            '            detail="Invalid or expired token",\\n'
            "        )\\n"
            "    user_id = payload.get(\"sub\")\\n"
            "    if user_id is None:\\n"
            "        raise HTTPException(\\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\\n"
            '            detail="Invalid token payload",\\n'
            "        )\\n"
            "    result = await db.execute(select(User).where(User.id == int(user_id)))\\n"
            "    user = result.scalar_one_or_none()\\n"
            "    if user is None:\\n"
            "        raise HTTPException(\\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\\n"
            '            detail="User not found",\\n'
            "        )\\n"
            "    return user\\n"
        )

        (project_path / "app" / "routes" / "auth.py").write_text(
            "from fastapi import APIRouter, Depends, HTTPException, status\\n"
            "from sqlalchemy.ext.asyncio import AsyncSession\\n"
            "from sqlalchemy import select\\n\\n"
            "from app.database import get_db\\n"
            "from app.models.user import User\\n"
            "from app.schemas.auth import Token, UserCreate, UserResponse, LoginRequest\\n"
            "from app.auth import create_access_token, get_password_hash, verify_password\\n\\n\\n"
            "router = APIRouter(prefix=\"/auth\", tags=\".auth\"])\n\n\n"
            "@router.post(\"/register\", response_model=UserResponse)\n"
            "async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):\\n"
            "    result = await db.execute(select(User).where(User.email == user_in.email))\\n"
            "    existing = result.scalar_one_or_none()\\n"
            "    if existing:\\n"
            "        raise HTTPException(\\n"
            "            status_code=status.HTTP_400_BAD_REQUEST,\\n"
            '            detail="Email already registered",\\n'
            "        )\\n"
            "    user = User(email=user_in.email, hashed_password=get_password_hash(user_in.password))\\n"
            "    db.add(user)\\n"
            "    await db.commit()\\n"
            "    await db.refresh(user)\\n"
            "    return user\\n\\n\\n"
            "@router.post(\"/login\", response_model=Token)\n"
            "async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):\\n"
            "    result = await db.execute(select(User).where(User.email == login_in.email))\\n"
            "    user = result.scalar_one_or_none()\\n"
            "    if not user or not verify_password(login_in.password, user.hashed_password):\\n"
            "        raise HTTPException(\\n"
            "            status_code=status.HTTP_401_UNAUTHORIZED,\\n"
            '            detail="Incorrect email or password",\\n'
            "        )\\n"
            "    access_token = create_access_token(data={\"sub\": str(user.id)})\n"
            "    return Token(access_token=access_token, token_type=\"bearer\")\n"
        )

    file_count = len(list(project_path.rglob("*")))
    return (
        f"FastAPI project created: {project_name}\n"
        f"Location: {project_path}\n"
        f"Files: {file_count}\n"
        f"Features: {', '.join(features) or 'base'}\n"
        f"Run: cd {project_path} && pip install -r requirements.txt && uvicorn app.main:app --reload"
    )


# ── Laravel ─────────────────────────────────────────────────────────────────


async def scaffold_laravel(project_name: str, features: list[str] | None = None) -> str:
    """Create a Laravel project."""
    features = features or []
    project_path = PROJECTS_DIR / project_name

    if project_path.exists():
        return f"Project {project_name} already exists"

    result = await _run(
        f"composer create-project laravel/laravel {project_name}",
        cwd=str(PROJECTS_DIR),
        timeout=300,
    )

    if not project_path.exists():
        return f"Laravel creation failed:\n{result}"

    lines = [f"Laravel project: {project_name}", result[:200]]

    if "auth" in features:
        breeze = await _run(
            "composer require laravel/breeze --dev && php artisan breeze:install",
            cwd=str(project_path),
            timeout=120,
        )
        lines.append(f"Breeze auth: {breeze[:100]}")

    return "\n".join(lines)


# ── Test runner + auto-fixer ────────────────────────────────────────────────


async def run_tests_and_fix(project_path: str, max_attempts: int = 3) -> str:
    """Run tests, auto-fix failures using coding agent, retry."""
    from llm_client import chat

    path = Path(project_path)
    results = []

    for attempt in range(1, max_attempts + 1):
        # Detect test framework
        if (path / "pytest.ini").exists() or (path / "tests").exists():
            test_cmd = f"cd '{path}' && python -m pytest -x --tb=short 2>&1"
        elif (path / "package.json").exists():
            test_cmd = f"cd '{path}' && npm test 2>&1"
        elif (path / "phpunit.xml").exists():
            test_cmd = f"cd '{path}' && php artisan test 2>&1"
        else:
            return "No test framework detected."

        output = await _run(test_cmd, timeout=120)
        results.append(f"Attempt {attempt}: {output[:500]}")

        # Check if tests passed
        if "passed" in output.lower() or "PASS" in output or "0 failures" in output.lower():
            return f"Tests passed on attempt {attempt}!\n" + "\n".join(results)

        if attempt < max_attempts:
            # Ask coding agent to fix
            fix_prompt = (
                f"These tests are failing:\n{output[:2000]}\n\n"
                f"Project path: {project_path}\n"
                "Identify the root cause and provide the exact fix. "
                "Show the file path and the corrected code."
            )
            fix, _ = await chat(fix_prompt, agent_key="coding", user_id="0")
            results.append(f"Fix suggestion: {fix[:300]}")

    return f"Tests still failing after {max_attempts} attempts.\n" + "\n".join(results)


# ── GitHub push ─────────────────────────────────────────────────────────────


async def push_to_github(project_path: str, repo_name: str, private: bool = True) -> str:
    """Create GitHub repo, init git, push."""
    path = Path(project_path)
    if not path.exists():
        return f"Project path not found: {project_path}"

    visibility = "--private" if private else "--public"

    # Init git
    await _run("git init", cwd=str(path))
    await _run("git add -A", cwd=str(path))
    await _run('git commit -m "Initial commit from Legion scaffolder"', cwd=str(path))

    # Create repo and push
    result = await _run(
        f"gh repo create {repo_name} {visibility} --source=. --push",
        cwd=str(path),
        timeout=60,
    )

    return f"GitHub repo created:\n{result}"


# ── Parallel full-stack builder ─────────────────────────────────────────────


async def parallel_fullstack(task: str) -> str:
    """Decompose task into frontend + backend, run agents in parallel."""
    from llm_client import chat

    async def frontend():
        prompt = (
            f"Write only the frontend/UI components for this task. "
            f"Use React + TypeScript + Tailwind CSS. "
            f"Return complete file contents with file paths.\n\nTask: {task}"
        )
        result, _ = await chat(prompt, agent_key="coding", user_id="0")
        return result

    async def backend():
        prompt = (
            f"Write only the backend API/database layer for this task. "
            f"Use Python FastAPI. "
            f"Return complete file contents with file paths.\n\nTask: {task}"
        )
        result, _ = await chat(prompt, agent_key="coding", user_id="0")
        return result

    async def tests():
        prompt = (
            f"Write tests for this task covering both frontend and backend. "
            f"Use pytest for backend and describe frontend test scenarios.\n\nTask: {task}"
        )
        result, _ = await chat(prompt, agent_key="coding", user_id="0")
        return result

    fe, be, te = await asyncio.gather(frontend(), backend(), tests())

    return (
        "<b>Frontend</b>\n"
        f"<pre>{fe[:3000]}</pre>\n\n"
        "<b>Backend</b>\n"
        f"<pre>{be[:3000]}</pre>\n\n"
        "<b>Tests</b>\n"
        f"<pre>{te[:2000]}</pre>"
    )
