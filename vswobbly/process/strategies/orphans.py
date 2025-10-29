from vstools import (
    FieldBased,
    replace_ranges,
    vs,
    CustomValueError,
)
from vsdeinterlace import QTempGaussMC

from vswobbly.types import FilteringPositionEnum

from ...data.parse import WobblyParser
from .abstract import AbstractProcessingStrategy

__all__ = [
    'MatchBasedOrphanQTGMCStrategy',
]


FieldMatchGroupT = list[int]


class _OrphanFieldSplitter:
    """Helper class that splits orphaned fields into separate lists based on their field match."""

    def split_fields(
        self, wobbly_parsed: WobblyParser
    ) -> tuple[FieldMatchGroupT, FieldMatchGroupT, FieldMatchGroupT, FieldMatchGroupT]:
        orphan_n, orphan_b, orphan_u, orphan_p = [], [], [], []

        for frame in wobbly_parsed.orphan_frames:
            match frame.match:
                case 'b':
                    orphan_b.append(frame.frame)
                case 'n':
                    orphan_n.append(frame.frame)
                case 'u':
                    orphan_u.append(frame.frame)
                case 'p':
                    orphan_p.append(frame.frame)
                case _:
                    raise CustomValueError(f'Unknown field match: {frame.match} ({frame.frame})', self.split_fields)

        return orphan_n, orphan_b, orphan_u, orphan_p


class MatchBasedOrphanQTGMCStrategy(AbstractProcessingStrategy):
    """Strategy for dealing with orphan fields using match-based deinterlacing."""

    def __init__(self) -> None:
        self._match_grouper = _OrphanFieldSplitter()

    # This is largely copied from my old parser.
    # This should ideally be rewritten at some point to not use QTGMC.
    def apply(
        self, clip: vs.VideoNode, wobbly_parsed: WobblyParser, qtgmc_obj: QTempGaussMC | None = None
    ) -> vs.VideoNode:
        """
        Apply match-based deinterlacing to the given frames using QTGMC.

        This works by using the field match applied to orphan fields
        to determine which field is the correct one to keep.
        The other field gets deinterlaced.

        :param clip:            The clip to process.
        :param wobbly_parsed:   The parsed wobbly file. See the `WobblyParser` class for more information,
                                including all the data that is available.
        :param qtgmc_obj:       The `vsdeinterlace.QTempGaussMC` object to use. If not provided, a new one will be created.
                                Every relevant method should be called on this object by the user if provided,
                                up until the "deinterlace" method, which will be called in this strategy.

        :return:                Clip with the processing applied to the selected frames.
        """

        clip = clip.std.SetFrameProps(wobbly_orphan_deint=False)
        field_order = FieldBased.from_param_or_video(wobbly_parsed.field_order, clip)

        clip = field_order.apply(clip)

        if qtgmc_obj is None:
            qtgmc_obj = self._qtgmc(clip)
        else:
            qtgmc_obj.clip = clip  # type: ignore

        deint = qtgmc_obj.deinterlace()  # type: ignore

        assert isinstance(deint, vs.VideoNode)

        deint = deint.std.SetFrameProps(wobbly_orphan_deint=True)
        deint = deint[field_order.is_tff :: 2]

        deint = replace_ranges(clip, deint, [orphan.frame for orphan in wobbly_parsed.orphan_frames.find_matches('b')])

        return deint

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE

    def _qtgmc(self, clip: vs.VideoNode) -> QTempGaussMC:
        """Create a QTGMC object for the given clip."""

        return (
            QTempGaussMC(clip)
            .prefilter(tr=1)
            .analyze()
            .denoise(tr=1)
            .basic(tr=1)
            .source_match(tr=1)
            .lossless(mode=QTempGaussMC.LosslessMode.POSTSMOOTH)
            .sharpen()
            .back_blend()
            .sharpen_limit(mode=QTempGaussMC.SharpLimitMode.TEMPORAL_POSTSMOOTH)
            .final(tr=1)
            .motion_blur()
        )
