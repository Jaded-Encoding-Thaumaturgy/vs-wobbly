from dataclasses import dataclass
from typing import Iterable, Any, Self

from vstools import (
    CustomRuntimeError, CustomValueError, FrameRangesN,
    replace_ranges, vs
)

from ..types import FilteringPositionEnum
from .types import PresetProtocol, SectionsProtocol

__all__ = [
    'CustomList',
    'CustomLists'
]


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

    def apply(self, clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
        """Apply the custom list to a given clip."""

        try:
            flt = self.preset.apply(clip, **kwargs)
        except Exception as e:
            raise CustomRuntimeError(
                f'Error applying preset of custom list \'{self.name}\': '
                f'Invalid Python code in preset contents. Original error: {e}',
                self.apply
            )

        for _range in self._frames_to_ranges(self.frames):
            range_flt = flt.std.SetFrameProps(
                WobblyPreset=str(self.preset),
                WobblyPresetPosition=self.position.value,
                WobblyPresetFrames=_range
            )

            if isinstance(_range, tuple) and _range[1] >= clip.num_frames - 1:
                _range = (_range[0], clip.num_frames - 2)

            try:
                clip = replace_ranges(clip, range_flt, _range)
            except vs.Error as e:
                if 'invalid last frame' in str(e):
                    clip = replace_ranges(clip, range_flt, (_range[0], clip.num_frames - 2))

                raise CustomRuntimeError(
                    f'Error applying custom list \'{self.name}\' (range: {_range}): {e}',
                    self.apply
                )
            except Exception as e:
                raise CustomRuntimeError(
                    f'Error applying custom list \'{self.name}\' (range: {_range}): {e}',
                    self.apply
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
                FrameRangesN(section.start)
            )
            for section in sections
        )

    def apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Apply all custom lists to a given clip."""

        for custom_list in self:
            clip = custom_list.apply(clip)

        return clip

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for custom lists."""

        return 'custom lists'
