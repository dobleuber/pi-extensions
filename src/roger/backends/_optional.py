from __future__ import annotations

import importlib
from types import ModuleType
from typing import Callable

from roger.backends.errors import BackendUnavailable

ImportModule = Callable[[str], ModuleType]


def default_import_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


class OptionalDependencyMixin:
    dependency_module: str

    def __init__(self, import_module: ImportModule = default_import_module):
        self._import_module = import_module
        self._module: ModuleType | None = None
        self._import_error: ImportError | None = None

    def is_available(self) -> bool:
        try:
            self._load_module()
        except BackendUnavailable:
            return False
        return True

    def health_check(self) -> None:
        self._load_module()

    def _load_module(self) -> ModuleType:
        if self._module is not None:
            return self._module
        if self._import_error is not None:
            raise BackendUnavailable(str(self._import_error)) from self._import_error
        try:
            self._module = self._import_module(self.dependency_module)
        except ImportError as error:
            self._import_error = error
            raise BackendUnavailable(
                f"Backend dependency '{self.dependency_module}' is not installed or could not be imported."
            ) from error
        return self._module
