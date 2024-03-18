import subprocess
import re
import sys  # Import sys for writing to stdout

def check(line, error, output, penalty):
    p = re.compile(line, flags=0)
    m = p.search(output)
    if m is None:
        sys.stdout.write(error + '\n')
        return penalty
    else:
        return 0

def test_Compile():
    """Clean Compile"""

    # Running `make` directly, assuming `test1.txt` isn't actually needed for compilation.
    # Adjust this as per your actual requirements.
    process = subprocess.Popen(["make"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()  # This waits for the process to complete and captures stdout and stderr

    # Decode the output and error messages
    output = stdout.decode('utf-8')
    error_output = stderr.decode('utf-8')

    if not error_output:  # If error_output is empty, there were no compile errors
        sys.stdout.write("Code compiles without errors.\n")
    else:
        # If there are compile errors, print them to stdout
        sys.stdout.write("Compilation errors detected:\n" + error_output + '\n')

    # No need to terminate processes manually since communicate() waits for process to complete

if __name__ == "__main__":
    sys.stdout.write("here\n")
    test_Compile()
