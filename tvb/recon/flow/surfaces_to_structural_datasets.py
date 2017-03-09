import enum
import numpy as np
import os
import os.path
import logging
import time
from typing import List
from ..cli.runner import Runner, File
from ..cli import fs
from .core import Flow
from ..model.constants import FS_TO_CONN_INDICES_MAPPING_PATH
from ..algo.structural_dataset import StructuralDataset


SUBCORTICAL_REG_INDS = ['008', '010', '011', '012', '013', '016', '017', '018', '026', '047', '049',
                        '050', '051', '052', '053', '054', '058']


class Hemisphere(enum.Enum):
    rh = 'rh'
    lh = 'lh'


class Surface:
    def __init__(self, vertices, triangles, region_mapping):
        self.vertices = vertices
        self.triangles = triangles
        self.region_mapping = region_mapping




def compute_vertex_triangles(number_of_vertices, number_of_triangles, triangles):
    vertex_triangles = [[] for _ in range(number_of_vertices)]
    for k in range(number_of_triangles):
        vertex_triangles[triangles[k, 0]].append(k)
        vertex_triangles[triangles[k, 1]].append(k)
        vertex_triangles[triangles[k, 2]].append(k)
    return vertex_triangles


def compute_triangle_normals(triangles, vertices):
    """Calculates triangle normals."""
    tri_u = vertices[triangles[:, 1], :] - vertices[triangles[:, 0], :]
    tri_v = vertices[triangles[:, 2], :] - vertices[triangles[:, 0], :]
    tri_norm = np.cross(tri_u, tri_v)

    try:
        triangle_normals = tri_norm / np.sqrt(np.sum(tri_norm ** 2, axis=1))[:, np.newaxis]
    except FloatingPointError:
        # TODO: NaN generation would stop execution, however for normals this case could maybe be
        #  handled in a better way.
        triangle_normals = tri_norm
    return triangle_normals


def compute_triangle_angles(vertices, number_of_triangles, triangles):
    """
    Calculates the inner angles of all the triangles which make up a surface
    """
    verts = vertices
    # TODO: Should be possible with arrays, ie not nested loops...
    # A short profile indicates this function takes 95% of the time to compute normals
    # (this was a direct translation of some old matlab code)
    angles = np.zeros((number_of_triangles, 3))
    for tt in range(number_of_triangles):
        triangle = triangles[tt, :]
        for ta in range(3):
            ang = np.roll(triangle, -ta)
            angles[tt, ta] = np.arccos(np.dot(
                (verts[ang[1], :] - verts[ang[0], :]) /
                np.sqrt(np.sum((verts[ang[1], :] - verts[ang[0], :]) ** 2, axis=0)),
                (verts[ang[2], :] - verts[ang[0], :]) /
                np.sqrt(np.sum((verts[ang[2], :] - verts[ang[0], :]) ** 2, axis=0))))

    return angles


def compute_vertex_normals(number_of_vertices, vertex_triangles, triangles,
                           triangle_angles, triangle_normals, vertices):
    """
    Estimates vertex normals, based on triangle normals weighted by the
    angle they subtend at each vertex...
    """
    vert_norms = np.zeros((number_of_vertices, 3))
    bad_normal_count = 0
    for k in range(number_of_vertices):
        try:
            tri_list = list(vertex_triangles[k])
            angle_mask = triangles[tri_list, :] == k
            angles = triangle_angles[tri_list, :]
            angles = angles[angle_mask][:, np.newaxis]
            angle_scaling = angles / np.sum(angles, axis=0)
            vert_norms[k, :] = np.mean(angle_scaling * triangle_normals[tri_list, :], axis=0)
            # Scale by angle subtended.
            vert_norms[k, :] = vert_norms[k, :] / np.sqrt(np.sum(vert_norms[k, :] ** 2, axis=0))
            # Normalise to unit vectors.
        except (ValueError, FloatingPointError):
            # If normals are bad, default to position vector
            # A nicer solution would be to detect degenerate triangles and ignore their
            # contribution to the vertex normal
            vert_norms[k, :] = vertices[k] / np.sqrt(vertices[k].dot(vertices[k]))
            bad_normal_count += 1
    if bad_normal_count:
        print(" %d vertices have bad normals" % bad_normal_count)
    return vert_norms


