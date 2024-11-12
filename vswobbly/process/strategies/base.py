from vstools import CustomValueError, vs
from ...data.parse import WobblyParser

from ...types import FilteringPositionEnum
from .abstract import AbstractProcessingStrategy

__all__ = [
    'ProcessingStrategyManager'
]


class ProcessingStrategyManager:
    """Class for managing and executing processing strategies in a specific order."""

    def init_strategies(self, wobbly_parsed: WobblyParser) -> None:
        """Initialize and validate the list of strategies."""

        strategies = [
            value for name, value in vars(self).items()
            if name.endswith('_strategy') and value is not None
        ]

        strategies.extend(custom_list for custom_list in wobbly_parsed.custom_lists)

        self._strategies = strategies

        self._ensure_strategies_callable()

    def apply_strategies_of_position(self, position: FilteringPositionEnum) -> vs.VideoNode:
        """Apply all strategies of a given position."""

        if not hasattr(self, '_strategies'):
            self.init_strategies(self.parser)

        strategies = self._get_strategies_for_position(position)

        for strategy in strategies:
            self.proc_clip = strategy.apply(self.proc_clip, wobbly_parsed=self.parser)

    def _ensure_strategies_callable(self) -> None:
        """Ensure that all strategies are callable."""

        uncallable = []

        for strategy in self._strategies:
            if not callable(strategy):
                uncallable.append(strategy)

        if uncallable:
            raise CustomValueError(
                f"The following strategies are not callable: {uncallable}", self.init_strategies
            )

    def _get_strategies_for_position(self, position: FilteringPositionEnum) -> list[AbstractProcessingStrategy]:
        """Get all strategies that should run at the given position."""

        return [
            strategy for strategy in self._strategies
            if strategy.position == position
        ]

