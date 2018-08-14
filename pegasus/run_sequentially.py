import getpass
import os
import re
import subprocess
import time
import shutil
import sys
from enum import Enum
from string import Template

PATH_TO_INPUT_SUBJ_FOLDERS = "/home/submitter/data"
PATH_TO_SUBJ_CONFIG_FOLDERS = "/home/submitter/data"
PATH_TO_OUTPUT_SUBJ_FOLDER = "/home/submitter/data"

PREFIX_SUBJECT_FOLDER = "TVB"

SUBJECTS_TO_BE_PROCESSED = [24]

ATLASES = "default a2009s"

OS = "LINUX"

PATH_TO_DEFAULT_PEGASUS_CONFIGURATION = os.path.join(os.getcwd(), "config")

PREFIX_JOB_ID = "run"
REGEX_JOB_ID = PREFIX_JOB_ID + "\d\d\d\d"
MONITORED_FILE = "monitord.done"

class Atlas(object):
    DEFAULT = "default"
    A2009S = "a2009s"
    DKT = "DKT"

# TODO: better set properties to the exact atlases names to avoid if statements and easily add more parcellations
# i.e.:
# class AtlasSuffixDict(object):
#     default = ""
#     a2009s = ".a2009s"
#     DKT = ".DKTatlas"
# with desired use: atlas_suffix = getattr(AtlasSuffix, current_atlas, None)
class AtlasSuffix(object):
    DEFAULT = ""
    A2009S = ".a2009s"
    DKT = ".DKTatlas"


class configs(Enum):
    ENVIRON_CONFIGS = "environment_config.sh"
    PATIENT_PROPS = "patient_flow.properties"
    PEGASUS_PROPS = "pegasus.properties"
    SITES = "sites.xml"
    RC = "rc.txt"
    RC_OUT = "rc_out.txt"
    RC_OUT_ATLAS = "rc_out_atlas.txt"
    TC = "tc.txt"


def get_atlases_and_suffixes_lists(atlases):
    atlases_list = atlases.split(" ")
    atlas_suffixes = []
    for atlas in atlases_list:
        if atlas == Atlas.A2009S:
            atlas_suffixes.append(AtlasSuffix.A2009S)
        elif atlas == Atlas.DKT:
            atlas_suffixes.append(AtlasSuffix.DKT)
        else:
            atlas_suffixes.append(AtlasSuffix.DEFAULT)
    return atlases_list, atlas_suffixes


def create_config_files_for_subj(current_subject, atlases):

    default_pegasus_props_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.PEGASUS_PROPS.value)
    with open(default_pegasus_props_path) as default_pegasus_props_file:
        template = Template(default_pegasus_props_file.read())
        pegasus_props = template.substitute(path=current_dir)
        subj_pegasus_props_path = os.path.join(current_dir, configs.PEGASUS_PROPS.value)
        print(subj_pegasus_props_path)
        with open(subj_pegasus_props_path, "w+") as subj_pegasus_props_file:
            subj_pegasus_props_file.write(pegasus_props)

    default_patient_props_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.PATIENT_PROPS.value)
    with open(default_patient_props_path) as default_patient_props_file:
        template = Template(default_patient_props_file.read())
        patient_props = template.substitute(subject=current_subject, atlas=atlases, os=OS)
        subj_patient_props = os.path.join(current_dir, configs.PATIENT_PROPS.value)
        print(subj_patient_props)
        with open(subj_patient_props, "w+") as subj_patient_props_file:
            subj_patient_props_file.write(patient_props)

    default_environ_config_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.ENVIRON_CONFIGS.value)
    with open(default_environ_config_path) as default_environ_config_file:
        template = Template(default_environ_config_file.read())
        environ_config = template.substitute()
        subj_environ_config_path = os.path.join(current_dir, configs.ENVIRON_CONFIGS.value)
        print(subj_environ_config_path)
        try:
            with open(subj_environ_config_path, "w+") as subj_environ_config_file:
                subj_environ_config_file.write(environ_config)
        except:
            print("Writing subj_environ_config_file failed!")

    default_rc_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.RC.value)
    with open(default_rc_path) as default_rc_file:
        template = Template(default_rc_file.read())
        rc_config = template.substitute(path=os.path.join(PATH_TO_INPUT_SUBJ_FOLDERS, current_subject),
                                        subject=current_subject)
        subj_rc_path = os.path.join(current_dir, configs.RC.value)
        with open(subj_rc_path, "w+") as subj_rc_file:
            subj_rc_file.write(rc_config)

    # For outputs that do not depend on atlas
    default_rc_out_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.RC_OUT.value)
    with open(default_rc_out_path) as default_rc_out_file:
        template = Template(default_rc_out_file.read())
        rc_out_config = template.substitute(path=os.path.join(PATH_TO_OUTPUT_SUBJ_FOLDER, current_subject, "output"))

        # For outputs for all desired atlases
        atlases_list, atlas_suffixes = get_atlases_and_suffixes_lists(atlases)
        default_rc_out_atlas_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.RC_OUT_ATLAS.value)
        with open(default_rc_out_atlas_path) as default_rc_out_atlas_file:
            template_atlas = Template(default_rc_out_atlas_file.read())
            for atlas, atlas_suffix in zip(atlases_list, atlas_suffixes):
                rc_out_config +=\
                    template_atlas.substitute(path=os.path.join(PATH_TO_OUTPUT_SUBJ_FOLDER, current_subject, "output"),
                                              atlas=atlas, atlas_suffix=atlas_suffix)

            # Finally, write the subject's rc_out
            subj_rc_out_path = os.path.join(current_dir, configs.RC_OUT.value)
            with open(subj_rc_out_path, "w+") as subj_rc_out_file:
                subj_rc_out_file.write(rc_out_config)

    default_sites_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.SITES.value)
    shutil.copy(default_sites_path, current_dir)

    default_tc_path = os.path.join(PATH_TO_DEFAULT_PEGASUS_CONFIGURATION, configs.TC.value)
    shutil.copy(default_tc_path, current_dir)

    print("Configuration files for subject %s are ready!" % current_subject)


