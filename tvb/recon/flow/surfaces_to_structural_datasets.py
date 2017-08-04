import enum
import numpy as np
import os
import os.path
import logging
import re
import tempfile
import time
from typing import List, Optional
from zipfile import ZipFile

from tvb.recon.cli.runner import Runner, File
from tvb.recon.cli import fs
from tvb.recon.flow.core import Flow
from tvb.recon.algo.structural_dataset import StructuralDataset
from tvb.recon.io.factory import IOUtils


SUBCORTICAL_REG_INDS = [8, 10, 11, 12, 13, 16, 17, 18, 26, 47, 49, 50, 51, 52, 53, 54, 58]
FS_LUT_LH_SHIFT = 1000
FS_LUT_RH_SHIFT = 2000


class Hemisphere(enum.Enum):
    rh = 'rh'
    lh = 'lh'


class Surface:
    def __init__(self, vertices: np.array, triangles: np.array, region_mapping: np.array):
        assert vertices.ndim == 2
        assert triangles.ndim == 2
        assert region_mapping.ndim == 1

        assert vertices.shape[1] == 3
        assert triangles.shape[1] == 3
        assert region_mapping.shape[0] == vertices.shape[0]

        self.vertices = vertices
        self.triangles = triangles
        self.region_mapping = region_mapping

        self.nverts = self.vertices.shape[0]
        self.ntriangs = self.triangles.shape[0]

        self.vertex_triangles = compute_vertex_triangles(self.nverts, self.ntriangs, self.triangles)
        self.triangle_normals = compute_triangle_normals(self.triangles, self.vertices)
        self.triangle_angles = compute_triangle_angles(self.vertices, self.ntriangs, self.triangles)
        self.vertex_normals = compute_vertex_normals(self.nverts, self.vertex_triangles, self.triangles,
                                                     self.triangle_angles, self.triangle_normals, self.vertices)
        self.triangle_areas = compute_triangle_areas(self.vertices, self.triangles)

    def save_surf_zip(self, filename):
        tmpdir = tempfile.TemporaryDirectory()

        file_vertices = os.path.join(tmpdir.name, 'vertices.txt')
        file_triangles = os.path.join(tmpdir.name, 'triangles.txt')
        file_normals = os.path.join(tmpdir.name, 'normals.txt')

        np.savetxt(file_vertices, self.vertices, fmt='%.6f %.6f %.6f')
        np.savetxt(file_triangles, self.triangles, fmt='%d %d %d')
        np.savetxt(file_normals, self.vertex_normals, fmt='%.6f %.6f %.6f')

        with ZipFile(filename, 'w') as zip_file:
            zip_file.write(file_vertices, os.path.basename(file_vertices))
            zip_file.write(file_triangles, os.path.basename(file_triangles))
            zip_file.write(file_normals, os.path.basename(file_normals))

    def save_region_mapping_txt(self, filename):
        np.savetxt(filename, self.region_mapping, fmt="%d")


class ColorLut:
    def __init__(self, filename: os.PathLike):
        table = np.genfromtxt(os.fspath(filename), dtype=None)

        if len(table.dtype) == 6:
            # id name R G B A
            self.inds = table[table.dtype.names[0]]
            self.names = table[table.dtype.names[1]].astype('U')
            self.r = table[table.dtype.names[2]]
            self.g = table[table.dtype.names[3]]
            self.b = table[table.dtype.names[4]]
            self.a = table[table.dtype.names[5]]
            self.shortnames = np.zeros(len(self.names), dtype='U')

        elif len(table.dtype) == 7:
            # id shortname name R G B A
            self.inds = table[table.dtype.names[0]]
            self.shortnames = table[table.dtype.names[1]].astype('U')
            self.names = table[table.dtype.names[2]].astype('U')
            self.r = table[table.dtype.names[3]]
            self.g = table[table.dtype.names[4]]
            self.b = table[table.dtype.names[5]]
            self.a = table[table.dtype.names[6]]


