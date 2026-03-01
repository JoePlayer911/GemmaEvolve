import os
import glob
import re

def update_configs():
    config_files = glob.glob('examples/verilog_eval/Prob*/gemma_config.yaml')
    
    # We want num_islands=4 since parallel_evaluations=2 and we want them out of 4 GPUs? 
    # Actually wait - we have 4 GPUs, parallel_evaluations is 2. Let's make num_islands=4.
    new_islands = 4
    new_population = 40  # 4 * 10
    
    updated_count = 0
    error_count = 0
    
    for filename in config_files:
        try:
            with open(filename, 'r') as f:
                content = f.read()
                
            # Replace population_size using regex to preserve comments
            # Matches:   population_size: 10 # Some comment
            content = re.sub(r'(\s*population_size:\s*)\d+', fr'\g<1>{new_population}', content)
            
            # Replace num_islands
            content = re.sub(r'(\s*num_islands:\s*)\d+', fr'\g<1>{new_islands}', content)
            
            with open(filename, 'w') as f:
                f.write(content)
                
            updated_count += 1
        except Exception as e:
            print(f"Error updating {filename}: {e}")
            error_count += 1
            
    print(f"Successfully updated {updated_count} files.")
    if error_count > 0:
        print(f"Failed to update {error_count} files.")

if __name__ == '__main__':
    update_configs()
