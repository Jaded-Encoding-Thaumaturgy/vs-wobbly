from vstools import vs

from ...types import FilteringPositionEnum

from ...components import CustomList
from ...data.parse import WobblyParser
from .abstract import AbstractProcessingStrategy

__all__ = [
    'CustomListStrategy',
]


class CustomListStrategy(AbstractProcessingStrategy):
    """Default strategy that applies a custom list defined directly in the wobbly file."""

    def __init__(self, custom_list: CustomList) -> None:
        self._custom_list = custom_list

    def apply(self, clip: vs.VideoNode, wobbly_parsed: WobblyParser) -> vs.VideoNode:
        """
        Apply the custom list.

        :param clip:            The clip to process.
        :param wobbly_parsed:   The parsed wobbly file. See the `WobblyParser` class for more information,
                                including all the data that is available.

        :return:                Clip with the processing applied to the selected frames.
        """

        return self._custom_list.apply(clip, wobbly_parsed.decimations)

    @property
    def position(self) -> FilteringPositionEnum:
        """When to perform filtering."""

        return self._custom_list.position
