from dataclasses import dataclass

from vstools import CustomRuntimeError, CustomValueError, fallback, vs

from ..exceptions import NegativeFrameError

__all__ = [
    'FreezeFrame',
    'FreezeFrames',
]


@dataclass
class FreezeFrame:
    """Class for holding a freeze frame."""

    first: int
    """The first frame to freeze."""

    last: int
    """The last frame to freeze."""

    replacement: int
    """The frame to replace the frozen frames with."""

    def __post_init__(self) -> None:
        NegativeFrameError.check(self.__class__, [self.first, self.last, self.replacement])

        if self.first > self.last:
            raise CustomValueError(
                f'First frame ({self.first}) must start before the last frame ({self.last})!', self
            )

    def __iter__(self) -> tuple[int, int, int]:
        """Return a tuple of first, last and replacement frames for unpacking."""

        return self.first, self.last, self.replacement


class FreezeFrames(list[FreezeFrame]):
    """List of frozen frames."""

    def __post_init__(self) -> None:
        NegativeFrameError.check(self.__class__, [freeze.first for freeze in fallback(self, [])])
        NegativeFrameError.check(self.__class__, [freeze.last for freeze in fallback(self, [])])
        NegativeFrameError.check(self.__class__, [freeze.replacement for freeze in fallback(self, [])])

    def apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Apply the freeze frames to the clip."""

        try:
            return clip.std.FreezeFrames(
                [freeze.first for freeze in self],
                [freeze.last for freeze in self],
                [freeze.replacement for freeze in self]
            )
        except Exception as e:
            raise CustomRuntimeError(f'Failed to apply freeze frames: {e}', self.apply)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for freeze frames."""

        return 'frozen frames'
