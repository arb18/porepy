import numpy as np
import unittest

import porepy as pp
from test import test_utils


class BasicTest(unittest.TestCase):
    """
    Various tests of intersect_polygon_lines.

    """

    def test_0(self):
        # convex polygon
        polygon = np.array([[0.0, 1.0, 1.0, 0.0], [0.0, 0.0, 1.0, 1.0]])
        pts = np.array(
            [
                [0.0, 1.0, 0.0, 2.0, 0.5, 0.0, -0.5, 0.3, -1, 0.0],
                [0.0, 1.0, 0.0, 2.0, 1.0, 0.0, -0.5, 0.6, -1, 0.0],
            ]
        )
        lines = np.array([[0, 2, 4, 6, 8], [1, 3, 5, 7, 9]])

        new_pts, new_lines = pp.cg.intersect_polygon_lines(polygon, pts, lines)

        pts_known = np.array(
            [
                [0.0, 1.0, 0.0, 1.0, 0.5, 0.0, 0.0, 0.3],
                [0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 3 / 16, 0.6],
            ]
        )
        lines_known = np.array([[0, 2, 4, 6], [1, 3, 5, 7]])

        self.assertTrue(np.allclose(new_pts, pts_known))
        self.assertTrue(np.allclose(new_lines, lines_known))

    def test_1(self):
        # non-convex polygon
        polygon = np.array(
            [[0.0, 0.5, 0.75, 1.0, 1.5, 1.5, 0], [0.0, 0.0, 0.25, 0.0, 0, 1, 1]]
        )
        pts = np.array(
            [
                [0.0, 1.0, 0.0, 2.0, 0.5, 0.0, -0.5, 0.3, -1, 0.0, 0.0, 2.0, -0.1, 1.1],
                [0.0, 1.0, 0.0, 2.0, 1.0, 0.0, -0.5, 0.6, -1, 0.0, 0.2, 0.2, 0.0, 0.0],
            ]
        )
        lines = np.array([[0, 2, 4, 6, 8, 10, 12], [1, 3, 5, 7, 9, 11, 13]])

        new_pts, new_lines = pp.cg.intersect_polygon_lines(polygon, pts, lines)
        pts_known = np.array(
            [
                [0.0, 1.0, 0.0, 1.0, 0.5, 0.0, 0.0, 0.3, 0.0, 0.7, 0.8, 1.5],
                [0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 3 / 16, 0.6, 0.2, 0.2, 0.2, 0.2],
            ]
        )
        lines_known = np.array([[0, 2, 4, 6, 8, 10], [1, 3, 5, 7, 9, 11]])

        self.assertTrue(np.allclose(new_pts, pts_known))
        self.assertTrue(np.allclose(new_lines, lines_known))


