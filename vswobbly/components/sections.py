from dataclasses import dataclass, field
from math import ceil
from typing import Literal
from bisect import bisect_left

from vstools import Keyframes, vs

from ..exceptions import NegativeFrameError
from .decimations import Decimations
from .types import PresetProtocol, SectionProtocol
from .matches import FieldMatches

__all__ = [
    'Section',
    'Sections',
]


@dataclass
class Section(SectionProtocol):
    """Class for holding a section."""

    start: int
    """The start frame number."""

    presets: list[PresetProtocol] = field(default_factory=list)
    """The presets used for this section."""

    dominant_pattern: Literal[0, 1, 2, 3, 4, -1] = -1
    """The dominant pattern for this section. -1 means unknown."""

    def __post_init__(self):
        NegativeFrameError.check(self, self.start)

    def set_pattern(self, pattern: Literal[0, 1, 2, 3, 4]):
        """Set the dominant pattern for this section."""

        self.dominant_pattern = pattern


class Sections(list[Section]):
    """Class for holding sections."""

    def __init__(self, sections: list[Section]) -> None:
        super().__init__(sections or [])

    def __str__(self) -> str:
        if not self:
            return ''

        return ', '.join(str(section) for section in self)

    def to_keyframes(self, decimations: Decimations) -> Keyframes:
        """
        Convert the sections to keyframes.

        Accounts for decimated frames by adjusting section start frames
        based on the number of decimations that occur before each section start.

        :param decimations:     The decimations to account for.

        :return:                A keyframes object representing the section start frames adjusted for decimations.
        """

        if not self:
            return Keyframes([])

        if not decimations:
            return Keyframes([section.start for section in self])

        keyframes = [section.start - bisect_left(decimations, section.start) for section in self]

        return Keyframes(keyframes)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for sections."""

        return 'sections'

    def set_props(self, clip: vs.VideoNode, wobbly_parsed: 'WobblyParser') -> vs.VideoNode:  # noqa: F821
        """Set the section properties on the clip."""

        wclip = wobbly_parsed.work_clip
        # Ideally we get the cycle from the vfm params, but wobbly is hardcoded to 5 anyway.
        cycle = 5

        framerates = [wclip.fps.numerator / cycle * i for i in range(cycle, 0, -1)]

        fps_clips = [
            clip.std.AssumeFPS(None, int(fps), wclip.fps.denominator).std.SetFrameProps(
                WobblyCycleFps=int(fps // 1000), _DurationNum=int(fps), _DurationDen=wclip.fps.denominator
            )
            for fps in framerates
        ]

        max_dec = max(wobbly_parsed.decimations) + 1

        split_decimations = [
            [j for j in range(i * cycle, min((i + 1) * cycle, max_dec)) if j in wobbly_parsed.decimations]
            for i in range(ceil(max_dec / cycle))
        ]

        n_split_decimations = len(split_decimations)

        indices = [
            0 if (sd_idx := ceil(n / cycle)) >= n_split_decimations else len(split_decimations[sd_idx])
            for n in range(clip.num_frames)
        ]

        # Set pattern for each frame based on which section it falls into
        pattern_props = []

        for n in range(clip.num_frames):
            section_idx = 0

            for i, _ in enumerate(self):
                if i < len(self) - 1 and n >= self[i + 1].start:
                    continue

                section_idx = i
                break

            pattern_props.append(self[section_idx].dominant_pattern)

        return clip.std.FrameEval(lambda n: fps_clips[indices[n]].std.SetFrameProps(WobblyPattern=pattern_props[n]))

    def set_patterns(self, matches: FieldMatches) -> None:
        """Set the dominant patterns for all sections based on the matches."""

        import warnings

        warnings.warn(
            'Sections.set_patterns: This method is not yet implemented and will be implemented in a future version.',
            DeprecationWarning,
        )

        return
