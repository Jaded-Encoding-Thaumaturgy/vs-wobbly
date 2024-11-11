from typing import Any, Iterable

from vstools import (CustomTypeError, CustomValueError, FuncExceptT,
                     SupportsString)

__all__ = [
    'NegativeFrameError',
]


class NegativeFrameError(CustomValueError):
    """Exception for negative frame numbers."""

    def __init__(
        self, func: FuncExceptT, invalid_frames: int | list[int],
        message: SupportsString = 'Frame number(s) cannot be negative!',
        reason: Any = '{invalid_frame}', **kwargs: Any
    ) -> None:
        super().__init__(message, func, reason, **kwargs, invalid_frame=invalid_frames)

    @classmethod
    def check(cls, func: FuncExceptT, frames: int | Iterable[int]) -> None:
        """Check if the frame number is negative."""

        if not frames:
            return

        if isinstance(frames, int):
            if frames < 0:
                raise cls(func, frames)

            return

        if not isinstance(frames, Iterable):
            raise CustomTypeError(
                'Frame number must be an integer!', func,
                invalid_frame=frames, reason=type(frames)
            )

        if any(not isinstance(frame, int) for frame in frames):
            raise CustomTypeError(
                'Frame numbers must be integers!', func,
                reason=type(frames)
            )

        for i, frame in enumerate(frames):
            if frame >= 0:
                if i > 0:  # Stop checking once we find a positive frame
                    raise cls(func, frames[:i])
                return

        raise cls(func, frames)
