from typing import Any

from vstools import vs, replace_ranges
from vsdeinterlace import fix_interlaced_fades

from ...types import FilteringPositionEnum

from ...data.parse import WobblyParser
from .abstract import AbstractProcessingStrategy

__all__ = [
    'AdaptiveFixInterlacedFadesStrategy',
]


class _FrameRangeGrouper:
    """Helper class for grouping frame numbers into ranges."""

    def group_frames_into_ranges(self, clip: vs.VideoNode, frame_nums: list[int], max_gap: int = 3) -> list[tuple[int, int]]:
        """
        Group frame numbers into ranges if they are close enough together.

        :param clip:        Clip used to determine valid frame range
        :param frame_nums:  List of frame numbers to group
        :param max_gap:     Maximum gap between frames to consider them part of the same range

        :return:           List of (start, end) frame ranges
        """

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

        frame_groups = self._frame_grouper.group_frames_into_ranges(clip, wobbly_parsed.fade_frames, 5)

        return replace_ranges(clip, fix_interlaced_fades.Average(clip), frame_groups)

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

        frame_groups = self._frame_grouper.group_frames_into_ranges(clip, wobbly_parsed.fade_frames, 5)

        # TODO: Add fade detection and adaptive selection methods. For now, just use Average.

        return replace_ranges(clip, fix_interlaced_fades.Average(clip), frame_groups)

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE
