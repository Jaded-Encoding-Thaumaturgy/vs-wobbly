from vstools import fallback, replace_ranges, vs

from ..exceptions import NegativeFrameError
from ..util import deduplicate_list

__all__ = [
    'CombedFrames',
]


class CombedFrames(list[int]):
    """Class for holding combed frames."""

    def __init__(self, frames: list[int] | None = None) -> None:
        super().__init__(frames or [])

        NegativeFrameError.check(self.__class__, fallback(self, []))

        self.sort()

        self[:] = deduplicate_list(self)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for combed frames."""

        return 'combed frames'

    def find_frame(self, frame: int) -> int | None:
        """Find a frame in the list."""

        if frame in self:
            return next(f for f in self if f == frame)

        return None

    def get_frame(self, frame: int) -> int:
        """Get a frame from the list, and raise an error if not found."""

        if frame < 0:
            raise NegativeFrameError(self.__class__, frame)

        if (found := self.find_frame(frame)) is None:
            raise ValueError(f'Frame {frame} not found!')

        return found

    def set_props(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Set the combed frame properties on the clip."""

        return replace_ranges(
            clip.std.SetFrameProps(WobblyCombed=False),
            clip.std.SetFrameProps(WobblyCombed=True),
            self
        )
