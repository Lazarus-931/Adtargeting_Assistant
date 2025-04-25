#!/usr/bin/env python
# run_all.py
import sys
import subprocess
import argparse
import os
import time

def run_script(script, csv_path, vector_db_path, additional_args=None):
    """Run a script with the given arguments and return the result"""
    if not os.path.exists(script):
        return 1, f"Script not found: {script}"
    
    cmd = [sys.executable, script, "--csv-path", csv_path, "--vector-db-path", vector_db_path]
    
    # Add any additional arguments
    if additional_args:
        cmd.extend(additional_args)
    
    print(f"Running: {' '.join(cmd)}")
    
    # Run the command
    start_time = time.time()
    result = subprocess.run(
        cmd,
        capture_output=True, 
        text=True
    )
    end_time = time.time()
    
    # Return the result
    return result.returncode, f"Command completed in {end_time - start_time:.2f} seconds\n{result.stdout + result.stderr}"

def main():
    """Main entry point for running the full pipeline"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the entire AdTargeting Assistant pipeline")
    parser.add_argument("--csv-path", required=True, help="Path to the CSV data file")
    parser.add_argument("--vector-db-path", required=True, help="Path to the vector database directory")
    parser.add_argument("--force-rebuild", action="store_true", help="Force rebuild the vector database")
    parser.add_argument("--skip-setup", action="store_true", help="Skip the setup step")
    parser.add_argument("--interactive", action="store_true", help="Run main.py in interactive mode")
    
    args = parser.parse_args()
    
    # Check if paths exist
    if not os.path.exists(args.csv_path):
        print(f"Error: CSV file not found at {args.csv_path}")
        sys.exit(1)
    
    # Create vector_db_path directory if it doesn't exist
    os.makedirs(args.vector_db_path, exist_ok=True)
    
    # Run setup.py if not skipped
    if not args.skip_setup:
        setup_args = []
        if args.force_rebuild:
            setup_args.append("--force-rebuild")
        
        print("\n=== Running Setup ===")
        setup_code, setup_output = run_script("setup.py", args.csv_path, args.vector_db_path, setup_args)
        print("SETUP OUTPUT:")
        print(setup_output)
        
        if setup_code != 0:
            print(f"Error: setup.py exited with code {setup_code}")
            sys.exit(setup_code)
    else:
        print("\n=== Skipping Setup ===")
    
    # Run main.py
    main_args = []
    if args.interactive:
        main_args.append("--interactive")
    
    print("\n=== Running Main ===")
    main_code, main_output = run_script("main.py", args.csv_path, args.vector_db_path, main_args)
    print("MAIN OUTPUT:")
    print(main_output)
    
    if main_code != 0:
        print(f"Error: main.py exited with code {main_code}")
    
    return main_code

if __name__ == "__main__":
    sys.exit(main())