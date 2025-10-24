"""
Custom exceptions for feature engineering operations.

These exceptions enforce the principle of explicit errors over fallback values.
NO synthetic data or default values should be used when these are raised.
"""


class DataNotFoundError(Exception):
    """
    Raised when required data cannot be found - NO FALLBACK allowed.

    This error indicates that the requested calculation cannot proceed
    because necessary data is missing. The caller should NOT use default
    or estimated values - instead, inform the user and halt execution.

    Examples:
        - No census tract found within acceptable distance
        - No population data available for coordinates
        - Required demographic data is missing
    """
    pass


class InvalidStateError(Exception):
    """
    Raised when state is not supported by the model.

    The multi-state model only supports FL (Florida) and PA (Pennsylvania).
    This error is raised when attempting to calculate features for any
    other state.
    """
    pass


class InvalidCoordinatesError(Exception):
    """
    Raised when coordinates are invalid or outside expected bounds.

    Examples:
        - Latitude not in range -90 to 90
        - Longitude not in range -180 to 180
        - Coordinates fall outside FL or PA state boundaries
    """
    pass