def get_currently_running_job_ids():
    print("Checking currently running job ids...")
    status = subprocess.Popen("pegasus-status", stdout=subprocess.PIPE)
    output, error = status.communicate()

    if output.find(PREFIX_JOB_ID) == -1:
        existent_job_ids = []
    else:
        existent_job_ids = [m.replace(PREFIX_JOB_ID, "") for m in re.findall(REGEX_JOB_ID, output)]
    print("Currently running job ids are: %s" % existent_job_ids)

    return existent_job_ids


def get_specified_submit_folder(current_dir):
    environ_config_path = os.path.join(current_dir, configs.ENVIRON_CONFIGS.value)
    myvars = {}

    with open(environ_config_path) as environ_config_file:
        for line in environ_config_file:
            if line.startswith("#") or len(line) == 0 or line == "\n":
                continue
            name, var = line.partition("=")[::2]
            myvars[name.replace("export ", "")] = var.replace("\n", "")

    submit_folder = myvars['PEGASUSSUBMIT']
    if "$" in submit_folder:
        for key in myvars.keys():
            key_format1 = "${" + key + "}"
            key_format2 = "$" + key
            if key_format1 in submit_folder:
                submit_folder = submit_folder.replace(key_format1, myvars[key])
            if key_format2 in submit_folder:
                submit_folder = submit_folder.replace(key_format2, myvars[key])

    return submit_folder


if __name__ == "__main__":
    arg_subjects = sys.argv[1].split(" ")
    SUBJECTS_TO_BE_PROCESSED = [int(val) for val in arg_subjects]
    print("Starting to process the following subjects: %s", SUBJECTS_TO_BE_PROCESSED)

    if not os.path.exists(PATH_TO_SUBJ_CONFIG_FOLDERS):
        os.mkdir(PATH_TO_SUBJ_CONFIG_FOLDERS)
        print("Folder %s has been created..." % PATH_TO_SUBJ_CONFIG_FOLDERS)

    for subject_number in SUBJECTS_TO_BE_PROCESSED:
        current_subject = PREFIX_SUBJECT_FOLDER + str(subject_number)
        print("Starting to process the subject: %s" % current_subject)

        current_dir = os.path.join(PATH_TO_SUBJ_CONFIG_FOLDERS, current_subject, "configs")

        if not os.path.exists(current_dir):
            os.mkdir(current_dir)
            print("Folder %s has been created..." % current_dir)
            create_config_files_for_subj(current_subject, ATLASES)

        existent_job_ids = get_currently_running_job_ids()

        print("Starting pegasus run for subject: " + current_subject)
        current_dax_dir = os.path.join(current_dir, "dax")
        p = subprocess.call(["sh", "main_pegasus.sh", current_dir, current_dax_dir])

        new_job_ids = get_currently_running_job_ids()

        for job in existent_job_ids:
            new_job_ids.remove(job)

        current_job_id = new_job_ids[0]
        print("The job that has been started has the id: %s" % current_job_id)

        submit_dir = os.path.join(get_specified_submit_folder(current_dir), getpass.getuser(), "pegasus",
                                  "TVB-PIPELINE", PREFIX_JOB_ID + current_job_id)

        print("Starting to monitor the submit folder: %s ..." % submit_dir)

        while True:
            if MONITORED_FILE in os.listdir(submit_dir):
                break
            else:
                print("Checked at %s and %s file was not generated yet!" % (
                    str(time.strftime("%a, %d %b %Y %H:%M:%S", time.gmtime())), MONITORED_FILE))
                time.sleep(900)

        print("The run has finished for job with id: %s" % current_job_id)
