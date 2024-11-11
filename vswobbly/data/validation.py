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
