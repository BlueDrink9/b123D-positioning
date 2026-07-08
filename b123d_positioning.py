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
from build123d import ShapeList, Axis, Vertex, Edge, Face, Solid, Vector

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

# ==========================================
# ORIENTATION ENGINE
# ==========================================

AXIS_VECTORS = {
    Axis.X: Vector(1, 0, 0),
    Axis.Y: Vector(0, 1, 0),
    Axis.Z: Vector(0, 0, 1),
}


AXIS_NAMES = {
    Axis.X: "x",
    Axis.Y: "y",
    Axis.Z: "z",
}


def _select_orientation(
    shapes: ShapeList, mode: str, axis: Axis = None, as_list: bool = False
) -> Any:
    """
    Core engine for filtering shapes by structural orientation (horizontal, vertical, along, facing).

    Iterates through the provided ShapeList and filters items using `_check_orientation`.
    When requesting a single item (as_list=False), emits a warning if multiple shapes match
    the orientation criteria and returns the first matching instance.

    Args:
        shapes (ShapeList): The collection of Edges or Faces to filter.
        mode (str): The filtering mode ('horizontal', 'vertical', 'along', 'facing').
        axis (Axis, optional): The target coordinate axis for directional modes. Defaults to None.
        as_list (bool, optional):
            If False (default), returns a single arbitrary Shape from the matching group.
            If True, returns a ShapeList containing all matching shapes.

    Returns:
        Any: A single Shape (if as_list=False) or a ShapeList (if as_list=True).

    Raises:
        ValueError: If no shapes match the requested orientation, or if structural rules
            are violated (e.g., requesting 'facing' on an Edge).
    """
    if not shapes:
        return shapes

    matching = ShapeList([s for s in shapes if _check_orientation(s, mode, axis)])

    if not matching:
        if as_list:
            return ShapeList()
        # Safely resolve the string name for the error message
        name = f"{mode}_{AXIS_NAMES[axis]}" if axis in AXIS_NAMES else mode
        raise ValueError(f"No shapes matching orientation '{name}' were found.")

    if not as_list:
        if len(matching) > 1:
            # Safely resolve the string name for the warning message
            name = f"{mode}_{AXIS_NAMES[axis]}" if axis in AXIS_NAMES else mode
            warnings.warn(
                f"Ambiguous selection: You asked for a single shape using '{name}()', "
                f"but {len(matching)} shapes match this orientation. Returning an arbitrary shape. "
                f"To fix this, pass 'as_list=True' to select the entire group, or use spatial "
                f"selectors to narrow it down.",
                UserWarning,
                stacklevel=3,
            )
        return matching[0]

    return matching


def _check_orientation(s: Any, mode: str, axis: Axis) -> bool:
    """
    Evaluates whether a shape's primary geometric vector matches a target spatial orientation.

    For Edges, the primary vector is the Tangent line evaluated at the midpoint (t=0.5).
    For Faces, the primary vector is the perpendicular surface Normal.

    Args:
        s (Any): The build123d Edge or Face to evaluate.
        mode (str): The orientation mode to test. Valid options are:
            - 'horizontal': Tangent is orthogonal to Z (Edges) or Normal is parallel to Z (Faces).
            - 'vertical': Tangent is parallel to Z (Edges) or Normal is orthogonal to Z (Faces).
            - 'along': Tangent runs parallel to the specified axis (Edges only).
            - 'facing': Normal points parallel or anti-parallel to the specified axis (Faces only).
        axis (Axis): The target coordinate axis (required for 'along' and 'facing' modes).

    Returns:
        bool: True if the shape's orientation aligns with the target criteria.

    Raises:
        ValueError: If an unsupported shape type is passed, or if 'along' is applied to a Face
            or 'facing' is applied to an Edge.
    """
    if isinstance(s, Edge):
        if mode == "facing":
            raise ValueError(
                "The 'facing_*' selectors are for Faces. For Edges, use 'along_*'."
            )
        vec = s.tangent_at(0.5)
        if mode == "along":
            return _is_parallel(vec, AXIS_VECTORS[axis])
        elif mode == "horizontal":
            return _is_orthogonal(vec, AXIS_VECTORS[Axis.Z])
        elif mode == "vertical":
            return _is_parallel(vec, AXIS_VECTORS[Axis.Z])

    elif isinstance(s, Face):
        if mode == "along":
            raise ValueError(
                "The 'along_*' selectors are for Edges. For Faces, use 'facing_*'."
            )
        vec = s.normal_at()
        if mode == "facing":
            return _is_parallel(vec, AXIS_VECTORS[axis])
        elif mode == "horizontal":
            return _is_parallel(vec, AXIS_VECTORS[Axis.Z])
        elif mode == "vertical":
            return _is_orthogonal(vec, AXIS_VECTORS[Axis.Z])

    else:
        raise ValueError(
            f"Orientation selectors are not supported for {type(s).__name__}."
        )
    return False


def _is_parallel(vec1: Vector, vec2: Vector) -> bool:
    """Checks if two vectors are parallel or anti-parallel within standard CAD epsilon (1e-6)."""
    n1, n2 = vec1.normalized(), vec2.normalized()
    return abs(abs(n1.dot(n2)) - 1.0) < 1e-6


def _is_orthogonal(vec1: Vector, vec2: Vector) -> bool:
    """Checks if two vectors are perpendicular within standard CAD epsilon (1e-6)."""
    n1, n2 = vec1.normalized(), vec2.normalized()
    return abs(n1.dot(n2)) < 1e-6


# ==========================================
# ORIENTATION EXPLICIT INTERFACE
# ==========================================


def _make_orient_sel(mode: str, axis: Axis = None):
    """Factory to generate orientation selector lambdas."""
    return lambda self, as_list=False: _select_orientation(
        self, mode=mode, axis=axis, as_list=as_list
    )


# Universal Selectors (Works on both Edges and Faces)
ShapeList.horizontal = _make_orient_sel("horizontal")
ShapeList.vertical = _make_orient_sel("vertical")

# Edge Selectors (Line path / Tangent)
ShapeList.along_x = _make_orient_sel("along", Axis.X)
ShapeList.along_y = _make_orient_sel("along", Axis.Y)
ShapeList.along_z = _make_orient_sel("along", Axis.Z)

# Face Selectors (Surface Normal)
ShapeList.facing_x = _make_orient_sel("facing", Axis.X)
ShapeList.facing_y = _make_orient_sel("facing", Axis.Y)
ShapeList.facing_z = _make_orient_sel("facing", Axis.Z)
