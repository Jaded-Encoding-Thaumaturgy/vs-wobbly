from typing import Any

from vstools import (CustomValueError, DependencyNotFoundError,
                     VSFunctionKwArgs, replace_ranges, vs)

from vswobbly.types import FilteringPositionEnum

from ...data.parse import WobblyParser
from .abstract import AbstractProcessingStrategy

__all__ = [
    'MatchBasedOrphanQTGMCStrategy',
]


FieldMatchGroupT = list[int]


class _OrphanFieldSplitter:
    """Helper class that splits orphaned fields into separate lists based on their field match."""

    def split_fields(self, wobbly_parsed: WobblyParser) -> tuple[FieldMatchGroupT, FieldMatchGroupT, FieldMatchGroupT, FieldMatchGroupT]:
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
    def apply(self, clip: vs.VideoNode, wobbly_parsed: WobblyParser) -> vs.VideoNode:
        """
        Apply match-based deinterlacing to the given frames using QTGMC.

        This works by using the field match applied to orphan fields
        to determine which field is the correct one to keep.
        The other field gets deinterlaced.

        :param clip:            The clip to process.
        :param wobbly_parsed:   The parsed wobbly file. See the `WobblyParser` class for more information,
                                including all the data that is available.

        :return:                Clip with the processing applied to the selected frames.
        """

        try:
            from vsdeinterlace import QTempGaussMC, SourceMatchMode, LosslessMode
            from havsfunc import QTGMC
        except ImportError:
            raise DependencyNotFoundError(self.apply, 'havsfunc')

        clip = clip.std.SetFrameProps(wobbly_orphan_deint=False)

        qtgmc_kwargs = (
            self._qtgmc_kwargs()
            | dict(
                TFF=wobbly_parsed.field_order.is_tff,
                FPSDivisor=1,
                InputType=0,
            )
        )

        deint_clip = self._qtgmc(QTGMC, clip, **(qtgmc_kwargs | dict()))
        qtgmc = deint_clip[wobbly_parsed.field_order.is_tff::2]

        # qtgmc = (
        #     QTempGaussMC(clip, tff=wobbly_parsed.field_order.is_tff)
        #     .prefilter(tr=1)
        #     .basic(tr=1)
        #     .denoise(tr=1)
        #     .source_match(mode=SourceMatchMode.TWICE_REFINED)
        #     .lossless(mode=LosslessMode.POSTSMOOTH)
        #     .sharpen()
        #     .sharpen_limit()
        #     .motion_blur()
        #     .back_blend()
        #     .final(tr=3)
        #     .process(blksize=8)
        # )[wobbly_parsed.field_order.is_tff::2]

        n_deint_frames = [
            f.frame for f in wobbly_parsed.orphan_frames.find_matches('n')
            if wobbly_parsed.field_matches[f.frame] == 'c'
        ]

        b_deint_frames = [
            f.frame for f in wobbly_parsed.orphan_frames.find_matches('b')
            if wobbly_parsed.field_matches[f.frame] == 'c'
        ]

        if not n_deint_frames and not b_deint_frames:
            return clip

        clip = replace_ranges(clip, qtgmc.std.SetFrameProps(wobbly_orphan_deint_field='n'), n_deint_frames)
        clip = replace_ranges(clip, qtgmc.std.SetFrameProps(wobbly_orphan_deint_field='b'), b_deint_frames)

        return clip

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE

    def _qtgmc(self, qtgmc: VSFunctionKwArgs, clip: vs.VideoNode, **kwargs: Any) -> vs.VideoNode:
        """Apply QTGMC to the given clip."""

        return qtgmc(clip, **kwargs).std.SetFrameProps(wobbly_orphan_deint=True)

    def _qtgmc_kwargs(self) -> dict[str, int | bool | str]:
        """QTGMC kwargs."""

        return dict(
            TR0=2, TR1=2, TR2=2, Lossless=2, EdiMode='EEDI3+NNEDI3', EdiQual=2, Rep0=4, Rep1=4, Rep2=3,
            SourceMatch=3, MatchPreset='Placebo', MatchPreset2='Placebo', Sbb=3, SubPel=4, SubPelInterp=2,
            RefineMotion=True, Preset='Placebo', TrueMotion=True, GlobalMotion=True, opencl=False
        )
