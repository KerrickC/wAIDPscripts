import random
import string
import os
import stat
import sys
import time
import subprocess


WORKING_DIR = "/home/kerrickcavanaugh/tomcat_dir/Data1/"
OUTPUT_PATH = os.path.join(WORKING_DIR, "AIDP_Data_Raw/")
# OUTPUT_PATH = "/opt/tomcat/webapps/"


# generates and returns a unique JobID that can be used to identify individual jobs (random alphanumberic string of length 16)
def generateJobID():
    OID = sys.argv[1]
    jobID = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    JOBID_PATH = os.path.join(OUTPUT_PATH, jobID)
    while os.path.exists(JOBID_PATH):
        jobID = ''.join(random.choices(
            string.ascii_letters + string.digits, k=16))
        JOBID_PATH = os.path.join(OUTPUT_PATH, jobID)

    # make output path if doesnt exist
    isExists = os.path.exists(OUTPUT_PATH)
    if not isExists:
        os.makedirs(OUTPUT_PATH)

    # create jobID path
    os.makedirs(JOBID_PATH)

    jobIdJson = "{\"jobId\":" + "\"" + jobID + "\"" + "}"
    reformat(OID, jobID, JOBID_PATH)

    # make file readable, writable, and executable by group.
    os.chmod(JOBID_PATH, stat.S_IRWXG | stat.S_IRWXU)

    # send json back to frontend
    print(jobIdJson)


# reformats DICOM to prepare for imaging and ML
def reformat(OID, jobID, JOBID_PATH):
    out = subprocess.Popen(['python3', './reformat_dicom.py', OID, jobID, JOBID_PATH],
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)

    stdout, stderr = out.communicate()

    # print(stdout)
    # print(stderr)

    # imagingPipeline(OID, jobID)

# imaging pipeline
# def imagingPipeline(OID, jobID):
#     subprocess.Popen(['conda', 'create', '-n', 'testenv', 'python=3.8'])
#     time.sleep(5)
#     subprocess.Popen(['conda', 'activate', 'myenv'])
#     time.sleep(5)
#     subprocess.Popen(['pip', 'install', 'pandas'])
#     time.sleep(10)
#     subprocess.Popen(['cd' '/home/kerrickcavanaugh/Data1/CODE'])
#     time.sleep(5)
#     subprocess.Popen(['./Master_code', WORKING_DIR])


generateJobID()


# still return jobId
# modify files to new dirs
# all should be dependent on work_dir
