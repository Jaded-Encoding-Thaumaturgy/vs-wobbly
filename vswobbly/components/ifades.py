from dataclasses import dataclass
from typing import Any

from vstools import (CustomValueError, VSFunctionNoArgs, fallback,
                     replace_ranges, vs)

from ..exceptions import NegativeFrameError

__all__ = [
    'InterlacedFade',
    'InterlacedFades',
]


@dataclass
class InterlacedFade:
    """Class for holding an interlaced fade."""

    frame: int
    """The frame number."""

    field_difference: float
    """The field difference."""

    def __post_init__(self):
        NegativeFrameError.check(self.__class__, self.frame)

        if not 0 <= self.field_difference <= 1:
            raise CustomValueError('Field difference must be between 0 and 1!', self, self.field_difference)

    def apply(
        self,
        clip: vs.VideoNode,
        filter: VSFunctionNoArgs | None = None
    ) -> vs.VideoNode:
        """
        Apply the interlaced fade to the frame of the given clip using the specified filter.

        If no filter is provided, it will use `vsdeinterlace.fix_interlaced_fades`.

        :param clip:        The clip to process.
        :param filter:      The filter to use. The callable must only accept a clip as an argument.

        :return:            The clip with the interlaced fade applied.
        """

        if filter is None:
            from vsdeinterlace import fix_interlaced_fades

            filter = fix_interlaced_fades

        if not callable(filter):
            raise CustomValueError('Filter must be a callable!', self, filter)

        return filter(clip)


class InterlacedFades(list[InterlacedFade]):
    """Class for holding a list of interlaced fades."""

    def __init__(self, fades: list[InterlacedFade] | list[dict[str, Any]] | None = None, **kwargs) -> None:
        if isinstance(fades, list) and fades and isinstance(fades[0], dict):
            fades = [InterlacedFade(**fade) for fade in fades]

        super().__init__(fades or [])

        NegativeFrameError.check(self.__class__, [fade.frame for fade in fallback(self, [])])

    def apply(
        self,
        clip: vs.VideoNode,
        filter: VSFunctionNoArgs | None = None
    ) -> vs.VideoNode:
        """
        Apply the interlaced fades to the clip using the specified filter.

        This filter is applied on all frames, so to properly handle dark/bright
        and other similar fades, you must handle them in the given filter.

        If no filter is provided, it will use `vsdeinterlace.fix_interlaced_fades`.

        :param clip:        The clip to process.
        :param filter:      The filter to use. The callable must only accept a clip as an argument.

        :return:            The clip with the interlaced fade applied.
        """

        if not self:
            return clip

        if filter is None:
            from vsdeinterlace import fix_interlaced_fades

            filter = fix_interlaced_fades

        if not callable(filter):
            raise CustomValueError('Filter must be a callable!', self, filter)

        return replace_ranges(
            clip, filter(clip), lambda n: n in set().union(*(fade.frame for fade in self))
        )

    def set_props(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Set the interlaced fade properties on the clip."""

        return replace_ranges(
            clip.std.SetFrameProps(WobblyInterlacedFades=False),
            clip.std.SetFrameProps(WobblyInterlacedFades=True),
            [fade.frame for fade in self]
        )

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for interlaced fades."""

        return 'interlaced fades'
