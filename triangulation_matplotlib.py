import numpy as np
from scipy.spatial import Delaunay
from matplotlib import pyplot as plt
from matplotlib import tri as mtri
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial import ConvexHull
import math
import stl
import json


def read_json_files(filepath):
    json_filename = str(filepath)
    with open(json_filename, 'r') as fp:
        dict_d = json.load(fp)
    return dict_d


def xyz_to_points_array(filepath):
    whole_array = []
    with open(filepath, 'r') as file:
        for i in file:
            line_array = []
            split_line = i.split()
            for j in split_line:
                coord = float(j)
                line_array.append(coord)
            whole_array.append(line_array)
    array = np.array(whole_array)
    return array


def points_array_to_xyz(point_cloud, filepath):
    with open(filepath, 'w') as file:
        for i in point_cloud:
            for j in i:
                file.write(str(j) + ' ')
            file.write('\n')


def stl_to_triangle_array(filepath):
    tree_mesh = stl.mesh.Mesh.from_file(filepath)
    triangles = []
    for i in range(len(tree_mesh.vectors)):
        triangles.append(tree_mesh.vectors[i])
    return np.array(triangles)


def triangle_array_to_stl(triangles, filepath):
    point_count = len(triangles)
    data = np.zeros(point_count, dtype=stl.mesh.Mesh.dtype)
    for i, j in enumerate(triangles):
        data["vectors"][i] = np.array([j[0], j[1], j[2]])

    tree_mesh = stl.mesh.Mesh(data)
    tree_mesh.save(filepath)


def make_proportional_axis(ax):
    """
    Resizes an axis so that it is proportional
    :param ax: axis that needs to be resized
    """
    extents = np.array([getattr(ax, 'get_{}lim'.format(dim))() for dim in 'xy'])
    sz = extents[:, 1] - extents[:, 0]
    centers = np.mean(extents, axis=1)
    maxsize = max(abs(sz))
    r = maxsize / 2
    for ctr, dim in zip(centers, 'xy'):
        getattr(ax, 'set_{}lim'.format(dim))(ctr - r, ctr + r)


def scatter_plot(points):
    """
    Plots a given set of points in a scatter plot
    :param points: the points that are to be scatter plotted
    """
    xp = [row[0] for row in points]
    yp = [row[1] for row in points]
    zp = [row[2] for row in points]

    fig = plt.figure()
    ax = Axes3D(fig)
    ax.scatter(xp, yp, zp, s=1, c='Green')
    #make_proportional_axis(ax)
    plt.show()


def triangulate_convex_hull(points):
    """
    Triangulates a given set of points using convex hull triangulation
    :param points: the points that are to be triangulated
    :return tri: the triangulation of the points
    :return z: the set of z (height) points - only necessary for plotting
    """
    points_t = points.T
    x, y, z = points_t
    cvx = ConvexHull(points)
    tri = mtri.Triangulation(x, y, triangles=cvx.simplices)
    return tri, z


def triangulate_delaunay(points):
    x = [row[0] for row in points]
    y = [row[1] for row in points]
    z = [row[2] for row in points]
    tri = Delaunay(points)
    return tri, x, y, z


def triangulate_plot(points, method):
    """
    Triangulates a given set of points using either Delaunay or convex hull triangulation then plots that
    :param points: the points that are to be triangulated
    :param method: either 'Delaunay' or 'CH', describing desired triangulation method
    """
    if method == 'Delaunay':
        tri, x, y, z = triangulate_delaunay(points)
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.plot_trisurf(x, y, z, triangles=tri.simplices, cmap=plt.cm.Spectral)
    elif method == 'CH':
        tri, z = triangulate_convex_hull(points)
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        ax.plot_trisurf(tri, z, color='Green')
        make_proportional_axis(ax)
    plt.show()


