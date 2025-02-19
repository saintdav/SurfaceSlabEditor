#!/usr/bin/env python3
import sys

def format_number(x):
    """Format a single float with 16 decimal places in a 23-character field."""
    return f"{x:23.16f}"

def format_vector(vector):
    """Format a 3-element vector using format_number for uniform alignment."""
    return " " + " ".join(format_number(x) for x in vector)

def is_atom_count_line(line):
    """Return True if every token in the line is numeric (an integer)."""
    tokens = line.strip().split()
    return tokens and all(token.isdigit() for token in tokens)

def parse_header(lines):
    """
    Parse the header of a POSCAR file and re-format lattice vectors using format_vector.
    Returns a tuple (header_block, coords_start, num_atoms, coord_sys_line)
      - header_block: list of header lines to be written to the output
      - coords_start: index of the first coordinate line
      - num_atoms: total number of atoms
      - coord_sys_line: coordinate system indicator (should start with d or D)
    """
    header_block = []
    # Preserve the first two lines (comment and scaling factor) as-is.
    header_block.append(lines[0].rstrip("\n"))
    header_block.append(lines[1].rstrip("\n"))
    
    # Re-format lattice vectors (lines 3-5, i.e. indices 2-4)
    for i in range(2, 5):
        try:
            lattice = [float(x) for x in lines[i].strip().split()]
        except Exception as e:
            print(f"Error parsing lattice vector on line {i+1}: {e}")
            sys.exit(1)
        header_block.append(format_vector(lattice))
    
    # Now check line 6 (index 5): either atom counts (if numeric) or chemical symbols.
    if is_atom_count_line(lines[5]):
        # No chemical symbols provided.
        atom_counts_line = lines[5].strip()
        header_block.append(atom_counts_line)
        coord_sys_line = lines[6].strip()
        header_block.append(coord_sys_line)
        coords_start = 7
    else:
        # Chemical symbols provided on line 6.
        chem_symbols_line = lines[5].rstrip("\n")
        header_block.append(chem_symbols_line)
        atom_counts_line = lines[6].strip()
        header_block.append(atom_counts_line)
        coord_sys_line = lines[7].strip()
        header_block.append(coord_sys_line)
        coords_start = 8

    try:
        counts = [int(x) for x in atom_counts_line.split()]
        num_atoms = sum(counts)
    except Exception as e:
        print("Error parsing atom counts:", e)
        sys.exit(1)
    
    return header_block, coords_start, num_atoms, coord_sys_line

def main():
    if len(sys.argv) != 5:
        print("Usage: python shift_c_direct.py <input_POSCAR> <output_POSCAR> <atom_index> <target_fraction>")
        sys.exit(1)
    
    infile = sys.argv[1]
    outfile = sys.argv[2]
    
    try:
        atom_index = int(sys.argv[3])  # 1-indexed atom number.
    except ValueError:
        print("Error: <atom_index> must be an integer.")
        sys.exit(1)
    
    try:
        target = float(sys.argv[4])
    except ValueError:
        print("Error: <target_fraction> must be a float number.")
        sys.exit(1)
    
    with open(infile, "r") as f:
        lines = f.readlines()
    
    header_block, coords_start, num_atoms, coord_sys_line = parse_header(lines)
    
    # Ensure that the coordinate system is direct.
    if not coord_sys_line or coord_sys_line[0].lower() != "d":
        print("Error: The coordinate system indicator does not start with 'd' (direct coordinates).")
        sys.exit(1)
    
    coords_lines = lines[coords_start: coords_start + num_atoms]
    new_coords_lines = []
    
    # Parse coordinates (first three tokens assumed as direct coordinates)
    coords = []
    for line in coords_lines:
        tokens = line.strip().split()
        try:
            d = [float(tok) for tok in tokens[:3]]
        except Exception as e:
            print("Error parsing coordinates in line:", line)
            sys.exit(1)
        # Save extra tokens if present (e.g., selective dynamics flags)
        extras = tokens[3:] if len(tokens) > 3 else []
        coords.append((d, extras))
    
    if atom_index < 1 or atom_index > len(coords):
        print("Error: Atom index out of range. There are only", len(coords), "atoms.")
        sys.exit(1)
    
    # Determine the current fractional c coordinate for the specified atom.
    current_c = coords[atom_index - 1][0][2]
    delta = target - current_c
    
    # Apply the shift: update the c coordinate for every atom.
    for (d, extras) in coords:
        new_c = (d[2] + delta) % 1.0
        new_d = [d[0], d[1], new_c]
        formatted_line = format_vector(new_d)
        if extras:
            formatted_line += " " + " ".join(extras)
        new_coords_lines.append(formatted_line)
    
    # Write out the new POSCAR file.
    with open(outfile, "w") as f:
        for line in header_block:
            f.write(line + "\n")
        for line in new_coords_lines:
            f.write(line + "\n")
    
    print(f"Shift applied: delta = {delta:23.16f}. New POSCAR written to {outfile}.")

if __name__ == '__main__':
    main()
