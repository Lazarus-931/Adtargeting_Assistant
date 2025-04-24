import sys
import subprocess
import argparse

def run_script(script, csv_path, vector_db_path):
    result = subprocess.run(
        [sys.executable, script, "--csv-path", csv_path, "--vector-db-path", vector_db_path],
        capture_output=True, text=True
    )
    return result.returncode, result.stdout + result.stderr

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv-path", required=True)
    parser.add_argument("--vector-db-path", required=True)
    args = parser.parse_args()

    setup_code, setup_output = run_script("setup.py", args.csv_path, args.vector_db_path)
    print("SETUP OUTPUT:")
    print(setup_output)
    if setup_code != 0:
        sys.exit(setup_code)

    main_code, main_output = run_script("main.py", args.csv_path, args.vector_db_path)
    print("MAIN OUTPUT:")
    print(main_output)
    sys.exit(main_code)