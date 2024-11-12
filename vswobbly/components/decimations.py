from vstools import fallback, vs

from ..exceptions import NegativeFrameError
from ..util import deduplicate_list

__all__ = [
    'Decimations',
]


class Decimations(list[int]):
    """Class for holding decimations."""

    def __init__(self, decimations: list[int] | None = None) -> None:
        super().__init__(decimations or [])

        NegativeFrameError.check(self.__class__, fallback(self, []))

        self.sort()

        self[:] = deduplicate_list(self)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for decimated frames."""

        return 'decimated frames'

    def find_decimation(self, frame: int) -> int | None:
        """Find a decimation in the list."""

        try:
            return self[self.index(frame)]
        except ValueError:
            return None

    def apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Apply the decimations to the clip."""

        if len(self) == 0:
            return clip

        dec = clip.std.DeleteFrames(self)

        return dec.std.AssumeFPS(fpsnum=24000, fpsden=1001)
