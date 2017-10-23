from Commentator import get_target_method
from XMLer import write_blob
from lxml import etree
import git
import re


def get_project_repository(repo_dir):

    repository = git.Repo(repo_dir)
    assert not repository.bare
    return repository


def get_file_diffs(diff_object, file_name):
    for item in diff_object:
        if item.a_blob is not None:
            if item.a_blob.path == file_name:
                return item

    return None


def get_implicated_methods(method_element):
    print("TODO get all the methods that are called from within a method xml element")
    # xpath('/src:call')


def get_incidental_changes(commit):
    print("TODO get all changes done to things where a method is affected")


def method_changed(method_object, old_file, new_file):
    old_method = None
    new_method = None

    if old_file is not None:
        xml_file = etree.fromstring(old_file)
        old_method = get_target_method(xml_file, method_object)

    if new_file is not None:
        new_xml_file = etree.fromstring(new_file)
        new_method = get_target_method(new_xml_file, method_object)

    if old_method is not None and new_method is not None:
        original_method = etree.tostring(old_method)
        updated_method = etree.tostring(new_method)

        if original_method == updated_method:
            return False
        else:
            return True
    elif old_method is None and new_method is None:
        return False
    else:
        return True


def separate_diff_into_subsections(diff):
    sections = []
    current_section = []
    for line in diff:

        # this takes care of only having a single diff section to observe at a time
        if "@@" in line:
            if len(current_section) > 0:
                sections.append(current_section)
                current_section = []
        current_section.append(line)

    if len(current_section) > 0:
        sections.append(current_section)

    return sections


def method_in_line(method_object, line):

    if line is not None:
        name = method_object.method_name + "("
        all_param_in_line = True

        if name in line:
            if method_object.parameters is not None:
                for param in method_object.parameters:
                    if not (clean_param(param) in line):
                        all_param_in_line = False

            if all_param_in_line:
                return True

    return False


def clean_param(param):
    cleaned = param.strip("<>{}[];'\",.?/|+=_-")
    return cleaned


def get_method_in_line(line, method):
    original_line = str(line).strip()

    search_string = "(" + method.method_name + "\(.*?\))"
    original_method = re.search(search_string, original_line)

    if original_method is not None:
        original_method = original_method.group()
        return original_method
    else:
        return None


def find_replacement(replace_line, method_objects, method_object):

    for key in replace_line:
        original_line = key
    replacement_line = replace_line[original_line]

    original_method = get_method_in_line(original_line, method_object)

    if original_method is not None:

        for potential_method in method_objects:
            if method_in_line(potential_method, replacement_line):

                replacement_method = get_method_in_line(replacement_line, potential_method)

                if replacement_method == original_method and "deprecated" in replacement_line:
                    replacement = {original_method: "DEPRECATED"}
                    return replacement
                elif replacement_method is not None and replacement_method != original_method:
                    replacement = {original_method: replacement_method}
                    return replacement
                elif replacement_method == original_method:
                    return None

    return {original_method: replacement_line}


def list_all_methods(method_objects):
    object_list = []
    for path in method_objects:
        object_list.extend(method_objects[path])

    return object_list


def get_current_changes(file_diff, method_objects, commit_sha, methods_list):

    file_diff_list = []
    for item in file_diff:
        file_diff_list.extend(item.diff.decode('utf8', errors="ignore").splitlines(keepends=True))

    file_diff_list_sections = separate_diff_into_subsections(file_diff_list)

    for section in file_diff_list_sections:

        for line in section:

            for method_object in method_objects:

                if method_in_line(method_object, line):
                    if '- ' in line:
                        replacement_line = get_replacement_line(line, section)
                        replacement_method = find_replacement(replacement_line, methods_list, method_object)

                        if replacement_method is not None:
                            if not (commit_sha in method_object.affected_commits):
                                method_object.affected_commits[commit_sha] = {'Removals': []}
                            elif not ('Removals' in method_object.affected_commits[commit_sha]):
                                method_object.affected_commits[commit_sha].update({'Removals': []})

                            lst = method_object.affected_commits[commit_sha]['Removals']
                            if not duplicate_in_list(lst, replacement_method):
                                method_object.affected_commits[commit_sha]['Removals'].append(replacement_method)

    return method_objects


def duplicate_in_list(lst, to_check):
    id_to_check = to_check.keys()

    for item in lst:
        checking = item.keys()
        if checking == id_to_check:
            return True

    return False


def get_line_type(line):

    if line[0] == '+':
        current_line_type = line[0]
    elif line[0] == '-':
        current_line_type = line[0]
    else:
        current_line_type = None

    return current_line_type


def get_replacement_line(target_line, file_diff_list):
    replacement = None

    got_it = False
    getting_it = False
    previous_line_type = None
    original = []
    new = []
    for line in file_diff_list:

        current_line_type = get_line_type(line)

        if target_line in line:
            original = [line]
            getting_it = True
            got_it = True
        elif '+' == current_line_type and previous_line_type == '-' and got_it is True:
            new.append(line)
            getting_it = False
        elif '-' == current_line_type == previous_line_type and getting_it is True:
            original.append(line)
        elif '+' == current_line_type == previous_line_type and got_it is True:
            new.append(line)
        elif None is current_line_type and got_it is True:
            break

        previous_line_type = current_line_type

    old_line = ''.join(original)
    replacement = ''.join(new)

    change = {old_line: replacement}

    return change


def get_affected_commits(method_object_dict, repo_dir, class_commits):
    repo = get_project_repository(repo_dir)

    methods_list = list_all_methods(method_object_dict)

    total_paths = len(method_object_dict)
    current_path_studied = 0

    for path in method_object_dict:
        percent_done = str(round(current_path_studied/total_paths * 100, 2))
        print("Looking for commits affected with modifications of: " + path + " " + percent_done + " % DONE")
        current_path_studied += 1

        for commit_sha in class_commits[path]['Commits']:
            interesting_commit = repo.commit(commit_sha)
            parent_commit = interesting_commit.parents[0]

            diff = parent_commit.diff(interesting_commit, create_patch=True)
            file_diff = get_file_diffs(diff, path)

            if file_diff is not None:

                if file_diff.a_blob is not None:
                    original_blob = write_blob(file_diff.a_blob, file_diff.a_path)
                else:
                    original_blob = None

                if file_diff.b_blob is not None:
                    new_blob = write_blob(file_diff.b_blob, file_diff.b_path)
                else:
                    new_blob = None

                method_object_dict[path] = get_current_changes(diff, method_object_dict[path], commit_sha, methods_list)

                method_object_dict[path] = muti_threaded_search(method_object_dict[path], original_blob, new_blob, commit_sha)

    return method_object_dict


def muti_threaded_search(method_object_list, original_blob, new_blob, current_commit_sha):

    for method_object in method_object_list:
        if method_changed(method_object, original_blob, new_blob):
            if not (current_commit_sha in method_object.affected_commits):
                method_object.affected_commits[current_commit_sha] = {'Changed Implementation': True}
            else:
                method_object.affected_commits[current_commit_sha].update({'Changed Implementation': True})

    return method_object_list
