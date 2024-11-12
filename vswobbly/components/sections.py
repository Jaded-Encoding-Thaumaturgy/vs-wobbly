from dataclasses import dataclass, field
from math import ceil

from vstools import Keyframes, vs

from ..exceptions import NegativeFrameError
from .decimations import Decimations
from .types import PresetProtocol, SectionProtocol

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

    def __post_init__(self):
        NegativeFrameError.check(self, self.start)


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

        :return:                A keyframes object representing the section start frames
                                adjusted for decimations.
        """

        keyframes = []

        for section in self:
            decimation_count = sum(1 for d in decimations if d < section.start)
            adjusted_start = section.start - decimation_count

            keyframes.append(adjusted_start)

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
            clip.std.AssumeFPS(None, int(fps), wclip.fps.denominator)
            .std.SetFrameProps(
                WobblyCycleFps=int(fps // 1000),
                _DurationNum=int(fps),
                _DurationDen=wclip.fps.denominator
            ) for fps in framerates
        ]

        max_dec = max(wobbly_parsed.decimations) + 1

        split_decimations = [
            [j for j in range(i * cycle, min((i + 1) * cycle, max_dec)) if j in wobbly_parsed.decimations]
            for i in range(ceil(max_dec / cycle))
        ]

        n_split_decimations = len(split_decimations)

        indices = [
            0 if (sd_idx := ceil(n / cycle)) >= n_split_decimations
            else len(split_decimations[sd_idx]) for n in range(clip.num_frames)
        ]

        return clip.std.FrameEval(lambda n: fps_clips[indices[n]])

