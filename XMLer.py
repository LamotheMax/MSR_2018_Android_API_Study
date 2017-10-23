import os
import random
import string
import subprocess


def write_blob(blob, file_path):

    if not ('.java' in file_path):
        return None

    random_element = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    fifo_name = "xml_temp"+random_element+".java"

    try:
        os.mkfifo(fifo_name)
        process = subprocess.Popen(['srcml', fifo_name], stdout=subprocess.PIPE)
        with open(fifo_name, 'wb') as f:
            f.write(blob.data_stream.read())
        output, error = process.communicate()
    finally:
        os.remove(fifo_name)

    return output


def convert_string_to_xml(java_string):

    fifo_name = "xml_temp.java"
    os.mkfifo(fifo_name)

    try:
        process = subprocess.Popen(['srcml', fifo_name], stdout=subprocess.PIPE)
        with open(fifo_name, 'w') as f:
            f.write(java_string)
        output = process.stdout.read()
    finally:
        os.remove(fifo_name)

    return output


def diff_xml_writer(commit_diff, commit_sha):

    commit_files = {}
    for x in commit_diff:

        xml_a = None
        xml_b = None

        if x.a_blob is not None:
            if x.a_blob.path.endswith('.java'):
                print("Looking at: " + str(commit_sha) + x.a_blob.path)
                xml_a = write_blob(x.a_blob, x.a_blob.path)

        if x.b_blob is not None:
            if '.java' in x.b_blob.path:
                xml_b = write_blob(x.b_blob, x.b_blob.path)

        commit_files[x] = [xml_a, xml_b]

    return commit_files


def get_commit_differences(commit):
    branch_commit = commit.parents[0]
    diff = commit.diff(branch_commit)
    commit_differences = diff_xml_writer(diff, commit.hexsha)

    return commit_differences


def get_file_from_commit(commit):

    print(commit)
