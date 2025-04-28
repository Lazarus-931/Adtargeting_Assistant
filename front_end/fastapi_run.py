import logging
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, constr
import subprocess
import sys
from typing import Optional
import os

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory where subprocesses are allowed to run
WORK_DIR = os.path.abspath("work")
os.makedirs(WORK_DIR, exist_ok=True)

class RunResponse(BaseModel):
    setup_success: bool
    main_success: bool
    setup_output: str
    main_output: str
    error: Optional[str] = None

def run_subprocess(cmd, timeout=60):
    """Utility to run a subprocess with timeout and error handling in a controlled directory."""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=WORK_DIR  # Restrict execution to the work directory
        )
        return proc.returncode == 0, proc.stdout + proc.stderr, None
    except subprocess.TimeoutExpired as e:
        logger.error(f"Timeout running command: {cmd}\n{e}")
        return False, '', f"Timeout running command: {cmd}"
    except Exception as e:
        logger.error(f"Error running command: {cmd}\n{e}")
        return False, '', str(e)

@app.post("/run", response_model=RunResponse)
def run_setup_and_main(
    csv_path: constr(strip_whitespace=True, min_length=1) = Query("data.csv"),
    vector_db_path: constr(strip_whitespace=True, min_length=1) = Query("data.pt")
):
    # Basic input validation: restrict to .csv and .pt files in allowed directories
    if not csv_path.endswith('.csv') or not vector_db_path.endswith('.pt'):
        raise HTTPException(status_code=400, detail="Invalid file extension.")

    # Run run_all.py (which handles both setup and main)
    run_all_cmd = [sys.executable, "run_all.py", "--csv-path", csv_path, "--vector-db-path", vector_db_path]
    success, output, error = run_subprocess(run_all_cmd)

    # Parse output for setup and main sections
    setup_output = ""
    main_output = ""
    if output:
        setup_marker = "SETUP OUTPUT:"
        main_marker = "MAIN OUTPUT:"
        setup_start = output.find(setup_marker)
        main_start = output.find(main_marker)
        if setup_start != -1 and main_start != -1:
            setup_output = output[setup_start + len(setup_marker):main_start].strip()
            main_output = output[main_start + len(main_marker):].strip()
        else:
            setup_output = output

    return RunResponse(
        setup_success=success,  # True if both succeeded
        main_success=success,
        setup_output=setup_output,
        main_output=main_output,
        error=error
    )