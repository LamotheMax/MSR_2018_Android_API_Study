import itertools
import re
import Commit_Observer

percent_done = 0


def get_connections(method_object, method_to_compare, links):
    method_unique_id = method_to_compare.get_unique_name()

    if method_object.original_doc_mentions(method_to_compare):
        if not (method_unique_id in links["Original_Doc_mention"]):
            links["Original_Doc_mention"].append(method_unique_id)

    if method_object.final_doc_mentions(method_to_compare):
        if not (method_unique_id in links["Final_Doc_mention"]):
            links["Final_Doc_mention"].append(method_unique_id)

    if method_object.original_calls_contain(method_to_compare):
        if not (method_unique_id in links["Originally_called"]):
            links["Originally_called"].append(method_unique_id)

    if method_object.final_calls_contain(method_to_compare):
        if not (method_unique_id in links["Finally_called:"]):
            links["Finally_called:"].append(method_unique_id)

    if method_object.affected_commits_contain(method_to_compare):
        if not (method_unique_id in links["Commit_Link"]):
            links["Commit_Link"].append(method_unique_id)

    if method_object.implementation_changed_together(method_to_compare):
        if not (method_unique_id in links["Implementation_changed_together"]):
            links["Implementation_changed_together"].append(method_unique_id)

    return links


def print_progress(links_dict, total_methods):
    global percent_done
    new_percent_done = round(len(links_dict["Methods"]) / total_methods * 100, 1)

    if new_percent_done > percent_done:
        print("Now {}% done.".format(new_percent_done))
        percent_done = new_percent_done


def get_commit_message_links(method, method_to_compare, commit_info):

    affected_commits = []

    for commit in commit_info[method.repo_path]["Commits"]:
        commit_message = commit_info[method.repo_path]["Commits"][commit]["Message"]
        if method_in_string(method_to_compare, commit_message):
            if method_in_string(method, commit_message):
                affected_commits.append(commit)
    return affected_commits


def method_in_string(connected_method, sentence):
    if connected_method is not None and sentence is not None:
        in_sentence = re.search(r'\b' + connected_method.method_name + '\W', sentence)

        if in_sentence:
            return True
        else:
            return False
    else:
        return False


def get_links(method_objects, commit_info, all_API_methods):
    links_dict = {"Methods": {}}

    all_API_methods = remove_repeats(method_objects, all_API_methods)
    method_objects = remove_high_link_commits(method_objects)
    second_level = method_objects.copy()

    total_methods = len(method_objects)

    viewed = ''

    for a in method_objects:

        for b in second_level:
            viewing = a

            if a.get_unique_name() != b.get_unique_name():
                print_progress(links_dict, total_methods)

                if not (a.get_unique_name() in links_dict["Methods"]):
                    links_dict["Methods"][a.get_unique_name()] = {"Kind": a.kind, "Original_Doc_mention": [], "Final_Doc_mention": [], "Originally_called": [], "Finally_called:": [], "Commit_Link": [], "Commit_Message_Mention": [], "Implementation_changed_together": []}

                message_links = get_commit_message_links(a, b, commit_info)
                if len(message_links) > 0:
                    if not (b.get_unique_name() in links_dict["Methods"][a.get_unique_name()]["Commit_Message_Mention"]):
                        links_dict["Methods"][a.get_unique_name()]["Commit_Message_Mention"].append(b.get_unique_name())
                get_connections(a, b, links_dict["Methods"][a.get_unique_name()])

                if a.kind == "Removed":
                    if viewed != viewing.get_unique_name():
                        print("Getting General links for: {}".format(a.get_unique_name()))
                        get_general_links(a, all_API_methods, links_dict, commit_info)
                        viewed = viewing.get_unique_name()

    links_dict = get_ori_final_diffs(links_dict)

    return links_dict


def get_ori_final_diffs(links_dict):
    for method, values in links_dict['Methods'].items():
        doc_diff = []
        for item in values['Final_Doc_mention']:
            if not (item in values["Original_Doc_mention"]):
                doc_diff.append(item)

        links_dict['Methods'][method].update({'Doc_diff': doc_diff})

    return links_dict


def remove_high_link_commits(method_objects):
    top_stuff = Commit_Observer.get_top_churn_commits(method_objects, 10)
    print("Removing high link commits")
    percent_done = 0
    to_print = 0
    for method_object in method_objects:
        to_print = print_how_done(percent_done, len(method_objects), to_print)
        for sha in top_stuff:
            if sha in method_object.affected_commits:
                del method_object.affected_commits[sha]
        percent_done += 1

    return method_objects


def remove_repeats(method_objects, all_API_methods):
    print("Removing repeats")
    percent_done = 0
    to_print = 0
    for item in method_objects:
        to_print = print_how_done(percent_done, len(method_objects), to_print)
        method_name = item.get_unique_name()

        for value in all_API_methods:
            if value.repo_path is not None:
                value_name = value.get_unique_name()

                if method_name == value_name:
                    all_API_methods.remove(value)
                    break
            else:
                all_API_methods.remove(value)

        percent_done += 1

    return all_API_methods


def print_how_done(progress, total, old_amount):
    new_percent_done = round(progress / total * 100, 1)

    if new_percent_done//2 > old_amount//2:
        print("Now {}% done.".format(new_percent_done))
        old_amount = new_percent_done

    return old_amount


def get_general_links(method_object, all_current_methods, links_dict, commit_info):

    for method in all_current_methods:
        if method.get_unique_name() is not None and method_object.get_unique_name() is not None:

            message_links = get_commit_message_links(method_object, method, commit_info)

            if len(message_links) > 0:
                if not (method.get_unique_name() in links_dict["Methods"][method_object.get_unique_name()]["Commit_Message_Mention"]):
                    links_dict["Methods"][method_object.get_unique_name()]["Commit_Message_Mention"].append(method.get_unique_name())

            links = get_connections(method_object, method, links_dict["Methods"][method_object.get_unique_name()])

    return method_object


def count_occurrence(method, method_link_type, links):
    count = 0

    for link_type, items in links.items():
        if not (link_type is method_link_type):

            if "Commit_Message_Mention" == link_type:
                found = False
                for subdict in items:
                    if not found:
                        for item in subdict:
                            if method is item:
                                count += 1
                                found = True
                    else:
                        break

            elif method in items:
                count += 1

    return count


def determine_link_count(links_dict):
    link_list = {}
    for method, links in links_dict['Methods'].items():
        if not (method.repo_path in link_list):
            link_list[method.repo_path] = {method.method_name: {"MethodObject": method, "Links": []}}
        else:
            link_list[method.repo_path][method.method_name] = {"MethodObject": method, "Links": []}

        occurrences = []
        for link_type, items in links.items():
            for item in items:
                if not any(item in occurrence for occurrence in occurrences):
                    occurrence_count = count_occurrence(item, link_type, links)
                    if occurrence_count > 0:
                        occurrences.append((item, occurrence_count))

        link_list[method.repo_path][method.method_name]["Links"].extend(occurrences)

    return link_list
