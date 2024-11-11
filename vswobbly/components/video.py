from dataclasses import dataclass
from typing import Any

from vstools import CustomValueError, SPath, VSFunctionNoArgs, core, vs

__all__ = [
    'WobblyVideo',
]


@dataclass
class WobblyVideo:
    """Class for holding wobbly video data."""

    src_file: SPath
    """The path to the source file."""

    work_clip: vs.VideoNode
    """The clip to work on. Trimmed if necessary."""

    trim: tuple[int, int] | None
    """The trim to apply to the source clip. Inclusive/inclusive."""

    source_filter: VSFunctionNoArgs
    """The source filter to index the source file."""

    def __init__(self, src_file: SPath, wob_data: dict[str, Any]) -> None:
        self.src_file = SPath(src_file)
        self._set_trim(wob_data)

        self.source_filter = self._validate_source_filter(wob_data.get('source filter', ''))
        self._set_source_clip(wob_data.get('input file', str(self.src_file).removesuffix('.wob')))

    def _set_trim(self, wob_data: dict[str, Any]) -> None:
        trim_data = wob_data.get('trim')

        if not trim_data:
            self.trim = None

            return

        self.trim = tuple(trim_data[0])

    def _validate_source_filter(self, source_filter: str | VSFunctionNoArgs) -> VSFunctionNoArgs:
        """Validate the source filter and return the filter function."""

        if not source_filter:
            raise CustomValueError('Source filter cannot be empty!', self)

        if hasattr(source_filter, '__call__'):
            return source_filter

        if not isinstance(source_filter, str):
            raise CustomValueError('Invalid source filter!', self, source_filter)

        source_filter = source_filter.strip()

        if len(parts := source_filter.split('.')) != 2:
            raise CustomValueError('Invalid source filter format!', self, source_filter)

        namespace, filter_name = parts

        if not hasattr(core, namespace):
            raise CustomValueError(f'Namespace \'{namespace}\' not found in core', self)

        namespace_obj = getattr(core, namespace)

        if not hasattr(namespace_obj, filter_name):
            raise CustomValueError(f'Function \'{filter_name}\' not found in {namespace}', self)

        return getattr(namespace_obj, filter_name)

    def _set_source_clip(self, src_file: SPath) -> None:
        """Index and set the source clip using the source filter, and trim if necessary."""

        try:
            self.work_clip = self.source_filter(src_file)
        except Exception as e:
            raise CustomValueError(f'Error indexing source clip: {e}', self.__class__)

        if self.trim:
            self.work_clip = self.work_clip.std.Trim(self.trim[0], self.trim[1])