class TestIntersectionPolygonsEmbeddedIn3d(unittest.TestCase):
    def test_single_fracture(self):
        f_1 = np.array([[-1, 1, 1, -1], [0, 0, 0, 0], [-1, -1, 1, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1])
        self.assertTrue(new_pt.size == 0)
        self.assertTrue(isect_pt.size == 1)
        self.assertTrue(len(isect_pt[0]) == 0)
        self.assertTrue(on_bound.size == 1)
        self.assertTrue(len(on_bound[0]) == 0)

    def test_two_intersecting_fractures(self):

        f_1 = np.array([[-1, 1, 1, -1], [0, 0, 0, 0], [-1, -1, 1, 1]])
        f_2 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-0.7, -0.7, 0.8, 0.8]])

        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(np.allclose(np.sort(isect_pt[0]), [0, 1]))
        self.assertTrue(np.allclose(np.sort(isect_pt[1]), [0, 1]))
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)

        known_points = np.array([[0, 0, -0.7], [0, 0, 0.8]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_three_intersecting_fractures(self):
        f_1 = np.array([[-1, 1, 1, -1], [0, 0, 0, 0], [-1, -1, 1, 1]])
        f_2 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-0.7, -0.7, 0.8, 0.8]])
        f_3 = np.array([[-1, 1, 1, -1], [-1, -1, 1, 1], [0, 0, 0, 0]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2, f_3])
        self.assertTrue(new_pt.shape[1] == 6)
        self.assertTrue(isect_pt.size == 3)
        self.assertTrue(len(isect_pt[0]) == 4)
        self.assertTrue(len(isect_pt[1]) == 4)
        self.assertTrue(len(isect_pt[2]) == 4)
        self.assertTrue(on_bound.size == 3)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)
        self.assertTrue(np.all(on_bound[2]) == False)

        known_points = np.array(
            [[0, 0, -0.7], [0, 0, 0.8], [1, 0, 0], [-1, 0, 0], [0, 1, 0], [0, -1, 0]]
        ).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_three_intersecting_fractures_one_intersected_by_two(self):
        f_1 = np.array([[-1, 1, 1, -1], [0, 0, 0, 0], [-1, -1, 1, 1]])
        f_2 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-0.7, -0.7, 0.8, 0.8]])
        f_3 = f_2 + np.array([0.5, 0, 0]).reshape((-1, 1))
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2, f_3])
        self.assertTrue(new_pt.shape[1] == 4)
        self.assertTrue(isect_pt.size == 3)
        self.assertTrue(len(isect_pt[0]) == 4)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(len(isect_pt[2]) == 2)
        self.assertTrue(on_bound.size == 3)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)
        self.assertTrue(np.all(on_bound[2]) == False)

        known_points = np.array(
            [[0, 0, -0.7], [0, 0, 0.8], [0.5, 0.0, -0.7], [0.5, 0.0, 0.8]]
        ).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_three_intersecting_fractures_sharing_segment(self):
        f_1 = np.array([[-1, 1, 1, -1], [0, 0, 0, 0], [-1, -1, 1, 1]])
        f_2 = np.array([[-1, 1, 1, -1], [-1, 1, 1, -1], [-1, -1, 1, 1]])
        f_3 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-1, -1, 1, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2, f_3])
        self.assertTrue(new_pt.shape[1] == 6)
        self.assertTrue(isect_pt.size == 3)
        self.assertTrue(len(isect_pt[0]) == 4)
        self.assertTrue(len(isect_pt[1]) == 4)
        self.assertTrue(len(isect_pt[2]) == 4)
        self.assertTrue(on_bound.size == 3)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)
        self.assertTrue(np.all(on_bound[2]) == False)

        known_points = np.array(
            [
                [0, 0, -1],
                [0, 0, 1],
                [0.0, 0.0, -1],
                [0.0, 0.0, 1],
                [0.0, 0.0, -1],
                [0.0, 0.0, 1],
            ]
        ).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_three_intersecting_fractures_split_segment(self):
        """
        Three fractures that all intersect along the same line, but with the
        intersection between two of them forming an extension of the intersection
        of all three.
        """
        f_1 = np.array([[-1, 1, 1, -1], [0, 0, 0, 0], [-1, -1, 1, 1]])
        f_2 = np.array([[-0.5, 0.5, 0.5, -0.5], [-1, -1, 1, 1], [-2, -2, 2, 2]])
        f_3 = np.array([[-1, 1, 1, -1], [-1, -1, 1, 1], [0, 0, 0, 0]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2, f_3])
        self.assertTrue(new_pt.shape[1] == 6)
        self.assertTrue(isect_pt.size == 3)
        self.assertTrue(len(isect_pt[0]) == 4)
        self.assertTrue(len(isect_pt[1]) == 4)
        self.assertTrue(len(isect_pt[2]) == 4)
        self.assertTrue(on_bound.size == 3)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)
        self.assertTrue(np.all(on_bound[2]) == False)

        known_points = np.array(
            [
                [-1, 0, 0],
                [1, 0, 0],
                [-0.5, 0.0, 0],
                [0.5, 0.0, 0],
                [-0.5, 0.0, 0],
                [0.5, 0.0, 0],
            ]
        ).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_two_points_in_plane_of_other_fracture(self):
        """
        Two fractures. One has two (non-consecutive) vertexes in the plane
        of another fracture
        """
        f_1 = np.array([[-0.5, 0.5, 0.5, -0.5], [-1, -1, 1, 1], [-1, -1, 1, 1]])
        f_2 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-1, -1, 1, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)

        known_points = np.array([[0, -1, -1], [0, 1, 1]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_two_points_in_plane_of_other_fracture_order_reversed(self):
        """
        Two fractures. One has two (non-consecutive) vertexes in the plane
        of another fracture. Order of polygons is reversed compared to similar test
        """
        f_1 = np.array([[-0.5, 0.5, 0.5, -0.5], [-1, -1, 1, 1], [-1, -1, 1, 1]])
        f_2 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-1, -1, 1, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_2, f_1])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)

        known_points = np.array([[0, -1, -1], [0, 1, 1]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_one_point_in_plane_of_other_fracture(self):
        """
        Two fractures. One has one vertexes in the plane
        of another fracture
        """
        f_1 = np.array([[-0.5, 0.5, 0.5, -0.5], [-1, -1, 1, 1], [-1, -1, 1, 1]])
        f_2 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-1, -1, 2, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)

        known_points = np.array([[0, -1, -1], [0, 1, 1]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_one_point_in_plane_of_other_fracture_order_reversed(self):
        """
        Two fractures. One has one vertexes in the plane
        of another fracture
        """
        f_1 = np.array([[-0.5, 0.5, 0.5, -0.5], [-1, -1, 1, 1], [-1, -1, 1, 1]])
        f_2 = np.array([[0, 0, 0, 0], [-1, 1, 1, -1], [-1, -1, 2, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.all(on_bound[0]) == False)
        self.assertTrue(np.all(on_bound[1]) == False)

        known_points = np.array([[0, -1, -1], [0, 1, 1]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_L_intersection(self):
        """
        Two fractures, L-intersection.
        """
        f_1 = np.array([[0, 1, 1, 0], [0, 0, 1, 1], [0, 0, 0, 0]])
        f_2 = np.array([[0, 0, 0, 0], [0.3, 0.7, 0.7, 0.3], [0, 0, 1, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 1)
        self.assertTrue(np.sum(on_bound[1]) == 1)

        known_points = np.array([[0, 0.3, 0], [0, 0.7, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_L_intersection_one_node_common(self):
        """
        Two fractures, L-intersection, one common node.
        """
        f_1 = np.array([[0, 1, 1, 0], [0, 0, 1, 1], [0, 0, 0, 0]])
        f_2 = np.array([[0, 0, 0, 0], [0.3, 1.0, 1, 0.3], [0, 0, 1, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 1)
        self.assertTrue(np.sum(on_bound[1]) == 1)

        known_points = np.array([[0, 0.3, 0], [0, 1, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_L_intersection_extends_beyond_each_other(self):
        """
        Two fractures, L-intersection, partly overlapping segments
        """
        f_1 = np.array([[0, 1, 1, 0], [0, 0, 1, 1], [0, 0, 0, 0]])
        f_2 = np.array([[0, 0, 0, 0], [0.3, 1.5, 1.5, 0.3], [0, 0, 1, 1]])
        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 1)
        self.assertTrue(np.sum(on_bound[1]) == 1)

        known_points = np.array([[0, 0.3, 0], [0, 1, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_T_intersection_within_polygon(self):
        """
        Two fractures, T-intersection, segment contained within the other polygon.
        """
        f_1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]).T
        f_2 = np.array([[0.5, 0.5, 1], [0.5, 0.5, 0], [0.5, 0.9, 0.0]]).T

        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 0)
        self.assertTrue(np.sum(on_bound[1]) == 1)

        known_points = np.array([[0.5, 0.5, 0], [0.5, 0.9, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_T_intersection_one_outside_polygon(self):
        """
        Two fractures, L-intersection, partly overlapping segments
        """
        f_1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]).T
        f_2 = np.array([[0.5, 0.5, 1], [0.5, 0.5, 0], [0.5, 1.9, 0.0]]).T

        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 0)
        self.assertTrue(np.sum(on_bound[1]) == 1)

        known_points = np.array([[0.5, 0.5, 0], [0.5, 1.0, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_T_intersection_one_outside_one_on_polygon(self):
        """
        Two fractures, L-intersection, partly overlapping segments
        """
        f_1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]).T
        f_2 = np.array([[0.5, 0.5, 1], [0.5, 0.0, 0], [0.5, 1.9, 0.0]]).T

        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 0)
        self.assertTrue(np.sum(on_bound[1]) == 1)

        known_points = np.array([[0.5, 0.0, 0], [0.5, 1.0, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_T_intersection_one_outside_one_on_polygon_reverse_order(self):
        """
        Two fractures, L-intersection, partly overlapping segments
        """
        f_1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]).T
        f_2 = np.array([[0.5, 0.5, 1], [0.5, 0.0, 0], [0.5, 1.9, 0.0]]).T

        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_2, f_1])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 1)
        self.assertTrue(np.sum(on_bound[1]) == 0)

        known_points = np.array([[0.5, 0.0, 0], [0.5, 1.0, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))

    def test_T_intersection_both_on_boundary(self):
        """
        Two fractures, L-intersection, partly overlapping segments
        """
        f_1 = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]]).T
        f_2 = np.array([[0.5, 0.5, 1], [0.5, 0.0, 0], [0.5, 1.0, 0.0]]).T

        new_pt, isect_pt, on_bound, _ = pp.cg.intersect_polygons_3d([f_1, f_2])
        self.assertTrue(new_pt.shape[1] == 2)
        self.assertTrue(isect_pt.size == 2)
        self.assertTrue(len(isect_pt[0]) == 2)
        self.assertTrue(len(isect_pt[1]) == 2)
        self.assertTrue(on_bound.size == 2)
        self.assertTrue(np.sum(on_bound[0]) == 0)
        self.assertTrue(np.sum(on_bound[1]) == 1)

        known_points = np.array([[0.5, 0.0, 0], [0.5, 1.0, 0]]).T
        self.assertTrue(test_utils.compare_arrays(new_pt, known_points))


if __name__ == "__main__":
    unittest.main()
    TestIntersectionPolygonsEmbeddedIn3d().test_L_intersection()
