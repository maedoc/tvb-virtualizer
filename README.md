<h1 align="center">
  <br>
  <a href="http://www.amitmerchant.com/electron-markdownify"><img src="https://cdn.evbuc.com/eventlogos/50084740/tvbtaglinecrop.jpg" alt="The Virtual Brain" width="300"></a>
  <br>
  Reconstruction pipeline
  <br>
</h1>
<h4 align="center">This pipeline is offering a solution to build full brain network models starting from standard structural MR scans.</h4>
<p align="center">
  <a href="https://pegasus.isi.edu/downloads/">
    <img src="https://img.shields.io/badge/Pegasus%20WMS-4.9.3-%2349A13D"
         alt="Gitter">
  </a>
  <a href="https://groups.google.com/forum/#!forum/tvb-users ">
	  <img src="https://img.shields.io/badge/Chat-TVB%20forum-%236B3E90">
</a>
  <a href="https://req.thevirtualbrain.org/">
      <img src="https://img.shields.io/badge/Install-Jira-%23624426">
  </a>
  <a href="https://www.thevirtualbrain.org/tvb/zwei/brainsimulator-software">
    <img src="https://img.shields.io/badge/Download-TVB%20v1.5.8-%23902B29">
  </a>
</p>

<p align="center">
  <a href="#Folder-structure">Folder structure</a> •
  <a href="#Data-structure">Data structure</a> •
  <a href="#How-to-launch">How to launch</a> •
  <a href="#How-to-rerun">How to rerun</a> •
  <a href="#Environment">Environment</a> 
</p>
<p>
<hr>

It is used to preprocess the MR scans in order to get actual files that are compatible with TVB. The result can be later uploaded in TVB or used independently for modeling.

The mandatory inputs are DWI and T1 scans. Optionally, CT scans can be given as input, if sensors preprocessing is needed.

We are using the <a href="https://pegasus.isi.edu/">Pegasus WMS</a> in order to connect and automatize the pipeline steps. Pegasus is distributed under the Apache v2.0 license, while our own code is GPL v3.
</p>

<p align="center">
  <img height="600" src="https://ars.els-cdn.com/content/image/1-s2.0-S1053811915002505-gr1.jpg">
	
</p>
<p align="center">
	Illustration of pipeline input and output based on imaging data of one subject.<br>
	Image taken from <a href="#Bibliography"> article [2],Bibliography</a>.
</p>


## Folder structure

- **data**  
	Here is where we keep some example data files. Some of them are intermediate files generated during the pipeline run. There is also a minimal set of files that defines a TVB head. These files are currently used only for tests.  
- **docs**  
    This folder holds some visual hints of the dependencies between the pipeline steps.  
    For example, there is an overview diagram representing the pipeline stages.   
	These stages are defined by scripts that can be found inside the bin folder. 
	These scripts are no longer maintained, nor used directly in the pipeline run. 
	They belong under "docs" because they are now used only for documentation purposes, or for some extreme partial debugging.   
	On the other hand, there is also an example graph diagram which is displaying more detailed steps. 
	This kind of diagram is automatically generated at each pipeline run.  
- **pegasus**  
	All the configuration files necessary for the software run are kept here.  
	At the first level, there are the entry points which are explained below in the ***Entry Point*** section.  
	Inside the *config* folder, there is a folder called *scripts*. This holds bash files with calls to pipeline commands that need some specific environment configuration. These bash files should not be changed, neither their names, because they are mapped inside the workflow.  
	The *config* folder also contains the configuration files which are patient-specific. These are the only files that will change for each run and/or patient. The possible configurations are explained in **How to launch** section.
- **provision**  
	Inside this folder, you can find more details about the project dependencies.
- **tvb**  
	Actual python implementation is kept here.  
	Package *dax* is using the Pegasus API to define a pipeline workflow and generate the jobs graph.  
	Inside *algo* package, we have all the computations, services and algorithms used during the pipeline steps. Here we also have the *reconutils.py* which defines an API for calls made from the *config/scripts* bash files.  
	The model classes can be found inside *model* package.  
	Package *io* provides read/write functionalities from/to a variety of file formats.  
	We also have a set of tests for this module and they are kept inside the *tests* package.

## Data structure
**For an automated pipeline run, the patient data is divided into three categories:**
- ***raw data***  
    Usually, scans, that are used as input files for the pipeline (e.g. T1, DWI, CT).
- ***configurations*** <br>
    This is a folder with configuration files. Each configuration file is described in the **How to launch** section.  
    This folder is patient specific. All the files should be filled in by the user or generated automatically with the **run_sequential.py** described also in **How to launch** section.
- ***output data***  
    These are the files generated by the pipeline. The output can be structured using the configuration file **rc_out.txt**.

