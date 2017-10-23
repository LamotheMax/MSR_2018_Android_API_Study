import git
import difflib
import re


def get_project_repository(repo_dir):

    repository = git.Repo(repo_dir)
    assert not repository.bare
    return repository


def get_file_diffs(diff_object, file_name):
    for item in diff_object:

        if item.a_blob.path == file_name:
            return item

    return None


def diff_with_tags(repo, start_tag, end_tag, file ):
    start_commit = repo.tags[start_tag].commit
    end_commit = repo.tags[end_tag].commit
    diff = end_commit.diff(start_commit, file, create_patch=True)

    file_diff = get_file_diffs(diff, file)

    return file_diff


def get_diff(file_diff):
    a_file = file_diff.a_blob.data_stream.read().decode('utf8').splitlines(keepends=True)
    b_file = file_diff.b_blob.data_stream.read().decode('utf8').splitlines(keepends=True)

    diff = difflib.ndiff(b_file, a_file)

    return diff


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


def get_method(line):
    method_parts = line.split('(')
    method_parameters_string = method_parts[1].split(')')[0]

    parameters = get_parameters(method_parameters_string)

    method = method_parts[0]
    method_name = method.split()[-1]

    prefixes = line.split(" " + method_name)
    return_type = get_return_type(prefixes)

    full_method = {'method_name': method_name, 'parameters': parameters, 'return_type': return_type}

    return full_method


def get_return_type(item):
    return_type = item[0].split()[-1]
    return return_type


def get_parameters(method_parameters_string):
    fully_def_parameters = re.compile(",(?![^<>]*>)").split(method_parameters_string)
    parameters = []

    for item in fully_def_parameters:
        if '<' in item:
            param_parts = item.split('<')
            param_head = param_parts[0].split('.')[-1]
            full_param_internals = param_parts[1].split(',')

            param = param_head + '<'

            first = True
            for intern in full_param_internals:
                if first:
                    param += intern.split('.')[-1]
                    first = False
                else:
                    param += ',' + intern.split('.')[-1]

        else:
            param = item.split('.')[-1]

        parameters.append(param)

    return parameters


def insert_into_changed(changed_methods, line, package_line, class_line, method_line):
    if not already_exists(changed_methods, package_line, class_line, method_line):

        if '- ' in line:
            add_changed_method(changed_methods, package_line, class_line, method_line, 'Removed')

        elif '+ ' in line:
            add_changed_method(changed_methods, package_line, class_line, method_line, 'Added')

    return changed_methods


def add_changed_method(changed_methods, package_item, class_item, method_item, type):
    if package_item in changed_methods[type]['Methods']:
        if class_item in changed_methods[type]['Methods'][package_item]:
            changed_methods[type]['Methods'][package_item][class_item].append(method_item)
        else:
            changed_methods[type]['Methods'][package_item][class_item] = [method_item]
    else:
        changed_methods[type]['Methods'][package_item] = {class_item: [method_item]}

    return


def insert_package_change(changed_methods, line, package_line):
    if '- ' in line:
        changed_methods['Removed']['Packages'].append(package_line)
    elif '+ ' in line:
        changed_methods['Added']['Packages'].append(package_line)
    return changed_methods


def insert_class_change(changed_methods, line, package_line, class_line):
    if '- ' in line:
        changed_methods['Removed']['Classes'].append(package_line + '.' + class_line)
    elif '+ ' in line:
        changed_methods['Added']['Classes'].append(package_line+ '.' + class_line)
    return changed_methods


def already_exists(changed_methods, package_item, class_item, method_item):
    removed_methods = changed_methods['Removed']['Methods']
    added_methods = changed_methods['Added']['Methods']

    if package_item in removed_methods:
        if class_item in removed_methods[package_item]:
            if method_item in removed_methods[package_item][class_item]:
                removed_methods[package_item][class_item].remove(method_item)
                add_changed_method(changed_methods, package_item, class_item, method_item, 'Changed')
                return True
    elif package_item in added_methods:
        if class_item in added_methods[package_item]:
            if method_item in added_methods[package_item][class_item]:
                added_methods[package_item][class_item].remove(method_item)
                add_changed_method(changed_methods, package_item, class_item, method_item, 'Changed')
                return True
    else:
        return False


