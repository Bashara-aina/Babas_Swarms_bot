"""
SWE-agent CLI — Command-line interface for native SWE-agent.

Usage:
    python -m core.swe_agent.cli --issue "Issue description" --repo /path/to/repo
    python -m core.swe_agent.cli --issue-url "https://github.com/owner/repo/issues/123"
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from core.swe_agent.config import DEFAULT_CONFIG, load_config
from core.swe_agent.environment import Environment
from core.swe_agent.loop import MaxStepsExceeded, SWEAgentLoop

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


async def run_swe_agent(
    instance_id: str,
    problem_statement: str,
    repo_path: str,
    *,
    model: str = "minimax-coding-plan/MiniMax-M3",
    max_steps: int = 30,
    trajectory_dir: str | None = None,
    no_stream: bool = False,
) -> int:
    """Run SWE-agent on a problem.

    Args:
        instance_id: Unique identifier for this run
        problem_statement: The problem/issue description
        repo_path: Path to the repository
        model: Model to use
        max_steps: Maximum steps before giving up
        trajectory_dir: Where to save trajectory files
        no_stream: If True, don't stream output

    Returns:
        0 on success, 1 on failure
    """
    # Initialize environment
    env = Environment(repo_path=repo_path)

    try:
        # Create agent loop
        loop = SWEAgentLoop(
            instance_id=instance_id,
            problem_statement=problem_statement,
            model=model,
            max_steps=max_steps,
            working_dir=str(env.repo_path),
            trajectory_dir=trajectory_dir,
        )

        # Build prompts
        _ = loop.build_system_prompt(
            repo_path=str(env.repo_path),
            repo_url=env.repo_url or "",
        )
        _ = loop.build_instance_prompt(problem_statement)

        # Run the agent loop
        logger.info(f"Starting SWE-agent run: {instance_id}")
        logger.info(f"Model: {model}, Max steps: {max_steps}")

        step = 0
        while step < max_steps:
            step += 1
            logger.info(f"Step {step}/{max_steps}")

            # For now, this is a stub - actual implementation would call the LLM
            # The full implementation would integrate with litellm for model calls
            print(f"[Step {step}] This is a placeholder - LLM integration pending")

            # Check if submitted
            if loop.trajectory.submitted:
                logger.info("Solution submitted successfully!")
                break

        # Finalize
        if loop.trajectory.submitted:
            loop.finalize(success=True)
        else:
            loop.finalize(success=False, error="Max steps reached or solution not submitted")

        # Save trajectory
        traj_path = loop.save_trajectory()
        logger.info(f"Trajectory saved to: {traj_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("RUN SUMMARY")
        print("=" * 60)
        print(f"Instance: {instance_id}")
        print(f"Steps: {loop.trajectory.total_steps}")
        print(f"Cost: ${loop.trajectory.total_cost:.4f}")
        print(f"Success: {loop.trajectory.success}")
        print(f"Submitted: {loop.trajectory.submitted}")
        if loop.trajectory.final_patch:
            print(f"\nPatch:\n{loop.trajectory.final_patch[:500]}...")
        print("=" * 60)

        return 0 if loop.trajectory.success else 1

    except MaxStepsExceeded as e:
        logger.error(f"Max steps exceeded: {e}")
        return 1
    except Exception as e:
        logger.exception("SWE-agent run failed")
        print(f"Error: {e}")
        return 1
    finally:
        env.cleanup()


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="SWE-agent CLI — Native SWE-agent implementation")
    parser.add_argument("--instance-id", "-i", default="cli-run", help="Instance ID")
    parser.add_argument("--issue", help="Problem/issue description")
    parser.add_argument("--issue-url", help="GitHub issue URL")
    parser.add_argument("--repo", required=True, help="Path to repository")
    parser.add_argument("--model", "-m", default="minimax-coding-plan/MiniMax-M3", help="Model to use")
    parser.add_argument("--max-steps", "-k", type=int, default=30, help="Max steps")
    parser.add_argument("--trajectory-dir", "-t", help="Trajectory output directory")
    parser.add_argument("--config", "-c", help="Path to config YAML")
    parser.add_argument("--no-stream", action="store_true", help="Don't stream output")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config if provided
    config = load_config(args.config) if args.config else DEFAULT_CONFIG

    # Get problem statement
    if args.issue:
        problem_statement = args.issue
    elif args.issue_url:
        # Fetch issue from GitHub
        import json
        import urllib.request

        # Parse GitHub URL
        url = args.issue_url
        if "github.com" in url and "/issues/" in url:
            # Extract owner/repo/issue_number
            parts = url.replace("https://github.com/", "").replace("www.github.com/", "").split("/")
            if len(parts) >= 4 and parts[2] == "issues":
                owner, repo = parts[0], parts[1]
                issue_num = parts[3]
                api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"

                try:
                    req = urllib.request.Request(api_url, headers={"Accept": "application/json"})
                    with urllib.request.urlopen(req, timeout=30) as resp:
                        data = json.loads(resp.read())
                        problem_statement = f"{data.get('title', '')}\n\n{data.get('body', '')}"
                except Exception as e:
                    print(f"Warning: Could not fetch issue from GitHub API: {e}")
                    print("Falling back to using URL as problem statement")
                    problem_statement = args.issue_url
            else:
                problem_statement = args.issue_url
        else:
            problem_statement = args.issue_url
    else:
        print("Error: Either --issue or --issue-url is required")
        return 1

    # Run the agent
    return asyncio.run(
        run_swe_agent(
            instance_id=args.instance_id,
            problem_statement=problem_statement,
            repo_path=args.repo,
            model=args.model or config.agent.model.name,
            max_steps=args.max_steps or config.agent.max_steps,
            trajectory_dir=args.trajectory_dir,
            no_stream=args.no_stream,
        )
    )


if __name__ == "__main__":
    sys.exit(main())
