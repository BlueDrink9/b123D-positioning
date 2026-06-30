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
    shapes: ShapeList, *directives: tuple[Axis, int], group: bool = False
) -> Any:
    """
    Core engine for spatial selections.

    Args:
        shapes (ShapeList): The list of shapes to filter.
        directives (tuple[Axis, int]): A sequence of Axis and Index (FIRST/LAST) instructions.
        single (bool):
            If True, uses sort_by for the final directive to return a single shape.
            If False, uses group_by for all directives to return a grouped ShapeList.

    Returns:
        Any: A single Shape (if single=True) or a ShapeList (if single=False).
    """
    if not shapes:
        return shapes

    result = shapes
    for i, (axis, idx) in enumerate(directives):
        groups = result.group_by(axis)
        extreme_group = groups[idx]

        if not group and i == len(directives) - 1:
            if len(extreme_group) > 1:
                warnings.warn(
                    f"Ambiguous selection: You asked for a single shape, but the current geometry "
                    f"makes this ambiguous ({len(extreme_group)} shapes share this exact boundary). "
                    f"Returning an arbitrary shape. To fix this, use an 'all_' prefix to select the "
                    f"entire group, or chain more axes (e.g., 'top_left()') to narrow it down.",
                    UserWarning,
                    stacklevel=3
                )
            # Return a single shape from the tied group (mimics default OCCT fallback)
            return extreme_group[idx]
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
ShapeList.all_bottom = lambda self: _select(self, (Axis.Z, FIRST), group=True)

ShapeList.top = lambda self: _select(self, (Axis.Z, LAST))
ShapeList.all_top = lambda self: _select(self, (Axis.Z, LAST), group=True)

ShapeList.front = lambda self: _select(self, (Axis.Y, FIRST))
ShapeList.all_front = lambda self: _select(self, (Axis.Y, FIRST), group=True)

ShapeList.back = lambda self: _select(self, (Axis.Y, LAST))
ShapeList.all_back = lambda self: _select(self, (Axis.Y, LAST), group=True)

ShapeList.left = lambda self: _select(self, (Axis.X, FIRST))
ShapeList.all_left = lambda self: _select(self, (Axis.X, FIRST), group=True)

ShapeList.right = lambda self: _select(self, (Axis.X, LAST))
ShapeList.all_right = lambda self: _select(self, (Axis.X, LAST), group=True)


# --- 2D Shortcuts (Double Axis) ---
ShapeList.bottom_front = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST)
)
ShapeList.all_bottom_front = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST), group=True
)

ShapeList.bottom_back = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST)
)
ShapeList.all_bottom_back = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST), group=True
)

ShapeList.bottom_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.X, FIRST)
)
ShapeList.all_bottom_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.X, FIRST), group=True
)

ShapeList.bottom_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.X, LAST)
)
ShapeList.all_bottom_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.X, LAST), group=True
)

ShapeList.top_front = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST)
)
ShapeList.all_top_front = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST), group=True
)

ShapeList.top_back = lambda self: _select(self, (Axis.Z, LAST), (Axis.Y, LAST))
ShapeList.all_top_back = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, LAST), group=True
)

ShapeList.top_left = lambda self: _select(self, (Axis.Z, LAST), (Axis.X, FIRST))
ShapeList.all_top_left = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.X, FIRST), group=True
)

ShapeList.top_right = lambda self: _select(self, (Axis.Z, LAST), (Axis.X, LAST))
ShapeList.all_top_right = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.X, LAST), group=True
)

ShapeList.front_left = lambda self: _select(
    self, (Axis.Y, FIRST), (Axis.X, FIRST)
)
ShapeList.all_front_left = lambda self: _select(
    self, (Axis.Y, FIRST), (Axis.X, FIRST), group=True
)

ShapeList.front_right = lambda self: _select(
    self, (Axis.Y, FIRST), (Axis.X, LAST)
)
ShapeList.all_front_right = lambda self: _select(
    self, (Axis.Y, FIRST), (Axis.X, LAST), group=True
)

ShapeList.back_left = lambda self: _select(
    self, (Axis.Y, LAST), (Axis.X, FIRST)
)
ShapeList.all_back_left = lambda self: _select(
    self, (Axis.Y, LAST), (Axis.X, FIRST), group=True
)

ShapeList.back_right = lambda self: _select(
    self, (Axis.Y, LAST), (Axis.X, LAST)
)
ShapeList.all_back_right = lambda self: _select(
    self, (Axis.Y, LAST), (Axis.X, LAST), group=True
)


# --- 3D Shortcuts (Triple Axis) ---
ShapeList.bottom_front_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, FIRST)
)
ShapeList.all_bottom_front_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, FIRST), group=True
)

ShapeList.bottom_front_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, LAST)
)
ShapeList.all_bottom_front_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, LAST), group=True
)

ShapeList.bottom_back_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, FIRST)
)
ShapeList.all_bottom_back_left = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, FIRST), group=True
)

ShapeList.bottom_back_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, LAST)
)
ShapeList.all_bottom_back_right = lambda self: _select(
    self, (Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, LAST), group=True
)

ShapeList.top_front_left = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, FIRST)
)
ShapeList.all_top_front_left = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, FIRST), group=True
)

ShapeList.top_front_right = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, LAST)
)
ShapeList.all_top_front_right = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, LAST), group=True
)

ShapeList.top_back_left = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, FIRST)
)
ShapeList.all_top_back_left = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, FIRST), group=True
)

ShapeList.top_back_right = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, LAST)
)
ShapeList.all_top_back_right = lambda self: _select(
    self, (Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, LAST), group=True
)
