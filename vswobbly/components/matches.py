from vstools import CustomIndexError

from .types import ValidMatchT

__all__ = [
    'FieldMatches',
]


class FieldMatches(list[str]):
    """Class for holding field matches."""

    def __init__(self, matches: list[str] | None = None) -> None:
        super().__init__(matches or [])

    def __contains__(self, match: str | int) -> bool:
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

                return property(
                    getter,
                    doc=f"Get all frames with a '{match}' match."
                )

            setattr(cls, f'{match}_matches', create_match_property(match))

    def __str__(self) -> str:
        return ', '.join(str(match) for match in self)

    @property
    def fieldhint_string(self) -> str:
        """Get a string representation of the matches to pass to FieldHint."""

        return ''.join(match.match for match in self)

    def get_match_at_frame(self, frame: int) -> str:
        """Get the match value for a given frame index."""

        try:
            return self[frame]
        except IndexError:
            raise CustomIndexError(f'Frame {frame} is out of bounds (0-{len(self)})!', self.get_match_at_frame)

    @classmethod
    def wob_json_key(cls) -> str:
        """The JSON key for matches."""

        return 'matches'
