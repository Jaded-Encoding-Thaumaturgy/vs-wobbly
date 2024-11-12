import ast
from dataclasses import dataclass
from typing import Any

from vstools import CustomValueError, vs

__all__ = [
    'Preset',
    'Presets',
]


@dataclass
class Preset:
    """Class for holding a preset."""

    name: str
    """The name of the preset."""

    contents: str
    """The contents of the preset."""

    def __post_init__(self) -> None:
        """Validate and check safety of preset after initialization."""

        if not self.name:
            raise CustomValueError('Preset name cannot be empty!', self._err_name)

        if not self.contents:
            del self
            return

        self._check_code_exec()

    def __call__(self, clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
        """Apply the preset code to a given clip."""

        return self.apply(clip, **kwargs)

    def __str__(self) -> str:
        return f'{self.name}:\n\n{self.contents}'

    def apply(self, clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
        """Apply the preset code to a given clip."""

        namespace = {'clip': clip}

        exec(self.contents, namespace)

        return namespace['clip']

    def _check_code_exec(self) -> None:
        """Check if the preset is executable."""

        try:
            compile(self.contents, '<string>', 'exec')
        except SyntaxError as e:
            raise CustomValueError(f'Invalid Python code in preset contents: {e}', self._err_name)
        except Exception as e:
            raise CustomValueError(f'Invalid preset contents: {e}', self._err_name)

        tree = ast.parse(self.contents)

        has_clip = False

        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == 'clip':
                has_clip = True

                break

        if not has_clip:
            raise CustomValueError('Preset must use the "clip" variable', self._err_name)

    def _check_unsafe_node(self, node: ast.AST, depth: int = 0) -> None:
        """Check if an individual AST node contains unsafe operations."""

        if depth > 100:  # Add recursion depth limit
            raise CustomValueError('Maximum recursion depth exceeded while checking preset safety', self._err_name)

        if not isinstance(node, ast.AST):
            return

        try:
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in {'eval', 'exec', 'open', 'system'}:
                        raise CustomValueError(f'Unsafe function call: {node.func.id}()', self._err_name)

            for child in ast.iter_child_nodes(node):  # Use iter_child_nodes instead of walk
                self._check_unsafe_node(child, depth + 1)

        except CustomValueError:
            raise
        except Exception as e:
            raise CustomValueError(f'Error checking preset safety: {e}', self._err_name)

    @property
    def _err_name(self) -> str:
        """The error name for the preset."""

        if not self.name:
            return self.__class__.__name__

        return f'{self.__class__.__name__}:{self.name}'


class Presets(list[Preset]):
    """Class for holding a list of presets."""

    def __init__(self, presets: list[Preset]) -> None:
        super().__init__(presets or [])

    def __str__(self) -> str:
        return ', '.join(self)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for presets."""

        return 'presets'
