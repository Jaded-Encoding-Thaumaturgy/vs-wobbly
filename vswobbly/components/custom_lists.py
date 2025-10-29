from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from typing import Any, Iterable, Self

from vstools import CustomRuntimeError, CustomValueError, FrameRangesN, replace_ranges, vs

from ..types import FilteringPositionEnum
from .decimations import Decimations
from .types import PresetProtocol, SectionsProtocol

__all__ = ['CustomList', 'CustomLists']


@dataclass
class CustomList:
    """Class for holding a custom list."""

    name: str
    """The name of the custom list."""

    preset: PresetProtocol
    """The preset used for this custom list."""

    position: FilteringPositionEnum
    """When to apply the preset."""

    frames: FrameRangesN
    """The frames to apply the preset to."""

    def __init__(self, **kwargs) -> None:
        if 'frames' in kwargs and isinstance(kwargs['frames'], list):
            kwargs['frames'] = self._frames_to_ranges(kwargs['frames'])

        self.name = kwargs.get('name', '')
        self.preset = kwargs.get('preset', '')
        self.position = FilteringPositionEnum(kwargs.get('position', 'pre decimation'))
        self.frames = kwargs.get('frames', [])

    def __post_init__(self) -> None:
        """Validate the custom list after initialization."""

        if not self.frames:
            raise CustomValueError('Custom list frames cannot be empty!', self)

    def __call__(self, clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
        """Apply the custom list to a given clip."""

        return self.apply(clip, **kwargs)

    @staticmethod
    def _frames_to_ranges(frames: list[list[int]]) -> FrameRangesN:
        """Convert the frames to a list of frame ranges."""

        ranges = []
        invalid = []

        for frame in frames:
            if not isinstance(frame, (Iterable, int)):
                invalid.append(frame)
                continue

            if isinstance(frame, int):
                ranges.append(frame)
                continue

            if not isinstance(frame, tuple):
                frame = tuple(frame)

            if len(frame) != 2:
                invalid.append(frame)
                continue

            if frame[0] == frame[1]:
                ranges.append(frame[0])
                continue

            if frame[0] > frame[1]:
                invalid.append(frame)
                continue

            ranges.append(frame)

        if invalid:
            raise CustomValueError(f'Invalid frame ranges in custom list: {invalid}', CustomList)

        return ranges

    def apply(self, clip: vs.VideoNode, decimations: Decimations, **kwargs: Any) -> vs.VideoNode:
        """
        Apply the custom list to a given clip.

        If this custom list's :attr:`position` is :attr:`FilteringPositionEnum.POST_DECIMATE`,
        then this accounts for decimated frames by adjusting frame ranges
        based on the number of decimations that occur before each range endpoint.

        :param clip:            The clip to apply the custom list to.
        :param decimations:     The decimations to account for.

        :return:                The clip with the custom list applied.
        """

        try:
            flt = self.preset.apply(clip, **kwargs)
        except Exception as e:
            raise CustomRuntimeError(
                f"Error applying preset of custom list '{self.name}': "
                f'Invalid Python code in preset contents.\nOriginal error: {e}',
                self.apply,
            )

        for _range in self._frames_to_ranges(self.frames):
            range_flt = flt.std.SetFrameProps(
                WobblyPreset=str(self.preset), WobblyPresetPosition=self.position.value, WobblyPresetFrames=_range
            )

            if self.position is FilteringPositionEnum.POST_DECIMATE:
                first, last = _range if isinstance(_range, tuple) else (_range, _range)
                first -= bisect_left(decimations, first)
                last -= bisect_right(decimations, last)
                if first > last:
                    # Wobbly-generated scripts fail at runtime in this case, but that's annoying
                    continue
                effective_range = first if first == last else (first, last)
            else:
                effective_range = _range

            if isinstance(_range, tuple) and _range[1] >= clip.num_frames:
                _range = (_range[0], clip.num_frames - 1)

            explained_range = _range if _range == effective_range else f'{_range}, after decimation: {effective_range}'

            try:
                clip = replace_ranges(clip, range_flt, effective_range)
            except vs.Error as e:
                if 'invalid last frame' in str(e):
                    clip = replace_ranges(clip, range_flt, (effective_range[0], clip.num_frames - 1))
                else:
                    raise CustomRuntimeError(
                        f"Error applying custom list '{self.name}' (range: {explained_range}): {e}", self.apply
                    )
            except Exception as e:
                raise CustomRuntimeError(
                    f"Error applying custom list '{self.name}' (range: {explained_range}): {e}", self.apply
                )

        return clip


class CustomLists(list[CustomList]):
    """Class for holding a list of custom lists."""

    def __str__(self) -> str:
        return ', '.join(
            f'{custom_list.name}: preset={custom_list.preset}, '
            f'position={custom_list.position.name}, frames={custom_list.frames}'
            for custom_list in self
        )

    @classmethod
    def from_sections(cls, sections: SectionsProtocol) -> Self:
        """Create custom lists from sections."""

        return cls(
            CustomList(
                f'section_{section.start}',
                section.presets,
                FilteringPositionEnum.PRE_DECIMATE,
                FrameRangesN(section.start),
            )
            for section in sections
        )

    def apply(self, clip: vs.VideoNode, decimations: Decimations) -> vs.VideoNode:
        """Apply all custom lists to a given clip."""

        for custom_list in self:
            clip = custom_list.apply(clip, decimations)

        return clip

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for custom lists."""

        return 'custom lists'
