"""
Extends Build123d ShapeLists with spatial and dimensional selection shortcuts,
allowing natural and more ergonomic selectors

Usage:
    import b123d_positioning
    # ShapeList is patched globally upon import.
"""

from typing import Any
import warnings
import math
from build123d import ShapeList, Axis, Vertex, Edge, Face, Solid

FIRST = 0
LAST = -1
# Directional Primitives
TOP = (Axis.Z, LAST)
BOTTOM = (Axis.Z, FIRST)
FRONT = (Axis.Y, FIRST)
BACK = (Axis.Y, LAST)
LEFT = (Axis.X, FIRST)
RIGHT = (Axis.X, LAST)


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
                    stacklevel=3,
                )
            # Return a single shape from the tied group (mimics default OCCT fallback)
            return extreme_group[0]
        else:
            # Continue filtering the subset
            result = extreme_group

    return result


def _select_size(
    shapes: ShapeList, find_max: bool = True, as_list: bool = False, tol: float = 1e-5
) -> Any:
    """
    Core engine for dimensional selections (largest/smallest/longest/shortest).

    Args:
        shapes (ShapeList): The list of shapes to filter.
        find_max (bool): If True, finds largest/longest. If False, finds smallest/shortest.
        as_list (bool):
            If False (default), returns the single most extreme Shape by size.
            If True, returns a ShapeList containing all shapes tied for that size.
        tol (float): Relative tolerance for tie-breaking. Defaults to 1e-5 (0.001%).

    Returns:
        Any: A single Shape (if as_list=False) or a ShapeList (if as_list=True).
    """
    if not shapes:
        return shapes

    # 1. Evaluate sizes exactly once to avoid duplicate CAD kernel computations
    cached_sizes = [(s, _get_size(s)) for s in shapes]

    # 2. Find extreme value in O(N) time
    extreme_val = (
        max(cached_sizes, key=lambda x: x[1])[1]
        if find_max
        else min(cached_sizes, key=lambda x: x[1])[1]
    )

    # 3. Filter using cached floats and user-configurable relative tolerance
    extreme_group = ShapeList(
        [
            item[0]
            for item in cached_sizes
            if math.isclose(item[1], extreme_val, rel_tol=tol, abs_tol=1e-7)
        ]
    )

    if not as_list:
        if len(extreme_group) > 1:
            warnings.warn(
                f"Ambiguous selection: You asked for a single shape, but the current geometry "
                f"makes this ambiguous ({len(extreme_group)} shapes share this exact size). "
                f"Returning an arbitrary shape. To fix this, pass 'as_list=True' to select the "
                f"entire group, or use spatial selectors to narrow it down.",
                UserWarning,
                stacklevel=3,
            )
        return extreme_group[0]

    return extreme_group


# ==========================================
# DIMENSIONAL EXPLICIT INTERFACE
# ==========================================


def _make_sizer(find_max: bool = True):
    """Factory to generate size selector lambdas (largest/smallest/longest/shortest)."""
    return lambda self, as_list=False, tol=1e-5: _select_size(
        self, find_max=find_max, as_list=as_list, tol=tol
    )


ShapeList.largest = _make_sizer(find_max=True)
ShapeList.longest = ShapeList.largest
ShapeList.smallest = _make_sizer(find_max=False)
ShapeList.shortest = ShapeList.smallest


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


# ==========================================
# SPATIAL EXPLICIT INTERFACE
# ==========================================


def _make_sel(*directives: tuple[Axis, int]):
    """Factory to generate spatial selector lambdas."""
    return lambda self, as_list=False: _select(self, *directives, as_list=as_list)


# --- 1D Shortcuts (Single Axis) ---
ShapeList.bottom = _make_sel(BOTTOM)
ShapeList.top = _make_sel(TOP)
ShapeList.front = _make_sel(FRONT)
ShapeList.back = _make_sel(BACK)
ShapeList.left = _make_sel(LEFT)
ShapeList.right = _make_sel(RIGHT)

# --- 2D Shortcuts (Double Axis) ---
# Z & Y
ShapeList.bottom_front = _make_sel(BOTTOM, FRONT)
ShapeList.front_bottom = _make_sel(FRONT, BOTTOM)
ShapeList.bottom_back = _make_sel(BOTTOM, BACK)
ShapeList.back_bottom = _make_sel(BACK, BOTTOM)
ShapeList.top_front = _make_sel(TOP, FRONT)
ShapeList.front_top = _make_sel(FRONT, TOP)
ShapeList.top_back = _make_sel(TOP, BACK)
ShapeList.back_top = _make_sel(BACK, TOP)

# Z & X
ShapeList.bottom_left = _make_sel(BOTTOM, LEFT)
ShapeList.left_bottom = _make_sel(LEFT, BOTTOM)
ShapeList.bottom_right = _make_sel(BOTTOM, RIGHT)
ShapeList.right_bottom = _make_sel(RIGHT, BOTTOM)
ShapeList.top_left = _make_sel(TOP, LEFT)
ShapeList.left_top = _make_sel(LEFT, TOP)
ShapeList.top_right = _make_sel(TOP, RIGHT)
ShapeList.right_top = _make_sel(RIGHT, TOP)

