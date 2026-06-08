"""
hello.py — greeting utilities with multiple logic branches
so mutation testing has plenty of mutants to generate.
"""


def say_hello(name: str) -> str:
    """Return a greeting. Special-cases 'World'."""
    if name == "World":
        return "Hello, World!"
    return f"Hello, {name}!"


def say_hello_times(name: str, times: int) -> list[str]:
    """Return the greeting repeated `times` times."""
    if times <= 0:
        return []
    return [say_hello(name) for _ in range(times)]


def greet_all(names: list[str]) -> list[str]:
    """Greet every name in the list."""
    if not names:
        return []
    return [say_hello(name) for name in names]


def formal_greeting(name: str, title: str = "") -> str:
    """Return a formal greeting, optionally with a title."""
    if not name:
        return "Hello, stranger!"
    if title:
        return f"Good day, {title} {name}."
    return f"Good day, {name}."


def shout_hello(name: str) -> str:
    """Return an upper-cased greeting."""
    if not name:
        return "HELLO!"
    return say_hello(name).upper()


def count_hellos(names: list[str]) -> int:
    """Return how many names would receive a greeting."""
    return len([n for n in names if n])


def is_special_name(name: str) -> bool:
    """Return True if the name gets a special greeting."""
    return name == "World"
