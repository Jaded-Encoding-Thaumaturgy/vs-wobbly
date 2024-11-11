from typing import Any

from vstools import (CustomTypeError, CustomValueError, FuncExceptT,
                     SupportsString)

__all__ = [
    'InvalidMatchError',
]


class InvalidMatchError(CustomValueError):
    """Raised when an invalid match character is used."""

    def __init__(
        self, func: FuncExceptT, invalid_matches: str | list[str],
        message: SupportsString = 'Invalid match(es)!',
        reason: Any = '{invalid_matches}', **kwargs: Any
    ) -> None:
        super().__init__(message, func, reason, **kwargs, invalid_matches=invalid_matches)

    @classmethod
    def check(cls, func: FuncExceptT, matches: str | list[str]) -> None:
        """Check if the match is valid."""

        from ..components.matches import ValidMatchT

        try:
            matches = ''.join({m for m in matches})
        except TypeError:
            raise CustomTypeError('Matches must be a string or list of strings!', func, reason=type(matches))

        if invalid_matches := [m for m in matches if m not in set(ValidMatchT.__args__)]:
            raise cls(func, invalid_matches)