def triangulate_plot_whole_convex_hull(points_a, points_b):
    """
    Triangulates two sets of points (trunk and crown) separately using convex hull triangulation and plots that
    :param points_a: first set of points that are to be triangulated
    :param points_b: second set of points that are to be triangulated
    """
    tri_a, z_a = triangulate_convex_hull(points_a)
    tri_b, z_b = triangulate_convex_hull(points_b)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1, projection='3d')
    ax.plot_trisurf(tri_a, z_a, color='Green')
    ax.plot_trisurf(tri_b, z_b, color='Brown')
    make_proportional_axis(ax)


def xy_centroid_function(points):
    """
    Gives the xy centre coordinate of a set of points at the minimum z height
    :param points: points from which centre is found
    :return: point that is at the base of the centre of the tree
    """
    length = points.shape[0]
    sum_x = np.sum(points[:, 0])
    sum_y = np.sum(points[:, 1])
    low_z = min(points[:, 2])
    try:
        return sum_x / length, sum_y / length, low_z
    except ZeroDivisionError:
        print("Size of given point cloud is 0")


def create_crown(points, ratio_trunk):
    """
    Creates the crown by cutting and triangulating a certain upper area of the tree
    :param points: points from tree point cloud used to create crown
    :param ratio_trunk: proportion of tree that is made up of trunk
    :return new_points: points representing the crown
    :return crown_span: the minimum horizontal span of the the crown - for trunk width calculation
    """
    z = [row[2] for row in points]
    limit_z = int(min(z) + ratio_trunk * (max(z) - min(z)))  # lowest point of the crown
    remove_array = []  # points that are below desired height and need to be removed
    for index, height in enumerate(z):
        if height <= limit_z:
            remove_array.append(index)
    new_points = np.delete(points, remove_array, axis=0)
    x, y, z_extra = new_points.T
    crown_span = min([max(x) - min(x), max(y) - min(y)])  # minimum span of the crown
    return new_points, crown_span


def create_trunk(points, centroid, distance):
    """
    Creates the trunk by projecting a cylinder of certain width through the tree to the base
    :param points: points from the tree point cloud
    :param centroid: centre of the crown, which can be used as centre point of trunk
    :param distance: minimum span of the crown, used to create tree width
    :return: points representing the trunk
    """
    x, y, z = points.T
    centre_x = centroid[0]
    centre_y = centroid[1]
    limit_z = int(min(z) + 0.75 * (max(z) - min(z)))  # maximum height of the trunk - now at 75% of tree
    min_z = int(min(z))

    radius = 0.06 * distance  # tree radius - now at 6% of crown span

    new_points = []
    number = 20
    rad = np.radians(np.linspace(360.0 / number, 360.0, number))
    for i in range(min_z, limit_z + 1):
        for c in rad:
            xyz = [(radius * math.cos(c)) + centre_x, (radius * math.sin(c)) + centre_y, i]
            new_points.append(xyz)

    return np.array(new_points)


def create_coordinate_triangles_from_index_points(coord_points, index_points):
    """
    Converts set of index points of triangles into the corresponding coordinate points of triangles
    :param coord_points: original set of points, representing actual coordinate values
    :param index_points: triangulated set of index points
    :return: np array of coordinates representing triangles
    """
    final_new_points = []
    first = True
    first_xyz_points = []
    for i in index_points:
        three_new_xyz_points = []
        for j in range(3):
            new_xyz_point = coord_points[i[j]]
            three_new_xyz_points.append(new_xyz_point)
        if first:
            first_xyz_points = three_new_xyz_points
            first = False
        final_new_points.append(three_new_xyz_points)
    final_new_points.append(first_xyz_points)
    final_array_points = np.array(final_new_points)
    return final_array_points


def create_triangle_array_from_points(points_a, points_b):
    """
    Triangulates two sets of points (trunk and crown) separately using convex hull triangulation and creates array
    :param points_a: first set of points that are to be triangulated
    :param points_b: second set of points that are to be triangulated
    :return: np array of coordinates representing triangulation of entire tree
    """
    tri_a, z_a = triangulate_convex_hull(points_a)
    tri_b, z_b = triangulate_convex_hull(points_b)
    array_a = create_coordinate_triangles_from_index_points(points_a, tri_a.triangles)
    array_b = create_coordinate_triangles_from_index_points(points_b, tri_b.triangles)
    triangles = np.vstack((array_a, array_b))
    return triangles