class RegionIndexMapping:

    def __init__(self, color_lut_src_file: os.PathLike, color_lut_trg_file: os.PathLike):
        self.src_table = ColorLut(color_lut_src_file)
        self.trg_table = ColorLut(color_lut_trg_file)

        names_to_trg = dict(zip(self.trg_table.names, self.trg_table.inds))

        self.src_to_trg = dict()
        for src_ind, src_name in zip(self.src_table.inds, self.src_table.names):
            trg_ind = names_to_trg.get(src_name, None)
            if trg_ind is not None:
                self.src_to_trg[src_ind] = trg_ind

        self.unknown_ind = names_to_trg.get('Unknown', 0)   # zero as the default unknown area

    def source_to_target(self, index):
        return self.src_to_trg.get(index, self.unknown_ind)


def merge_surfaces(surfaces: List[Surface]) -> Surface:
    offsets = np.cumsum([0] + [vs.shape[0] for vs in [surf.vertices for surf in surfaces]][:-1])
    vertices = np.vstack([surf.vertices for surf in surfaces])
    triangles = np.vstack([ts + offset for ts, offset in zip([surf.triangles for surf in surfaces], offsets)])
    region_mappings = np.hstack([surf.region_mapping for surf in surfaces])
    return Surface(vertices, triangles, region_mappings)


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


def compute_triangle_areas(vertices, triangles):
    """Calculates the area of triangles making up a surface."""
    tri_u = vertices[triangles[:, 1], :] - vertices[triangles[:, 0], :]
    tri_v = vertices[triangles[:, 2], :] - vertices[triangles[:, 0], :]
    tri_norm = np.cross(tri_u, tri_v)
    triangle_areas = np.sqrt(np.sum(tri_norm ** 2, axis=1)) / 2.0
    triangle_areas = triangle_areas[:, np.newaxis]
    return triangle_areas


def compute_region_orientations(regions, vertex_normals, region_mapping):
    """Compute the orientation of given regions from vertex_normals and region mapping"""

    average_orientation = np.zeros((regions.size, 3))
    # Average orientation of the region
    for i, k in enumerate(regions):
        orient = vertex_normals[region_mapping == k, :]
        if orient.shape[0] > 0:
            avg_orient = np.mean(orient, axis=0)
            average_orientation[i, :] = avg_orient / np.sqrt(np.sum(avg_orient ** 2))

    return average_orientation


def compute_region_areas(regions, triangle_areas, vertex_triangles, region_mapping):
    """Compute the areas of given regions"""

    region_surface_area = np.zeros(regions.size)
    avt = np.array(vertex_triangles)
    # NOTE: Slightly overestimates as it counts overlapping border triangles,
    #       but, not really a problem provided triangle-size << region-size.
    for i, k in enumerate(regions):
        regs = map(set, avt[region_mapping == k])
        region_triangles = set.union(*regs)
        if region_triangles:
            region_surface_area[i] = triangle_areas[list(region_triangles)].sum()

    return region_surface_area


def compute_region_centers(regions, vertices, region_mapping):

    region_centers = np.zeros((regions.size, 3))
    for i, k in enumerate(regions):
        vert = vertices[region_mapping == k, :]
        if vert.shape[0] > 0:
            region_centers[i, :] = np.mean(vert, axis=0)

    return region_centers


def compute_region_params(surface: Surface, subcortical: bool=False)\
        -> (np.ndarray, np.ndarray, np.ndarray, np.ndarray):
    verts, triangs, region_mapping = surface.vertices, surface.triangles, surface.region_mapping

    regions = np.unique(region_mapping)
    areas = compute_region_areas(regions, surface.triangle_areas, surface.vertex_triangles, region_mapping)
    orientations = compute_region_orientations(regions, surface.vertex_normals, region_mapping)
    centers = compute_region_centers(regions, verts, region_mapping)

    return regions, areas, orientations, centers

def extract_vector(string: str, name: str) -> Optional[List[float]]:
    r"""
    Extract numerical vector from a block of text. The vector has to be on a single line with the format:
    <name> : (x0, x1, x2 [,...])
    If the vector in the correct format is missing, return None.

    >>> extract_vector("EXAMPLE\na: (1.0, 2.0, 3.0)\nb: (0.0, 0.0, 0.0)", "a")
    [1.0, 2.0, 3.0]

    >>> extract_vector("EMPTY", "a") is None
    True
    """

    for line in string.split("\n"):
        match = re.match(r"""^\s*
                         (.+?)              # name
                         \s*:\s*            # separator
                         \(([0-9.,\s-]+)\)   # vector: (x0, x1, ....)
                         \s*$""",
                         line, re.X)

        if match and match.group(1) == name:
            try:
                vector = [float(x) for x in match.group(2).split(",")]
                return vector
            except ValueError:
                pass

    return None


