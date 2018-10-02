from Pegasus.DAX3 import File, Job, Link
from tvb.recon.dax.configuration import ConfigKey
from tvb.recon.dax.mappings import SensorGainCompJobNames, SensorGainCompFiles, AsegFiles


class SensorGainComputation(object):
    def __init__(self, subject, sensors_type, atlas_suffix):
        self.subject = subject
        self.sensors_type = sensors_type
        self.atlas_suffix = atlas_suffix
        if len(self.atlas_suffix) == 0:
            self.atlas_name = "default"
        else:
            self.atlas_name = self.atlas_suffix[1:]

    def add_sensor_dipole_gain_computation_steps(self, dax, job_sensor_xyz, job_mapping_details):
        sensor_positions = File(SensorGainCompFiles.SENSORS_POSITIONS.value % self.sensors_type)
        cort_surf = File(AsegFiles.SURF_CORT_ZIP.value)
        subcort_surf = File(AsegFiles.SURF_SUBCORT_ZIP.value)
        cort_rm = File(AsegFiles.RM_CORT_TXT.value % self.atlas_suffix)
        subcort_rm = File(AsegFiles.RM_SUBCORT_TXT.value % self.atlas_suffix)

        gain_mat = File(SensorGainCompFiles.SENSOR_GAIN_DIPOLE_MAT.value % (self.sensors_type, self.atlas_suffix))

        job = Job(SensorGainCompJobNames.COMPUTE_SENSOR_GAIN_DIPOLE.value % self.sensors_type,
                  node_label="Compute dipole %s gain matrix for atlas %s" % (self.sensors_type, self.atlas_suffix))
        job.addArguments(sensor_positions, cort_surf, subcort_surf, cort_rm, subcort_rm, gain_mat,
                         ConfigKey.SENSOR_GAIN_NORMALIZATION_PERCENTILE, self.subject)
        job.uses(sensor_positions, link=Link.INPUT)
        job.uses(cort_surf, link=Link.INPUT)
        job.uses(subcort_surf, link=Link.INPUT)
        job.uses(cort_rm, link=Link.INPUT)
        job.uses(subcort_rm, link=Link.INPUT)
        job.uses(gain_mat, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job)

        if job_sensor_xyz is not None:
            dax.depends(job, job_sensor_xyz)
        dax.depends(job, job_mapping_details)

    def add_sensor_inv_square_gain_computation_steps(self, dax, job_sensor_xyz, job_mapping_details):
        sensor_positions = File(SensorGainCompFiles.SENSORS_POSITIONS.value % self.sensors_type)
        cort_surf = File(AsegFiles.SURF_CORT_ZIP.value)
        subcort_surf = File(AsegFiles.SURF_SUBCORT_ZIP.value)
        cort_rm = File(AsegFiles.RM_CORT_TXT.value % self.atlas_suffix)
        subcort_rm = File(AsegFiles.RM_SUBCORT_TXT.value % self.atlas_suffix)

        gain_mat = File(SensorGainCompFiles.SENSOR_GAIN_INV_SQUARE_MAT.value % (self.sensors_type, self.atlas_suffix))

        job = Job(SensorGainCompJobNames.COMPUTE_SENSOR_GAIN_INV_SQUARE.value % self.sensors_type,
                  node_label="Compute inverse square %s gain matrix for atlas %s" %
                             (self.sensors_type, self.atlas_suffix))
        job.addArguments(sensor_positions, cort_surf, subcort_surf, cort_rm, subcort_rm, gain_mat,
                         ConfigKey.SENSOR_GAIN_NORMALIZATION_PERCENTILE, self.subject)
        job.uses(sensor_positions, link=Link.INPUT)
        job.uses(cort_surf, link=Link.INPUT)
        job.uses(subcort_surf, link=Link.INPUT)
        job.uses(cort_rm, link=Link.INPUT)
        job.uses(subcort_rm, link=Link.INPUT)
        job.uses(gain_mat, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job)

        if job_sensor_xyz is not None:
            dax.depends(job, job_sensor_xyz)
        dax.depends(job, job_mapping_details)


    def add_sensor_regions_inv_square_gain_computation_steps(self, dax, job_sensor_xyz, job_mapping_details):
        sensor_positions = File(SensorGainCompFiles.SENSORS_POSITIONS.value % self.sensors_type)
        centers_txt = File(AsegFiles.CENTERS_TXT.value % self.atlas_suffix)
        areas_txt = File(AsegFiles.AREAS_TXT.value % self.atlas_suffix)

        gain_mat = File(SensorGainCompFiles.SENSOR_GAIN_INV_SQUARE_MAT.value % (self.sensors_type, self.atlas_suffix))

        job = Job(SensorGainCompJobNames.COMPUTE_SENSOR_GAIN_REGIONS_INV_SQUARE.value % self.sensors_type,
                  node_label = "Compute regions' wise inverse square %s gain matrix for atlas %s" %
                               (self.sensors_type, self.atlas_suffix))
        job.addArguments(sensor_positions, centers_txt, areas_txt, gain_mat,
                         ConfigKey.SENSOR_GAIN_NORMALIZATION_PERCENTILE, self.subject)
        job.uses(sensor_positions, link=Link.INPUT)
        job.uses(centers_txt, link=Link.INPUT)
        job.uses(areas_txt, link=Link.INPUT)
        job.uses(gain_mat, link=Link.OUTPUT, transfer=True, register=True)
        dax.addJob(job)

        if job_sensor_xyz is not None:
            dax.depends(job, job_sensor_xyz)
        dax.depends(job, job_mapping_details)

