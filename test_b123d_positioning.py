"""
test_b123d_positioning.py
Unit tests for the Build123d ShapeList spatial and dimensional extensions.

Run with: `pytest test_b123d_positioning.py`
"""

import warnings
import pytest
import math
from build123d import Cone, Box, Vector
import b123d_positioning  # Applies the monkey-patch to ShapeList


# ==========================================
# 1. EXTENTS (Largest / Smallest)
# ==========================================

def test_extents_faces():
    """Test that largest/smallest correctly identifies faces by area."""
    shape = Cone(20, 1, height=0.5)
    faces = shape.faces()

    assert faces.largest().area == pytest.approx(math.pi * 20**2)
    assert faces.smallest().area == pytest.approx(math.pi * 1**2)


def test_extents_edges():
    """Test that largest/smallest correctly identifies edges by length."""
    shape = Cone(20, 1, height=2)
    edges = shape.edges()

    assert edges.largest().length == math.pi * 2 * 20
    assert edges.smallest().length == math.pi * 2 * 1

def test_extents_singular_warns_on_ties():
    """Test that singular extents emit a warning when multiple shapes tie for size."""
    # Box dimensions: X=10, Y=6, Z=2
    # Face areas: Z-normal=60, Y-normal=20, X-normal=12 (2 of each, creating a tie for largest/smallest)
    shape = Box(10, 6, 2)
    faces = shape.faces()

    with pytest.warns(UserWarning, match=r"makes this ambiguous \(2 shapes share this exact size\)"):
        largest_face = faces.largest()
        assert largest_face.area == pytest.approx(60)

    with pytest.warns(UserWarning, match=r"makes this ambiguous \(2 shapes share this exact size\)"):
        smallest_face = faces.smallest()
        assert smallest_face.area == pytest.approx(12)


def test_extents_grouped_as_list():
    """Test that extents return a ShapeList of all tied shapes when as_list=True."""
    # A cube has 6 identical faces (area=100) and 12 identical edges (length=10)
    shape = Box(10, 10, 10)

    largest_faces = shape.faces().largest(as_list=True)
    assert len(largest_faces) == 6
    assert all(f.area == pytest.approx(100) for f in largest_faces)

    shortest_edges = shape.edges().shortest(as_list=True)
    assert len(shortest_edges) == 12
    assert all(e.length == pytest.approx(10) for e in shortest_edges)


def test_extents_tolerance_filtering():
    """Test that a large relative tolerance groups shapes of dissimilar sizes together."""
    # Box(10, 6, 2) has 4 edges of length 10, 4 of length 6, and 4 of length 2.
    shape = Box(10, 6, 2)
    edges = shape.edges()

    # With default tolerance, ONLY the 4 longest edges (length 10) should be returned.
    strict_edges = edges.longest(as_list=True)
    assert len(strict_edges) == 4
    assert {e.length for e in strict_edges} == {10}

    # With a 50% relative tolerance (tol=0.5), any edge within 10 ± 5 is included.
    # This should return the 4 edges of length 10 AND the 4 edges of length 6 (8 total).
    loose_edges = edges.longest(as_list=True, tol=0.5)
    assert len(loose_edges) == 8
    assert {e.length for e in loose_edges} == {6, 10}


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

    # ==========================================
# 5. ORIENTATION SELECTORS (along / facing / universal)
# ==========================================

def test_universal_horizontal_and_vertical():
    """
    Test horizontal and vertical selectors on an asymmetric Box(10, 6, 2).
    - X length = 10, Y length = 6, Z length = 2.
    - Face areas: Z-normal=60 (10x6), Y-normal=20 (10x2), X-normal=12 (6x2).
    """
    shape = Box(10, 6, 2)

    # 1. Check Horizontal Faces (Top and Bottom floors -> area=60)
    h_faces = shape.faces().horizontal(as_list=True)
    assert len(h_faces) == 2
    assert all(f.area == pytest.approx(60) for f in h_faces)

    # 2. Check Vertical Faces (Side walls -> areas 12 and 20)
    v_faces = shape.faces().vertical(as_list=True)
    assert len(v_faces) == 4
    assert {round(f.area) for f in v_faces} == {12, 20}

    # 3. Check Horizontal Edges (XY perimeter lines -> lengths 6 and 10)
    h_edges = shape.edges().horizontal(as_list=True)
    assert len(h_edges) == 8
    assert {round(e.length) for e in h_edges} == {6, 10}

    # 4. Check Vertical Edges (Upright corner lines -> length=2)
    v_edges = shape.edges().vertical(as_list=True)
    assert len(v_edges) == 4
    assert all(e.length == pytest.approx(2) for e in v_edges)


def test_edge_along_selectors():
    """
    Test along_* selectors on Box(10, 6, 2) to ensure strict axial line separation.
    """
    shape = Box(10, 6, 2)
    edges = shape.edges()

    # along_x must extract ONLY the 4 edges running left-to-right (length = 10)
    x_edges = edges.along_x(as_list=True)
    assert len(x_edges) == 4
    assert all(e.length == pytest.approx(10) for e in x_edges)

    # along_y must extract ONLY the 4 edges running front-to-back (length = 6)
    y_edges = edges.along_y(as_list=True)
    assert len(y_edges) == 4
    assert all(e.length == pytest.approx(6) for e in y_edges)

    # along_z must extract ONLY the 4 upright corner edges (length = 2)
    z_edges = edges.along_z(as_list=True)
    assert len(z_edges) == 4
    assert all(e.length == pytest.approx(2) for e in z_edges)


def test_face_facing_selectors():
    """
    Test facing_* selectors on Box(10, 6, 2) to ensure strict surface normal separation.
    """
    shape = Box(10, 6, 2)
    faces = shape.faces()

    # facing_x must extract ONLY the left/right walls (area = 6x2 = 12)
    x_faces = faces.facing_x(as_list=True)
    assert len(x_faces) == 2
    assert all(f.area == pytest.approx(12) for f in x_faces)

    # facing_y must extract ONLY the front/back walls (area = 10x2 = 20)
    y_faces = faces.facing_y(as_list=True)
    assert len(y_faces) == 2
    assert all(f.area == pytest.approx(20) for f in y_faces)

    # facing_z must extract ONLY the top/bottom floors (area = 10x6 = 60)
    z_faces = faces.facing_z(as_list=True)
    assert len(z_faces) == 2
    assert all(f.area == pytest.approx(60) for f in z_faces)


def test_orientation_singular_selection_and_warnings():
    """
    Test that singular orientation calls warn on multiple matches and return a geometrically valid shape.
    """
    shape = Box(10, 6, 2)

    with pytest.warns(UserWarning, match=r"but 2 shapes match this orientation"):
        single_y_face = shape.faces().facing_y()
        assert single_y_face.area == pytest.approx(20)

    with pytest.warns(UserWarning, match=r"but 4 shapes match this orientation"):
        single_x_edge = shape.edges().along_x()
        assert single_x_edge.length == pytest.approx(10)


def test_orientation_type_guardrails():
    """Test that using along on faces or facing on edges raises helpful domain errors."""
    shape = Box(10, 6, 2)

    with pytest.raises(ValueError, match="For Faces, use 'facing_\\*'"):
        shape.faces().along_x()

    with pytest.raises(ValueError, match="For Edges, use 'along_\\*'"):
        shape.edges().facing_x()
