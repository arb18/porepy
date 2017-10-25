import numpy as np
import scipy.sparse as sps

from porepy.viz import exporter
from porepy.fracs import importer

from porepy.params import tensor
from porepy.params.bc import BoundaryCondition
from porepy.params.data import Parameters

from porepy.grids.grid import FaceTag
from porepy.grids import coarsening as co

from porepy.numerics.vem import dual

from porepy.utils import comp_geom as cg
from porepy.utils import sort_points

#------------------------------------------------------------------------------#

def add_data(gb, tol):
    """
    Define the permeability, apertures, boundary conditions
    """
    gb.add_node_props(['param'])

    for g, d in gb:
        param = Parameters(g)

        if g.dim == 2:
            # Permeability
            kxx = np.ones(g.num_cells)
            param.set_tensor("flow", tensor.SecondOrder(g.dim, kxx))

            # Source term
            param.set_source("flow", np.zeros(g.num_cells))

            # Boundaries
            bound_faces = g.get_domain_boundary_faces()
            if bound_faces.size != 0:
                bound_face_centers = g.face_centers[:, bound_faces]

                bottom = bound_face_centers[1, :] < tol

                labels = np.array(['neu'] * bound_faces.size)
                labels[bottom] = 'dir'

                bc_val = np.zeros(g.num_faces)
                mask = bound_face_centers[0, :] < tol
                bc_val[bound_faces[np.logical_and(bottom, mask)]] = 1

                param.set_bc("flow", BoundaryCondition(g, bound_faces, labels))
                param.set_bc_val("flow", bc_val)
            else:
                param.set_bc("flow", BoundaryCondition(
                    g, np.empty(0), np.empty(0)))

        d['param'] = param

#------------------------------------------------------------------------------#

def plot_over_line(gb, pts, name, tol):

    values = np.zeros(pts.shape[1])
    is_found = np.zeros(pts.shape[1], dtype=np.bool)

    for g, d in gb:
        if g.dim < gb.dim_max():
            continue

        if not cg.is_planar(np.hstack((g.nodes, pts)), tol=1e-4):
            continue

        faces_cells, _, _ = sps.find(g.cell_faces)
        nodes_faces, _, _ = sps.find(g.face_nodes)

        normal = cg.compute_normal(g.nodes)
        for c in np.arange(g.num_cells):
            loc = slice(g.cell_faces.indptr[c], g.cell_faces.indptr[c+1])
            pts_id_c = np.array([nodes_faces[g.face_nodes.indptr[f]:\
                                                g.face_nodes.indptr[f+1]]
                                                   for f in faces_cells[loc]]).T
            pts_id_c = sort_points.sort_point_pairs(pts_id_c)[0, :]
            pts_c = g.nodes[:, pts_id_c]

            mask = np.where(np.logical_not(is_found))[0]
            if mask.size == 0:
                break
            check = np.zeros(mask.size, dtype=np.bool)
            last = False
            for i, pt in enumerate(pts[:, mask].T):
                check[i] = cg.is_point_in_cell(pts_c, pt)
                if last and not check[i]:
                    break
            is_found[mask] = check
            values[mask[check]] = d[name][c]

    return values

#def plot_over_line(gb, pts, name, tol):
#
#    values = np.empty(pts.shape[1])
#
#    for g, d in gb:
#        if g.dim == gb.dim_max():
#
#            faces, cells, sign = sps.find(g.cell_faces)
#            index = np.argsort(cells)
#            faces, sign = faces[index], sign[index]
#
#            for c in np.arange(g.num_cells):
#                # For the current cell retrieve its faces
#                loc = slice(g.cell_faces.indptr[c], g.cell_faces.indptr[c+1])
#                faces_loc, sign_loc = faces[loc], sign[loc]
#                normals = sign_loc*g.face_normals[:, faces_loc]
#                c_normal = np.cross(normals[:, 0], normals[:, 1])
#                c_normal /= np.linalg.norm(c_normal)
#                check = np.ones(pts.shape[1], dtype=np.bool)
#
#                for face, normal in zip(faces_loc, normals.T):
#                    delta = (pts.T - g.face_centers[:, face]).T
#                    check_face = np.zeros(pts.shape[1], dtype=np.bool)
#                    for i in np.arange(check_face.shape[0]):
#                        delta_n = delta[:, i]/np.linalg.norm(delta[:, i])
#                        normal_n = normal/np.linalg.norm(normal)
#                        co_plan = np.abs(np.dot(delta_n, c_normal))
#                        check_face[i] = (np.dot(delta_n, normal_n) < tol) and \
#                                        (co_plan < tol)
#                    check = np.logical_and(check, check_face)
#                values[check] = d[name][c]
#
#    return values
#
##------------------------------------------------------------------------------#

def compute_flow_rate(gb, tol):

    total_flow_rate = 0
    for g, d in gb:
        bound_faces = g.get_domain_boundary_faces()
        if bound_faces.size != 0:
            bound_face_centers = g.face_centers[:, bound_faces]
            mask = np.logical_and(bound_face_centers[1, :] < tol,
                                  bound_face_centers[0, :] > 1.5 - tol)
            flow_rate = d['discharge'][bound_faces[mask]]
            total_flow_rate += np.sum(flow_rate)

    diam = gb.diameter(lambda g: g.dim==gb.dim_max())
    return diam, total_flow_rate

#------------------------------------------------------------------------------#

def main(id_problem, is_coarse=False, tol=1e-5, N_pts=1000):

    folder = 'example_2_2_geometry/'
    file_name = folder + 'DFN_2.fab'
    file_intersections = folder + 'TRACES_2.dat'

    folder_export = 'example_2_2_vem'
    file_export = 'vem'

    mesh_kwargs = {}
    mesh_kwargs['mesh_size'] = {'mode': 'constant',
                                'value': 0.09,
                                'bound_value': 1}

    gb = importer.read_dfn(file_name, file_intersections, tol=tol, **mesh_kwargs)
    gb.remove_nodes(lambda g: g.dim == 0)
    gb.compute_geometry()
    if is_coarse:
        co.coarsen(gb, 'by_volume')
    gb.assign_node_ordering()

    internal_flag = FaceTag.FRACTURE
    [g.remove_face_tag_if_tag(FaceTag.BOUNDARY, internal_flag) for g, _ in gb]

    # Assign parameters
    add_data(gb, tol)

    # Choose and define the solvers and coupler
    solver = dual.DualVEMDFN(gb.dim_max(), 'flow')
    up = sps.linalg.spsolve(*solver.matrix_rhs(gb))
    solver.split(gb, "up", up)

    gb.add_node_props(["discharge", "p", "P0u"])
    solver.extract_u(gb, "up", "discharge")
    solver.extract_p(gb, "up", "p")
    solver.project_u(gb, "discharge", "P0u")

    exporter.export_vtk(gb, file_export, ["p", "P0u"], folder=folder_export)

    b_box = gb.bounding_box()
    y_range = np.linspace(b_box[0][1]+tol, b_box[1][1]-tol, N_pts)
    pts = np.stack((1.5*np.ones(N_pts), y_range, 0.5*np.ones(N_pts)))
    values = plot_over_line(gb, pts, 'p', tol)

    # compute the flow rate
    diam, flow_rate = compute_flow_rate(gb, tol)
    np.savetxt(folder_export+"flow_rate.txt", (diam, flow_rate))

#------------------------------------------------------------------------------#

num_simu = 20
is_coarse = False
for i in np.arange(num_simu):
    main(i+1, is_coarse)

#------------------------------------------------------------------------------#
