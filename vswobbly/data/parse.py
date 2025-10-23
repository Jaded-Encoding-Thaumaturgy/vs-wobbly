from dataclasses import dataclass, field
from typing import Any, Self
from ..components import (
    CombedFrames,
    CustomLists,
    Decimations,
    FieldMatches,
    FreezeFrames,
    InterlacedFades,
    OrphanFrames,
    Presets,
    Sections,
    WobblyVideo,
)

from vstools import FieldBased, FieldBasedT, SPath, SPathLike, vs

__all__ = [
    'WobblyParser',
]


@dataclass
class WobblyParser:
    """Class for parsing wobbly files."""

    file_path: SPath
    """The path to the wobbly file."""

    work_clip: vs.VideoNode
    """The clip to work on."""

    video_data: WobblyVideo
    """Source clip information."""

    field_order: FieldBasedT = FieldBased.TFF
    """Field order of the source clip."""

    sections: Sections = field(default_factory=Sections)
    """Sections of the wobbly file."""

    field_matches: FieldMatches = field(default_factory=FieldMatches)
    """List of field matches."""

    decimations: Decimations = field(default_factory=Decimations)
    """List of frames to decimate."""

    presets: Presets = field(default_factory=Presets)
    """List of filtering presets."""

    custom_lists: CustomLists = field(default_factory=CustomLists)
    """List of custom filtering ranges."""

    freeze_frames: FreezeFrames = field(default_factory=FreezeFrames)
    """List of freeze frames."""

    interlaced_fades: InterlacedFades = field(default_factory=InterlacedFades)
    """List of interlaced fades."""

    combed_frames: CombedFrames = field(default_factory=CombedFrames)
    """List of combed frames."""

    orphan_frames: OrphanFrames = field(default_factory=OrphanFrames)
    """List of orphan frames."""

    def __init__(
        self,
        file_path: SPath,
        work_clip: vs.VideoNode,
        video_data: WobblyVideo,
        field_order: FieldBasedT,
        sections: Sections | None = None,
        field_matches: FieldMatches | None = None,
        decimations: Decimations | None = None,
        presets: Presets | None = None,
        custom_lists: CustomLists | None = None,
        freeze_frames: FreezeFrames | None = None,
        interlaced_fades: InterlacedFades | None = None,
        combed_frames: CombedFrames | None = None,
        orphan_frames: OrphanFrames | None = None,
    ) -> None:
        self.file_path = file_path
        self.work_clip = work_clip
        self.video_data = video_data
        self.field_order = field_order

        self.sections = sections or Sections()
        self.field_matches = field_matches or FieldMatches()
        self.decimations = decimations or Decimations()
        self.presets = presets or Presets()
        self.custom_lists = custom_lists or CustomLists()
        self.freeze_frames = freeze_frames or FreezeFrames()
        self.interlaced_fades = interlaced_fades or InterlacedFades()
        self.combed_frames = combed_frames or CombedFrames()
        self.orphan_frames = orphan_frames or OrphanFrames()

    @classmethod
    def from_file(cls, file_path: SPathLike) -> Self:
        """Parse a wobbly object from a wobbly file."""

        from .builder import WobblyBuilder

        return WobblyBuilder(file_path).build()

    @staticmethod
    def _get_video_data(wob_file: SPath, data: dict[str, Any]) -> WobblyVideo:
        """Get the video data."""

        return WobblyVideo(wob_file.as_posix(), data.get('trim', None), data.get('source filter', ''))

    @staticmethod
    def _get_fieldbased_data(data: dict[str, Any]) -> FieldBasedT:
        """Get the fieldbased data."""

        vivtc_params = data.get('vfm parameters', {})
        order = bool(vivtc_params.get('order', 1))

        return FieldBased.from_param(order)
