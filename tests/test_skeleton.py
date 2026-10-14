import importlib


def test_package_modules_are_importable() -> None:
    """T02: the skeleton from plan §1 exists and imports without errors."""
    for module in ("habits", "habits.core", "habits.storage", "habits.cli"):
        importlib.import_module(module)
