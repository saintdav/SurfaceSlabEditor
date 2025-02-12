#!/usr/bin/env python3
import sys
import numpy as np

def parse_floats_from_line(line):
    """Parse a list of floats from a whitespace‐separated line."""
    return [float(x) for x in line.split()]

def format_coord(coord):
    """Return a formatted string for a 3-element coordinate array.
       Each number is printed in a 15-character field with 10 digits after the decimal."""
    return " " + f"{coord[0]:15.10f}" + " " + f"{coord[1]:15.10f}" + " " + f"{coord[2]:15.10f}"

def is_atom_count_line(line):
    """
    Check if every token in the line is an integer.
    """
    tokens = line.strip().split()
    return all(token.isdigit() for token in tokens)

def main(infile, outfile, atom_indices_str):
    # Parse the list of atom indices (assumed 1-indexed, comma separated)
    try:
        atom_indices = [int(x) - 1 for x in atom_indices_str.split(",")]
    except Exception as e:
        print("Error parsing atom indices:", e)
        sys.exit(1)

    with open(infile, "r") as f:
        lines = f.readlines()

    if len(lines) < 7:
        print("Error: input file appears too short to be a valid POSCAR file.")
        sys.exit(1)

    # --- Header section ---
    # Line 1: Header (could contain chemical symbols)
    header = lines[0].rstrip("\n")
    # Line 2: Scaling factor (left unchanged)
    scaling = lines[1].rstrip("\n")

    # Lines 3-5: Lattice vectors.
    # We assume the standard POSCAR structure: lattice vectors on lines 3,4,5.
    # We need the third lattice vector ("c") for the translation.
    lattice_lines = [lines[i].rstrip("\n") for i in range(2, 5)]
    try:
        a_vec = np.array(parse_floats_from_line(lattice_lines[0]))
        b_vec = np.array(parse_floats_from_line(lattice_lines[1]))
        c_vec = np.array(parse_floats_from_line(lattice_lines[2]))
    except Exception as e:
        print("Error parsing lattice vectors:", e)
        sys.exit(1)

    # --- Determine if chemical symbols are provided ---
    # After the lattice vectors, line 6 (index 5) can be either a list of chemical symbols
    # or the atom counts. If all tokens on that line are numeric, assume chemical symbols are missing.
    idx = 5
    if is_atom_count_line(lines[idx]):
        # Chemical symbols are not provided.
        # Use the header tokens as the chemical symbols.
        chem_symbols = " ".join(header.split())
        atom_counts_line = lines[idx].strip()
        coord_sys_line = lines[idx+1].rstrip("\n")
        coords_start = idx + 2
        header_lines = [header, scaling] + lattice_lines + [chem_symbols, atom_counts_line, coord_sys_line]
    else:
        # Chemical symbols are provided on line 6.
        chem_symbols = lines[idx].rstrip("\n")
        atom_counts_line = lines[idx+1].strip()
        coord_sys_line = lines[idx+2].rstrip("\n")
        coords_start = idx + 3
        header_lines = [header, scaling] + lattice_lines + [chem_symbols, atom_counts_line, coord_sys_line]

    # --- Determine the total number of atoms ---
    try:
        counts = [int(x) for x in atom_counts_line.split()]
        natoms = sum(counts)
    except Exception as e:
        print("Error parsing atom counts:", e)
        sys.exit(1)
    
    # Check that there are enough coordinate lines
    if len(lines) < coords_start + natoms:
        print("Error: not enough coordinate lines. Expected", natoms, "found", len(lines) - coords_start)
        sys.exit(1)
    
    # --- Read and process atomic coordinates ---
    # We assume the coordinates are given in Cartesian format.
    new_coords = []
    # Create a unit vector in the c direction
    c_norm = np.linalg.norm(c_vec)
    if c_norm == 0:
        print("Error: zero-length c lattice vector.")
        sys.exit(1)
    c_unit = c_vec / c_norm
    threshold = c_norm / 2.0

    # Process each coordinate line.
    for i in range(natoms):
        line = lines[coords_start + i]
        try:
            coord_vals = np.array(parse_floats_from_line(line))
        except Exception as e:
            print(f"Error parsing coordinate on line {coords_start+i+1}:", e)
            sys.exit(1)
        # If the atom index is in the list provided, translate it.
        if i in atom_indices:
            # Compute the projection of the coordinate onto the c direction.
            proj = np.dot(coord_vals, c_unit)
            # If projection is less than half of |c|, add c_vec, else subtract c_vec.
            if proj < threshold:
                new_coord = coord_vals + c_vec
            else:
                new_coord = coord_vals - c_vec
        else:
            new_coord = coord_vals
        new_coords.append(new_coord)
    
    # --- Write output file ---
    with open(outfile, "w") as f:
        # Write header section (all lines before coordinates)
        for line in header_lines:
            f.write(line + "\n")
        # Write coordinates, re-formatted.
        for coord in new_coords:
            f.write(format_coord(coord) + "\n")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python translate_c.py <input_POSCAR> <output_POSCAR> <atom_indices>")
        print("  <atom_indices> should be a comma-separated list (e.g., 1,3,5) of 1-indexed atom numbers to translate.")
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2]
    atom_indices_str = sys.argv[3]
    main(infile, outfile, atom_indices_str)