**For a multi-patient sequential run, the data needs to be structured in a similar manner for each patient. Also, it is important to name the patient folders in a predefined manner. As an example, a simple folder structure can be:**

```
	TVB_patients 
		│
		├── TVB1 
		|     |
		|     └── raw  
		|	    |
		|	    └── mri 
		|		  |
		|		  ├── t1_input.nii.gz
		|		  |
		|		  ├── dwi_raw.nii
		|		  |
		|		  ├── dwi.bvec
		|		  |
		|		  └── dwi.bval		
		└── TVB2 
		      |
		      └── raw  
			    |
			    └── mri 
				  |
				  ├── t1_input.nii.gz
				  |
				  ├── dwi_raw.nii
				  |
				  ├── dwi.bvec
				  |
				  └── dwi.bval	
```

## How to launch

### Docker image
We provide a docker image which gathers all the dependencies necessary for tvb-recon code to run.
The docker image can be found on docker hub at: **thevirtualbrain/tvb-recon**. Take it using the most recent tag, with:

```bash
# import docker image
$ docker pull thevirtualbrain/tvb-recon
```

Also, it would be good to have tvb-recon code locally, in case some changes are necessary. Take it with:

```bash
# Clone this repository
$ git clone https://github.com/the-virtual-brain/tvb-recon.git

# Go into the repository
$ cd tvb-recon

```

In order to use tvb-recon within the proposed docker image, you will need some details about its configurations and steps to follow for specifying your input data and start a workflow.
We recommend new users to start with the ***default configurations*** and ***adjust their data structure*** as required. After a first workflow run has finished successfully, the configurations and data structure can be chosen by the user.

First of all, we process mostly T1 and DWI data. There is an option to process also CT scans. But, we would advise you to start only with T1 and DWI.
In order to access the T1 and DWI input, tvb-recon pipeline expects, by default, a certain folder structure, and file naming. These can be changed later as you wish, but keep the default configurations for a first test.
This means you should ***adjust your input*** data folder to the following structure (also rename your files as below):

```
	TVB_patients 
		│
		├── TVB1 
		|     |
		|     └── raw  
		|	    |
		|	    └── mri 
		|		  |
		|		  ├── t1_input.nii.gz
		|		  |
		|		  ├── dwi_raw.nii
		|		  |
		|		  ├── dwi.bvec
		|		  |
		|		  └── dwi.bval		
		└── TVB2 
		      |
		      └── raw  
			    |
			    └── mri 
				  |
				  ├── t1_input.nii.gz
				  |
				  ├── dwi_raw.nii
				  |
				  ├── dwi.bvec
				  |
				  └── dwi.bval	
```

(TVB1, TVB2, etc, being the ID of the patients. If your DWI data is not made of: dwi.nii + dwi.bvec + dwi.bval, let us know and we will tell you how to specify it differently.)

Once you have this folder structure for your data, you can run the tvb-recon docker image with the command below.
Please make sure Docker has enough RAM memory assigned, we recommend at least 6 GB.

``` bash
# To run the tvb-recon docker image
$ docker run -it -v your_path_to_TVB_patients/TVB_patients/:/home/submitter/data -v your_path_to_tvb_recon/tvb-recon/:/opt/tvb-recon thevirtualbrain/tvb-recon /bin/bash
``` 
(here you need to replace *your_path_to_TVB_patients* and *your_path_to_tvb_recon* with the paths of your local machine)

Now, you will be able to use bash commands inside the tvb-recon container. And here, you need to do the next steps:

``` bash 
# Run the following command and provide the sudo password: 123456
$ sudo condor_master

# Move to pegasus folder 
$ cd pegasus

# Run the pipeline by the following command. The "1" argument is the patient number you want to process. By specifying "1", you choose to process TVB1. For running multiple patients (TVB1, TVB2 and TVB3), the argument should be: "1 2 3".
$ python run_sequentially.py "1"
```
If everything is correct, some messages will be displayed. Look for the following flow of messages:   
```
*...  
Starting to process the subject: TVB1  
...  
2018.06.28 11:11:40.285 UTC:    Your workflow has been started and is running in the base directory:  
2018.06.28 11:11:40.293 UTC:     /home/submitter/pegasus/submit/submitter/pegasus/TVB-PIPELINE/run0001   
...  

The job that has been started has the id: 0001  
Starting to monitor the submit folder: /home/submitter/pegasus/submit/submitter/pegasus/TVB-PIPELINE/run0001 ...  
Checked at Thu, 28 Jun 2018 11:11:42 and monitord.done file was not generated yet!*

```

If the messages flow is not similar, let us know what is the error.

Once, you have started the workflow, you should see a new folder, named ***configs***, on your local machine at path:<br> ***your_path_to_TVB_patients/TVB_patients/TVB1***
Here you will have all the default configurations we need for a patient (these can be changed).