def pial_to_verts_and_triangs(runner: Runner, pial_surf: File) -> (np.ndarray, np.ndarray):
    pial_asc = runner.tmp_fname(os.path.basename(pial_surf.path + ".asc"))
    runner.run(fs.mris_convert_run(pial_surf, pial_asc))

    with open(pial_asc, 'r') as f:
        f.readline()
        nverts, ntriangs = [int(n) for n in f.readline().strip().split(' ')]

    vertices = np.genfromtxt(pial_asc.path, dtype=float, skip_header=2, skip_footer=ntriangs, usecols=(0, 1, 2))
    triangles = np.genfromtxt(pial_asc.path, dtype=int, skip_header=2+nverts, usecols=(0, 1, 2))
    assert vertices.shape == (nverts, 3)
    assert triangles.shape == (ntriangs, 3)

    mris_info = runner.run(fs.mris_info_run(pial_surf), capture_output=True)
    c_ras_list = extract_vector(mris_info, "c_(ras)")
    assert c_ras_list is not None
    vertices[:, 0:3] += np.array(c_ras_list)

    return vertices, triangles


def read_cortical_region_mapping(label_direc: os.PathLike, hemisphere: Hemisphere, fs_to_conn: RegionIndexMapping)\
        -> np.ndarray:
    filename = os.path.join(label_direc, hemisphere.value + ".aparc.annot")
    annot = IOUtils.read_annotation(filename)
    region_mapping = annot.region_mapping

    region_mapping[region_mapping == -1] = 0   # Unknown regions in hemispheres

    # $FREESURFER_HOME/FreeSurferColorLUT.txt describes the shift
    if hemisphere == Hemisphere.lh:
        region_mapping += FS_LUT_LH_SHIFT
    else:
        region_mapping += FS_LUT_RH_SHIFT

    fs_to_conn_fun = np.vectorize(lambda n: fs_to_conn.source_to_target(n))
    region_mapping = fs_to_conn_fun(region_mapping)

    return region_mapping


def get_cortical_surfaces(runner: Runner, cort_surf_direc: os.PathLike, label_direc: os.PathLike,
                          region_index_mapping: RegionIndexMapping) -> Surface:
    verts_l, triangs_l = pial_to_verts_and_triangs(runner,
                                                   File(os.path.join(cort_surf_direc, Hemisphere.lh.value + ".pial")))
    verts_r, triangs_r = pial_to_verts_and_triangs(runner,
                                                   File(os.path.join(cort_surf_direc, Hemisphere.rh.value + ".pial")))

    region_mapping_l = read_cortical_region_mapping(label_direc, Hemisphere.lh, region_index_mapping)
    region_mapping_r = read_cortical_region_mapping(label_direc, Hemisphere.rh, region_index_mapping)

    surface = merge_surfaces([Surface(verts_l, triangs_l, region_mapping_l),
                              Surface(verts_r, triangs_r, region_mapping_r)])

    return surface


def get_subcortical_surfaces(subcort_surf_direc: os.PathLike, region_index_mapping: RegionIndexMapping) -> Surface:
    surfaces = []

    for fs_idx in SUBCORTICAL_REG_INDS:
        conn_idx = region_index_mapping.source_to_target(fs_idx)
        filename = os.path.join(subcort_surf_direc, 'aseg_%03d.srf' % fs_idx)
        with open(filename, 'r') as f:
            f.readline()
            nverts, ntriangs = [int(n) for n in f.readline().strip().split(' ')]

        vertices = np.genfromtxt(filename, dtype=float, skip_header=2, skip_footer=ntriangs, usecols=(0, 1, 2))
        triangles = np.genfromtxt(filename, dtype=int, skip_header=2 + nverts, usecols=(0, 1, 2))
        region_mapping = conn_idx * np.ones(nverts, dtype=int)
        surfaces.append(Surface(vertices, triangles, region_mapping))

    surface = merge_surfaces(surfaces)
    return surface


