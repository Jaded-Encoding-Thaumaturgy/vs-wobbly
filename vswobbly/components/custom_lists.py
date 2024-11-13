from dataclasses import dataclass
from typing import Any, Self

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
            if isinstance(frame, int):
                ranges.append((frame, frame))
            elif len(frame) == 2:
                ranges.append(frame)
            else:
                invalid.append(frame)

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

        for start, end in self._frames_to_ranges(self.frames):
            range_flt = flt.std.SetFrameProps(
                WobblyPreset=str(self.preset),
                WobblyPresetPosition=self.position.value,
                WobblyPresetFrames=[start, end]
            )

            clip = replace_ranges(clip, range_flt, [(start, end)])

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