Later on, after some important steps have finished, you will also have an ***output*** folder inside:<br> ***your_path_to_TVB_patients/TVB_patients/TVB1***. 
Here is where all the output data will be stored, and of more interest will be the folders:
- **output/figs** (figures generated during different pipeline steps to check the quality of the data)
- **output/tvb** (files that are compatible with TVB and can be uploaded and used there)

We use the Pegasus workflow engine in order to automatize the pipeline steps. This tool will let you check the status of the workflow anytime.
In order to check the status of your current workflow:

``` bash 
# You can open a new terminal on the tvb-recon docker container with:
$ docker exec -i -t container_id /bin/bash

# Then run this command
$ pegasus-status -l /home/submitter/pegasus/submit/submitter/pegasus/TVB-PIPELINE/run0001
```
( Here container_id needs to be replaced with the id of your docker container. You can find it in the terminal itself. The string container_id in "submitter@'container_id':" is your container_id)

After you manage to test a first default workflow, we can speak about adjusting the configurations instead of adjusting the data structure.

### Entry point
There are 2 available entry points for the pipeline. They are both under the *pegasus* folder. In order to use these entry points, there are, in both cases, some configurations to be defined first. These configurations are kept as a folder specific to each patient and are explained in the next section.

The pipeline can be started using one of the following entry points:
- **main_pegasus.sh**  
    This is the most straight-forward one. It starts one pipeline run for a single patient based on a set of predefined configurations. Command to launch the pipeline with this script:   
     ``` bash
     $ sh main_pegasus.sh path_to_configurations_folder path_to_dax_folder
     ```
     
    The arguments:
    - *path_to_configurations_folder* represents the path to the patient configuration files (e.g. data_folder/configurations) 
    - *path_to_dax_folder* represents the folder where the dax will be generated (e.g. data_folder/configurations/dax)
    
    This entry point has the disadvantage that the user should manually fill in all the configuration files under the *configurations* folder.

- **run_sequential.py**   
    This is a little more complex. It is used to start pipeline runs for a list of patients with similar configurations. As the name is suggesting, the runs will be started sequentially.  
    Command to launch the pipeline with this script:
    ``` bash
    $  python run_sequentially.py
    ```
   
    This script does not need arguments, but it needs the user to edit the necessary configurations inside file *run_sequential.py*. The configurations to edit are described below:
    - **PATH_TO_INPUT_SUBJ_FOLDERS**:<br> path to the folder where you keep your patient raw data (e.g. data_folder/raw_data)
    - **PATH_TO_SUBJ_CONFIG_FOLDERS**:<br> path to the folder where you keep your patient configurations (e.g. data_folder/configurations)
    - **PATH_TO_OUTPUT_SUBJ_FOLDER**:<br> path to the folder where you want your outputs to be saved (e.g. data_folder/outputs)
    - **PREFIX_SUBJECT_FOLDER**:<br> prefix of the patient folder name (e.g. patient in patient1, patient2, patient3)
    - **SUBJECTS_TO_BE_PROCESSED**:<br> suffix of the patient folder name (e.g. [1, 2, 3] in patient1, patient2, patient3)
    - **ATLASES**:<br> a list with all the atlases to be used (e.g. [default])
    - **PATH_TO_DEFAULT_PEGASUS_CONFIGURATION**:<br> path to the folder where you keep the default configuration files. (e.g. tvb-recon/pegasus/config)  
    This entry point can be also used to start a single patient run in order for the user to avoid the need to manually fill in all the configuration files. This can be achieved by specifying a single suffix in the **SUBJECTS_TO_BE_PROCESSED** list (e.g. SUBJECTS_TO_BE_PROCESSED=[1]).
    
### Configurations
All the configuration files are under *pegasus/config* at the top level. There are configurations specific to the patient, to the machine where the workflow is running or to the actual run. Some details about each file, are given below:
- **environment_config.sh**  
    These are the machine-specific configurations. The configurations are mostly paths of the software and other variables that are needed for the pipeline environment setup.
- **patient_flow.properties**  
    These are the patient-specific configurations. 
- **pegasus.properties**  
    This is a pegasus specific configuration file. It just defined the paths to sites.xml, rc.txt, tc.txt, and rc_out.txt.
- **rc.txt**  
    Inside this file, the inputs should be defined in a key-value format, where value is the path to the input file.  
    During the pipeline run, the rc.txt will be filled in with all the generated files and their paths. This mapping is important to keep especially in case of a partial rerun.
- **rc_out.txt**  
    Using this file, the output can be structured in a similar way as the input.
- **sites.xml**  
    This should not change since the configurable variables will be taken from the environment.
- **tc.xml**  
    This should not be changed since it contains the commands mapping.


