import sys

# TODO: in the current form, the Tracts are not aligned with the surfaces exported for TVB
# we miss a centering operation

if len(sys.argv) < 3:
    print("Loads NiPy module to transform .tck file to .trk file")
    print("Dependencies: nipype, dipy, nibabel")
    print("Usage:", sys.argv[0], "<base_image> <input_file>")
    print("""base_image - file with resolution of template (T1.nii.gz)
             input_file - MRTrix track file (.tck)""")
    print("Output: TrackVis track vile (.trk)")
    sys.exit(0)

import nipype.interfaces.mrtrix as mrt

mr = mrt.MRTrix2TrackVis()
mr.inputs.image_file = sys.argv[1]
mr.inputs.in_file = sys.argv[2]
mr.inputs.out_filename = sys.argv[2].split('.')[-2] + '.trk'
mr.run()
mr.inputs.print_traits()
