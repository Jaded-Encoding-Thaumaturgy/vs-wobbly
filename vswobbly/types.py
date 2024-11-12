from stgpytools import CustomStrEnum

__all__ = [
    'FilteringPositionEnum',
]


class FilteringPositionEnum(CustomStrEnum):
    """Enum denoting when to perform filtering."""

    POST_SOURCE = 'post source'
    """Perform filtering on the source clip."""

    POST_FIELD_MATCH = 'post field match'
    """Perform filtering after field matching."""

    PRE_DECIMATE = 'pre decimate'
    """Perform filtering before decimation."""

    POST_DECIMATE = 'post decimate'
    """Perform filtering after decimation."""
