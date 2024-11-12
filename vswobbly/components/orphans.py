from dataclasses import dataclass
from typing import Self

from vstools import CustomValueError, fallback, replace_ranges, vs

from ..exceptions import NegativeFrameError
from .matches import FieldMatches, ValidMatchT

__all__ = [
    'OrphanFrame',
    'OrphanFrames',
]


@dataclass
class OrphanFrame:
    """Class for holding an orphan frame."""

    frame: int
    """The frame number."""

    match: ValidMatchT
    """
    The match used for this frame.
    Used to determine how to handle the frame by the orphan handler.
    """

    def __post_init__(self) -> None:
        NegativeFrameError.check(self.__class__, self.frame)

        if self.match not in ValidMatchT.__args__:  # type: ignore
            raise CustomValueError(f'Invalid match character: {self.match}', self)

        if self.match == 'c':
            raise CustomValueError('Orphan frames cannot have a \'c\' match!', self)

    def __str__(self) -> str:
        return f'Frame {self.frame} ({self.match})'


class OrphanFrames(list[OrphanFrame]):
    """Class for holding orphan frames."""

    def __init__(self, frames: list[OrphanFrame] | None = None) -> None:
        super().__init__(frames or [])

        self.sort(key=lambda x: x.frame)

        NegativeFrameError.check(self.__class__, [frame.frame for frame in fallback(self, [])])

        seen = set()
        unique_frames = []

        for frame in self:
            if frame.frame not in seen:
                seen.add(frame.frame)
                unique_frames.append(frame)

        self[:] = unique_frames

    def __init_subclass__(cls) -> None:
        """Create matches properties for the class."""

        for match in cls.ValidMatchT.__args__:  # type: ignore
            if match == 'c':
                continue

            def create_match_property(match: cls.ValidMatchT) -> property:
                """Create a match property for the class."""

                def getter(self: OrphanFrames) -> list[OrphanFrame]:
                    """Get all frames with a specific match."""

                    return self.find_matches(match)

                return property(
                    getter,
                    doc=f"Get all frames with a '{match}' match."
                )

            setattr(cls, f'{match}_matches', create_match_property(match))

    def __str__(self) -> str:
        return ', '.join(str(frame) for frame in self)

    @classmethod
    def from_sections(cls, sections: 'Sections', matches: 'FieldMatches') -> Self:  # noqa: F821
        """Create orphan frames from sections and matches."""

        orphans = []

        for idx, section in enumerate(sections):
            if matches[section.start] == 'n':
                orphans.append(OrphanFrame(section.start, 'n'))

            end_frame = (
                sections[idx + 1].start - 1
                if idx < len(sections) - 1
                else len(matches) - 1
            )

            if matches[end_frame] == 'b':
                orphans.append(OrphanFrame(end_frame, 'b'))

        return OrphanFrames(orphans)

    def find_frame(self, frame: int) -> OrphanFrame | None:
        """Find a frame in the list."""

        try:
            return next(f for f in self if f.frame == frame)
        except StopIteration:
            return None

    def find_matches(self, match: ValidMatchT) -> list[OrphanFrame]:
        """Find all frames with a specific match."""

        return [f for f in self if f.match == match]

    def set_props(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Set the orphan frame properties on the clip."""

        return replace_ranges(
            clip.std.SetFrameProps(WobblyOrphanFrame=False),
            clip.std.SetFrameProps(WobblyOrphanFrame=True),
            self
        )
