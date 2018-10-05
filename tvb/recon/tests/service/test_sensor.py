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


def inplace_change(filename, old_string, new_string):
    # Safely read the input filename using 'with'
    with open(filename) as f:
        s = f.read()
        if old_string not in s:
            return

    # Safely write the changed content, if found in the file
    with open(filename, 'w') as f:
        s = s.replace(old_string, new_string)
        f.write(s)


# if __name__ == "__main__":
#
#     datapath = "/Users/dionperd/Dropbox/Work/VBtech/VEP/data/CC"
#
#     subjects = (np.array(range(1, 30)) + 1).tolist()
#     subjects = ["TVB%s" % subject for subject in subjects]
#     subjects += ["TVB34", "TVB40", "TVB45"]
#     tvb1_configs_path = os.path.join(datapath, "TVB1", "configs")
#     # rc_out_path_template = os.path.join(tvb1_configs_path, "rc_out.txt")
#     tc_path_template = os.path.join(tvb1_configs_path, "tc.txt")
#     pfp_path_template = os.path.join(tvb1_configs_path, "patient_flow.properties")
#
#     for subject in subjects:
#         print(subject)
#         configspath = os.path.join(datapath, subject, "configs")
#         # rc_out_path = os.path.join(configspath, "rc_out.txt")
#         # rc_out1_path = os.path.join(configspath, "rc_out1.txt")
#         tc_path = os.path.join(configspath, "tc.txt")
#         tc1_path = os.path.join(configspath, "tc1.txt")
#         pfp_path = os.path.join(configspath, "patient_flow.properties")
#         pfp1_path = os.path.join(configspath, "patient_flow.properties1")
#
#         # os.rename(rc_out_path, rc_out1_path)
#         os.rename(tc_path, tc1_path)
#         os.rename(pfp_path, pfp1_path)
#         # copyfile(rc_out_path_template, rc_out_path)
#         copyfile(tc_path_template, tc_path)
#         copyfile(pfp_path_template, pfp_path)
#
#         if subject == "TVB34":
#             subject_string = "TVB4"
#         elif subject == "TVB40":
#                 subject_string = "TVB10"
#         elif subject == "TVB45":
#                 subject_string = "TVB15"
#         else:
#             subject_string = subject
#
#         # inplace_change(rc_out_path, "TVB1", subject_string)
#         inplace_change(pfp_path, "TVB1", subject_string)



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

            gain_filename = "seeg_distance_gain.txt"
            out_gain_path = os.path.join(atlaspath, gain_filename)
            gain_matrices[subject][atlas]["distance"] = \
                sensor_service.compute_seeg_distance_gain_matrix(seeg_xyz, cort_surf_path, subcort_surf_path,
                                                                 cort_rm_path, subcort_rm_path, out_gain_path,
                                                                 normalize=100)
            # atlasgain_filename = gain_filename.split(".txt")[0] + atlas_suffix + ".txt"
            # copyfile(out_gain_path, os.path.join(outpath, atlasgain_filename))
            try:
                os.remove(out_gain_path.replace("distance", "inv_square"))
            except:
                pass

            gain_filename = "seeg_regions_distance_gain.txt"
            out_gain_path = os.path.join(atlaspath, gain_filename)
            gain_matrices[subject][atlas]["regions_distance"] = \
                sensor_service.compute_seeg_regions_distance_gain_matrix(seeg_xyz, centers_path, areas_path,
                                                                         out_gain_path, normalize=100)
            # atlasgain_filename = gain_filename.split(".txt")[0] + atlas_suffix + ".txt"
            # copyfile(out_gain_path, os.path.join(outpath, atlasgain_filename))
            try:
                os.remove(out_gain_path.replace("distance", "inv_square"))
            except:
                pass

            rmtree(conn_path)