class SurfacesToStructuralDataset(Flow):

    def __init__(self,
                 cort_surf_direc: os.PathLike,
                 label_direc: os.PathLike,
                 subcort_surf_direc: os.PathLike,
                 source_lut: os.PathLike,
                 target_lut: os.PathLike,
                 weights_file: os.PathLike,
                 tract_lengths_file: os.PathLike,
                 struct_zip_file: os.PathLike,
                 out_surfaces_dir: os.PathLike=None):
        """

        Parameters
        ----------
        cort_surf_direc: Directory that should contain:
                           rh.pial
                           lh.pial
        label_direc: Directory that should contain:
                       rh.aparc.annot
                       lh.aparc.annot
        subcort_surf_direc: Directory that should contain:
                              aseg_<NUM>.srf
                            for each <NUM> in SUBCORTICAL_REG_INDS
        source_lut: File with the color look-up table used for the original parcellation
        target_lut: File with the color look-up table used for the connectome generation
        weights_file: text file with weights matrix (which should be upper triangular)
        tract_lengths_file: text file with tract length matrix (which should be upper triangular)
        struct_zip_file: zip file containing TVB structural dataset to be created
        out_surfaces_dir: directory where to put the surfaces and region mappings in TVB format
        """
        self.cort_surf_direc = cort_surf_direc
        self.subcort_surf_direc = subcort_surf_direc
        self.label_direc = label_direc
        self.source_lut = source_lut
        self.target_lut = target_lut
        self.weights_file = weights_file
        self.tract_lenghts_file = tract_lengths_file
        self.struct_zip_file = struct_zip_file
        self.out_surfaces_dir = out_surfaces_dir

    def run(self, runner: Runner, include_unknown=False):

        log = logging.getLogger('SurfacesToStructuralDataset')
        tic = time.time()

        region_index_mapping = RegionIndexMapping(self.source_lut, self.target_lut)

        surf_subcort = get_subcortical_surfaces(self.subcort_surf_direc, region_index_mapping)
        surf_cort = get_cortical_surfaces(runner, self.cort_surf_direc, self.label_direc, region_index_mapping)

        if self.out_surfaces_dir:
            surf_subcort.save_region_mapping_txt(os.path.join(self.out_surfaces_dir, "region_mapping_subcort.txt"))
            surf_subcort.save_surf_zip(os.path.join(self.out_surfaces_dir, "surface_subcort.zip"))
            surf_cort.save_region_mapping_txt(os.path.join(self.out_surfaces_dir, "region_mapping_cort.txt"))
            surf_cort.save_surf_zip(os.path.join(self.out_surfaces_dir, "surface_cort.zip"))

        region_params_subcort = compute_region_params(surf_subcort, True)
        region_params_cort = compute_region_params(surf_cort, False)

        nregions = max(region_index_mapping.trg_table.inds) + 1
        orientations = np.zeros((nregions, 3))
        areas = np.zeros(nregions)
        centers = np.zeros((nregions, 3))
        cortical = np.zeros(nregions, dtype=bool)

        for region_params, is_cortical in [(region_params_subcort, False), (region_params_cort, True)]:
            regions, reg_areas, reg_orientations, reg_centers = region_params
            orientations[regions, :] = reg_orientations
            areas[regions] = reg_areas
            centers[regions, :] = reg_centers
            cortical[regions] = is_cortical

        weights = np.genfromtxt(os.fspath(self.weights_file))
        tract_lengths = np.genfromtxt(os.fspath(self.tract_lenghts_file))

        if not include_unknown:
            # Remove the region from orientations, areas and centers
            indices = list(range(0, region_index_mapping.unknown_ind)) \
                      + list(range(region_index_mapping.unknown_ind + 1, nregions))

            names = region_index_mapping.trg_table.names[indices]
            orientations = orientations[indices]
            areas = areas[indices]
            centers = centers[indices]
            cortical = cortical[indices]
        else:
            # Add the region to weights and tract lengths
            names = region_index_mapping.trg_table.names

            np.insert(weights, region_index_mapping.unknown_ind, 0.0, axis=0)
            np.insert(weights, region_index_mapping.unknown_ind, 0.0, axis=1)
            np.insert(tract_lengths, region_index_mapping.unknown_ind, 0.0, axis=0)
            np.insert(tract_lengths, region_index_mapping.unknown_ind, 0.0, axis=1)

        dataset = StructuralDataset(orientations, areas, centers, cortical, weights, tract_lengths, names)
        dataset.save_to_txt_zip(self.struct_zip_file)

        log.info('complete in %0.2fs', time.time() - tic)
