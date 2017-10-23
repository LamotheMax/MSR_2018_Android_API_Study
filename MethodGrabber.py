import git
import re
from TargetMethod import TargetMethod
from MethodTargeter import get_method


def create_file_path(repo, tag, end_tag):

    diff = diff_with_tags(repo, tag, end_tag)
    file_item = get_file(diff)

    return file_item


def diff_with_tags(repo, start_tag, end_tag):
    start_commit = repo.tags[start_tag].commit
    end_commit = repo.tags[end_tag].commit
    diff = end_commit.diff(start_commit, "api/current.txt", create_patch=False)

    file_diff = get_file_diffs(diff, 'api/current.txt')

    return file_diff


def get_file(file_diff):
    a_file = file_diff.a_blob.data_stream.read().decode('utf8').splitlines(keepends=True)
    return a_file


def get_file_diffs(diff_object, file_name):
    for item in diff_object:

        if item.a_blob.path == file_name:
            return item

    return None


def get_project_repository(repo_dir):

    repository = git.Repo(repo_dir)
    assert not repository.bare
    return repository


def insert_into_methods(changed_methods, package_line, class_line, method_line):

    if package_line in changed_methods['Methods']:
        if class_line in changed_methods['Methods'][package_line]:
            changed_methods['Methods'][package_line][class_line].append(method_line)
        else:
            changed_methods['Methods'][package_line][class_line] = [method_line]
    else:
        changed_methods['Methods'][package_line] = {class_line: [method_line]}

    return changed_methods


def ignored_package(package_line):

    if "junit" in package_line:
        return True
    elif "apache" in package_line:
        return True
    else:
        return False


def get_all_current_methods(repo_dir, start_tag, end_tag):

    repo = get_project_repository(repo_dir)
    methods_file = create_file_path(repo, start_tag, end_tag)

    methods = extract_methods_from_file(methods_file)

    methods = get_real_file_paths(methods, repo, start_tag)
    methods = clean_methods(methods)

    return methods


def extract_methods_from_file(methods_file):
    # methods = {'Methods': {}}
    methods = []

    package_line = None
    class_line = None
    for line in methods_file:
        clean_line = line.strip()
        if 'package ' in clean_line and '{' in clean_line:
            package_line = get_package(clean_line)

            if 'java' in package_line:
                package_line = None

        if package_line is not None:
            if 'class' in clean_line and '{' in clean_line:
                class_line = get_class(clean_line)

            elif 'method public' in clean_line:
                if not ignored_package(package_line):

                    method_object = get_method_object(clean_line, package_line, class_line)
                    # methods = insert_into_methods(methods, package_line, class_line, method_object)
                    methods.append(method_object)

    return methods


def clean_methods(methods):

    for item in methods:
        path = item.repo_path
        if path is not None:
            if '/icu' in path:
                methods.remove(item)
        else:
            methods.remove(item)
    return methods


def get_real_file_paths(methods, repo, tag1):

    index = git.IndexFile.from_tree(repo, tag1)

    done = 0
    for item in methods:
        get_repo_path(item, index)
        print("Found {} methods".format(done))
        done += 1

    return methods


def get_repo_path(method_object, index):
    pseudo_path = method_object.pseudo_path()
    real_path = get_real_file_path(pseudo_path, index)
    method_object.repo_path = real_path


def get_real_file_path(pseudo_path, removed_index):

    path = None
    for entry, value in removed_index.entries.items():
        potential_path = value.path
        if pseudo_path in potential_path:
            if potential_path.endswith(".java"):
                return potential_path

    return path


def get_method_object(line, package_line, class_line):
    method = get_method(line)

    target = TargetMethod(method['method_name'])
    target.parameters = method['parameters']
    target.return_type = method['return_type']
    target.class_name = class_line
    target.package_name = package_line
    target.kind = 'Current'

    return target


def get_package(line):
    regex = 'package (.*) {'
    result = re.search(regex, line)

    if result is not None:
        result = result.group(1)

    return result


def get_class(line):
    regex = 'class (.*) {'
    result = re.search(regex, line)

    if result is not None:
        result = result.group(1)
        if 'extends' in result:
            result = result.split(' extends')[0]
        elif 'implements' in result:
            result = result.split(' implements')[0]

    return result
