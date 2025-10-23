"""
Input normalization service.

Converts various input formats to standard {id, data} format for batch processing.

Examples:
    Simple list:
        ["text1", "text2"] → [{"id": 0, "data": "text1"}, {"id": 1, "data": "text2"}]

    Dict format:
        [{"id": "custom", "data": "text"}] → [{"id": "custom", "data": "text"}]

    Mixed:
        ["text", {"id": "custom", "data": "text2"}] → [{"id": 0, "data": "text"}, {"id": "custom", "data": "text2"}]
"""

from typing import Any, Dict, List


class InputNormalizer:
    """Service to normalize various input formats to standard {id, data} format."""

    @staticmethod
    def normalize(input_list: List[Any]) -> List[Dict[str, Any]]:
        """
        Convert various input formats to standard {id, data} format.

        Args:
            input_list: List of items (strings, numbers, dicts, etc.)

        Returns:
            List of dicts with {id, data} format

        Raises:
            TypeError: If input is not a list

        Examples:
            >>> InputNormalizer.normalize(["text1", "text2"])
            [{"id": 0, "data": "text1"}, {"id": 1, "data": "text2"}]

            >>> InputNormalizer.normalize([{"id": "custom", "data": "text"}])
            [{"id": "custom", "data": "text"}]

            >>> InputNormalizer.normalize(["text", {"id": 99, "data": "text2"}])
            [{"id": 0, "data": "text"}, {"id": 99, "data": "text2"}]
        """
        if not isinstance(input_list, list):
            raise TypeError(f"Input must be a list, got {type(input_list).__name__}")

        normalized = []
        auto_id_counter = 0

        for item in input_list:
            # Case 1: Already in {id, data} format - preserve as-is
            if isinstance(item, dict) and "id" in item and "data" in item:
                normalized.append(item)

            # Case 2: Dict with id but no data field
            elif isinstance(item, dict) and "id" in item:
                # Treat the whole dict as data
                normalized.append({"id": item["id"], "data": item})

            # Case 3: Dict without id field
            elif isinstance(item, dict):
                # Assign auto id
                normalized.append({"id": auto_id_counter, "data": item})
                auto_id_counter += 1

            # Case 4: Simple value (string, number, bool, None, etc.)
            else:
                normalized.append({"id": auto_id_counter, "data": item})
                auto_id_counter += 1

        return normalized

    @staticmethod
    def denormalize(normalized_list: List[Dict[str, Any]]) -> List[Any]:
        """
        Convert normalized {id, data} format back to simple list.

        Args:
            normalized_list: List of dicts with {id, data} format

        Returns:
            List of data values

        Examples:
            >>> InputNormalizer.denormalize([{"id": 0, "data": "text1"}, {"id": 1, "data": "text2"}])
            ["text1", "text2"]
        """
        return [item["data"] for item in normalized_list]
