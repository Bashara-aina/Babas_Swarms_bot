"""core/integrations/prefect_integration.py — Prefect workflow orchestration.

Prefect provides workflow orchestration with retries, scheduling, and state
management. It wraps SwarmBot agent tasks into reliable pipelines with
automatic retry, timeout, and state persistence.

Pipeline position: wraps agent tasks with retry/scheduling on top of langgraph
Architecture:
    SwarmBot task → Prefect Flow → retry/timeout → state storage

Usage:
    from core.integrations.prefect_integration import swarmbot_flow, agent_task

    @swarmbot_flow(name="research-task", retries=2)
    async def research():
        result = await run_langgraph_task("Research AI trends")
        return result

    # Run with retry and timeout
    state = await research(return_state=True)
"""

from __future__ import annotations

import logging
import os
from functools import wraps
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

PREFECT_AVAILABLE = True

try:
    import prefect
    from prefect import flow, task
    from prefect import serve as prefect_serve
    from prefect.concurrency.sync import concurrency
except ImportError:
    PREFECT_AVAILABLE = False
    prefect = None  # type: ignore
    flow = task = prefect_serve = concurrency = None  # type: ignore


def swarmbot_flow(
    name: str | None = None,
    retries: int = 1,
    timeout_seconds: int | float = 300,
    retry_delay_seconds: int | float = 30,
    max_concurrency: int | None = None,
) -> Callable:
    """Decorator to create a Prefect flow wrapping a SwarmBot async task.

    Args:
        name: Flow name (defaults to function name)
        retries: Number of retries on failure
        timeout_seconds: Max execution time
        retry_delay_seconds: Delay between retries
        max_concurrency: Concurrency limit

    Returns:
        Decorated async function as a Prefect flow
    """
    def decorator(fn: Callable) -> Callable:
        if not PREFECT_AVAILABLE:
            return fn

        @wraps(fn)
        async def wrapper(*args, **kwargs):
            @flow(
                name=name or fn.__name__,
                retries=retries,
                timeout_seconds=timeout_seconds,
                retry_delay_seconds=retry_delay_seconds,
            )
            async def prefect_task_flow():
                return await fn(*args, **kwargs)

            if max_concurrency:
                with concurrency(max_concurrency):
                    return await prefect_task_flow()
            return await prefect_task_flow()

        return wrapper
    return decorator


def agent_task(
    name: str | None = None,
    retries: int = 1,
    timeout_seconds: int | float = 120,
    cache_policy_seconds: int | float = 3600,
) -> Callable:
    """Decorator to create a Prefect task from an agent function.

    Args:
        name: Task name
        retries: Number of retries
        timeout_seconds: Max execution time
        cache_policy_seconds: Cache result for N seconds

    Returns:
        Decorated function as a Prefect task
    """
    def decorator(fn: Callable) -> Callable:
        if not PREFECT_AVAILABLE:
            return fn

        @task(
            name=name or fn.__name__,
            retries=retries,
            timeout_seconds=timeout_seconds,
            cache_key_fn=lambda ctx, call_args: f"{name}:{str(call_args)}",
            cache_expiration=cache_policy_seconds,
        )
        async def prefect_task(*args, **kwargs):
            return await fn(*args, **kwargs)

        return prefect_task
    return decorator


async def run_with_prefect(
    flow_fn: Callable[[], Coroutine],
    name: str | None = None,
) -> Any:
    """Run an async flow function with Prefect orchestration.

    Args:
        flow_fn: Async function to wrap in Prefect flow
        name: Optional flow name

    Returns:
        Flow result
    """
    if not PREFECT_AVAILABLE:
        return await flow_fn()

    @flow(name=name or "swarmbot-orchestrated")
    async def managed_flow():
        return await flow_fn()

    return await managed_flow()


class PrefectPipeline:
    """A Prefect-based pipeline for SwarmBot multi-step tasks.

    Allows defining a pipeline of agent steps with retry, timeout,
    and state management between steps.
    """

    def __init__(
        self,
        name: str = "swarmbot-pipeline",
        retries: int = 1,
        timeout_seconds: int = 300,
    ) -> None:
        self.name = name
        self.retries = retries
        self.timeout_seconds = timeout_seconds
        self._steps: list[dict[str, Any]] = []

    def add_step(
        self,
        name: str,
        task_fn: Callable[[], Coroutine],
        retry_delay: int | float = 30,
    ) -> None:
        """Add a step to the pipeline."""
        self._steps.append({
            "name": name,
            "fn": task_fn,
            "retry_delay": retry_delay,
        })

    @task
    async def _run_step(self, step: dict[str, Any]) -> Any:
        """Internal task to run a single pipeline step."""
        return await step["fn"]()

    async def execute(self) -> list[Any]:
        """Execute the pipeline and return results for all steps."""
        if not PREFECT_AVAILABLE:
            results = []
            for step in self._steps:
                results.append(await step["fn"]())
            return results

        @flow(name=self.name, retries=self.retries, timeout_seconds=self.timeout_seconds)
        async def pipeline_flow():
            results = []
            for step in self._steps:
                try:
                    result = await self._run_step(step)
                    results.append(result)
                except Exception as exc:
                    logger.warning("Pipeline step %s failed: %s", step["name"], exc)
                    results.append(f"[step failed: {exc}]")
            return results

        return await pipeline_flow()


def create_swarmbot_deployment(
    flow_fn: Callable,
    name: str,
    schedule: str | None = None,
    tags: list[str] | None = None,
) -> str | None:
    """Create a Prefect deployment for a SwarmBot flow.

    Args:
        flow_fn: The async flow function to deploy
        name: Deployment name
        schedule: Cron-style schedule (e.g., "0 * * * *")
        tags: Optional tags for the deployment

    Returns:
        Deployment ID or None if Prefect unavailable
    """
    if not PREFECT_AVAILABLE:
        return None

    try:
        from prefect.deployments.runner import RunnerDeployment

        runner_deployment = RunnerDeployment.from_flow(
            flow=flow_fn,
            name=name,
            tags=tags or [],
        )
        await runner_deployment.apply()
        logger.info("Prefect deployment created: %s", name)
        return name
    except Exception as exc:
        logger.warning("Prefect deployment failed: %s", exc)
        return None
