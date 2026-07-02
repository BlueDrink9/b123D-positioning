"""
Extends Build123d ShapeLists with spatial and dimensional selection shortcuts,
allowing natural and more ergonomic selectors

Usage:
    import b123d_positioning
    # ShapeList is patched globally upon import.
"""

from typing import Any
import warnings
from build123d import ShapeList, Axis, Vertex, Edge, Face, Solid

FIRST = 0
LAST = -1


def _get_size(shape: Any) -> float:
    """
    Evaluates the physical size of a shape dynamically based on its class type.

    Args:
        shape (Any): A build123d Edge, Face, or Solid.

    Returns:
        float: The length, area, or volume of the shape.

    Raises:
        ValueError: If the shape is dimensionless (e.g., a Vertex) or unsupported.
    """
    match shape:
        case Edge():
            return shape.length
        case Face():
            return shape.area
        case Solid():
            return shape.volume
        case _:
            raise ValueError(
                f"Size operations not supported for {type(shape).__name__}."
            )


def _select(
    shapes: ShapeList, *directives: tuple[Axis, int], as_list: bool = False
) -> Any:
    """
    Core engine for spatial selections.

    Args:
        shapes (ShapeList): The list of shapes to filter.
        directives (tuple[Axis, int]): A sequence of Axis and Index (FIRST/LAST) instructions.
        as_list (bool):
            If False (default), returns the single most extreme Shape.
            If True, returns a ShapeList containing all shapes sharing that extreme boundary.

    Returns:
        Any: A single Shape (if as_list=False) or a ShapeList (if as_list=True).
    """
    if not shapes:
        return shapes

    result = shapes
    for i, (axis, idx) in enumerate(directives):
        groups = result.group_by(axis)
        extreme_group = groups[idx]

        if not as_list and i == len(directives) - 1:
            if len(extreme_group) > 1:
                warnings.warn(
                    f"Ambiguous selection: You asked for a single shape, but the current geometry "
                    f"makes this ambiguous ({len(extreme_group)} shapes share this exact boundary). "
                    f"Returning an arbitrary shape. To fix this, pass 'as_list=True' to select the "
                    f"entire group, or chain more axes (e.g., 'top_left()') to narrow it down.",
                    UserWarning,
                    stacklevel=3
                )
            # Return a single shape from the tied group (mimics default OCCT fallback)
            return extreme_group[0]
        else:
            # Continue filtering the subset
            result = extreme_group

    return result


def largest(self: ShapeList) -> Any:
    """Returns the largest shape in the list based on length, area, or volume."""
    return sorted(self, key=_get_size)[LAST] if self else self


def smallest(self: ShapeList) -> Any:
    """Returns the smallest shape in the list based on length, area, or volume."""
    return sorted(self, key=_get_size)[FIRST] if self else self


ShapeList.largest = largest
ShapeList.smallest = smallest

# ==========================================
# SPATIAL EXPLICIT INTERFACE
# ==========================================
# Z-Axis: bottom (FIRST), top (LAST)
# Y-Axis: front (FIRST), back (LAST)
# X-Axis: left (FIRST), right (LAST)

# --- 1D Shortcuts (Single Axis) ---
ShapeList.bottom = lambda self: _select(self, (Axis.Z, FIRST))

ShapeList.top = lambda self: _select(self, (Axis.Z, LAST))

ShapeList.front = lambda self: _select(self, (Axis.Y, FIRST))

ShapeList.back = lambda self: _select(self, (Axis.Y, LAST))

ShapeList.left = lambda self: _select(self, (Axis.X, FIRST))

ShapeList.right = lambda self: _select(self, (Axis.X, LAST))


# --- 2D Shortcuts (Double Axis) ---
ShapeList.bottom_front = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST)
)

ShapeList.bottom_back = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST)
)

ShapeList.bottom_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.X, FIRST)
)

ShapeList.bottom_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.X, LAST)
)

ShapeList.top_front = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST)
)

ShapeList.top_back = lambda self: _select(self, (Axis.Z, LAST), (Axis.Y, LAST))

ShapeList.top_left = lambda self: _select(self, (Axis.Z, LAST), (Axis.X, FIRST))

ShapeList.top_right = lambda self: _select(self, (Axis.Z, LAST), (Axis.X, LAST))

ShapeList.front_left = lambda self: _select(
    self, (Axis.Y, FIRST), (Axis.X, FIRST)
)

ShapeList.front_right = lambda self: _select(
    self, (Axis.Y, FIRST), (Axis.X, LAST)
)

ShapeList.back_left = lambda self: _select(
    self, (Axis.Y, LAST), (Axis.X, FIRST)
)

ShapeList.back_right = lambda self: _select(
    self, (Axis.Y, LAST), (Axis.X, LAST)
)


# --- 3D Shortcuts (Triple Axis) ---
ShapeList.bottom_front_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, FIRST)
)

ShapeList.bottom_front_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, LAST)
)

ShapeList.bottom_back_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, FIRST)
)

ShapeList.bottom_back_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, LAST)
)

ShapeList.top_front_left = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, FIRST)
)

ShapeList.top_front_right = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, LAST)
)

ShapeList.top_back_left = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, FIRST)
)

ShapeList.top_back_right = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, LAST)
)
