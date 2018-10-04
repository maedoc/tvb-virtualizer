import os
import zipfile
from shutil import copyfile, rmtree
import numpy as np
from tvb.recon.algo.service.sensor import SensorService


def unzip_folder(zippath, outdir=None):
    zippath = zippath.split(".zip")[0]
    if outdir == None:
        outdir = zippath
    zip_ref = zipfile.ZipFile(zippath+".zip", 'r')
    zip_ref.extractall(outdir)
    zip_ref.close()


if __name__ == "__main__":

    datapath = "/Users/dionperd/Dropbox/Work/VBtech/VEP/data/CC"
    respath = "/Users/dionperd/Dropbox/Work/VBtech/VEP/results/CC"

    subjects = (np.array(range(30)) + 1).tolist()
    del subjects[14]
    subjects = ["TVB%s" % subject for subject in subjects]
    subjects += ["TVB4_mrielec", "TVB10_mrielec"]

    atlases = ["default", "a2009s"]

    sensor_service = SensorService()

    gain_matrices = {}

    for subject in subjects:

        print(subject)

        gain_matrices[subject] = {}

        for atlas in atlases:

            print(atlas)

            gain_matrices[subject][atlas] = {}

            atlas_suffix = str(np.where(atlas == "default", "", ".a2009s"))

            outpath = os.path.join(datapath, subject, "output")
            tvbpath = os.path.join(respath, subject, "tvb")
            atlaspath = os.path.join(tvbpath, atlas)

            seeg_xyz = os.path.join(tvbpath, "seeg_xyz.txt")

            cort_surf_path = os.path.join(tvbpath, "surface_cort.zip")
            subcort_surf_path = os.path.join(tvbpath, "surface_subcort.zip")

            cort_rm_path = os.path.join(atlaspath, "region_mapping_cort.txt")
            subcort_rm_path = os.path.join(atlaspath, "region_mapping_subcort.txt")

            conn_path = os.path.join(atlaspath, "connectivity")
            unzip_folder(conn_path, outdir=None)
            centers_path = os.path.join(conn_path, "centers.txt")
            areas_path = os.path.join(conn_path, "areas.txt")

            gain_filename = "seeg_dipole_gain.txt"
            out_gain_path = os.path.join(atlaspath, gain_filename)
            gain_matrices[subject][atlas]["dipole"] = \
                sensor_service.compute_seeg_dipole_gain_matrix(seeg_xyz, cort_surf_path, subcort_surf_path,
                                                               cort_rm_path, subcort_rm_path, out_gain_path,
                                                               normalize=100)
            # atlasgain_filename = gain_filename.split(".txt")[0] + atlas_suffix + ".txt"
            # copyfile(out_gain_path, os.path.join(outpath, atlasgain_filename))

            gain_filename = "seeg_inv_square_gain.txt"
            out_gain_path = os.path.join(atlaspath, gain_filename)
            gain_matrices[subject][atlas]["inv_square"] = \
                sensor_service.compute_seeg_inv_square_gain_matrix(seeg_xyz, cort_surf_path, subcort_surf_path,
                                                                   cort_rm_path, subcort_rm_path, out_gain_path,
                                                                   normalize=100)
            # atlasgain_filename = gain_filename.split(".txt")[0] + atlas_suffix + ".txt"
            # copyfile(out_gain_path, os.path.join(outpath, atlasgain_filename))

            gain_filename = "seeg_regions_inv_square_gain.txt"
            out_gain_path = os.path.join(atlaspath, gain_filename)
            gain_matrices[subject][atlas]["regions_inv_square"] = \
                sensor_service.compute_seeg_regions_inv_square_gain_matrix(seeg_xyz, centers_path, areas_path,
                                                                           out_gain_path, normalize=100)
            # atlasgain_filename = gain_filename.split(".txt")[0] + atlas_suffix + ".txt"
            # copyfile(out_gain_path, os.path.join(outpath, atlasgain_filename))

            rmtree(conn_path)

