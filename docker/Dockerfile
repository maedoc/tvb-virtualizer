FROM thevirtualbrain/tvb-recon-software:docker-6Jul

#TVB-RECON
RUN apt-get install -y python-pip
RUN cd /opt && git clone https://github.com/the-virtual-brain/tvb-recon.git
RUN conda install -y setuptools numpy scipy matplotlib pytest h5py scikit-learn Cython graphviz
RUN pip install trimesh anytree gdist configobj
RUN cd /opt/tvb-recon && python setup.py develop
RUN conda create -n tvb_recon_python3_env python=3.6 anaconda

WORKDIR /opt/tvb-recon
RUN [ "/bin/bash", "-c", "source /opt/conda/bin/activate tvb_recon_python3_env && python setup.py develop && pip install nibabel" ]

USER ${SUBMIT_USER}
COPY start_condor_and_run.sh /opt/
#CMD ["sh", "/opt/start_condor_and_run.sh"]
