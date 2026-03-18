"""Loads agent prompts from .md files at runtime."""

from pathlib import Path

_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt .md file and return its content."""
    path = _DIR / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def get_planner_prompt() -> str:
    return load_prompt("planner")


def get_generator_prompt() -> str:
    return load_prompt("generator")


def get_healer_prompt() -> str:
    return load_prompt("healer")