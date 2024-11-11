from vstools import CustomValueError

__all__ = [
    'WobblyParseError',

    'WobblyValidationError',
    'WobblyAttributeError',
    'NotAWobblyFileError',
]


class WobblyParseError(CustomValueError):
    """Raised when parsing wobbly files fails."""

    ...

class NotAWobblyFileError(WobblyParseError):
    """Raised when a file is not a wobbly file."""

    ...

class WobblyValidationError(WobblyParseError):
    """Raised when validation fails."""

    ...

class WobblyAttributeError(WobblyParseError, AttributeError):
    """Raised when an attribute is not found."""

    ...
