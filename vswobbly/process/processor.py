from dataclasses import dataclass, field
from typing import Self

from vstools import SPathLike, FieldBased, vs
from vswobbly.data.parse import WobblyParser
from vswobbly.types import FilteringPositionEnum

from .strategies.abstract import AbstractProcessingStrategy
from .strategies.base import ProcessingStrategyManager

__all__ = [
    'WobblyProcessor'
]


@dataclass
class WobblyProcessor(ProcessingStrategyManager):
    """Class for processing a videonode using the data parsed from a wobbly file."""

    work_clip: vs.VideoNode
    """The videonode to process."""

    parser: WobblyParser
    """The parsed wobbly data."""

    # Strategies for handling certain types of issues.
    strategies: list[AbstractProcessingStrategy] = field(default_factory=list)
    """
    The strategies to use during specific processing steps.
    This can be strategies like combed-frame handling, how to deinterlace orphan fields, etc.
    See the `AbstractProcessingStrategy` class for more information.
    """

    def __init__(
        self,
        parser: WobblyParser,
        work_clip: vs.VideoNode | None = None,
        strategies: list[AbstractProcessingStrategy] = []
    ) -> None:
        if work_clip is None:
            work_clip = parser.work_clip

        self.work_clip = work_clip
        self.parser = parser
        self.strategies = strategies

    def __post_init__(self) -> None:
        if not isinstance(self.strategies, list):
            self.strategies = [self.strategies]

    @classmethod
    def from_file(
        cls,
        wobbly_filepath: SPathLike,
        strategies: list[AbstractProcessingStrategy] | None = None,
    ) -> Self:
        """Create a processor from a wobbly file."""

        return cls(
            WobblyParser.from_file(wobbly_filepath),
            strategies=strategies,
        )

    def apply(self, clip: vs.VideoNode | None = None) -> vs.VideoNode:
        """Apply the wobbly processing to the given clip."""

        self._init_process(clip)

        self.apply_post_source()
        self.apply_post_field_match()
        self.apply_pre_decimation()
        self.apply_post_decimation()

        return self.proc_clip

    def _init_process(self, clip: vs.VideoNode | None = None) -> None:
        """Initialize the process."""

        self.proc_clip = clip or self.parser.work_clip
        self.init_strategies(self.parser, self.strategies)

    def apply_post_source(self) -> None:
        """Post-source filtering, followed by field matching."""

        self.apply_strategies_of_position(FilteringPositionEnum.POST_SOURCE)

        if any('orphan' in strategy.__class__.__name__.lower() for strategy in self.strategies):
            self.parser.field_matches.set_orphans_to_combed_matches(self.parser.orphan_frames)

        self.proc_clip = self.parser.sections.set_props(self.proc_clip, wobbly_parsed=self.parser)
        self.proc_clip = self.parser.field_matches.apply(self.proc_clip)
        self.proc_clip = self.parser.combed_frames.set_props(self.proc_clip)
        self.proc_clip = self.parser.interlaced_fades.set_props(self.proc_clip)

    def apply_post_field_match(self) -> None:
        """Post-field matching filtering."""

        self.apply_strategies_of_position(FilteringPositionEnum.POST_FIELD_MATCH)
        self.proc_clip = self.parser.freeze_frames.apply(self.proc_clip)

    def apply_pre_decimation(self) -> None:
        """
        Pre-decimation filtering. This should explicitly happen *after* post-field matching filtering
        because that's how presets work in wobbly. This is followed by decimation.
        """

        self.apply_strategies_of_position(FilteringPositionEnum.PRE_DECIMATE)
        self.proc_clip = self.parser.decimations.apply(self.proc_clip)

    def apply_post_decimation(self) -> None:
        """Post-decimation filtering."""

        self.apply_strategies_of_position(FilteringPositionEnum.POST_DECIMATE)
        self.proc_clip = FieldBased.PROGRESSIVE.apply(self.proc_clip)