## How to rerun
There are cases when the user is not satisfied with the obtained results. 
Maybe the volume overlapping is not correct. Maybe more tracts or longer tracts are needed. Maybe the user has T2 scans and wants to add them.   
These are all cases that imply the need to rerun the pipeline. But in the best-case scenario, the user does not need to rerun the whole pipeline again but rerun only the wanted steps.  
With Pegasus, the pipeline can be rerun partially. This means that it will rerun only the steps for which the corresponding outputs are missing from the **rc.txt**

### Rerun with different parameters
This is possible with pegasus, but it is not automatized. It needs user input and attention.
In order to rerun with different parameters, the user has to:
- modify the parameters inside the configuration files
- search the steps that need to rerun inside the **main_bnm.dax** and identify their output files
- remove the files (output files above) that need to be regenerated from **rc.txt**
- start a pipeline run using one of the entry points
  
As stated before, the **rc.txt** contains a mapping between the generated file names and their paths. In order for Pegasus to rerun a group of steps, the user has to remove their output files from **rc.txt**. 
During the pipeline rerun, the **rc.txt** will be once again filled in, by re-running the steps (and all their dependencies) which are meant to produce the missing resources from **rc.txt**.  
Inside the **main_bnm.dax** file, there is a XML representation of the workflow graph. Here is where the user can check all the pipeline steps and their input/output files.


### Recover over shutdown
Pegasus already has support for this. When the machine is started after an unexpected shutdown, it restarts the flow.
If the recovery run is not started, there is also the option to force it by calling **pegasus-start** inside its *submit* folder.


## Environment
The pipeline steps are dependent on the following external tools:
- **Freesurfer**  
	Freesurfer is used to process the T1 images and generate the anatomy of a patient brain.
- **Mrtrix**  
	Mrtrix is used to preprocess the DWI images and also to generate the tracts.
- **FSL**  
	FSL is used to register images from different spaces to a common one.
- **MNE**  
	MNE is used to generate BEM surfaces.
- **OpenMEEG**  
	OpenMEEG can be used for sensor computations.

The automatized workflow is based on:
- **HTCondor**  
	Pegasus uses HTCondor as a job scheduler.  
	Download the tarballs (current stable release) from here: http://research.cs.wisc.edu/htcondor/downloads/
	Install for MacOS: 
	```
	- tar xzf condor-8.6.9-x86_64_MacOSX-stripped.tar.gz
	- cd condor-8.6.9-x86_64_MacOSX10-stripped
	- ./condor_install --type=execute, manager, submit
	```
	 
    Prepare environment:
    - optionally, it may need the next lines inside condor_config: 
        - use ROLE : Personal
	    - NETWORK_INTERFACE = $(CONDOR_HOST)
	    - COLLECTOR_NAME = Personal Condor at $(CONDOR_HOST)
	- export CONDOR_CONFIG=../condor-8.6.9-x86_64_MacOSX10-stripped/etc/condor_config
    - source ../condor-8.6.9-x86_64_MacOSX10-stripped/condor.sh
    - start it with: condor_master
    - check it works by running: condor_status

- **Pegasus**  
	This is the workflow engine we have used for automatizing the pipeline steps.  
	Download tarball for MacOSX from here: https://pegasus.isi.edu/downloads/?filename=4.8.1%2Fpegasus-binary-4.8.1-x86_64_macos_10.tar.gz
	
	Prepare the environment:
	```
	- tar xzf ../pegasus-binary-4.8.1-x86_64_macos_10.tar.gz
	- export PATH=../pegasus-4.8.1/bin/:$PATH
	- check it works by running: pegasus-status
	```

### Bibliography

[1] Proix T, Spiegler A, Schirner M, Rothmeier S, Ritter P, Jirsa VK, How do parcellation size and short-range connectivity affect dynamics in large-scale brain network models?, Neuroimage (2016).

[2] Schirner M, Rothmeier S, Jirsa VK, McIntosh AR, Ritter P, An automated pipeline for constructing personalized virtual brains from multimodal neuroimaging data, Neuroimage, (2015) Aug 15 117:343-357. [Available here](https://www.sciencedirect.com/science/article/pii/S1053811915002505)

[3] Andre Santos Ribeiro, Luis Miguel Lacerda, Hugo Alexandre Ferreira, Multimodal Imaging Brain Connectivity Analysis (MIBCA) toolbox, 2015 Jul 14. [Available here](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4511822/)


[![Build Status](https://travis-ci.org/the-virtual-brain/tvb-recon.svg)](https://travis-ci.org/the-virtual-brain/tvb-recon) [![Coverage Status](https://coveralls.io/repos/github/the-virtual-brain/tvb-recon/badge.svg)](https://coveralls.io/github/the-virtual-brain/tvb-recon)
