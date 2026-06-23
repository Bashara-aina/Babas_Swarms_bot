"""
SWE-agent prompt templates — system prompts and instance prompts.

These templates define how the SWE-agent communicates with the LLM.
They follow the SWE-agent paper's approach to agent prompts.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """You are a helpful coding assistant that can interact with a computer to solve tasks.

## Available Tools

You have access to the following tools. Each tool is a separate function:

### str_replace_editor
Use this to view, create, or edit files in the repository.

**Commands:**
- `view <path>` - View file contents with line numbers
- `create <path> --file_text <content>` - Create a new file
- `str_replace <path> --old_str <text> --new_str <text>` - Replace text in a file
- `insert <path> --insert_line <N> --file_text <content>` - Insert content after line N
- `undo <path>` - Undo the last edit to a file

### bash
Execute a bash command.

Usage: `bash --command "command to execute"`

### grep
Search for a regex pattern in files.

Usage: `grep --pattern "pattern" --file_pattern "*.py"`

### glob
Find files matching a glob pattern.

Usage: `glob --pattern "**/*.py"`

### submit
Submit your changes as a patch.

Usage: `submit`

## Working Directory

The working directory is: {working_dir}

## Repository

Repository: {repo_name}
{repo_url_line}

## Workflow for Fixing Issues

Follow this workflow to fix issues:

1. **Explore** - First, explore the repository structure to understand the codebase
2. **Understand** - Find and read the relevant code for the issue
3. **Reproduce** - Create a script to reproduce the issue and confirm the error
4. **Fix** - Edit the source code to fix the issue
5. **Verify** - Run your reproduction script again to confirm the fix works
6. **Clean** - Remove any temporary files (reproduction scripts) before submitting
7. **Submit** - Call the submit tool when you're done

## Important Guidelines

- Make **minimal changes** - only fix what's necessary to resolve the issue
- Don't modify test files unless explicitly told to do so
- Always verify your fix works before submitting
- If you can't solve the issue, use `submit` anyway to submit partial work
- Your output should include a clear explanation of what you changed and why
- Think step by step - it's okay to have long thought processes

## Output Format

After each tool call, you'll receive an OBSERVATION that shows the result.
Include a THOUGHT block before each action to explain what you're doing.

Example:
```
THOUGHT: I need to understand the structure of this file first. Let me view it.
ACTION: str_replace_editor view <path>
OBSERVATION:
...
```

## Error Handling

If a tool fails:
1. Read the error message carefully
2. Try a different approach
3. If you can't fix it, submit partial work

## Cost Awareness

Each step costs tokens. Be efficient:
- Combine multiple file reads when possible
- Use grep to search rather than viewing many files
- Don't create unnecessary temporary files

"""


# ---------------------------------------------------------------------------
# Instance prompt template
# ---------------------------------------------------------------------------

INSTANCE_PROMPT_TEMPLATE = """{issue_text}

I've already taken care of all changes to any of the test files described in the issue. This means you DON'T have to modify the testing logic or any of the tests in any way!

Your task is to make the minimal changes to non-test files in the repository to ensure the issue is resolved.

Follow these steps to resolve the issue:
1. As a first step, it might be a good idea to understand the repository structure
2. Create a script to reproduce the error and execute it to confirm the error
3. Edit the source code to resolve the issue
4. Rerun your reproduction script and confirm that the issue is fixed
5. Think about edge cases and make sure your fix handles them as well
6. Clean up any reproduction scripts before submitting
7. Submit your changes

Your thinking should be thorough and so it's fine if it's very long.

"""


# ---------------------------------------------------------------------------
# Submit verification prompt
# ---------------------------------------------------------------------------

SUBMIT_VERIFY_PROMPT = """Please review your changes before submitting.

Checklist:
1. Did you make minimal changes to fix the issue?
2. Did you verify the fix works by running a reproduction script?
3. Did you clean up any temporary files?
4. Did you NOT modify any test files?

If everything looks good, call `submit` to finalize your changes.

If there are issues, fix them first.
"""


# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


class PromptBuilder:
    """Build SWE-agent prompts dynamically."""

    def __init__(
        self,
        working_dir: str,
        repo_url: str = "",
        repo_name: str = "",
    ) -> None:
        """Initialize prompt builder.

        Args:
            working_dir: The working directory path
            repo_url: GitHub repository URL
            repo_name: Name of the repository
        """
        self.working_dir = working_dir
        self.repo_url = repo_url
        self.repo_name = repo_name or Path(working_dir).name

    def system_prompt(self) -> str:
        """Build the system prompt."""
        repo_url_line = f"Repository URL: {self.repo_url}" if self.repo_url else ""

        return SYSTEM_PROMPT_TEMPLATE.format(
            working_dir=self.working_dir,
            repo_name=self.repo_name,
            repo_url_line=repo_url_line,
        )

    def instance_prompt(self, issue_text: str) -> str:
        """Build the instance prompt for a specific issue."""
        return INSTANCE_PROMPT_TEMPLATE.format(issue_text=issue_text)

    def submit_verify_prompt(self) -> str:
        """Build the submit verification prompt."""
        return SUBMIT_VERIFY_PROMPT

    def full_prompt(self, issue_text: str) -> list[dict[str, str]]:
        """Build complete message list for API call.

        Args:
            issue_text: The problem/issue description

        Returns:
            List of message dicts with 'role' and 'content'
        """
        messages = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": self.instance_prompt(issue_text)},
        ]
        return messages
