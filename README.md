# b123d_positioning

An extension for `build123d` that installs ergonomic methods for face, edge and vertex selection, e.g. `object.vertices().top_front_left()`.

## Usage

Importing the module automatically monkey-patches the `build123d.ShapeList` class. Your standard objects will immediately possess the new functionality.

```python
import b123d_positioning
from build123d import Box

base = Box(10, 10, 10)

# Extract a single vertex
top_left_corner = base.vertices().top_left()

# Extract a group of edges
top_edges = base.edges().all_top()

# Extract a face by size
biggest_face = base.faces().largest()

```

---

## Spatial Selectors

Spatial selectors filter shapes based on their bounding box centers relative to the global 3D coordinate system.

### API Grammar

The naming convention strictly follows standard CAD axes:

* **Z-Axis:** `bottom` / `top`
* **Y-Axis:** `front` / `back`
* **X-Axis:** `left` / `right`

Methods can target a single axis or chain up to three dimensions (e.g., `bottom_front_left()`).

### Singular vs. Grouped

| Prefix | Behavior | Return Type | Examples |
| --- | --- | --- | --- |
| *(None)* | Returns the **single** shape at the absolute extreme of the specified vector. | `Shape` | `top()`, `bottom_back()`, `top_front_right()` |
| `all_` | Returns a **subset** (group) of shapes sharing the specified extreme boundary. | `ShapeList` | `all_top()`, `all_bottom_back()`, `all_top_front_right()` |

### Ambiguity Warnings
If you use a singular selector (e.g., `.left()`) on a dimension where multiple shapes share the exact same extreme coordinate (like the 4 left-most vertices of a 3D box), `b123d_positioning` will emit a `UserWarning`. It will still return a single arbitrary shape to prevent crashing your script, but alerts you that the selection is mathematically ambiguous. To resolve the warning, switch to an `all_` prefix or use a fully constrained 2D/3D selector.

## Dimensional Selectors

Sorts the `ShapeList` based on physical size properties (`.length` for Edges, `.area` for Faces, and `.volume` for Solids).

| Method | Description |
| --- | --- |
| `largest()` | Returns the single largest shape in the list. |
| `smallest()` | Returns the single smallest shape in the list. |

*Note: Dimensional selectors will raise a `ValueError` if used on `Vertex` objects, as they are dimensionless.*

---

## Technical Notes

* **Evaluation Engine:** Under the hood, spatial selectors rely on standard `build123d` bounding box centers. Singular selectors chain `group_by` operations for intermediate axes and conclude with a `sort_by` operation to extract the exact shape. (i.e. `top_front_left` will retrieve the Z-most group, then Y-least group of those, then sort and pull out the X-least instance). Grouped (`all_`) selectors exclusively use `group_by` to return subsets.
