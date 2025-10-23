from typing import Any

from vsdeinterlace import FixInterlacedFades
from vstools import CustomTypeError, replace_ranges, vs

from ...data.parse import WobblyParser
from ...types import FilteringPositionEnum
from .abstract import AbstractProcessingStrategy

__all__ = [
    'AdaptiveFixInterlacedFadesStrategy',
]


class _FrameRangeGrouper:
    """Helper class for grouping frame numbers into ranges."""

    def group_frames_into_ranges(
        self, clip: vs.VideoNode, frame_nums: list[int], max_gap: int = 3
    ) -> list[tuple[int, int]]:
        """
        Group frame numbers into ranges if they are close enough together.

        :param clip:        Clip used to determine valid frame range
        :param frame_nums:  List of frame numbers to group
        :param max_gap:     Maximum gap between frames to consider them part of the same range

        :return:           List of (start, end) frame ranges
        """

        frame_nums = [
            x.frame if not isinstance(x, int) and hasattr(x, 'frame') and isinstance(x.frame, int) else x
            for x in frame_nums
        ]

        if invalid_frames := [x for x in frame_nums if not isinstance(x, int)]:
            raise CustomTypeError(
                'All frame numbers must be integers or have an integer frame attribute!',
                self.group_frames_into_ranges,
                invalid_frames,
            )

        frame_nums = sorted(frame_nums)
        last_frame = clip.num_frames - 1

        ranges = []
        start = end = frame_nums[0]

        for curr in frame_nums[1:]:
            if curr > last_frame:
                break

            if curr - end > max_gap:
                ranges.append((start, end))
                start = curr

            end = curr

        if end <= last_frame:
            ranges.append((start, end))

        return ranges


class AverageFixInterlacedFadesStrategy(AbstractProcessingStrategy):
    """Strategy for fixing interlaced fades using the Average method."""

    def __init__(self) -> None:
        self._frame_grouper = _FrameRangeGrouper()

    def apply(self, clip: vs.VideoNode, wobbly_parsed: WobblyParser) -> vs.VideoNode:
        """
        Use FixInterlacedFades.Average to fix interlaced fades.

        :param clip:            The clip to process.
        :param wobbly_parsed:   The parsed wobbly file. See the `WobblyParser` class for more information,
                                including all the data that is available.
        :param kwargs:          Additional keyword arguments.

        :return:                Clip with the processing applied to the selected frames.
        """

        frame_groups = self._frame_grouper.group_frames_into_ranges(clip, wobbly_parsed.interlaced_fades, 5)

        return replace_ranges(clip, FixInterlacedFades.Average(clip), frame_groups)

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE


class AdaptiveFixInterlacedFadesStrategy(AbstractProcessingStrategy):
    """Strategy for fixing interlaced fades adaptively."""

    def __init__(self) -> None:
        self._frame_grouper = _FrameRangeGrouper()

    def apply(self, clip: vs.VideoNode, wobbly_parsed: WobblyParser, **kwargs: Any) -> vs.VideoNode:
        """
        Use FixInterlacedFades to fix interlaced fades, and apply it adaptively.

        This works by first combining all (nearly) adjacent frames into a list, and then comparing surrounding frames
        to determine if it's a fade from black or white. If it's unsure, it'll average instead.

        :param clip:            The clip to process.
        :param wobbly_parsed:   The parsed wobbly file. See the `WobblyParser` class for more information,
                                including all the data that is available.
        :param kwargs:          Additional keyword arguments.

        :return:                Clip with the processing applied to the selected frames.
        """

        frame_groups = self._frame_grouper.group_frames_into_ranges(clip, wobbly_parsed.interlaced_fades, 5)

        # TODO: Add fade detection and adaptive selection methods. For now, just use Average.

        return replace_ranges(clip, FixInterlacedFades.Average(clip), frame_groups)

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE
