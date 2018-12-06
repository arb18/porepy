import numpy as np
import porepy as pp

import examples.papers.dfn_transport.discretization as discr
from examples.papers.dfn_transport.flux_trace import jump_flux

def bc_flag(g, domain, tol):
    b_faces = g.tags["domain_boundary_faces"].nonzero()[0]
    b_face_centers = g.face_centers[:, b_faces]

    # define inflow type boundary conditions
    out_flow_z = b_face_centers[2] > 0.4
    out_flow_x = b_face_centers[0] < tol

    out_flow = np.logical_and(out_flow_x, out_flow_z)

    # define outflow type boundary conditions
    in_flow_start = np.array([0, 0, 0.3])
    in_flow_end = np.array([0, 1, 0.3])

    # detect all the points aligned with the segment
    dist, _ = pp.cg.dist_points_segments(b_face_centers, in_flow_start, in_flow_end)
    dist = dist.flatten()
    in_flow = np.logical_and(dist < tol, dist >=-tol)

    return in_flow, out_flow

def main():

    input_folder = "../geometries/example1/"

    #mesh_size = 1 # for 1k triangles
    #mesh_size = 0.9 * np.power(2., -4) # for 3k triangles
    mesh_size = 0.875 * np.power(2., -5) # for 10k triangles
    mesh_kwargs = {"mesh_size_frac": mesh_size, "mesh_size_min": mesh_size / 20}
    tol = 1e-6

    num_simul = 21
    for simul in np.arange(1, num_simul+1):

        file_name = input_folder + "DFN_" + str(simul) + ".fab"
        file_inters = input_folder + "TRACES_" + str(simul) + ".dat"

        folder = "solution_" + str(simul)

        gb = pp.importer.dfn_3d_from_fab(file_name, file_inters, tol=tol, **mesh_kwargs)

        gb.remove_nodes(lambda g: g.dim == 0)
        gb.compute_geometry()
        gb.assign_node_ordering()

        domain = gb.bounding_box(as_dict=True)

        param = {"domain": domain, "tol": tol, "k": 1,
                 "diff": 1e-4, "time_step": 0.05, "n_steps": 300,
                 "folder": folder}

        # the flow problem
        model_flow = discr.flow(gb, param, bc_flag)

        jump_flux(gb, param["mortar_flux"])

        # the advection-diffusion problem
        discr.advdiff(gb, param, model_flow, bc_flag)


if __name__ == "__main__":
    main()