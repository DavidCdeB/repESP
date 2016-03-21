from repESP import resp, resp_helpers, rep_esp, charges, graphs
from repESP.field_comparison import _check_grids, difference, rms_and_rep

from numpy import mean, sqrt, square, linspace, meshgrid
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import os
import shutil

import numpy as np
import pickle

esp_charge_type = 'mk'
# esp_charge_type = 'chelpg'

# molecule_name = 'methane'
molecule_name = 'tma'
path = '../data/' + molecule_name + '/'
output_path = path + "esp_fit" + '_' + esp_charge_type + '/'
resp_output_path = output_path + 'resp_calcs/'

charge_type = 'nbo'
charge_log_fn = path + molecule_name + "_" + charge_type + ".log"
temp_output_path = output_path + 'ratio/'

common_fn = path + molecule_name + "_" + esp_charge_type
log_fn = common_fn + ".log"
input_esp = common_fn + ".esp"
esp_fn = molecule_name + "_" + esp_charge_type + ".esp"
output_esp = common_fn + ".esp"

print("To see a demonstration of all the capabilities of the script, change "
      "the hard-coded conditional values to True. You can also change the "
      "charges type between MK and CHelp(G).")
print("\nMolecule:    ", molecule_name.capitalize())
print("Charge type: ", esp_charge_type.upper(), '\n')

g = resp_helpers.G09_esp(input_esp)

# Write the .esp file in the correct format expected by the `resp` program
if False:
    g.field.write_to_file(output_esp, g.molecule)

# Division into Voronoi basins:
# parent_atom, dist = rep_esp.calc_non_grid_field(g.molecule, g.field.points,
#                                                 'dist')

title = molecule_name.capitalize() + " " + esp_charge_type.upper()
# Plot the grid in 3 and 2D:
if False:
    color_span = [min(g.field.values), max(g.field.values)]
    for dimension in (3, 2):
        graphs.plot_points(
            g.field, dimension, title=title, molecule=g.molecule,
            plane_eqn=graphs.plane_through_atoms(g.molecule, 1, 3, 17),
            dist_thresh=0.5, axes_limits=[(-5, 5)]*dimension,
            color_span=color_span)
        graphs.plot_points(
            g.field, dimension, title=title, molecule=g.molecule,
            plane_eqn=[1, 0, 0, 0], dist_thresh=0.5,
            axes_limits=[(-5, 5)]*dimension, color_span=color_span)

# Calculate RMS for various charges
import copy
from itertools import chain
molecule = copy.deepcopy(g.molecule)


class Result(object):

    def __init__(self, num, c_xlim, n_xlim):
        self.num = num
        self.c_xlim = c_xlim
        self.n_xlim = n_xlim
        self.c_inp, self.n_inp = self.get_meshgrid(c_xlim, n_xlim, num)
        self.rrms = []

    @staticmethod
    def get_meshgrid(c_xlim, n_xlim, num):
        c_charges = linspace(c_xlim[0], c_xlim[1], num=num)
        n_charges = linspace(n_xlim[0], n_xlim[1], num=num)
        return meshgrid(c_charges, n_charges)


# Calculation --- set to True if running the 'one charge variation' version.
# Also set to True when performing the calculations for the 'two charges'
# version. Then you must also switch on the other calculation section.
if True:
    os.mkdir(output_path)
    os.mkdir(resp_output_path)

    print("\nNOTE: Running unrestrained RESP to fit ESP with equivalence:")
    esp_equiv_molecule = resp.run_resp(
        path, resp_output_path + 'unrest', resp_type='unrest',
        esp_fn=esp_fn)

    charges.update_with_charges(esp_charge_type, log_fn, g.molecule)
    charge_rms, charge_rrms = rms_and_rep(g.field, g.molecule,
                                          esp_charge_type)[:2]
    resp_rms, resp_rrms = rms_and_rep(g.field, esp_equiv_molecule, 'resp')[:2]

    print("\nThe molecule with {0} charges:".format(esp_charge_type.upper()))
    print(" RMS: {0:.5f}".format(charge_rms))
    print("RRMS: {0:.5f}".format(charge_rrms))
    # The above value should be compared with that in the log file.
    for atom in g.molecule:
        atom.print_with_charge(esp_charge_type)

    print("\nThe molecule with equivalenced {0} charges (unrestrained RESP):"
          .format(esp_charge_type.upper()))
    print(" RMS: {0:.5f}".format(resp_rms))
    print("RRMS: {0:.5f}".format(resp_rrms))
    for atom in esp_equiv_molecule:
        atom.print_with_charge('resp')

