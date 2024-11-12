from typing import Any, Iterator, Literal, Protocol, Sequence

from vstools import vs

__all__ = [
    'ValidMatchT',

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
    def apply(self, clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode: ...


class SectionProtocol(Protocol):
    """Protocol defining the interface for sections."""

    start: int
    presets: Sequence[PresetProtocol]


class SectionsProtocol(Protocol):
    """Protocol defining the interface for a collection of sections."""

    def __iter__(self) -> Iterator[SectionProtocol]: ...
