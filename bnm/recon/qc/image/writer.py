# -*- coding: utf-8 -*-

import numpy
import matplotlib.pyplot as pyplot
from mpl_toolkits.mplot3d import Axes3D
import meshcut

class ImageWriter(object):
    # TODO possible: Validate target path
    # maybe create missing folder
    # get nextName

    def write_matrix(self, matrix, result_name):
        pyplot.matshow(matrix, cmap=pyplot.gray())
        pyplot.imsave(result_name, matrix)

    def write_2_matrices(self, matrix_background, matrix_overlap, result_name):
        pyplot.imshow(matrix_background, cmap="gray")
        pyplot.imshow(matrix_overlap, cmap="hot", alpha=0.3)
        pyplot.axis('off')
        pyplot.savefig(result_name, bbox_inches='tight', pad_inches=0.0)

    def write_3_matrices(self, matrix_background, matrix_overlap_1, matrix_overlap_2, result_name):
        pyplot.savefig(result_name)

    def write_surf(self, surf_matrix, result_name):
        x = surf_matrix[:,0]
        y = surf_matrix[:,1]
        z = surf_matrix[:,2]
        fig=pyplot.figure()
        ax=fig.gca(projection='3d')
        ax.plot_surface(x,y,z,rstride=3, cstride=3, cmap="hot")
        #Axes3D.plot3D(surf_matrix[:,0], surf_matrix[:,1])
        # pyplot.setp(f, color='r', linewidth=2)
        #pyplot.imshow(surf_matrix, alpha=0.3)
        #pyplot.axis('off')
        pyplot.savefig(result_name)


    def write_matrix_and_surface(self, matrix_background, surface_x_array, surface_y_array, result_name):
        pyplot.clf()
        pyplot.imshow(matrix_background, cmap="gray")
        for s in range(0, len(surface_x_array)):
             pyplot.plot(surface_x_array[s][:], surface_y_array[s][:], 'y')
        pyplot.axis('off')
        pyplot.savefig(result_name, bbox_inches='tight', pad_inches=0.0)


    def write_matrix_and_surfaces(self, matrix_background, surf1_x_array, surf1_y_array, clear_flag, surf, result_name):
        if clear_flag == 'true':
            pyplot.clf()
        if surf == 'pial':
            contour_color = 'r'
        else:
            contour_color = 'y'
        pyplot.imshow(matrix_background, cmap="gray")
        for s in range(0, len(surf1_x_array)):
            pyplot.plot(surf1_x_array[s][:], surf1_y_array[s][:], contour_color)
        pyplot.axis('off')
        pyplot.savefig(result_name, bbox_inches='tight', pad_inches=0.0)