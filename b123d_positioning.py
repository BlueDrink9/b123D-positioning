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


def _make_selector(*directives: tuple[Axis, int]):
    """Factory to generate spatial selector lambdas."""
    return lambda self, as_list=False: _select(self, *directives, as_list=as_list)

# --- 1D Shortcuts (Single Axis) ---
ShapeList.bottom = _make_selector((Axis.Z, FIRST))
ShapeList.top = _make_selector((Axis.Z, LAST))
ShapeList.front = _make_selector((Axis.Y, FIRST))
ShapeList.back = _make_selector((Axis.Y, LAST))
ShapeList.left = _make_selector((Axis.X, FIRST))
ShapeList.right = _make_selector((Axis.X, LAST))

# --- 2D Shortcuts (Double Axis) ---
# Z & Y
ShapeList.bottom_front = _make_selector((Axis.Z, FIRST), (Axis.Y, FIRST))
ShapeList.front_bottom = _make_selector((Axis.Y, FIRST), (Axis.Z, FIRST))
ShapeList.bottom_back = _make_selector((Axis.Z, FIRST), (Axis.Y, LAST))
ShapeList.back_bottom = _make_selector((Axis.Y, LAST), (Axis.Z, FIRST))
ShapeList.top_front = _make_selector((Axis.Z, LAST), (Axis.Y, FIRST))
ShapeList.front_top = _make_selector((Axis.Y, FIRST), (Axis.Z, LAST))
ShapeList.top_back = _make_selector((Axis.Z, LAST), (Axis.Y, LAST))
ShapeList.back_top = _make_selector((Axis.Y, LAST), (Axis.Z, LAST))

# Z & X
ShapeList.bottom_left = _make_selector((Axis.Z, FIRST), (Axis.X, FIRST))
ShapeList.left_bottom = _make_selector((Axis.X, FIRST), (Axis.Z, FIRST))
ShapeList.bottom_right = _make_selector((Axis.Z, FIRST), (Axis.X, LAST))
ShapeList.right_bottom = _make_selector((Axis.X, LAST), (Axis.Z, FIRST))
ShapeList.top_left = _make_selector((Axis.Z, LAST), (Axis.X, FIRST))
ShapeList.left_top = _make_selector((Axis.X, FIRST), (Axis.Z, LAST))
ShapeList.top_right = _make_selector((Axis.Z, LAST), (Axis.X, LAST))
ShapeList.right_top = _make_selector((Axis.X, LAST), (Axis.Z, LAST))

# Y & X
ShapeList.front_left = _make_selector((Axis.Y, FIRST), (Axis.X, FIRST))
ShapeList.left_front = _make_selector((Axis.X, FIRST), (Axis.Y, FIRST))
ShapeList.front_right = _make_selector((Axis.Y, FIRST), (Axis.X, LAST))
ShapeList.right_front = _make_selector((Axis.X, LAST), (Axis.Y, FIRST))
ShapeList.back_left = _make_selector((Axis.Y, LAST), (Axis.X, FIRST))
ShapeList.left_back = _make_selector((Axis.X, FIRST), (Axis.Y, LAST))
ShapeList.back_right = _make_selector((Axis.Y, LAST), (Axis.X, LAST))
ShapeList.right_back = _make_selector((Axis.X, LAST), (Axis.Y, LAST))

# --- 3D Shortcuts (Triple Axis) ---
# (-Z, -Y, -X)
ShapeList.bottom_front_left = _make_selector((Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, FIRST))
ShapeList.bottom_left_front = _make_selector((Axis.Z, FIRST), (Axis.X, FIRST), (Axis.Y, FIRST))
ShapeList.front_bottom_left = _make_selector((Axis.Y, FIRST), (Axis.Z, FIRST), (Axis.X, FIRST))
ShapeList.front_left_bottom = _make_selector((Axis.Y, FIRST), (Axis.X, FIRST), (Axis.Z, FIRST))
ShapeList.left_bottom_front = _make_selector((Axis.X, FIRST), (Axis.Z, FIRST), (Axis.Y, FIRST))
ShapeList.left_front_bottom = _make_selector((Axis.X, FIRST), (Axis.Y, FIRST), (Axis.Z, FIRST))

# (-Z, -Y, +X)
ShapeList.bottom_front_right = _make_selector((Axis.Z, FIRST), (Axis.Y, FIRST), (Axis.X, LAST))
ShapeList.bottom_right_front = _make_selector((Axis.Z, FIRST), (Axis.X, LAST), (Axis.Y, FIRST))
ShapeList.front_bottom_right = _make_selector((Axis.Y, FIRST), (Axis.Z, FIRST), (Axis.X, LAST))
ShapeList.front_right_bottom = _make_selector((Axis.Y, FIRST), (Axis.X, LAST), (Axis.Z, FIRST))
ShapeList.right_bottom_front = _make_selector((Axis.X, LAST), (Axis.Z, FIRST), (Axis.Y, FIRST))
ShapeList.right_front_bottom = _make_selector((Axis.X, LAST), (Axis.Y, FIRST), (Axis.Z, FIRST))

