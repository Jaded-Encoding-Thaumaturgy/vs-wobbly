from typing import Iterator, Literal, Protocol, Sequence

from vstools import CustomStrEnum, vs

__all__ = [
    'ValidMatchT',

    'CustomPresetPosition',

    'PresetProtocol',
    'SectionProtocol',
    'SectionsProtocol',
]


ValidMatchT = Literal['p', 'c', 'n', 'b', 'u']
"""Type alias for valid match characters.

p: Match to previous field
c: Match to current field
n: Match to next field
b: Match to previous field (matches from opposite parity field)
u: Match to next field (matches from opposite parity field)

See `http://avisynth.nl/index.php/TIVTC/TFM` for more information.
"""


class PresetProtocol(Protocol):
    """Protocol defining the interface for presets."""

    name: str
    def apply(self, clip: vs.VideoNode) -> vs.VideoNode: ...


class SectionProtocol(Protocol):
    """Protocol defining the interface for sections."""

    start: int
    presets: Sequence[PresetProtocol]


class SectionsProtocol(Protocol):
    """Protocol defining the interface for a collection of sections."""

    def __iter__(self) -> Iterator[SectionProtocol]: ...


class CustomPresetPosition(CustomStrEnum):
    """Enum denoting when to apply a preset."""

    POST_SOURCE = 'post source'
    """Apply the preset to the source clip."""

    POST_FIELD_MATCH = 'post field match'
    """Apply the preset after field matching."""

    PRE_DECIMATION = 'pre decimation'
    """
    Apply the preset before decimation.
    This is used by section presets.
    """

    POST_DECIMATION = 'post decimation'
    """Apply the preset after decimation."""
