from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

from core.structured_outputs import CodeResult
from llm_client import chat


async def _run_python_safely(code: str, timeout: int = 30) -> CodeResult:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="code_exec_") as tmpdir:
        file_path = Path(tmpdir) / "task.py"
        file_path.write_text(code, encoding="utf-8")
        proc = await asyncio.create_subprocess_exec(
            "python3",
            str(file_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return CodeResult(
                code=code,
                stdout=(stdout or b"").decode("utf-8", errors="ignore")[:12000],
                stderr=(stderr or b"").decode("utf-8", errors="ignore")[:12000],
                exit_code=int(proc.returncode or 0),
                execution_time_ms=(time.perf_counter() - started) * 1000.0,
            )
        except TimeoutError:
            proc.kill()
            return CodeResult(
                code=code,
                stdout="",
                stderr="Execution timed out after 30s",
                exit_code=124,
                execution_time_ms=(time.perf_counter() - started) * 1000.0,
            )


async def run_code_agent(task: str) -> CodeResult:
    prompt = (
        "Generate ONLY runnable Python code to solve this task. "
        "Do not wrap in markdown fences.\n\n"
        f"Task: {task}"
    )
    generated, _ = await chat(prompt, agent_key="coding", user_id="code_exec")
    code = generated.strip()
    if code.startswith("```"):
        code = code.strip("`")
        if code.lower().startswith("python"):
            code = code[6:].lstrip()
    return await _run_python_safely(code)
