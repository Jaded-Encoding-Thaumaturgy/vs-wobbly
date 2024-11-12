from typing import Any

from vstools import VSFunctionKwArgs, DependencyNotFoundError, replace_ranges, vs, CustomValueError

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
            from havsfunc import QTGMC
        except ImportError:
            raise DependencyNotFoundError(self.apply, 'havsfunc')

        qtgmc_kwargs = self._qtgmc_kwargs | dict(FPSDivisor=1, TFF=wobbly_parsed.field_based.is_tff)

        deint_n = self._qtgmc(QTGMC, clip, not wobbly_parsed.field_based.field, **qtgmc_kwargs)
        deint_b = self._qtgmc(QTGMC, clip, wobbly_parsed.field_based.field, **qtgmc_kwargs)

        orphan_n, orphan_b, _, _ = self._match_grouper.split_fields(wobbly_parsed)

        deint = replace_ranges(clip, deint_n, orphan_n)
        deint = replace_ranges(deint, deint_b, orphan_b)

        return deint

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE

    def _qtgmc(self, qtgmc: VSFunctionKwArgs, clip: vs.VideoNode, slice_field: bool, **kwargs: Any) -> vs.VideoNode:
        """Apply QTGMC to the given clip."""

        return qtgmc(clip, **kwargs)[slice_field::2]

    def _qtgmc_kwargs(self) -> dict[str, int | bool | str]:
        """QTGMC kwargs."""

        return dict(
            TR0=2, TR1=2, TR2=2, Sharpness=0, Lossless=1, InputType=0,
            Rep0=3, Rep1=3, Rep2=2, SourceMatch=3, EdiMode='EEDI3+NNEDI3', EdiQual=2,
            Sbb=3, SubPel=4, SubPelInterp=2, opencl=False, RefineMotion=True,
            Preset='Placebo', MatchPreset='Placebo', MatchPreset2='Placebo'
        )
