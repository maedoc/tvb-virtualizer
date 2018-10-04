import os
import sys
import time
from Pegasus.DAX3 import ADAG
from tvb.recon.dax import AtlasSuffix, Atlas
from tvb.recon.dax.configuration import Configuration, ConfigKey, SensorsType
from tvb.recon.dax.t1_processing import T1Processing
from tvb.recon.dax.resampling import Resampling
from tvb.recon.dax.aseg_generation import AsegGeneration
from tvb.recon.dax.mapping_details import MappingDetails
from tvb.recon.dax.coregistration import Coregistration
from tvb.recon.dax.dwi_processing import DWIProcessing
from tvb.recon.dax.tracts_generation import TractsGeneration
from tvb.recon.dax.connectome_generation import ConnectomeGeneration
from tvb.recon.dax.head_model import HeadModel
from tvb.recon.dax.sensor_model import SensorModel
from tvb.recon.dax.source_model import SourceModel
from tvb.recon.dax.lead_field_model import LeadFieldModel
from tvb.recon.dax.mrielec_seeg_computation import MriElecSEEGComputation
from tvb.recon.dax.seeg_computation import SEEGComputation
from tvb.recon.dax.sensor_gain_computation import SensorGainComputation
from tvb.recon.dax.output_conversion import OutputConversion


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


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.stderr.write("Usage: %s DAXFILE\n" % (sys.argv[0]))
        sys.exit(1)
    daxfile = sys.argv[1]
    patient_file = sys.argv[2]

    dax = ADAG("TVB-PIPELINE")
    dax.metadata("created", time.ctime())

    config = Configuration(patient_file)

    subject = config.props[ConfigKey.SUBJECT]
    trg_subject = config.props[ConfigKey.TRGSUBJECT]

    atlases = config.props[ConfigKey.ATLAS]
    atlases_list, atlas_suffixes = get_atlases_and_suffixes_lists(atlases)
    n_atlases = len(atlases_list)

    # T1 processing

    t1_processing = T1Processing(subject, config.props[ConfigKey.OVERWRITE_RECONALL_FLAG],
                                 config.props[ConfigKey.T1_FRMT], config.props[ConfigKey.T2_FLAG],
                                 config.props[ConfigKey.T2_FRMT], config.props[ConfigKey.FLAIR_FLAG],
                                 config.props[ConfigKey.FLAIR_FRMT], config.props[ConfigKey.OPENMP_THRDS],
                                 atlas_suffixes)

    job_recon, job_t1, jobs_aparc_aseg = t1_processing.add_t1_processing_steps(dax, config.props[ConfigKey.RESAMPLE_FLAG])

    if config.props[ConfigKey.RESAMPLE_FLAG] == "True":
        resampling = Resampling(subject, trg_subject, config.props[ConfigKey.DECIM_FACTOR], atlas_suffixes)
        jobs_resamp_cort = resampling.add_surface_resampling_steps(dax, job_recon, job_t1)
        jobs_resamp_pial = jobs_resamp_cort[0]
        jobs_resamp_aparcs = jobs_resamp_cort[1]
    else:
        jobs_resamp_cort = None

    aseg_generation = \
        AsegGeneration(subject, config.props[ConfigKey.ASEG_LH_LABELS], config.props[ConfigKey.ASEG_RH_LABELS])
    job_aseg_lh, job_aseg_rh = aseg_generation.add_aseg_generation_steps(dax, job_recon)

    # DWI processing
    dwi_processing = DWIProcessing(config.props[ConfigKey.DWI_IS_REVERSED], config.props[ConfigKey.DWI_FRMT],
                                   config.props[ConfigKey.DWI_ADD_GRADIENT], config.props[ConfigKey.MRTRIX_THRDS],
                                   config.props[ConfigKey.DWI_SCAN_DIRECTION], config.props[ConfigKey.OS])
    job_b0, job_mask = dwi_processing.add_dwi_processing_steps(dax)

    # Coregistration
    coregistration = Coregistration(subject, config.props[ConfigKey.USE_FLIRT], atlas_suffixes)
    job_t1_in_d, jobs_aparc_aseg_in_d = coregistration.add_coregistration_steps(dax, job_b0, job_t1, jobs_aparc_aseg)

    # Tractography
    tracts_generation = TractsGeneration(config.props[ConfigKey.DWI_MULTI_SHELL],
                                         config.props[ConfigKey.MRTRIX_THRDS],
                                         config.props[ConfigKey.STRMLNS_NO],
                                         config.props[ConfigKey.STRMLNS_SIFT_NO],
                                         config.props[ConfigKey.STRMLNS_LEN],
                                         config.props[ConfigKey.STRMLNS_STEP],
                                         config.props[ConfigKey.OS])

    job_tcksift = tracts_generation.add_tracts_generation_steps(dax, job_t1_in_d, job_mask)

    # Deal with mapping details, connectome generation and output_conersion jobs by looping across atlases
    mapping_details = []
    jobs_mapping_details = []
    connectome_generation = []
    jobs_weights = []
    jobs_lengths = []
    output_conversion = []
    jobs_conn = []
    for iatlas, atlas_suffix in enumerate(atlas_suffixes):
        mapping_details.append(MappingDetails(trg_subject, atlas_suffix))
        if jobs_resamp_cort is not None:
            jobs_resamp_cort_per_atlas = jobs_resamp_pial + jobs_resamp_aparcs[iatlas]
        else:
            jobs_resamp_cort_per_atlas = None
        jobs_mapping_details.append(mapping_details[-1]. \
                                    add_mapping_details_step(dax, job_t1, job_aseg_lh, job_aseg_rh,
                                                             jobs_resamp_cort_per_atlas))

        connectome_generation.append(ConnectomeGeneration(config.props[ConfigKey.STRMLNS_SIFT_NO], atlas_suffix))
        temp_jobs_weights, temp_jobs_lengths = \
            connectome_generation[-1].add_tracts_generation_steps(dax, job_tcksift,
                                                                  jobs_aparc_aseg_in_d[iatlas],
                                                                  jobs_mapping_details[-1])
        jobs_weights.append(temp_jobs_weights)
        jobs_lengths.append(temp_jobs_lengths)

        # Ouput connectivity conversion
        output_conversion.append(OutputConversion(atlas_suffix))
        jobs_conn.append(output_conversion[-1].add_conversion_steps(dax, jobs_aparc_aseg[iatlas],
                                                                    jobs_mapping_details[-1],
                                                                    jobs_weights[-1], jobs_lengths[-1]))

    # Forward modeling:
    if config.props[ConfigKey.BEM_SURFACES] == "True" or config.props[ConfigKey.USE_OPENMEEG] == "True":
        head_model = HeadModel(subject)
        job_bem_surfaces = head_model.generate_bem_surfaces(dax, job_t1)

    if config.props[ConfigKey.PROCESS_SENSORS] == "True":
        gain_computation = []
        for sensor_type in [SensorsType.SEEG.value, SensorsType.EEG.value, SensorsType.MEG.value]:
            # We assume we know the positions of EEG and MEG sensors for the moment:
            job_sensor_xyz = None
            if sensor_type == SensorsType.SEEG.value:
                # We have the OpenMEEG choice only for seeg for now (?..)
                # TODO: finalize OpenMEEG workflow & include all sensors for it
                if config.props[ConfigKey.USE_OPENMEEG] == "True":
                    print("Using OpenMEEG for SEEG gain matrix computation!")
                    # OpenMEEG workflow
                    # Gain matrix will include only cortical sources
                    job_head_model = head_model.add_head_model_steps(dax, job_bem_surfaces)

                    source_model = SourceModel(subject, trg_subject, atlas_suffixes)
                    jobs_source_model = source_model.add_source_model_steps(dax, job_head_model,
                                                                            jobs_mapping_details)

                    sensor_model = SensorModel(subject, trg_subject, atlas_suffixes)
                    jobs_sensor_model_lh, jobs_sensor_model_rh = \
                        sensor_model.add_sensor_model_steps(dax, job_head_model, jobs_source_model)

                    lead_field_models = []
                    for atlas_suffix, job_sensor_model_lh, job_sensor_model_rh \
                            in zip(atlas_suffixes, jobs_sensor_model_lh, jobs_sensor_model_rh):
                        lead_field_models.append(LeadFieldModel(subject, trg_subject, atlas_suffix))
                        lead_field_models[-1].add_lead_field_model_steps(dax, job_sensor_model_lh,
                                                                         job_sensor_model_rh)

                    # TODO: Those should undergo the same process as SEEG for OPENMEEG workflow
                    continue

                else:
                    # Compute the seeg positions
                    if config.props[ConfigKey.MRIELEC_FLAG] == "True":
                        print("Using MRIelectrodes.nii.gz for SEEG positions' computation!")
                        # MRIELEC: SEEG sensors depicted on T1
                        mrielec_seeg_computation = \
                            MriElecSEEGComputation(subject, config.props[ConfigKey.MRIELEC_FRMT],
                                                   config.props[ConfigKey.SAME_SPACE_VOL_POM],
                                                   config.props[ConfigKey.MRIELEC_BIN_DILATE],
                                                   config.props[ConfigKey.MRIELEC_BIN_ERODE])
                        job_sensor_xyz = mrielec_seeg_computation.add_computation_steps(dax, job_t1)

                    else:
                        if config.props[ConfigKey.CT_FLAG] == "True":
                            print("Using CT.nii.gz for SEEG positions' computation!")
                            # CT scan with SEEG sensors' positions
                            seeg_computation = SEEGComputation(subject, config.props[ConfigKey.CT_FRMT],
                                                               config.props[ConfigKey.CT_ELEC_INTENSITY_TH])

                            job_sensor_xyz = \
                                seeg_computation.add_seeg_positions_computation_steps(dax, job_t1, job_recon)
                if job_sensor_xyz is None:
                    continue

            else:
                if sensor_type == SensorsType.EEG.value and config.props[ConfigKey.EEG_FLAG] == "False":
                    continue

                if sensor_type == SensorsType.MEG.value and config.props[ConfigKey.MEG_FLAG] == "False":
                    continue

            for iatlas, (atlas_suffix, job_mapping_details) in enumerate(zip(atlas_suffixes, jobs_mapping_details)):
                print("Gain matrix computation for %s sensors and atlas %s: %s ..." %
                      (sensor_type, str(iatlas+1), atlases_list[iatlas]))
                gain_computation.append(SensorGainComputation(config.props[ConfigKey.SUBJECT],
                                                              sensor_type, atlas_suffix))
                # Ignoring only subcortical sources dipoles' orientations.
                if config.props[ConfigKey.SENSOR_GAIN_USE_DIPOLE] == "True":
                    print("...using dipole orientations...")
                    gain_computation[-1].add_sensor_dipole_gain_computation_steps(dax, job_sensor_xyz,
                                                                                  job_mapping_details)
                # From here and on ignoring all sources dipoles orientations.
                # Gain matrix will result only from euclidean distances between sources and sensors.
                # Gain matrix will include subcortical sources as well
                if config.props[ConfigKey.SENSOR_GAIN_USE_DISTANCE] == "True":
                    print("...using only dipole distances to sensors...")
                    gain_computation[-1].add_sensor_distance_gain_computation_steps(dax, job_sensor_xyz,
                                                                                    job_mapping_details)
                # Here we compute directly for regions' centers and areas' centers, instead via vertices'sources
                if config.props[ConfigKey.SENSOR_GAIN_USE_REGIONS_DISTANCE] == "True":
                    print("...using only regions' centers' distances to sensors...")
                    gain_computation[-1]. \
                        add_sensor_regions_distance_gain_computation_steps(dax, job_sensor_xyz, job_mapping_details)

    out_dir = os.path.dirname(daxfile)
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    with open(daxfile, "w") as f:
        dax.writeXML(f)
