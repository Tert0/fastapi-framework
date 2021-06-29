from os import getenv
from dotenv import load_dotenv

load_dotenv()
from typing import List

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
    for module in dependencies.keys():  # type: str
        if module in disabled_modules:
            continue
        module_dependencies = dependencies[module]
        for module_dependency in module_dependencies:
            if module_dependency in disabled_modules:
                raise Exception(f"Module '{module}' needs the disabled Module '{module_dependency}'")
