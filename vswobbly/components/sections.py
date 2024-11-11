from dataclasses import dataclass, field

from vstools import Keyframes

from ..exceptions import NegativeFrameError
from .decimations import Decimations
from .types import PresetProtocol, SectionProtocol

__all__ = [
    'Section',
    'Sections',
]


@dataclass
class Section(SectionProtocol):
    """Class for holding a section."""

    start: int
    """The start frame number."""

    presets: list[PresetProtocol] = field(default_factory=list)
    """The presets used for this section."""

    def __post_init__(self):
        NegativeFrameError.check(self, self.start)


class Sections(list[Section]):
    """Class for holding sections."""

    def __init__(self, sections: list[Section]) -> None:
        super().__init__(sections or [])

    def __str__(self) -> str:
        if not self:
            return ''

        return ', '.join(str(section) for section in self)

    def to_keyframes(self, decimations: Decimations) -> Keyframes:
        """
        Convert the sections to keyframes.

        Accounts for decimated frames by adjusting section start frames
        based on the number of decimations that occur before each section start.

        :param decimations:     The decimations to account for.

        :return:                A keyframes object representing the section start frames
                                adjusted for decimations.
        """

        keyframes = []

        for section in self:
            decimation_count = sum(1 for d in decimations if d < section.start)
            adjusted_start = section.start - decimation_count

            keyframes.append(adjusted_start)

        return Keyframes(keyframes)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for sections."""

        return 'sections'
