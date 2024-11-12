from dataclasses import dataclass

from vstools import replace_ranges, CustomValueError, fallback, vs

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

        if len(self) == 0:
            return clip

        # I realise this is slower! See _better_apply for a faster WIP implementation.
        for freeze in self:
            frozen = clip.std.FreezeFrames(freeze.first, freeze.last, freeze.replacement)
            frozen = frozen.std.SetFrameProps(WobblyFreeze=[freeze.first, freeze.last, freeze.replacement])

            clip = replace_ranges(clip, frozen, [(freeze.first, freeze.last)])

        return clip

    # TODO: Finish implementing this
    def _better_apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        firsts, lasts, replacements = [], [], []

        for freeze in self:
            firsts.append(freeze.first)
            lasts.append(freeze.last)
            replacements.append(freeze.replacement)

            clip = replace_ranges(
                clip, clip.std.SetFrameProps(WobblyFreeze=[freeze.first, freeze.last, freeze.replacement]),
                [(freeze.first, freeze.last)]
            )

        # TODO: The current issue is that props don't persist if the replacement isn't in the range of (first, last).
        return clip.std.FreezeFrames(firsts, lasts, replacements)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for freeze frames."""

        return 'frozen frames'
