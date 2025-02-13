#!/usr/bin/env python3
import sys

def format_vector(vector):
    """
    Format a 3-element list of floats into a fixed-width string.
    Each number is printed in a 15-character field with 10 decimal places.
    """
    return " " + " ".join(f"{x:15.10f}" for x in vector)

def is_atom_count_line(line):
    """
    Return True if every token in the line is an integer.
    """
    tokens = line.strip().split()
    return tokens and all(token.isdigit() for token in tokens)

def main(infile, outfile, delta_z):
    with open(infile, "r") as f:
        lines = f.readlines()
    
    if len(lines) < 7:
        print("Error: input file appears too short to be a valid POSCAR file.")
        sys.exit(1)
    
    # --- Header and Scaling Factor ---
    header = lines[0].rstrip("\n")
    scaling = lines[1].rstrip("\n")
    
    # --- Lattice Vectors ---
    # Lines 3-5 (indices 2,3,4) are the lattice vectors.
    lattice_lines = [lines[i].strip() for i in range(2, 5)]
    
    # Parse the lattice vectors and reformat them.
    try:
        a_vector = [float(x) for x in lattice_lines[0].split()]
        b_vector = [float(x) for x in lattice_lines[1].split()]
        c_vector = [float(x) for x in lattice_lines[2].split()]
    except Exception as e:
        print("Error parsing lattice vectors:", e)
        sys.exit(1)
    
    if len(c_vector) != 3:
        print("Error: The c lattice vector does not have 3 components.")
        sys.exit(1)
    
    # Modify the c lattice vector: set x and y to zero and add delta_z to z.
    new_c_vector = [0.0, 0.0, c_vector[2] + delta_z]
    # Format the new c lattice vector.
    lattice_lines[2] = format_vector(new_c_vector)
    # Also reformat the a and b lattice vectors for tidy alignment.
    lattice_lines[0] = format_vector(a_vector)
    lattice_lines[1] = format_vector(b_vector)
    
    # --- Chemical Symbols, Atom Counts, and Coordinate System ---
    idx = 5  # Next line after lattice vectors.
    if is_atom_count_line(lines[idx]):
        # Chemical symbols are missing; create one from the header tokens.
        chem_symbols_line = " ".join(header.split())
        atom_counts_line = lines[idx].strip()
        coord_sys_line = lines[idx+1].strip()
        coords_start = idx + 2
        header_block = [header, scaling] + lattice_lines + [chem_symbols_line, atom_counts_line, coord_sys_line]
    else:
        # Chemical symbols are provided.
        chem_symbols_line = lines[idx].strip()
        atom_counts_line = lines[idx+1].strip()
        coord_sys_line = lines[idx+2].strip()
        coords_start = idx + 3
        header_block = [header, scaling] + lattice_lines + [chem_symbols_line, atom_counts_line, coord_sys_line]
    
    # --- Verify the Coordinate System ---
    if not coord_sys_line or coord_sys_line[0].lower() not in ('c', 'k'):
        print("Error: The coordinate system indicator does not start with 'c' or 'k'.")
        sys.exit(1)
    
    # --- Read and Reformat Coordinates ---
    # Reformat each coordinate line so that numbers are aligned by their decimal point.
    coords = []
    for line in lines[coords_start:]:
        tokens = line.strip().split()
        if len(tokens) < 3:
            # Skip or preserve lines that don't have at least three numbers.
            coords.append(line.rstrip("\n"))
            continue
        try:
            # Parse the first three columns as floats.
            coord = [float(tokens[i]) for i in range(3)]
        except Exception as e:
            coords.append(line.rstrip("\n"))
            continue
        coords.append(format_vector(coord))
    
    # --- Write the Modified POSCAR File ---
    with open(outfile, "w") as f:
        for line in header_block:
            f.write(line + "\n")
        for line in coords:
            f.write(line + "\n")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python modify_c_lattice.py <input_POSCAR> <output_POSCAR> <delta_z>")
        print("  <delta_z> is the value to add to the z component of the c lattice vector.")
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2]
    try:
        delta_z = float(sys.argv[3])
    except ValueError:
        print("Error: <delta_z> must be a valid number.")
        sys.exit(1)
    main(infile, outfile, delta_z)