# (-Z, +Y, -X)
ShapeList.bottom_back_left = _make_selector((Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, FIRST))
ShapeList.bottom_left_back = _make_selector((Axis.Z, FIRST), (Axis.X, FIRST), (Axis.Y, LAST))
ShapeList.back_bottom_left = _make_selector((Axis.Y, LAST), (Axis.Z, FIRST), (Axis.X, FIRST))
ShapeList.back_left_bottom = _make_selector((Axis.Y, LAST), (Axis.X, FIRST), (Axis.Z, FIRST))
ShapeList.left_bottom_back = _make_selector((Axis.X, FIRST), (Axis.Z, FIRST), (Axis.Y, LAST))
ShapeList.left_back_bottom = _make_selector((Axis.X, FIRST), (Axis.Y, LAST), (Axis.Z, FIRST))

# (-Z, +Y, +X)
ShapeList.bottom_back_right = _make_selector((Axis.Z, FIRST), (Axis.Y, LAST), (Axis.X, LAST))
ShapeList.bottom_right_back = _make_selector((Axis.Z, FIRST), (Axis.X, LAST), (Axis.Y, LAST))
ShapeList.back_bottom_right = _make_selector((Axis.Y, LAST), (Axis.Z, FIRST), (Axis.X, LAST))
ShapeList.back_right_bottom = _make_selector((Axis.Y, LAST), (Axis.X, LAST), (Axis.Z, FIRST))
ShapeList.right_bottom_back = _make_selector((Axis.X, LAST), (Axis.Z, FIRST), (Axis.Y, LAST))
ShapeList.right_back_bottom = _make_selector((Axis.X, LAST), (Axis.Y, LAST), (Axis.Z, FIRST))

# (+Z, -Y, -X)
ShapeList.top_front_left = _make_selector((Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, FIRST))
ShapeList.top_left_front = _make_selector((Axis.Z, LAST), (Axis.X, FIRST), (Axis.Y, FIRST))
ShapeList.front_top_left = _make_selector((Axis.Y, FIRST), (Axis.Z, LAST), (Axis.X, FIRST))
ShapeList.front_left_top = _make_selector((Axis.Y, FIRST), (Axis.X, FIRST), (Axis.Z, LAST))
ShapeList.left_top_front = _make_selector((Axis.X, FIRST), (Axis.Z, LAST), (Axis.Y, FIRST))
ShapeList.left_front_top = _make_selector((Axis.X, FIRST), (Axis.Y, FIRST), (Axis.Z, LAST))

# (+Z, -Y, +X)
ShapeList.top_front_right = _make_selector((Axis.Z, LAST), (Axis.Y, FIRST), (Axis.X, LAST))
ShapeList.top_right_front = _make_selector((Axis.Z, LAST), (Axis.X, LAST), (Axis.Y, FIRST))
ShapeList.front_top_right = _make_selector((Axis.Y, FIRST), (Axis.Z, LAST), (Axis.X, LAST))
ShapeList.front_right_top = _make_selector((Axis.Y, FIRST), (Axis.X, LAST), (Axis.Z, LAST))
ShapeList.right_top_front = _make_selector((Axis.X, LAST), (Axis.Z, LAST), (Axis.Y, FIRST))
ShapeList.right_front_top = _make_selector((Axis.X, LAST), (Axis.Y, FIRST), (Axis.Z, LAST))

# (+Z, +Y, -X)
ShapeList.top_back_left = _make_selector((Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, FIRST))
ShapeList.top_left_back = _make_selector((Axis.Z, LAST), (Axis.X, FIRST), (Axis.Y, LAST))
ShapeList.back_top_left = _make_selector((Axis.Y, LAST), (Axis.Z, LAST), (Axis.X, FIRST))
ShapeList.back_left_top = _make_selector((Axis.Y, LAST), (Axis.X, FIRST), (Axis.Z, LAST))
ShapeList.left_top_back = _make_selector((Axis.X, FIRST), (Axis.Z, LAST), (Axis.Y, LAST))
ShapeList.left_back_top = _make_selector((Axis.X, FIRST), (Axis.Y, LAST), (Axis.Z, LAST))

# (+Z, +Y, +X)
ShapeList.top_back_right = _make_selector((Axis.Z, LAST), (Axis.Y, LAST), (Axis.X, LAST))
ShapeList.top_right_back = _make_selector((Axis.Z, LAST), (Axis.X, LAST), (Axis.Y, LAST))
ShapeList.back_top_right = _make_selector((Axis.Y, LAST), (Axis.Z, LAST), (Axis.X, LAST))
ShapeList.back_right_top = _make_selector((Axis.Y, LAST), (Axis.X, LAST), (Axis.Z, LAST))
ShapeList.right_top_back = _make_selector((Axis.X, LAST), (Axis.Z, LAST), (Axis.Y, LAST))
ShapeList.right_back_top = _make_selector((Axis.X, LAST), (Axis.Y, LAST), (Axis.Z, LAST))