# Y & X
ShapeList.front_left = _make_sel(FRONT, LEFT)
ShapeList.left_front = _make_sel(LEFT, FRONT)
ShapeList.front_right = _make_sel(FRONT, RIGHT)
ShapeList.right_front = _make_sel(RIGHT, FRONT)
ShapeList.back_left = _make_sel(BACK, LEFT)
ShapeList.left_back = _make_sel(LEFT, BACK)
ShapeList.back_right = _make_sel(BACK, RIGHT)
ShapeList.right_back = _make_sel(RIGHT, BACK)

# --- 3D Shortcuts (Triple Axis) ---
# (-Z, -Y, -X)
ShapeList.bottom_front_left = _make_sel(BOTTOM, FRONT, LEFT)
ShapeList.bottom_left_front = _make_sel(BOTTOM, LEFT, FRONT)
ShapeList.front_bottom_left = _make_sel(FRONT, BOTTOM, LEFT)
ShapeList.front_left_bottom = _make_sel(FRONT, LEFT, BOTTOM)
ShapeList.left_bottom_front = _make_sel(LEFT, BOTTOM, FRONT)
ShapeList.left_front_bottom = _make_sel(LEFT, FRONT, BOTTOM)

# (-Z, -Y, +X)
ShapeList.bottom_front_right = _make_sel(BOTTOM, FRONT, RIGHT)
ShapeList.bottom_right_front = _make_sel(BOTTOM, RIGHT, FRONT)
ShapeList.front_bottom_right = _make_sel(FRONT, BOTTOM, RIGHT)
ShapeList.front_right_bottom = _make_sel(FRONT, RIGHT, BOTTOM)
ShapeList.right_bottom_front = _make_sel(RIGHT, BOTTOM, FRONT)
ShapeList.right_front_bottom = _make_sel(RIGHT, FRONT, BOTTOM)

# (-Z, +Y, -X)
ShapeList.bottom_back_left = _make_sel(BOTTOM, BACK, LEFT)
ShapeList.bottom_left_back = _make_sel(BOTTOM, LEFT, BACK)
ShapeList.back_bottom_left = _make_sel(BACK, BOTTOM, LEFT)
ShapeList.back_left_bottom = _make_sel(BACK, LEFT, BOTTOM)
ShapeList.left_bottom_back = _make_sel(LEFT, BOTTOM, BACK)
ShapeList.left_back_bottom = _make_sel(LEFT, BACK, BOTTOM)

# (-Z, +Y, +X)
ShapeList.bottom_back_right = _make_sel(BOTTOM, BACK, RIGHT)
ShapeList.bottom_right_back = _make_sel(BOTTOM, RIGHT, BACK)
ShapeList.back_bottom_right = _make_sel(BACK, BOTTOM, RIGHT)
ShapeList.back_right_bottom = _make_sel(BACK, RIGHT, BOTTOM)
ShapeList.right_bottom_back = _make_sel(RIGHT, BOTTOM, BACK)
ShapeList.right_back_bottom = _make_sel(RIGHT, BACK, BOTTOM)

# (+Z, -Y, -X)
ShapeList.top_front_left = _make_sel(TOP, FRONT, LEFT)
ShapeList.top_left_front = _make_sel(TOP, LEFT, FRONT)
ShapeList.front_top_left = _make_sel(FRONT, TOP, LEFT)
ShapeList.front_left_top = _make_sel(FRONT, LEFT, TOP)
ShapeList.left_top_front = _make_sel(LEFT, TOP, FRONT)
ShapeList.left_front_top = _make_sel(LEFT, FRONT, TOP)

# (+Z, -Y, +X)
ShapeList.top_front_right = _make_sel(TOP, FRONT, RIGHT)
ShapeList.top_right_front = _make_sel(TOP, RIGHT, FRONT)
ShapeList.front_top_right = _make_sel(FRONT, TOP, RIGHT)
ShapeList.front_right_top = _make_sel(FRONT, RIGHT, TOP)
ShapeList.right_top_front = _make_sel(RIGHT, TOP, FRONT)
ShapeList.right_front_top = _make_sel(RIGHT, FRONT, TOP)

# (+Z, +Y, -X)
ShapeList.top_back_left = _make_sel(TOP, BACK, LEFT)
ShapeList.top_left_back = _make_sel(TOP, LEFT, BACK)
ShapeList.back_top_left = _make_sel(BACK, TOP, LEFT)
ShapeList.back_left_top = _make_sel(BACK, LEFT, TOP)
ShapeList.left_top_back = _make_sel(LEFT, TOP, BACK)
ShapeList.left_back_top = _make_sel(LEFT, BACK, TOP)

# (+Z, +Y, +X)
ShapeList.top_back_right = _make_sel(TOP, BACK, RIGHT)
ShapeList.top_right_back = _make_sel(TOP, RIGHT, BACK)
ShapeList.back_top_right = _make_sel(BACK, TOP, RIGHT)
ShapeList.back_right_top = _make_sel(BACK, RIGHT, TOP)
ShapeList.right_top_back = _make_sel(RIGHT, TOP, BACK)
ShapeList.right_back_top = _make_sel(RIGHT, BACK, TOP)