def remove_removed(changed_methods, package_item, class_item, method_item):
    removed_methods = changed_methods['Removed']['Methods']

    if package_item in removed_methods:
        if class_item in removed_methods[package_item]:
            if method_item in removed_methods[package_item][class_item]:
                removed_methods[package_item][class_item].remove(method_item)

    return


def in_deprecated(changed_methods, package_item, class_item, method_item):
    if package_item in changed_methods['Deprecated']['Methods']:
        if class_item in changed_methods['Deprecated']['Methods'][package_item]:
            if method_item in changed_methods['Deprecated']['Methods'][package_item][class_item]:
                return True

    return False


def get_current_method_changes(repo_dir, start_tag, end_tag):
    changed_methods = {'Added': {'Packages': [], 'Classes': [], 'Methods': {}},
                       'Removed': {'Packages': [], 'Classes': [], 'Methods': {}},
                       'Changed': {'Methods': {}},
                       'Deprecated': {'Methods': {}}}

    repo = get_project_repository(repo_dir)

    file = "api/current.txt"
    file_diff = diff_with_tags(repo, start_tag, end_tag, file)

    diff = get_diff(file_diff)

    package_line = None
    class_line = None

    for line in diff:

        if 'package ' in line and '{\n' in line[-2:]:
            package_line = get_package(line)

            if 'java' in package_line:
                package_line = None
            else:
                changed_methods = insert_package_change(changed_methods, line, package_line)
        if package_line is not None:
            if 'class ' in line and '{\n' in line[-2:]:
                class_line = get_class(line)
                changed_methods = insert_class_change(changed_methods, line, package_line, class_line)
            elif 'method public' in line:
                if '- ' in line or '+ ' in line:
                    current_method = get_method(line)
                    if 'deprecated' in line and '+ ' in line:

                        add_changed_method(changed_methods, package_line, class_line, current_method, 'Deprecated')
                        remove_removed(changed_methods, package_line, class_line, current_method)
                    elif not ignored_package(package_line):

                        if not in_deprecated(changed_methods, package_line, class_line, current_method):
                            changed_methods = insert_into_changed(changed_methods, line, package_line, class_line, current_method)

    return changed_methods


def ignored_package(package_line):

    if "junit" in package_line:
        return True
    elif "apache" in package_line:
        return True
    else:
        return False


def get_current_changes(file_diff):
    file_diff = file_diff.diff.decode('utf8').splitlines(keepends=True)
    churn = {'Additions': [], 'Removals': []}

    for line in file_diff:
        if '- ' in line :
            churn['Removals'].append(line[1:])
        elif '+ ' in line:
            churn['Additions'].append(line[1:])

    return churn


def get_method_changes(changes, kind):

    methods = []

    for item in changes[kind]:
        if 'method public' in item:
            method = get_method(item)
            methods.append(method)

    return methods


def get_API_churn_per_commit(commit_list, repo_dir):

    repo = get_project_repository(repo_dir)

    for path in commit_list:
        print("Getting API/Current.txt churn for all commits in: " + path)
        for commit_sha in commit_list[path]['Commits']:
                interesting_commit = repo.commit(commit_sha)
                parent_commit = interesting_commit.parents[0]

                diff = parent_commit.diff(interesting_commit, "api/current.txt", create_patch=True)
                file_diff = get_file_diffs(diff, 'api/current.txt')
                if file_diff is not None:
                    changes = get_current_changes(file_diff)

                    commit_list[path]['Commits'][commit_sha]['Removals'] = get_method_changes(changes, 'Removals')
                    commit_list[path]['Commits'][commit_sha]['Additions'] = get_method_changes(changes, 'Additions')

    return commit_list

