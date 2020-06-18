import shutil
import sys
import tarfile

from pathlib import Path


# Function to create the test result directory 
def create_results_dir(results_dir):
    try:
        Path(results_dir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        sys.exit("Unable to create the results directory: " + str(e))


# Function to save all the results after test plugin exits 
def save_results(tar_filename, results_dir, done_file):
    print('Saving Results ...')
    try:
        make_tarfile(tar_filename, results_dir)
    except Exception as e:
        sys.exit("Error while creating results tarfile: " + str(e))
    try:
        with open(done_file, "w+") as f:
            f.write(results_dir + '/' + tar_filename)
    except Exception as e:
        sys.exit("Error while writing the donefile: " + str(e)) 


# Function to create a tarball of all the results. This is a required standard for sonobuoy 
def make_tarfile(output_filename, source_dir):
    with tarfile.open(output_filename, "w:gz") as tar:
        tar.add(source_dir, arcname="")
    shutil.move(output_filename, source_dir)


# Function to append logs from the test run into results file
def append_result_output(message, result_file_path):
    try:
        with open(result_file_path, "a") as result_file:
            result_file.write(message)
    except Exception as e:
        sys.exit("Error while appending message '{}' to results file: ".format(message) + str(e)) 
