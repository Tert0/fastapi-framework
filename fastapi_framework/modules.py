from os import getenv
from typing import List, Set

from dotenv import load_dotenv

load_dotenv()

dependencies = {
    "redis": [],
    "database": [],
    "logger": [],
    "jwt_auth": ["redis"],
    "rate_limit": ["redis"],
}
disabled_modules: List[str] = list(
    map(str.lower, getenv("DISABLED_MODULES", "").replace(" ", "").replace(",", ";").split(";"))
)


def check_dependencies():
    """Checks if Dependencies exists"""
    needed_dependencies: Set[tuple[str, str]] = set()
    for module in dependencies:  # type: str
        if module in disabled_modules:
            continue
        for module_dependency in dependencies[module]:
            needed_dependencies.add((module, module_dependency))
    needed_dependencies: List[tuple[str, str]] = [
        needed_dependency for needed_dependency in needed_dependencies if needed_dependency[1] in disabled_modules
    ]
    if len(needed_dependencies) == 0:
        return
    raise Exception(f"Module '{needed_dependencies[0][0]}' needs the disabled Module '{needed_dependencies[0][1]}'")
