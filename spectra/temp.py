import os
import sys

def redshift_to_observer_frame(filepath, entered_z):
    print(f"Processing {filepath} to observer frame with z={entered_z}...")
    
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    header = []
    data_lines = []
    original_z_in_header = None
    z_line_index = -1

    # Parse header to find original Z and other metadata
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            header.append(line)
            if 'Z ' in line and '=' in line:
                z_line_index = i # Store index to modify later
                try:
                    part_after_eq = line.split('=')[1]
                    if '/' in part_after_eq:
                        z_str = part_after_eq.split('/')[0]
                    else:
                        z_str = part_after_eq
                    original_z_in_header = float(z_str.strip())
                except ValueError:
                    pass
        else:
            if line.strip():
                data_lines.append(line)

    if original_z_in_header is not None:
        print(f"  Found original Z in header: {original_z_in_header}. "
              f"Assuming wavelengths are currently in REST FRAME relative to this Z.")
    else:
        print("  No redshift found in header. Assuming wavelengths are currently in REST FRAME.")

    # Determine input wavelength type based on header comment
    is_rest_frame_by_comment = False
    for line in header:
        if 'wavelengths divided by (1 + z)' in line:
            is_rest_frame_by_comment = True
            break
            
    if is_rest_frame_by_comment:
        print("  Header indicates wavelengths are in REST FRAME.")
    else:
        print("  Header does not explicitly state wavelength frame. "
              "Proceeding assuming REST FRAME as input for conversion to OBS FRAME.")

    # Calculate new observer-frame wavelengths
    new_data_lines = []
    for line in data_lines:
        parts = line.split()
        if len(parts) > 0:
            try:
                # Assuming input wavelengths are rest-frame (lambda_rest)
                # lambda_obs = lambda_rest * (1 + entered_z)
                wl_rest_original = float(parts[0])
                wl_obs_new = wl_rest_original * (1 + entered_z)
                
                # Format the first column, keep others
                new_line = f" {wl_obs_new:.4f}  " + "  ".join(parts[1:]) + "\n"
                new_data_lines.append(new_line)
            except ValueError:
                new_data_lines.append(line)
        else:
            new_data_lines.append(line)

    # Prepare output filename
    base, ext = os.path.splitext(filepath)
    output_filepath = f"{base}_obs{ext}"

    # Prepare new header lines
    new_header = []
    z_line_modified = False
    for i, line in enumerate(header):
        # Update or add information about the new observer frame conversion
        if i == z_line_index: # Modify the Z line if it existed
            orig_line = lines[z_line_index] # Get original full line to keep formatting
            pre_eq, post_eq = orig_line.split('=', 1)
            comment_part = ""
            if '/' in post_eq:
                val_part, comment_part = post_eq.split('/', 1)
                comment_part = " /" + comment_part.strip()
            
            # Construct new Z line, indicating it's now observed frame using the entered Z
            new_z_line_val = f"{entered_z:.6f}"
            new_z_line_comment = " / wavelengths in OBSERVER FRAME (from rest frame x (1+z))"
            new_header.append(f"{pre_eq}= {new_z_line_val}{new_z_line_comment}\n")
            z_line_modified = True
        else:
            new_header.append(line)

    # Add a new comment if Z line wasn't found or for clarity
    if not z_line_modified:
        new_header.append(f"# Converted to OBSERVER FRAME using z = {entered_z:.6f}\n")


    # Write to output file
    with open(output_filepath, 'w') as out:
        for line in new_header:
            out.write(line)
        for line in new_data_lines:
            out.write(line)
            
    print(f"  Converted spectrum written to: {output_filepath}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python temp.py <spectrum_filepath>")
        sys.exit(1)

    input_filepath = sys.argv[1]

    if not os.path.exists(input_filepath):
        print(f"Error: File not found at {input_filepath}")
        sys.exit(1)

    while True:
        try:
            z_input = input("Enter the redshift (e.g., 0.143) to convert to observer frame: ")
            entered_z = float(z_input)
            break
        except ValueError:
            print("Invalid redshift. Please enter a numerical value.")

    redshift_to_observer_frame(input_filepath, entered_z)

if __name__ == "__main__":
    main()