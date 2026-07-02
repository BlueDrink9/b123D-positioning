"""
test_b123d_positioning.py
Unit tests for the Build123d ShapeList spatial and dimensional extensions.

Run with: `pytest test_b123d_positioning.py`
"""

import warnings
import pytest
from build123d import Box, Vector
import b123d_positioning  # Applies the monkey-patch to ShapeList


# ==========================================
# 1. EXTENTS (Largest / Smallest)
# ==========================================


def test_extents_faces():
    """Test that largest/smallest correctly identifies faces by area."""
    # Box dimensions: X=10, Y=6, Z=2
    # Resulting face areas: Z-normal=60, Y-normal=20, X-normal=12
    shape = Box(10, 6, 2)
    faces = shape.faces()

    assert faces.largest().area == pytest.approx(60)
    assert faces.smallest().area == pytest.approx(12)


def test_extents_edges():
    """Test that largest/smallest correctly identifies edges by length."""
    shape = Box(10, 6, 2)
    edges = shape.edges()

    assert edges.largest().length == 10
    assert edges.smallest().length == 2


def test_extents_vertex_raises_value_error():
    """Test that size operations on dimensionless Vertices raise a ValueError."""
    shape = Box(1, 1, 1)

    with pytest.raises(
        ValueError, match="Size operations not supported for Vertex"
    ):
        shape.vertices().largest()


# ==========================================
# 2. SPATIAL SELECTION (Singular)
# ==========================================


def test_3d_vertex_selection():
    """Test absolute corner extraction using 3D spatial combinations."""
    # Box bounds: -5 to +5 on all axes
    shape = Box(10, 10, 10)
    verts = shape.vertices()

    # Top (+Z), Back (+Y), Right (+X)
    v_tbr = verts.top_back_right()
    assert (v_tbr.X, v_tbr.Y, v_tbr.Z) == (5, 5, 5)

    # Bottom (-Z), Front (-Y), Left (-X)
    v_bfl = verts.bottom_front_left()
    assert (v_bfl.X, v_bfl.Y, v_bfl.Z) == (-5, -5, -5)

    # Top (+Z), Front (-Y), Left (-X)
    v_tfl = verts.top_front_left()
    assert (v_tfl.X, v_tfl.Y, v_tfl.Z) == (-5, -5, 5)


# ==========================================
# 3. SPATIAL SELECTION (Grouped / as_list=True)
# ==========================================


def test_1d_grouped_vertex_selection():
    """Test that 1D selectors with as_list=True return a plane of vertices."""
    shape = Box(10, 10, 10)

    # A box has 4 vertices on its top face
    top_verts = shape.vertices().top(as_list=True)

    assert len(top_verts) == 4
    assert all(v.Z == 5 for v in top_verts)


def test_2d_grouped_vertex_selection():
    """Test that 2D selectors with as_list=True return an axis-aligned line of vertices."""
    shape = Box(10, 10, 10)

    # A box has 2 vertices along its front-left edge
    front_left_verts = shape.vertices().front_left(as_list=True)

    assert len(front_left_verts) == 2
    assert all(v.Y == -5 and v.X == -5 for v in front_left_verts)


# ==========================================
# 4. EDGE SELECTION & EVALUATION
# ==========================================


def test_edge_selection():
    """
    Test edge selectors and verify physical geometry using the @ operator.
    @ 0 / 1 yields start/end vertices. @ 0.5 yields the midpoint Vector.
    """
    shape = Box(10, 10, 10)
    edges = shape.edges()

    # Extract the top-front edge (Runs along the X-axis at Y=-5, Z=5)
    tf_edge = edges.top_front()

    # Assert the midpoint is correctly centered on the X-axis
    midpoint = tf_edge @ 0.5
    assert isinstance(midpoint, Vector)
    assert (midpoint.X, midpoint.Y, midpoint.Z) == (0, -5, 5)

    # Assert the ends of the edge evaluate correctly
    start_pt = tf_edge @ 0
    end_pt = tf_edge @ 1

    # Both ends should share the Top (-Z) and Front (-Y) positions
    assert start_pt.Y == -5 and start_pt.Z == 5
    assert end_pt.Y == -5 and end_pt.Z == 5

    # The ends should span the entire X width (-5 to 5)
    assert {start_pt.X, end_pt.X} == {-5, 5}


def test_ambiguous_selection_warning():
    """Test that a warning is emitted when a singular selector is ambiguous."""
    shape = Box(10, 10, 10)

    # A box has 4 left-most vertices. Asking for the single `.left()` vertex is ambiguous.
    with pytest.warns(UserWarning, match=r"makes this ambiguous \(4 shapes share this exact boundary\)"):
        _ = shape.vertices().left()

    # A box has exactly 1 left-most face. This is exact and should NOT warn.
    with warnings.catch_warnings():
        warnings.simplefilter(
            "error"
        )  # Forces the test to fail if any warning is raised
        _ = shape.faces().left()
