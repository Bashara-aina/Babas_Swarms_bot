# /home/newadmin/swarm-bot/interpreter_bridge.py
"""Bridge between Telegram and Open Interpreter with multi-provider support."""

from __future__ import annotations
import asyncio
import logging
import os
from interpreter import interpreter

logger = logging.getLogger(__name__)

# System prompts per agent
SYSTEM_PROMPTS = {
    "vision": (
        "You analyze screenshots, images, and visual interfaces on a Linux desktop (DISPLAY=:0). "
        "You can use computer.display.view() to take screenshots. "
        "Identify UI elements, read text via OCR, detect errors highlighted in red, "
        "and provide actionable next steps. When analyzing screens: "
        "1. Identify all visible elements. "
        "2. Read any text present. "
        "3. Detect errors or warnings. "
        "4. Suggest the next action."
    ),
    "coding": (
        "You are an expert software engineer with full computer control on a Linux desktop. "
        "You can: take screenshots with computer.display.view(), read VSCode files, "
        "execute shell commands, and click UI elements. "
        "When fixing code: 1. Screenshot to see the error. 2. Read the file. "
        "3. Analyze the issue. 4. Apply the minimal fix. 5. Run tests to verify. "
        "Always confirm before destructive actions (rm, git push --force, etc.)."
    ),
    "debug": (
        "You are a debugging expert for PyTorch/CUDA and Python systems. "
        "Analyze errors systematically: read the full traceback, identify root cause, "
        "explain WHY it failed in one sentence, then provide the minimal targeted fix. "
        "For CUDA OOM: enable AMP first (torch.cuda.amp), then reduce batch_size. "
        "For NaN loss: add gradient clipping (torch.nn.utils.clip_grad_norm_). "
        "Suggest a preventive assert or guard for the future."
    ),
    "math": (
        "You are a mathematics expert specializing in ML/deep learning math. "
        "Show step-by-step derivations. Verify numerical answers by writing and "
        "executing Python/NumPy code. For tensor operations, show shapes at each step. "
        "For gradient derivations, show the chain rule explicitly."
    ),
    "architect": (
        "You are a system architect. Design scalable, maintainable solutions. "
        "Focus on structure, data flow, and component boundaries. "
        "For ML systems: address data pipeline, training loop, evaluation, and deployment. "
        "For software systems: address APIs, storage, concurrency, and failure modes. "
        "Produce diagrams using ASCII art when helpful."
    ),
    "mentor": (
        "You are a patient teacher and expert explainer. "
        "Explain complex concepts using clear analogies and concrete examples. "
        "Always answer WHY, not just what. Structure explanations as: "
        "1. Simple intuition. 2. Technical detail. 3. Concrete example. "
        "4. One actionable takeaway. Adjust depth to the user's apparent level."
    ),
    "analyst": (
        "You are a data analyst specializing in ML training metrics and system performance. "
        "Extract insights from logs, metrics, and data. Identify trends and anomalies. "
        "Write Python code to produce visualizations (matplotlib/seaborn). "
        "For training runs: check loss curves, gradient norms, GPU utilization, and throughput. "
        "Alert on: NaN/Inf values, loss spikes > 2x, GPU utilization < 50%."
    ),
}

def configure_interpreter(model: str, agent_key: str) -> None:
    """Configure interpreter for the specified model and agent.
    
    Args:
        model: Model string with provider prefix (e.g. "zai/glm-4")
        agent_key: Agent identifier for system prompt selection
    """
    
    # Reset to defaults
    interpreter.auto_run = True
    interpreter.offline = True
    interpreter.llm.api_base = "http://localhost:11434"
    interpreter.llm.api_key = "ollama"
    interpreter.system_message = SYSTEM_PROMPTS.get(agent_key, "")
    
    # Parse provider from model string
    if model.startswith("ollama_chat/"):
        # Local Ollama
        interpreter.llm.model = model
        interpreter.offline = True
        logger.info("Using local Ollama: %s", model)
        
    elif model.startswith("openrouter/"):
        # OpenRouter
        model_name = model.replace("openrouter/", "")
        interpreter.llm.model = model_name
        interpreter.llm.api_base = "https://openrouter.ai/api/v1"
        interpreter.llm.api_key = os.getenv("OPENROUTER_API_KEY")
        interpreter.offline = False
        logger.info("Using OpenRouter: %s", model_name)
        
    elif model.startswith("zai/"):
        # Z.AI (GLM-4.7)
        interpreter.llm.model = "glm-4"
        interpreter.llm.api_base = "https://open.bigmodel.cn/api/paas/v4"
        interpreter.llm.api_key = os.getenv("ZAI_API_KEY")
        interpreter.offline = False
        logger.info("Using Z.AI: glm-4")
        
    elif model.startswith("cerebras/"):
        # Cerebras
        model_name = model.replace("cerebras/", "")
        interpreter.llm.model = model_name
        interpreter.llm.api_base = "https://api.cerebras.ai/v1"
        interpreter.llm.api_key = os.getenv("CEREBRAS_API_KEY")
        interpreter.offline = False
        logger.info("Using Cerebras: %s", model_name)
        
    elif model.startswith("gemini/"):
        # Google AI Studio
        model_name = model.replace("gemini/", "")
        interpreter.llm.model = model_name
        interpreter.llm.api_base = "https://generativelanguage.googleapis.com/v1beta/openai"
        interpreter.llm.api_key = os.getenv("GEMINI_API_KEY")
        interpreter.offline = False
        logger.info("Using Gemini: %s", model_name)
        
    elif model.startswith("groq/"):
        # Groq
        model_name = model.replace("groq/", "")
        interpreter.llm.model = model_name
        interpreter.llm.api_base = "https://api.groq.com/openai/v1"
        interpreter.llm.api_key = os.getenv("GROQ_API_KEY")
        interpreter.offline = False
        logger.info("Using Groq: %s", model_name)
    
    else:
        logger.warning("Unknown model prefix: %s — defaulting to Ollama", model)

async def run_task(model: str, task: str, agent_key: str = "coding") -> str:
    """Execute a task using Open Interpreter with the specified model.
    
    Args:
        model: Model string with provider prefix (e.g. "openrouter/...")
        task: User task description
        agent_key: Agent identifier for system prompt selection
        
    Returns:
        Concatenated output from interpreter
    """
    configure_interpreter(model, agent_key)
    
    # Run in thread pool to avoid blocking asyncio
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        lambda: interpreter.chat(task, display=False)
    )
    
    # Collect all message content
    output_parts = []
    for msg in result:
        if msg.get("type") == "message":
            content = msg.get("content", "")
            if isinstance(content, str) and content.strip():
                output_parts.append(content)
        elif msg.get("type") == "code":
            code = msg.get("content", "")
            if code.strip():
                output_parts.append(f"```\n{code}\n```")
        elif msg.get("type") == "console":
            console_out = msg.get("content", "")
            if console_out.strip():
                output_parts.append(f"Output: {console_out}")
    
    full_output = "\n\n".join(output_parts)
    return full_output if full_output else "Task completed (no output generated)"

def chunk_output(text: str, max_length: int = 4000) -> list[str]:
    """Split text into chunks safe for Telegram's message length limit.
    
    Args:
        text: Full output text
        max_length: Maximum characters per chunk (default 4000 for safety)
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
