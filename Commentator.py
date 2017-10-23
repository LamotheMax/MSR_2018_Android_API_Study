import git
import re
from lxml import etree
from XMLer import convert_string_to_xml

ns = {"src": "http://www.srcML.org/srcML/src"}


def get_target_method(xml_element, method_object):
    method_name = method_object.method_name
    method_params = method_object.parameters
    param_total = method_object.total_parameters()

    method_xpath_expression = "//src:function[src:name[text()='{0}']][src:parameter_list[count(src:parameter) = {1}]]".format(method_name, param_total)

    potential_methods = xml_element.xpath(method_xpath_expression, namespaces=ns)

    if len(potential_methods) > 1:
        method = parameter_check(potential_methods, method_params)
    elif len(potential_methods) == 0:
        method = None
    else:
        method = potential_methods[0]

    return method


def parameter_check(potential_methods, method_parameters):

    for item in potential_methods:
        parameter_xpath_exp = "./src:parameter_list/src:parameter/src:decl/src:type/src:name"

        params = item.xpath(parameter_xpath_exp, namespaces=ns)

        param_matches = []
        for par in params:
            string_element = etree.tostring(par)

            this_param_match = False
            for known_parameter in method_parameters:
                known_parameter = known_parameter.strip(',.(){}[]<>/\\').encode('utf8')

                if known_parameter in string_element:
                    this_param_match = True
                    break
                else:
                    this_param_match = False
            param_matches.append(this_param_match)

        if not (False in param_matches):
            return item

    return None


def clean_arguments(argument_line):
    clean = None
    if b'name' in argument_line:
        clean = re.sub(b"<.*?>", b"", argument_line)

    return clean


def get_method_calls(method_xml_element):

    call_xpath_exp = ".//src:call"
    calls = method_xml_element.xpath(call_xpath_exp, namespaces=ns)

    method_call_list = []
    for item in calls:
        call_name_expr = "./src:name"
        call_name = item.xpath(call_name_expr, namespaces=ns)

        method_call_list.append(call_name[0].text)

    return method_call_list


def get_specific_method_comment(xml_file_location, method_object):

    method_name = method_object.method_name

    xml_file = etree.fromstring(xml_file_location)
    methods = get_target_method(xml_file, method_object)

    if methods is not None:
        try:
            method_calls = get_method_calls(methods)

            comments = xml_file.xpath("//src:comment", namespaces=ns)
            method_comment = get_closest_comment(methods, comments)
        except:
            raise UnboundLocalError("More than one Method of name: " + method_name)
    else:
        return None, None

    return method_comment, method_calls


def get_closest_comment(method, comments):
    method_line = method.sourceline

    current_comment_line = 0
    current_comment = None
    for element in comments:
        comment_line = element.sourceline

        if method_line > comment_line > current_comment_line:
            current_comment = element
            current_comment_line = current_comment.sourceline

    return current_comment


def get_project_repository(repo_dir):

    repository = git.Repo(repo_dir)
    assert not repository.bare
    return repository


def get_original_comments(value, path, tag, repo):
    try:
        file_contents = repo.git.show('{}:{}'.format(repo.tags[tag].commit, path))

    except git.exc.GitCommandError:
        for key, methods in value.items():
            for method_object in methods:

                    method_object.original_doc = None
                    method_object.original_calls = None
        return

    xml_version = convert_string_to_xml(file_contents)

    for key, methods in value.items():
        for method_object in methods:
            method_element_comment, calls = get_specific_method_comment(xml_version, method_object)
            if method_element_comment is not None:
                method_object.original_doc = etree.tostring(method_element_comment).decode('utf8')
                method_object.original_calls = calls
    return


def get_newest_comments(value, path, tag, repo):
    try:
        file_contents = repo.git.show('{}:{}'.format(repo.tags[tag].commit, path))

    except git.exc.GitCommandError:
        for key, methods in value.items():
            for method_object in methods:

                method_object.final_doc = None
                method_object.final_calls = None
        return

    xml_version = convert_string_to_xml(file_contents)

    for key, methods in value.items():
        for method_object in methods:
            method_element_comment, calls = get_specific_method_comment(xml_version, method_object)
            if method_element_comment is not None:
                method_object.final_doc = etree.tostring(method_element_comment).decode('utf8')
            method_object.final_calls = calls

    return


def get_method_tag_comments(method_objects, repo_dir, oldest_tag, newest_tag):
    object_list = []
    repo = get_project_repository(repo_dir)

    for path, value in method_objects.items():
        print('Getting comments for methods in: ' + path)
        try:
            get_original_comments(value, path, oldest_tag, repo)
            get_newest_comments(value, path, newest_tag, repo)
            object_list.extend([o for o in value['Methods']])
        except UnboundLocalError:
            print('Failed to get comments for:' + path)

    return object_list


def get_commit_comments(commit_list, repo_dir):
    repo = get_project_repository(repo_dir)

    commit_messages = {}

    for class_name, value in commit_list.items():
        commit_messages[class_name] = {'Commits': {}}

        for item, commits in value.items():

            for commit in commits:
                commit_item = repo.commit(commit)
                commit_comment = commit_item.message
                if not commit_comment.startswith("Merge"):
                    commit_messages[class_name]['Commits'][commit] = {'Message': commit_comment}

    return commit_messages
