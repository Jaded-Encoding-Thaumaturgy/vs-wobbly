from abc import ABC, abstractmethod
from typing import Any

from vstools import vs

from ...data.parse import WobblyParser
from ...types import FilteringPositionEnum

__all__ = [
    'AbstractProcessingStrategy',
]


class AbstractProcessingStrategy(ABC):
    """
    Abstract base class for processing strategies.

    To write your own strategy, inherit from this class and implement
    the `apply` method and the `position` property.

    :param kwargs:              Additional keyword arguments.
                                These will be passed to the strategy when it is applied.
    """

    def __init__(self, **kwargs: Any) -> None:
        self._kwargs = kwargs

    @abstractmethod
    def apply(self, clip: vs.VideoNode, wobbly_parsed: WobblyParser) -> vs.VideoNode:
        """
        Apply the strategy to the given frames.

        :param clip:                The clip to process.
        :param wobbly_parsed:       The parsed wobbly file. See the `WobblyParser` class for more information,
                                    including all the data that is available.

        :return:                    Clip with the processing applied to the selected frames.
        """

        # It's recommended to use `replace_ranges` to apply your strategy.
        # This is gonna be the fastest and most straightforward way to do it,
        # and allows you to easily access surrounding frames if necessary.
        # See the implementations in this library for examples.

    @property
    @abstractmethod
    def position(self) -> FilteringPositionEnum:
        """When to apply the strategy."""

        return FilteringPositionEnum.POST_DECIMATE