def create_complete_tree_triangles_points(points, ratio_trunk, reference_point):
    """
    Function that creates crown and trunk points and complete tree triangulation from initial points
    :param points: set of points
    :param ratio_trunk: proportion of tree that is made up of trunk
    :return: crown_points, trunk_points and crown_and_trunk_triangles
    """
    crown_points, min_crown_span = create_crown(points, ratio_trunk)
    crown_centre = xy_centroid_function(crown_points)  # also reference coordinate, z-coordinate not needed here
    trunk_points = create_trunk(points, crown_centre, min_crown_span)
    crown_and_trunk_triangles = create_triangle_array_from_points(crown_points, trunk_points)
    crown_and_trunk_triangles = reorient_points(crown_and_trunk_triangles, reference_point)
    return crown_points, trunk_points, crown_and_trunk_triangles


def midpoint_maxheight_triangles(triangles):
    """
    Gives the midpoint and the maximum height from a set of triangles
    :param triangles: triangles that are analysed
    :return: the xy mid point of tree at lowest height (base) and maximum height of tree
    """
    points = []
    heights = []
    for i in range(len(triangles)):
        for j in range(3):
            points.append(triangles[i][j])
            heights.append(triangles[i][j][2])
    points = np.array(points)
    unique_points = np.unique(points, axis=0)
    mid_point = xy_centroid_function(unique_points)
    max_height = max(heights) - mid_point[2]
    return mid_point, max_height


def reorient_points(points, reference_point):
    """
    Reorients points so that the origin is the reference point
    :param points: points that are to be reoriented
    :param reference_point: new origin point
    :return: the newly reoriented points
    """
    print(points)
    for i in range(len(points)):
        for j in range(3):
            points[i][j][0] = points[i][j][0] - reference_point[0]
            points[i][j][1] = points[i][j][1] - reference_point[1]
            points[i][j][2] = points[i][j][2] - reference_point[2]
    return points


def resize_reorient_triangles(triangles, width_value, height_value):
    """
    Reorients and resizes a set of triangles. When width and/or height are 0, triangles are only reoriented.
    :param triangles: triangles to be altered
    :param width_value: diameter that the tree should be resized to
    :param height_value: height that the tree should be resized to
    :return: array of altered triangles
    """
    maximum_radius = 0
    centre_point, max_height = midpoint_maxheight_triangles(triangles)
    triangles = reorient_points(triangles, centre_point)

    if width_value != 0 and height_value != 0:
        for i in triangles:  # finds original diameter of tree
            for j in i:
                sub_maximum = np.linalg.norm(j[:2] - centre_point[:2])
                if sub_maximum > maximum_radius:
                    maximum_radius = sub_maximum
        maximum_diameter = maximum_radius * 2
        width_scale = width_value / maximum_diameter
        height_scale = height_value / max_height

        scale_triangles(triangles, width_scale, height_scale)

    return triangles


def scale_triangles(triangles, width_scale, height_scale):
    for i in range(len(triangles)):
        for j in range(3):
            triangles[i][j][0] = triangles[i][j][0] * width_scale
            triangles[i][j][1] = triangles[i][j][1] * width_scale
            triangles[i][j][2] = triangles[i][j][2] * height_scale
    return triangles


def reduce_point_density(point_cloud):
    """
    Reduces the density (number of points) of a point cloud
    :param point_cloud: point cloud which is being reduced
    :return: newly thinned out point cloud
    """
    rounded_points = []
    for i in point_cloud:
        round_x = int(2 * round(float(i[0])/2))
        round_y = int(2 * round(float(i[1])/2))
        round_z = round(i[2], 2)
        rounded_points.append([round_x, round_y, round_z])
    thinned_points = []
    [thinned_points.append(x) for x in rounded_points if x not in thinned_points]
    return thinned_points