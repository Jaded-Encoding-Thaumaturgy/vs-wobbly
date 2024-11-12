from vsdeinterlace import vinverse
from vstools import replace_ranges, vs

from ...types import FilteringPositionEnum

from ...data.parse import WobblyParser
from .abstract import AbstractProcessingStrategy

__all__ = [
    'DecombVinverseStrategy',
]

class DecombVinverseStrategy(AbstractProcessingStrategy):
    """Decomb strategy using vinverse to get rid of combed frames."""

    def apply(self, clip: vs.VideoNode, wobbly_parsed: WobblyParser) -> vs.VideoNode:
        """
        Use vinverse to get rid of combing on the given frames.

        Note that vinverse may be destructive. Be cautious when applying this strategy.

        :param clip:            The clip to process.
        :param wobbly_parsed:   The parsed wobbly file. See the `WobblyParser` class for more information,
                                including all the data that is available.
        :param kwargs:          Additional keyword arguments.

        :return:                Clip with the processing applied to the selected frames.
        """

        return replace_ranges(clip, vinverse(clip), wobbly_parsed.combed_frames)

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE
