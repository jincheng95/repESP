#!/usr/bin/env python3

from repESP.resp import equivalence, _get_input_files, _read_respin
from repESP.resp import _check_ivary, run_resp
from repESP import charges
from repESP import resp_helpers

import argparse
import charges_parser
import resp_parser

import os
import shutil
import copy

help_description = """Average charges according to atom equivalence information
    from 'respin' files. Note that ESP-based charges should be equivalenced
    instead! This can be achieved by passing the fitting points to the
    --esp_file option. Equivalencing is then performed by running an
    unconstrained RESP calculation."""

parser = argparse.ArgumentParser(
    parents=[charges_parser.parser, resp_parser.parser],
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description=help_description)

parser.add_argument("--esp_file",
                    help=resp_parser.esp_file_help,
                    metavar="ESP_FILE")

parser.add_argument("--thresh",
                    help="Inform about charges which change upon averaging "
                    "by more than THRESH",
                    default=0.05, type=float, metavar="THRESH")

parser.add_argument("--save_resp_to",
                    help="save the files of the RESP calculation to the given "
                    "directory",
                    metavar="SAVE_RESP_TO")

parser.add_argument("-o", "--output",
                    help="output file name",
                    default='averaged_charges.txt')

args = parser.parse_args()

# Check settings related to equivalencing
if args.save_resp_to is None:
    save_resp_to = "averaging_temp_dir-dont_remove"
else:
    save_resp_to = args.save_resp_to
    if args.esp_file is None:
        raise ValueError("The option '--save_resp_to' should only be specified"
                         " when the '--esp_file' option is set.")

if os.path.exists(args.output):
    raise FileExistsError("Output file exists: " + args.output)
if args.save_resp_to is not None and os.path.exists(args.save_resp_to):
    raise FileExistsError("Output directory exists: " + args.save_resp_to)

input_type = charges_parser.input_type(args.input_charge_type)

respin1, respin2 = _get_input_files(args.respin_location, respin1_fn="",
                                    respin2_fn="")
# Note: the molecule is taken from one of the respin files...
molecule = _read_respin(respin1)[-1]
# ... but this will throw an error if the molecule in log is not the same one
charges._get_charges(args.input_charge_type, args.input_charge_file,
                     input_type, molecule)

if args.esp_file is not None:
    try:
        averaged_molecule = run_resp(
            args.respin_location, save_resp_to, resp_type='unrest',
            check_ivary=True, esp_fn=args.esp_file)
    except Exception as e:
        shutil.rmtree(save_resp_to)
        raise e
    if args.save_resp_to is None:
        shutil.rmtree(save_resp_to)
else:
    averaged_charges, ivary_list = equivalence(
        molecule, args.input_charge_type, args.respin_location, respin1_fn="",
        respin2_fn="")
    # Check equivalence information from respin:
    _check_ivary(True, molecule, ivary_list)
    # The new molecule and name 'resp' is for consistency with the
    # equivalencing code above
    averaged_molecule = copy.deepcopy(molecule)
    charges._update_molecule_with_charges(averaged_molecule, averaged_charges,
                                          "resp")

message = charges.compare_charges(args.input_charge_type, "resp", molecule,
                                  averaged_molecule, thresh=args.thresh)
thresh_message = " vary by more than the threshold of " + str(args.thresh)

if message:
    print("\nThe following charges" + thresh_message)
    print(message)
else:
    print("\nNo charges" + thresh_message)

charges.dump_charges_to_qout(averaged_molecule, "resp", args.output)