def compute_region_orientations(regions, vertex_normals, region_mapping):
    """Compute the orientation of given regions from vertex_normals and region mapping"""

    average_orientation = np.zeros(regions.size, 3)
    # Average orientation of the region
    for i, k in enumerate(regions):
        orient = vertex_normals[region_mapping == k, :]
        if orient:
            avg_orient = np.mean(orient, axis=0)
            average_orientation[i, :] = avg_orient / np.sqrt(np.sum(avg_orient ** 2))

    return average_orientation


def compute_triangle_areas(vertices, triangles):
    """Calculates the area of triangles making up a surface."""
    tri_u = vertices[triangles[:, 1], :] - vertices[triangles[:, 0], :]
    tri_v = vertices[triangles[:, 2], :] - vertices[triangles[:, 0], :]
    tri_norm = np.cross(tri_u, tri_v)
    triangle_areas = np.sqrt(np.sum(tri_norm ** 2, axis=1)) / 2.0
    triangle_areas = triangle_areas[:, np.newaxis]
    return triangle_areas


def compute_region_areas(regions, triangle_areas, vertex_triangles, region_mapping):
    """Compute the areas of given regions"""

    region_surface_area = np.zeros(regions.size, 1)
    avt = np.array(vertex_triangles)
    # NOTE: Slightly overestimates as it counts overlapping border triangles,
    #       but, not really a problem provided triangle-size << region-size.
    for i, k in enumerate(regions):
        regs = map(set, avt[region_mapping == k])
        region_triangles = set.union(*regs)
        if region_triangles:
            region_surface_area[i] = triangle_areas[list(region_triangles)].sum()

    return region_surface_area


