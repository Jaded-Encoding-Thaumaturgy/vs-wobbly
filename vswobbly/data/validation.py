from typing import Any

from ..exceptions import WobblyValidationError


class WobblyValidator:
    """Class for validating wobbly files."""

    @staticmethod
    def validate_json_structure(data: dict[str, Any]) -> None:
        """Validate the JSON structure of a wobbly file."""

        required_fields = {
            'input file',
            'source filter',
        }

        missing = required_fields - set(data.keys())

        if missing:
            raise WobblyValidationError(
                f"Missing required fields: {missing}", WobblyValidator.validate_json_structure
            )

    @staticmethod
    def validate_version(data: dict[str, Any]) -> None:
        """Validate the version of a wobbly file."""

        if (version := data.get('wobbly version', 0)) < 6:
            raise WobblyValidationError(
                f"Unsupported wobbly version: {version}. Minimum supported version is 8. Please update!",
                WobblyValidator.validate_version
            )

