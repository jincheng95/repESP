from repESP import cube_helpers

import numpy as np
from scipy.ndimage.morphology import distance_transform_edt as scipy_edt

path = '../data/'
mol_name = 'NMe3H_plus'


def grid_point_nearest_atom(field, atom):
    """Returns indices of point nearest the given atom

    The indices refer to the supplied GridField.
    """
    result = []
    for i, coord in enumerate(atom.coords):
        # i is the dimension index (x, y, z)
        result.append(round((coord - field.grid.origin_coords[i]) /
                      field.grid.dir_intervals[i]))
    return result


def atom_distance_transform(field, molecule):
    """Distance transform from atoms of a molecule

    This is an ad hoc function for this script. However, a more advanced
    version, which would perform the distance transform in multiples of van der
    Waals radii, will likely be included as a method of the GridField class in
    the future (TODO).

    Note that this distance transform approximates atoms by their nearest grid
    points.
    """
    # An ndarray of the shape of the field, in which the atoms are marked as
    # zeros, from which the distance transform is then calculated.
    atom_field = np.ones_like(field.values)
    for atom in molecule:
        atom_point = grid_point_nearest_atom(field, atom)
        atom_field[atom_point[0]][atom_point[1]][atom_point[2]] = 0
    dist = scipy_edt(atom_field, sampling=field.grid.dir_intervals)
    return cube_helpers.GridField(dist, field.grid, 'atom_dist')

esp_cube = cube_helpers.Cube(path + mol_name + '/' + mol_name + '_esp.cub')
cavity_field = atom_distance_transform(esp_cube.field, esp_cube.molecule)
cavity_fn = mol_name + "_cavity.cub"
cavity_field.write_cube(cavity_fn, esp_cube.molecule)

print("Cavity cube written to '{}'".format(cavity_fn))