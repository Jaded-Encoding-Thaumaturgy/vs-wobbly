from dataclasses import dataclass, field
from typing import Any, Self
from ..components import (CombedFrames, CustomLists, Decimations,
                            FieldMatches, FreezeFrames, InterlacedFades,
                            OrphanFrames, Presets, Sections, WobblyVideo)

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

    @classmethod
    def from_file(cls, file_path: SPathLike) -> Self:
        """Parse a wobbly object from a wobbly file."""

        from .builder import WobblyBuilder

        return WobblyBuilder(file_path).build()

    @staticmethod
    def _get_video_data(wob_file: SPath, data: dict[str, Any]) -> WobblyVideo:
        """Get the video data."""

        return WobblyVideo(
            wob_file.as_posix(),
            data.get('trim', None),
            data.get('source filter', '')
        )

    @staticmethod
    def _get_fieldbased_data(data: dict[str, Any]) -> FieldBasedT:
        """Get the fieldbased data."""

        vivtc_params = data.get('vfm parameters', {})
        order = bool(vivtc_params.get('order', 1))

        return FieldBased.from_param(order)