# One charge (e.g. methane, water): 2D plot
if False:
    vary_atom_label = 1
    xlim = (-1, 0.5)
    num = 150
    charges = linspace(xlim[0], xlim[1], num=num)
    charge_dict = lambda c: {vary_atom_label: c}

    result = []
    for i, charge in enumerate(charges):
        if not i % 10:
            print("{0:.2f}%".format(100*i/num))
        inp_charges = resp.charges_from_dict(charge_dict(charge),
                                             len(molecule))
        updated_molecule = resp.run_resp(
            path, resp_output_path + "C{0:+.3f}".format(charge),
            resp_type='h_only', inp_charges=inp_charges, esp_fn=esp_fn)

        rrms_val = rms_and_rep(g.field, updated_molecule, 'resp')[1]
        result.append(rrms_val)

    min_charge = esp_equiv_molecule[0].charges['resp']

    plt.title(title)
    plt.xlabel("Charge on " + molecule[vary_atom_label-1].identity)
    plt.ylabel("RRMSE at fitting points")
    plt.plot(charges, result)
    plt.plot((-1.2, 1.2), (0, 0), 'r--')
    plt.plot((0, 0), (0, 1.2*max(result)), 'r--')
    plt.plot((min_charge, min_charge), (0, resp_rrms), 'g--')
    plt.plot((-1.2, min_charge), (resp_rrms, resp_rrms), 'g--')

    axes = plt.gca()
    axes.set_xlim(xlim)
    axes.set_ylim([0, max(result)])

    save_to = output_path + molecule_name + "_rrms_" + esp_charge_type
    plt.savefig(save_to + ".pdf", format='pdf')
    plt.show()
    plt.close()


def plot_common():
    plt.title(title)
    plt.xlabel("Charge on N")
    plt.ylabel("Charge on C")

# 2 charges (NMe3H_plus, NMe4_plus etc.): Calculation. Note that the previous
# calculation section must also be switched on.
if True:
    # Change input values here
    net_charge = 1
    charge_dict = lambda n, c: {17: n, 1: c, 5: c, 9: c, 13: c}
    c_xlim = (-1, 0.5)
    n_xlim = (-0.5, 1)
    num = 51
    new_result = Result(num, c_xlim, n_xlim)

    i = 0
    for n, c in zip(new_result.n_inp.flat, new_result.c_inp.flat):
        inp_charges = resp.charges_from_dict(charge_dict(n, c), len(molecule))
        updated_molecule = resp.run_resp(
            path, resp_output_path + "N{0:+.3f}C{1:+.3f}".format(n, c),
            resp_type='h_only', inp_charges=inp_charges, esp_fn=esp_fn)

        rrms_val = rms_and_rep(g.field, updated_molecule, 'resp')[1]
        new_result.rrms.append(rrms_val)
        for atom in updated_molecule:
            atom.print_with_charge('resp')
        i += 1
        print("{0:.2f} %".format(100*i/num**2))

    new_result.rrms = np.array(new_result.rrms)
    new_result.rrms.resize([num, num])
    new_result.resp_rms = resp_rms
    new_result.resp_rrms = resp_rrms

    with open(output_path + "result.p", "wb") as f:
        pickle.dump(new_result, f)

# 2 charges: Presentation
if True:
    with open(output_path + "result.p", "rb") as f:
        read_result = pickle.load(f)

    rel_rrms = [100*(elem-read_result.resp_rrms)/read_result.resp_rrms for
                elem in read_result.rrms]
    rel_rrms = np.array(rel_rrms)
    rel_rrms.resize([read_result.num, read_result.num])

    # Non-ESP charge and its minimized ratio
    charges.update_with_charges(charge_type, charge_log_fn, molecule)
    start_charges = [atom.charges[charge_type] for atom in molecule]
    os.mkdir(temp_output_path)
    # Scan roughly various ratios to find bracket for minimization
    heavy_args = (g.field, path, temp_output_path, esp_fn, True)
    heavy_result, indicator_charge, ratio_values = resp.eval_ratios(
        'heavy', (0, 2), start_charges, 10, 17, heavy_args)
    # Minimization
    heavy_args = (start_charges, g.field, path, temp_output_path,
                  esp_fn, False, True)
    heavy_min_ratio, heavy_min_ratio_rrms = resp.minimize_ratio(
        'heavy', ratio_values, heavy_result, heavy_args)
    shutil.rmtree(temp_output_path)

    # Presentation: 3D
    if False:
        fig = plt.figure()
        ax = fig.gca(projection='3d')
        surf = ax.plot_surface(read_result.n_inp, read_result.c_inp,
                               read_result.rrms, cmap=cm.plasma, rstride=1,
                               cstride=1)
        fig.colorbar(surf, label="RRMSE at fitting points")
        plot_common()
        plt.show()
        plt.close()

    # Presentation: 2D contour
    if True:
        levels = [1, 5, 10, 20, 30, 50, 100]
        CS = plt.contour(read_result.n_inp, read_result.c_inp, rel_rrms,
                         levels, rstride=1, ctride=1, inline=1, colors='k')
        plt.clabel(CS, fmt="%1.0f", inline=1, fontsize=10, colors='b')
        axes = plt.gca()

        # Change axes here:
        axes.set_xlim([-0.5, 1])
        axes.set_ylim([-1, 0])
        plt.axes().set_aspect('equal')

        # Add non-esp point. The indices are for N17 and C1 in TMA+
        new_point = (molecule[16].charges[charge_type],
                     molecule[0].charges[charge_type])
        plt.scatter(*new_point)
        # Non-esp ratio charge point
        plt.scatter(heavy_min_ratio*start_charges[16],
                    heavy_min_ratio*start_charges[0])
        # Add ratio line
        y_coord = axes.get_xlim()[0]*new_point[1]/new_point[0]
        plt.plot((axes.get_xlim()[0], 0), (y_coord, 0))

        plot_common()
        save_to = output_path + molecule_name + "_" + esp_charge_type
        plt.savefig(save_to + ".pdf", format='pdf')
        plt.close()
