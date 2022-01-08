import sys
from pathlib import Path
import json
import os
import stat
import struct
import subprocess
import random
import string
import shlex

# waidpDB path
waidpDB_PATH = "/home/angelos/waidpDB/"
# master folder with OIDs
DB_DATA = os.path.join(waidpDB_PATH, "master")
# output directory (must be created if doesnt exist)
OUTPUT_PATH = ""
# jobID path
JOBID_PATH = ''

# DICOM data dictionary
file_data = {
    'Job_ID': "",
    'successful': True,
    'error': "N/A",
    'parent_file': "",
    'files': 0,
    'subfolders': 0,
    'total_size (bytes)': 0,
    'dicom_type': 'raw',
}


def getFilesFromFolder(OID, path, at_parent):
    try:
        # source path
        root_path = os.path.join(DB_DATA, OID)
        # access info directory
        info_path = root_path + "/info"
        # read the info file
        info_content = Path(info_path).read_text()
        # format info file content to json
        json_format = "{\"CONTENT\": [" + info_content + "]}"
        json_content = json.loads(json_format)["CONTENT"]

        # for each line in json_content
        for line in json_content:
            # if parent folder, create dir, and continue with contents
            if at_parent and ".CLASS" in line and line[".CLASS"] == "List":
                # get name of parent file
                for line in json_content:
                    if ".NAME" in line:
                        name = line[".NAME"]
                        file_data['parent_file'] = name
                        # create parent folder
                        path = os.path.join(path, name)
                        # print(str(path))
                        os.mkdir(path)
                        # make file readable, writable, and executable by group.
                        os.chmod(path, stat.S_IRWXG | stat.S_IRWXU)
            else:
                if '.LIST' in line:
                    # print("sub folder/file")
                    data = line['.LIST']
                    # print(data)
                    oid = ''
                    for val in data:
                        oid = val
                        break
                    meta = data[oid]

                    # check whether subfolder or file
                    if('.CLASS' in meta):
                        # if subfolder
                        file_data['subfolders'] += 1
                        # get name
                        folder_name = meta['.NAME']
                        # print("Subfolder name: " + folder_name)
                        os.mkdir(os.path.join(path, folder_name))
                        os.chmod(os.path.join(path, folder_name),
                                 stat.S_IRWXG | stat.S_IRWXU)

                        new_path = os.path.join(path, folder_name)
                        getFilesFromFolder(oid, new_path, False)

                    else:
                        # if file
                        # get name
                        file_name = meta['.NAME']
                        # get the directory where raw data is stored
                        raw_path = os.path.join(DB_DATA, oid, "raw")

                        file_data['files'] += 1

                        # needed to account for out of order file parts
                        file_order = []
                        for file in os.listdir(raw_path):
                            # single digit decimal (like 1.4)
                            try:
                                file_val = int(file[-2:])
                                file_order.append(file_val)
                            except:
                                # two digit decimal (like 1.25)
                                file_val = int(file[-1:])
                                file_order.append(file_val)

                        file_order.sort()

                        for file in file_order:

                            sub_path = "part1." + str(file)

                            # create main woo file (all decompressed files will append to this file)
                            # open in append binary mode ('ab')
                            woo_file = open(os.path.join(
                                path, file_name), "ab")

                            # print(path + file_name + file + "                 ")

                            os.chmod(os.path.join(
                                path, file_name),
                                stat.S_IRWXG | stat.S_IRWXU)

                            file_size = os.path.getsize(
                                os.path.join(raw_path, path))
                            file_data['total_size (bytes)'] += file_size

                            # create a .zlib file for zlib-flate
                            fn = file_name + sub_path + ".zlib"
                            new_dcm = open(os.path.join(path, fn), "wb")

                            # go through each byte, convert to int, and bit-shift by 1
                            with open(os.path.join(raw_path, sub_path), "rb") as f:
                                byte = f.read(1)
                                while byte != b"":
                                    byte_val = struct.unpack('B', byte)[0]

                                    byte_val = byte_val - 1

                                    if byte_val < 0:
                                        byte_val = byte_val + 256

                                    by = struct.pack("B", byte_val)

                                    new_dcm.write(by)

                                    byte = f.read(1)
                            f.close()

                            new_dcm.close()

                            # zlib decompress
                            new_fn = file_name + sub_path
                            # zlib_path -> same path as new_dcm
                            zlib_path = os.path.join(path, fn)
                            out_file = os.path.join(path, new_fn)

                            proc = subprocess.Popen(['./zlib.sh', str(zlib_path), str(out_file)],
                                                    stdout=subprocess.PIPE)
                            proc.wait()
                            # print(proc.stdout.read())

                            # delete temp zlib file (uncomment)
                            if(os.path.exists(zlib_path)):
                                os.remove(zlib_path)

                            # append all files with matching file_name to main file (concatentation)
                            # if a file matches a main woo, then append to that file

                            if(os.path.exists(out_file)):
                                new_path = open(
                                    out_file, "rb")

                                # print('here')

                                # if a file exists with the current 'file_name' (image has multiple parts)
                                if(os.path.exists(os.path.join(path, file_name))):
                                    # print("appending...")
                                    # read all content from the zlib file
                                    cnt = new_path.read()
                                    new_path.close()
                                    # append to woo_file
                                    woo_file.write(cnt)
                                    # delete zlib-flate produced file
                                    os.remove(out_file)
                                    woo_file.close()

                    print('          ')

        return

    except Exception as e:
        # print(str(e))
        file_data['successful'] = False
        file_data['error'] = str(e)

# creates an info file with information about the DICOM


def generateInfoFile(jp):
    with open(os.path.join(jp, "log"), "w") as f:
        f.write(json.dumps(file_data))
        f.close()


def reformat_dicom():
    OID = sys.argv[1]
    JOB_ID = sys.argv[2]
    JOBID_PATH = sys.argv[3]

    file_data["Job_ID"] = JOB_ID

    # begin process
    getFilesFromFolder(OID, JOBID_PATH, True)

    # generate an info file
    generateInfoFile(JOBID_PATH)

    # return file_data['parent_file']


reformat_dicom()
