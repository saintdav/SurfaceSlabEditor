#!/usr/bin/env python3
import sys

def reorder_and_format_line(line):
    """
    Given a line with three float values separated by whitespace,
    assume the current order is (z, x, y) and return a new string in
    (x, y, z) order. Each number is formatted to a fixed width of 15 characters
    with 10 digits after the decimal point.
    """
    parts = line.split()
    if len(parts) != 3:
        return line.rstrip()  # return unchanged if not exactly 3 numbers
    try:
        # Parse numbers assuming current order: (z, x, y)
        z = float(parts[0])
        x = float(parts[1])
        y = float(parts[2])
    except ValueError:
        return line.rstrip()
    # New order: (x, y, z) formatted with fixed width
    return " " + f"{x:15.10f}" + " " + f"{y:15.10f}" + " " + f"{z:15.10f}"

def is_atom_count_line(line):
    """
    Checks if every token in the line is an integer.
    """
    tokens = line.strip().split()
    return all(token.isdigit() for token in tokens)

def main(infile, outfile):
    with open(infile, "r") as f:
        lines = f.readlines()

    if len(lines) < 7:
        print("Error: input file appears too short to be a valid POSCAR file.")
        sys.exit(1)

    out_lines = []

    # Line 1: Header (we assume this contains the chemical symbols if available)
    header = lines[0].rstrip("\n")
    out_lines.append(header)
    
    # Line 2: Scaling factor (we leave this as is)
    scaling = lines[1].rstrip("\n")
    out_lines.append(scaling)
    
    # Lines 3-5: Lattice vectors (reorder and format)
    for i in range(2, 5):
        out_lines.append(reorder_and_format_line(lines[i]))

    # Next: determine if the chemical symbols line is provided.
    # Two cases:
    #   Case A (with symbols): line6 (index 5) is non-numeric -> chemical symbols,
    #         line7 (index 6) is atom counts, line8 (index 7) is coordinate system.
    #   Case B (without symbols): line6 (index 5) is numeric -> atom counts,
    #         line7 (index 6) is coordinate system.
    idx = 5  # next line index after lattice vectors
    if is_atom_count_line(lines[idx]):
        # Case B: No chemical symbols provided.
        # Insert chemical symbols using tokens from the header.
        chem_symbols = " ".join(header.split())
        out_lines.append(chem_symbols)  # This becomes the new line 6.
        # Now, treat the current line as the atom counts.
        atom_counts_line = lines[idx].strip()
        out_lines.append(atom_counts_line)
        # Next line is the coordinate system indicator.
        coord_system_line = lines[idx+1].rstrip("\n")
        out_lines.append(coord_system_line)
        coords_start = idx + 2
    else:
        # Case A: Chemical symbols are provided.
        chem_symbols_line = lines[idx].rstrip("\n")
        out_lines.append(chem_symbols_line)
        # Next line: atom counts.
        atom_counts_line = lines[idx+1].strip()
        out_lines.append(atom_counts_line)
        # Next line: coordinate system indicator.
        coord_system_line = lines[idx+2].rstrip("\n")
        out_lines.append(coord_system_line)
        coords_start = idx + 3

    # Determine the total number of atoms from the atom counts line.
    try:
        counts = [int(x) for x in atom_counts_line.split()]
        natoms = sum(counts)
    except Exception as e:
        print("Error parsing atom counts:", e)
        sys.exit(1)

    # Check if there are enough coordinate lines.
    coords_end = coords_start + natoms
    if len(lines) < coords_end:
        print("Error: not enough coordinate lines. Expected", natoms,
              "found", len(lines) - coords_start)
        sys.exit(1)
    
    # Process each atomic coordinate line (reorder and format)
    for i in range(coords_start, coords_end):
        out_lines.append(reorder_and_format_line(lines[i]))

    # Write the output file.
    with open(outfile, "w") as f:
        for line in out_lines:
            f.write(line + "\n")

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: python restore_z.py <input_POSCAR> <output_POSCAR>")
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2]
    main(infile, outfile)
