import logging

from jetpytools import CustomValueError, DependencyNotFoundError
from vsdeinterlace import QTempGaussMC
from vstools import (
    FieldBased,
    core,
    depth,
    expect_bits,
    get_prop,
    replace_ranges,
    vs,
)

from ...components.orphans import OrphanFrame, OrphanFrames
from ...data.parse import WobblyParser
from ...types import FilteringPositionEnum
from .abstract import AbstractProcessingStrategy

__all__ = [
    'MatchBasedOrphanQTGMCStrategy',
]

logger = logging.getLogger(__name__)


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

    def __init__(self, thr: float = 0.0025, qtgmc_obj: QTempGaussMC | None = None) -> None:
        """
        :param thr:             Threshold for deinterlacing orphan fields.

                                If the difference between an orphan field and its adjacent same-type field
                                (as determined by field match) exceeds this value, the orphan field will be deinterlaced.
                                This helps avoid unnecessary deinterlacing for minor changes like mouth flaps,
                                while ensuring that significant differences trigger deinterlacing as intended.

                                Lower values will deinterlace more, but may also deinterlace fields that don't really need it.
                                Valid values are between 0 and 1.

                                Default: 0.0025.
        :param qtgmc_obj:       The `vsdeinterlace.QTempGaussMC` object to use. If not provided, a new one will be created.
                                Every relevant method should be called on this object by the user,
                                up until the "deinterlace" method, which will be called in this strategy.

                                Default: Automatically created by the strategy.
        """

        if not 0 <= thr <= 1:
            raise CustomValueError(f'Threshold must be between 0 and 1, not {thr}!', self.__init__)

        if qtgmc_obj is not None and not isinstance(qtgmc_obj, QTempGaussMC):
            raise CustomValueError(
                f'QTGMC object must be an instance of vsdeinterlace.QTempGaussMC, not {type(qtgmc_obj)}!', self.__init__
            )

        self.thr = thr
        self.qtgmc_obj = qtgmc_obj
        self._match_grouper = _OrphanFieldSplitter()

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

        clip = clip.std.SetFrameProps(wobbly_orphan_deint=False)

        field_order = FieldBased.from_param_or_video(wobbly_parsed.field_order, clip)

        clip = field_order.apply(clip)
        clip, orphans = self._should_deinterlace(clip, wobbly_parsed)

        if not orphans:
            return clip

        clip, bits = expect_bits(clip, 16)

        if self.qtgmc_obj is None:
            self.qtgmc_obj = self._qtgmc(clip)
        else:
            self.qtgmc_obj.clip = clip

        deint = self.qtgmc_obj.deinterlace()  # type: ignore

        assert isinstance(deint, vs.VideoNode)

        deint = deint[field_order.is_tff :: 2]
        deint = deint.std.SetFrameProps(wobbly_orphan_deint=True)

        frames = [o.frame for o in orphans if o.match in ('b', 'n')]

        logging.debug(f'Deinterlaced {len(frames)} orphan fields: {frames}')

        out = replace_ranges(clip, deint, frames)

        return depth(out, bits)

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return FilteringPositionEnum.PRE_DECIMATE

    def _should_deinterlace(self, clip: vs.VideoNode, wobbly_parsed: WobblyParser) -> tuple[vs.VideoNode, OrphanFrames]:
        """
        Determine if the clip should be deinterlaced.

        We do this by splitting the fields and comparing the similarity between them.
        Which fields get compared depends on the field order.

        :param clip: The clip to process.

        :return: A clip with the fieldmatches applied if it shouldn't be deinterlaced, and a list of orphans to deinterlace.
        """

        if not (orphan_fields := wobbly_parsed.orphan_frames):
            return clip, OrphanFrames([])

        if not hasattr(core, 'vszip'):
            raise DependencyNotFoundError(self.apply, 'vszip')

        is_tff = wobbly_parsed.field_order.is_tff

        orphans_to_keep = list[OrphanFrame]()
        orphans_to_deint = list[OrphanFrame]()

        for match in ('b', 'n'):
            for orphan in orphan_fields.find_matches(match):
                offset = -1 if match == 'b' else 1 if match == 'n' else 0

                sep_ref = clip[orphan.frame + offset].std.SeparateFields()[is_tff]
                sep_curr = clip[orphan.frame].std.SeparateFields()[is_tff]

                sep_avg = get_prop(sep_ref.vszip.PlaneAverage([0], sep_curr), 'psmDiff', float)

                logging.debug(
                    f'{orphan.frame} ({match}): {(sep_avg >= self.thr)=} '
                    f'(sep_ref={orphan.frame + offset}, sep_curr={orphan.frame}) ({sep_avg=})'
                )

                if sep_avg >= self.thr:
                    orphans_to_deint.append(orphan)
                else:
                    orphans_to_keep.append(orphan)

        orphans_to_deint = OrphanFrames(orphans_to_deint)

        if orphans_to_keep:
            clip = self._revert_field_matches(clip, wobbly_parsed, OrphanFrames(orphans_to_keep))

        return clip, orphans_to_deint

    def _revert_field_matches(
        self, clip: vs.VideoNode, wobbly_parsed: WobblyParser, orphans: OrphanFrames
    ) -> vs.VideoNode:
        reverted_matches = list(wobbly_parsed.field_matches.fieldhint_string)

        for orphan in orphans:
            reverted_matches[orphan.frame] = orphan.match

        reverted_matches = ''.join(reverted_matches)

        fh = clip.fh.FieldHint(None, wobbly_parsed.field_order.is_tff, reverted_matches)
        return replace_ranges(clip, fh.std.SetFrameProps(wobbly_orphan_deint=-1), [o.frame for o in orphans])

    def _qtgmc(self, clip: vs.VideoNode) -> QTempGaussMC:
        """Create a QTGMC object for the given clip."""

        tr = 1

        return (
            QTempGaussMC(clip)
            .prefilter(tr=tr)
            .analyze(blksize=128, refine=5)
            .basic(tr=tr, thsad=480)
            .source_match(tr=tr, mode=QTempGaussMC.SourceMatchMode.TWICE_REFINED)
            .lossless(mode=QTempGaussMC.LosslessMode.PRESHARPEN)
        )
