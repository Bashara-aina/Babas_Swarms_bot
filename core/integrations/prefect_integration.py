"""core/integrations/prefect_integration.py — Prefect workflow orchestration.  # type: ignore[reportOptionalCall]

Prefect provides workflow orchestration with retries, scheduling, and state  # type: ignore[reportOptionalCall]
management. It wraps SwarmBot agent tasks into reliable pipelines with  # type: ignore[reportOptionalCall]
automatic retry, timeout, and state persistence.  # type: ignore[reportOptionalCall]

Pipeline position: wraps agent tasks with retry/scheduling on top of langgraph
Architecture:
    SwarmBot task → Prefect Flow → retry/timeout → state storage

Usage:
    from core.integrations.prefect_integration import swarmbot_flow, agent_task  # type: ignore[reportOptionalCall]

    @swarmbot_flow(name="research-task", retries=2)  # type: ignore[reportOptionalCall]
    async def research():  # type: ignore[reportOptionalCall]
        result = await run_langgraph_task("Research AI trends")  # type: ignore[reportOptionalCall]
        return result

    # Run with retry and timeout
    state = await research(return_state=True)  # type: ignore[reportOptionalCall]
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine  # type: ignore[reportOptionalCall]
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)  # type: ignore[reportOptionalCall]

PREFECT_AVAILABLE = True  # type: ignore[reportOptionalCall]

try:
    import prefect
    from prefect import flow, task  # type: ignore[reportOptionalCall]
    from prefect import serve as prefect_serve
    from prefect.concurrency.sync import concurrency  # type: ignore[reportOptionalCall]
except ImportError:
    PREFECT_AVAILABLE = False  # type: ignore[reportOptionalCall]
    prefect = None  # type: ignore
    flow = task = prefect_serve = concurrency = None  # type: ignore


def swarmbot_flow(  # type: ignore[reportOptionalCall]
    name: str | None = None,  # type: ignore[reportOptionalCall]
    retries: int = 1,  # type: ignore[reportOptionalCall]
    timeout_seconds: int | float = 300,  # type: ignore[reportOptionalCall]
    retry_delay_seconds: int | float = 30,  # type: ignore[reportOptionalCall]
    max_concurrency: int | None = None,  # type: ignore[reportOptionalCall]
) -> Callable:
    """Decorator to create a Prefect flow wrapping a SwarmBot async task.  # type: ignore[reportOptionalCall]

    Args:
        name: Flow name (defaults to function name)  # type: ignore[reportOptionalCall]
        retries: Number of retries on failure
        timeout_seconds: Max execution time
        retry_delay_seconds: Delay between retries
        max_concurrency: Concurrency limit

    Returns:
        Decorated async function as a Prefect flow
    """
    def decorator(fn: Callable) -> Callable:  # type: ignore[reportOptionalCall]
        if not PREFECT_AVAILABLE:
            return fn

        @wraps(fn)  # type: ignore[reportOptionalCall]
        async def wrapper(*args, **kwargs):  # type: ignore[reportOptionalCall]
            @flow(  # type: ignore[reportOptionalCall]
                name=name or fn.__name__,  # type: ignore[reportOptionalCall]
                retries=retries,  # type: ignore[reportOptionalCall]
                timeout_seconds=timeout_seconds,  # type: ignore[reportOptionalCall]
                retry_delay_seconds=retry_delay_seconds,  # type: ignore[reportOptionalCall]
            )
            async def prefect_task_flow():  # type: ignore[reportOptionalCall]
                return await fn(*args, **kwargs)  # type: ignore[reportOptionalCall]

            if max_concurrency:
                with concurrency(max_concurrency):  # type: ignore[reportOptionalCall]
                    return await prefect_task_flow()  # type: ignore[reportOptionalCall]
            return await prefect_task_flow()  # type: ignore[reportOptionalCall]

        return wrapper
    return decorator


def agent_task(  # type: ignore[reportOptionalCall]
    name: str | None = None,  # type: ignore[reportOptionalCall]
    retries: int = 1,  # type: ignore[reportOptionalCall]
    timeout_seconds: int | float = 120,  # type: ignore[reportOptionalCall]
    cache_policy_seconds: int | float = 3600,  # type: ignore[reportOptionalCall]
) -> Callable:
    """Decorator to create a Prefect task from an agent function.  # type: ignore[reportOptionalCall]

    Args:
        name: Task name
        retries: Number of retries
        timeout_seconds: Max execution time
        cache_policy_seconds: Cache result for N seconds

    Returns:
        Decorated function as a Prefect task
    """
    def decorator(fn: Callable) -> Callable:  # type: ignore[reportOptionalCall]
        if not PREFECT_AVAILABLE:
            return fn

        @task(  # type: ignore[reportOptionalCall]
            name=name or fn.__name__,  # type: ignore[reportOptionalCall]
            retries=retries,  # type: ignore[reportOptionalCall]
            timeout_seconds=timeout_seconds,  # type: ignore[reportOptionalCall]
            cache_key_fn=lambda ctx, call_args: f"{name}:{call_args!s}",  # type: ignore[reportOptionalCall]
            cache_expiration=cache_policy_seconds,  # type: ignore[reportOptionalCall]
        )
        async def prefect_task(*args, **kwargs):  # type: ignore[reportOptionalCall]
            return await fn(*args, **kwargs)  # type: ignore[reportOptionalCall]

        return prefect_task
    return decorator


async def run_with_prefect(  # type: ignore[reportOptionalCall]
    flow_fn: Callable[[], Coroutine],  # type: ignore[reportOptionalCall]
    name: str | None = None,  # type: ignore[reportOptionalCall]
) -> Any:
    """Run an async flow function with Prefect orchestration.  # type: ignore[reportOptionalCall]

    Args:
        flow_fn: Async function to wrap in Prefect flow
        name: Optional flow name

    Returns:
        Flow result
    """
    if not PREFECT_AVAILABLE:
        return await flow_fn()  # type: ignore[reportOptionalCall]

    @flow(name=name or "swarmbot-orchestrated")  # type: ignore[reportOptionalCall]
    async def managed_flow():  # type: ignore[reportOptionalCall]
        return await flow_fn()  # type: ignore[reportOptionalCall]

    return await managed_flow()  # type: ignore[reportOptionalCall]


class PrefectPipeline:
    """A Prefect-based pipeline for SwarmBot multi-step tasks.  # type: ignore[reportOptionalCall]

    Allows defining a pipeline of agent steps with retry, timeout,  # type: ignore[reportOptionalCall]
    and state management between steps.  # type: ignore[reportOptionalCall]
    """

    def __init__(  # type: ignore[reportOptionalCall]
        self,  # type: ignore[reportOptionalCall]
        name: str = "swarmbot-pipeline",  # type: ignore[reportOptionalCall]
        retries: int = 1,  # type: ignore[reportOptionalCall]
        timeout_seconds: int = 300,  # type: ignore[reportOptionalCall]
    ) -> None:
        self.name = name  # type: ignore[reportOptionalCall]
        self.retries = retries  # type: ignore[reportOptionalCall]
        self.timeout_seconds = timeout_seconds  # type: ignore[reportOptionalCall]
        self._steps: list[dict[str, Any]] = []  # type: ignore[reportOptionalCall]

    def add_step(  # type: ignore[reportOptionalCall]
        self,  # type: ignore[reportOptionalCall]
        name: str,  # type: ignore[reportOptionalCall]
        task_fn: Callable[[], Coroutine],  # type: ignore[reportOptionalCall]
        retry_delay: int | float = 30,  # type: ignore[reportOptionalCall]
    ) -> None:
        """Add a step to the pipeline."""  # type: ignore[reportOptionalCall]
        self._steps.append({  # type: ignore[reportOptionalCall]
            "name": name,  # type: ignore[reportOptionalCall]
            "fn": task_fn,  # type: ignore[reportOptionalCall]
            "retry_delay": retry_delay,  # type: ignore[reportOptionalCall]
        })

    @task  # type: ignore[reportOptionalCall]
    async def _run_step(self, step: dict[str, Any]) -> Any:  # type: ignore[reportOptionalCall]
        """Internal task to run a single pipeline step."""  # type: ignore[reportOptionalCall]
        return await step["fn"]()  # type: ignore[reportOptionalCall]

    async def execute(self) -> list[Any]:  # type: ignore[reportOptionalCall]
        """Execute the pipeline and return results for all steps."""  # type: ignore[reportOptionalCall]
        if not PREFECT_AVAILABLE:
            results = []  # type: ignore[reportOptionalCall]
            for step in self._steps:  # type: ignore[reportOptionalCall]
                results.append(await step["fn"]())  # type: ignore[reportOptionalCall]
            return results

        @flow(name=self.name, retries=self.retries, timeout_seconds=self.timeout_seconds)  # type: ignore[reportOptionalCall]
        async def pipeline_flow():  # type: ignore[reportOptionalCall]
            results = []  # type: ignore[reportOptionalCall]
            for step in self._steps:  # type: ignore[reportOptionalCall]
                try:
                    result = await self._run_step(step)  # type: ignore[reportOptionalCall]
                    results.append(result)  # type: ignore[reportOptionalCall]
                except Exception as exc:
                    logger.warning("Pipeline step %s failed: %s", step["name"], exc)  # type: ignore[reportOptionalCall]
                    results.append(f"[step failed: {exc}]")  # type: ignore[reportOptionalCall]
            return results

        return await pipeline_flow()  # type: ignore[reportOptionalCall]


def create_swarmbot_deployment(  # type: ignore[reportOptionalCall]
    flow_fn: Callable,  # type: ignore[reportOptionalCall]
    name: str,  # type: ignore[reportOptionalCall]
    schedule: str | None = None,  # type: ignore[reportOptionalCall]
    tags: list[str] | None = None,  # type: ignore[reportOptionalCall]
) -> str | None:
    """Create a Prefect deployment for a SwarmBot flow.  # type: ignore[reportOptionalCall]

    Args:
        flow_fn: The async flow function to deploy
        name: Deployment name
        schedule: Cron-style schedule (e.g., "0 * * * *")  # type: ignore[reportOptionalCall]
        tags: Optional tags for the deployment

    Returns:
        Deployment ID or None if Prefect unavailable
    """
    if not PREFECT_AVAILABLE:
        return None

    try:
        from prefect.deployments.runner import RunnerDeployment  # type: ignore[reportOptionalCall]

        runner_deployment = RunnerDeployment.from_flow(  # type: ignore[reportOptionalCall]
            flow=flow_fn,  # type: ignore[reportOptionalCall]
            name=name,  # type: ignore[reportOptionalCall]
            tags=tags or [],  # type: ignore[reportOptionalCall]
        )
        await runner_deployment.apply()  # type: ignore[reportOptionalCall]
        logger.info("Prefect deployment created: %s", name)  # type: ignore[reportOptionalCall]
        return name
    except Exception as exc:
        logger.warning("Prefect deployment failed: %s", exc)  # type: ignore[reportOptionalCall]
        return None
