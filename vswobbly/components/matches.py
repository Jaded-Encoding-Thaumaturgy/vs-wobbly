from typing import Any
from vstools import CustomIndexError

from vstools import CustomValueError, DependencyNotFoundError, vs, core, FieldBased
from .types import ValidMatchT

__all__ = [
    'FieldMatches',
]


class FieldMatches(list[str]):
    """Class for holding field matches."""

    def __init__(self, matches: list[str] | None = None) -> None:
        super().__init__(matches or [])

    def __contains__(self, match: str | int | Any) -> bool:
        if isinstance(match, str):
            return any(m == match for m in self)

        if isinstance(match, int):
            return any(m == match for m in self)

        return match in self

    def __init_subclass__(cls) -> None:
        """Create match properties for the class."""

        for match in ValidMatchT.__args__:  # type: ignore
            def create_match_property(match: ValidMatchT) -> property:
                """Create a match property for the class."""

                def getter(self: FieldMatches) -> list[str]:
                    """Get all frames with a specific match."""

                    return [f for f in self if f.match == match]

                return property(getter, doc=f"Get all frames with a '{match}' match.")

            setattr(cls, f'{match}_matches', create_match_property(match))

    def __str__(self) -> str:
        return ', '.join(str(match) for match in self)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for matches."""

        return 'matches'

    @property
    def fieldhint_string(self) -> str:
        """Get a string representation of the matches to pass to FieldHint."""

        return ''.join(self)

    def get_match_at_frame(self, frame: int) -> str:
        """Get the match value for a given frame index."""

        try:
            return self[frame]
        except IndexError:
            raise CustomIndexError(f'Frame {frame} is out of bounds (0-{len(self)})!', self.get_match_at_frame)

    def set_orphans_to_combed_matches(self, orphans: Any) -> None:
        """Set the matches of orphan frames to 'c'."""

        from .orphans import OrphanFrames

        if not isinstance(orphans, OrphanFrames):
            raise CustomValueError('Orphans must be an OrphanFrames instance!', orphans)

        for orphan in orphans:
            self[orphan.frame] = 'c'

    def apply(self, clip: vs.VideoNode) -> vs.VideoNode:
        """Apply the matches to the clip."""

        if not hasattr(core, 'fh'):
            raise DependencyNotFoundError(self.apply, 'FieldHint')

        fh = clip.fh.FieldHint(
            tff=FieldBased.from_video(clip), matches=self.fieldhint_string
        )

        match_clips = dict[str, vs.VideoNode]()

        for match in set(self):
            match_clips[match] = fh.std.SetFrameProps(WobblyMatch=match)

        return fh.std.FrameEval(lambda n: match_clips[self[n]])
