import os
import glob

def load_params(csv_path):
    params = {}
    with open(csv_path, 'r') as f:
        lines = f.readlines()
    header = lines[0].strip().split(',')
    # Assuming structure: SN_name,RA,DEC,redshift,dm15
    # We need redshift by SN_name
    for line in lines[1:]:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            sn_name = parts[0]
            try:
                z = float(parts[3])
                params[sn_name] = z
            except ValueError:
                pass
    return params

def process_file(filepath, target_z):
    print(f"Processing {filepath}...")
    with open(filepath, 'r') as f:
        lines = f.readlines()
        
    header = []
    data_lines = []
    current_z = 0.0
    is_smoothed = False
    z_line_index = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('#'):
            header.append(line)
            if 'SMOOTHED' in line:
                is_smoothed = True
            if 'Z ' in line and '=' in line:
                z_line_index = i
                try:
                    # Format: # Z       =             0.142900 / wavelengths divided by (1 + z)
                    part_after_eq = line.split('=')[1]
                    if '/' in part_after_eq:
                        z_str = part_after_eq.split('/')[0]
                    else:
                        z_str = part_after_eq
                    current_z = float(z_str.strip())
                except ValueError:
                    pass
        else:
            if line.strip():
                data_lines.append(line)
                
    if not is_smoothed:
        print("Skipping: Not SMOOTHED")
        return

    print(f"  Current Z: {current_z}, Target Z: {target_z}")
    
    if abs(current_z - target_z) < 1e-5:
        print("  Z matches target. No change needed.")
        return

    # Perform correction
    # W_new = W_current * (1 + current_z) / (1 + target_z)
    # W_current is W_rest_old
    # W_obs = W_current * (1 + current_z)
    # W_new_rest = W_obs / (1 + target_z)
    
    new_data_lines = []
    for line in data_lines:
        parts = line.split()
        if len(parts) > 0:
            try:
                w_old = float(parts[0])
                w_obs = w_old * (1 + current_z)
                w_new = w_obs / (1 + target_z)
                # preserve formatting roughly
                # Assuming column 0 is wavelength
                new_line = f" {w_new:.5f}  " + "  ".join(parts[1:]) + "\n"
                new_data_lines.append(new_line)
            except ValueError:
                new_data_lines.append(line)
        else:
            new_data_lines.append(line)

    # Update header Z
    if z_line_index != -1:
        # Preserve spacing/comment
        # Old: # Z       =             0.142900 / wavelengths divided by (1 + z)
        # We want to replace the number
        orig_line = lines[z_line_index]
        pre_eq, post_eq = orig_line.split('=', 1)
        comment_part = ""
        if '/' in post_eq:
            val_part, comment_part = post_eq.split('/', 1)
            comment_part = " /" + comment_part
        else:
            val_part = post_eq
        
        # Format new Z with similar padding if possible, or just standard
        new_val_str = f"{target_z:.6f}"
        # construct new line
        # Padding is tricky, let's do fixed spacing
        new_z_line = f"# Z       =             {new_val_str}{comment_part}"
        # If original had newline, ensure this does too
        if orig_line.endswith('\n') and not new_z_line.endswith('\n'):
            new_z_line += '\n'
        
        # We need to update the 'header' list, but we read it from 'lines'
        # better to reconstruct lines to write
        pass

    # Write output
    # We will overwrite the file
    with open(filepath, 'w') as f:
        # Write header
        for i, line in enumerate(header):
            if i == z_line_index:
                f.write(new_z_line)
            else:
                f.write(line)
        # Write data
        for line in new_data_lines:
            f.write(line)
            
    print(f"  Updated {filepath}")

def main():
    params = load_params('/Users/pxm588@student.bham.ac.uk/PhD/SLSE_database/spectra/params.csv')
    # We only have logic for '2011ke' in params provided, but let's be generic if possible
    # The directory is 'spectra/2011ke', so the SN name is likely '2011ke'
    
    target_dir = 'spectra/2011ke'
    sn_name = '2011ke' # Derived from directory name? Or just use the params key
    
    if sn_name not in params:
        print(f"No params for {sn_name}")
        return
        
    target_z = params[sn_name]
    print(f"Target Redshift for {sn_name}: {target_z}")
    
    # Find all .dat files
    files = glob.glob(os.path.join(target_dir, '*.dat'))
    
    for fpath in files:
        process_file(fpath, target_z)

if __name__ == "__main__":
    main()