class SurfacesToStructuralDataset(Flow):

    def __init__(self, cort_surf_direc: os.PathLike, subcort_surf_direc):
        """

        Parameters
        ----------
        cort_surf_direc: Directory that should contain:
                           rh.pial
                           lh.pial
        subcort_surf_direc: Directory that should contain:
                              aseg_<NUM>.srf
                            for each <NUM> in SUBCORTICAL_REG_INDS
        """
        self.cort_surf_direc = cort_surf_direc
        self.subcort_surf_direc = subcort_surf_direc

    @staticmethod
    def _pial_to_verts_and_triangs(runner: Runner, pial_surf: File) -> (np.ndarray, np.ndarray):
        pial_asc = runner.tmp_fname(pial_surf.path + ".asc")
        pial_info = runner.tmp_fname(pial_surf.path + ".info.txt")

        runner.run(fs.mris_convert_run(pial_surf, pial_asc))
        runner.run(fs.mris_convert_run(pial_surf, pial_info))

        with open(pial_info, 'r') as f:
            lines = f.readlines()

        c_ras_line = lines[32]
        ista = c_ras_line.index(' (') + 2
        iend = c_ras_line.index(')\n')
        lc_ras = c_ras_line[ista:iend].split(',')
        c_ras = np.array(lc_ras).astype('float')

        with open(pial_asc, 'r') as f:
            f.readline()
            nb_vert = f.readline().split(' ')[0]
            read_data = [[np.double(line.rstrip('\n').split()[0]),
                          np.double(line.rstrip('\n').split()[1]),
                          np.double(line.rstrip('\n').split()[2])] for line in f]

        a = np.array(read_data)
        vertices = a[0:int(nb_vert), 0:3] + c_ras
        triangles = a[int(nb_vert):, 0:3]

        return vertices, triangles

    @staticmethod
    def _reunify_both_regions(verts_l, verts_r, triangs_l, triangs_r, region_mapping_l, region_mapping_r):
        verts = np.vstack([verts_l, verts_r])
        triangs = np.vstack([triangs_l,  triangs_r + verts_l.shape[0]])
        region_mapping = np.hstack([region_mapping_l, region_mapping_r])
        return verts, triangs, region_mapping

    @staticmethod
    def _unify_regions(surfaces: List[Surface]) -> Surface:
        offsets = np.cumsum([0] + [vs.shape[0] for vs in [surf.vertices for surf in surfaces]][:-1])
        vertices = np.vstack([surf.vertices for surf in surfaces])
        triangles = np.vstack([ts + offset for ts, offset in zip([surf.triangles for surf in surfaces], offsets)])
        region_mappings = np.hstack([surf.region_mapping for surf in surfaces])
        return Surface(vertices, triangles, region_mappings)

    def _get_cortical_surfaces(self, runner: Runner):
        verts_l, triangs_l = self._pial_to_verts_and_triangs(
            runner, File(os.path.join(self.cort_surf_direc, Hemisphere.lh + ".pial")))
        verts_r, triangs_r = self._pial_to_verts_and_triangs(
            runner, File(os.path.join(self.cort_surf_direc, Hemisphere.rh + ".pial")))

        region_mapping_l = self.magic()
        region_mapping_r = self.magic()

        surface = self._unify_regions([Surface(verts_l, triangs_l, region_mapping_l),
                                       Surface(verts_r, triangs_r, region_mapping_r)])

        return surface

    @staticmethod
    def _read_fs_to_conn_indices_mapping(mapping_path):
        fs_to_conn_indices_mapping = {}
        with open(mapping_path, 'r') as fd:
            for line in fd.readlines():
                key, _, val = line.strip().split()
                fs_to_conn_indices_mapping[int(key)] = int(val)

        return fs_to_conn_indices_mapping

    @staticmethod
    def _compute_region_areas_and_orientation(surface: Surface, subcortical: bool=False):
        verts, triangs, region_mapping = surface.vertices, surface.triangles, surface.region_mapping

        nverts = verts.shape[0]
        ntriangs = triangs.shape[0]

        vertex_triangles = compute_vertex_triangles(nverts, ntriangs, triangs)
        triangle_normals = compute_triangle_normals(triangs, verts)
        triangle_angles = compute_triangle_angles(verts, ntriangs, triangs)
        vertex_normals = compute_vertex_normals(nverts, vertex_triangles, triangs,
                                                triangle_angles, triangle_normals, verts)
        triangle_areas = compute_triangle_areas(verts, triangs)

        regions = np.unique(region_mapping)
        areas = compute_region_areas(regions, triangle_areas, vertex_triangles, region_mapping)
        orientations = compute_region_orientations(regions, vertex_normals, region_mapping)

        return regions, areas, orientations

    def _get_subcortical_surfaces(self):
        indices_mapping = self._read_fs_to_conn_indices_mapping(FS_TO_CONN_INDICES_MAPPING_PATH)
        surfaces = []

        for fs_idx in SUBCORTICAL_REG_INDS:
            conn_idx = indices_mapping[fs_idx]
            filename = os.path.join(self.subcort_surf_direc, 'aseg_' + fs_idx + '.srf')
            with open(filename, 'r') as f:
                f.readline()
                nverts, ntriangs = f.readline().rstrip().split(' ')

            a = np.loadtxt(filename, skiprows=2, usecols=(0, 1, 2))
            vertices = a[:nverts]
            triangles = a[nverts:].astype(int)
            region_mapping = conn_idx * np.ones(nverts, dtype=int)
            surfaces.append(Surface(vertices, triangles, region_mapping))

        surface = self._unify_regions(surfaces)
        return surface

    def run(self, runner: Runner):

        log = logging.getLogger('SurfacesToStructuralDataset')
        tic = time.time()

        surf_subcort = self._get_subcortical_surfaces()
        surf_cort = self._get_cortical_surfaces(runner)

        regions_subcort, areas_subcort, orients_subcort = self._compute_region_areas_and_orientation(surf_subcort, True)
        regions_cort, areas_cort, orients_cort = self._compute_region_areas_and_orientation(surf_cort, False)

        max_reg = max(np.max(regions_subcort), np.max(regions_cort))
        orientations = np.zeros(max_reg + 1, 3)
        areas = np.zeros(max_reg + 1, 1)

        orientations[regions_subcort, :] = orients_subcort
        orientations[regions_cort, :] = orients_cort
        areas[regions_subcort] = areas_subcort
        areas[regions_cort] = areas_cort

        dataset = StructuralDataset(orientations, areas)

        log.info('complete in %0.2fs', time.time() - tic)
