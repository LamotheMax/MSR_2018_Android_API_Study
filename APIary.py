from MethodTargeter import get_current_method_changes, get_API_churn_per_commit
from FileFollower import extract_methods
from Scoper import scope, add_root_path
from Commentator import get_commit_comments, get_method_tag_comments
from TargetMethod import TargetMethod
from CommonChangeTracker import get_affected_commits
from Linker import get_links
from Suggester import get_suggestion
from MethodGrabber import get_all_current_methods
import os
import json
import csv


def order_objects_by_file(object_list):
    method_object_dict = {}
    for method_object in object_list:
        if not (method_object.repo_path in method_object_dict):
            method_object_dict[method_object.repo_path] = [method_object]
        else:
            method_object_dict[method_object.repo_path].append(method_object)

    return method_object_dict


def turn_dict_to_list(object_dict):
    object_list = []
    for path in object_dict:
        for o in object_dict[path]:
            object_list.append(o)
    return object_list


def get_changed_methods(repo_dict, s_tag, e_tag):

    if os.path.isfile('changed_methods'+e_tag+'.json'):
        with open('changed_methods'+e_tag+'.json', 'r') as fp:
            changes = json.load(fp)
    else:
        changes = get_current_method_changes(repo_dict, s_tag, e_tag)

        with open('changed_methods'+e_tag+'.json', 'w') as fp:
            json.dump(changes, fp)

    return changes


def get_class_commits(repo_directory, s_tag, e_tag, method_objs):

    if os.path.isfile('class_commits'+e_tag+'.json'):
        with open('class_commits'+e_tag+'.json', 'r') as fp:
            commits = json.load(fp)
    else:
        commits = extract_methods(repo_directory, s_tag, e_tag, method_objs)

        with open('class_commits'+e_tag+'.json', 'w') as fp:
            json.dump(commits, fp)

    return commits


def get_method_tag_coms(repository_directory, start_tag, end_tag, rooted_method_objects):

    if os.path.isfile('method_comments_at_tags'+end_tag+'.json'):
        method_comments = []
        with open('method_comments_at_tags'+end_tag+'.json', 'r') as fp:

            json_methods = json.load(fp)
        for method in json_methods:
            item = TargetMethod('temp')
            item.__dict__ = method
            method_comments.append(item)
    else:
        method_comments = get_method_tag_comments(rooted_method_objects, repository_directory, start_tag, end_tag)

        with open('method_comments_at_tags'+end_tag+'.json', 'w') as fp:
            json.dump([o.__dict__ for o in method_comments], fp)

    return method_comments


def save_affected_commits(repository_directory, end_tag, method_objects, class_commits):
    output_file = 'method_objects'+end_tag+'.json'

    if os.path.isfile(output_file):
        method_list = []
        with open(output_file,'r') as fp:
            json_methods = json.load(fp)
        for method in json_methods:
            item = TargetMethod('temp')
            item.__dict__ = method
            method_list.append(item)
    else:
        method_object_dict = order_objects_by_file(method_objects)
        method_results = get_affected_commits(method_object_dict, repository_directory, class_commits)
        method_list = turn_dict_to_list(method_results)

        with open(output_file, 'w') as fp:
            json.dump([o.__dict__ for o in method_list], fp)

    return method_list


def get_API_churn_per_com(repository_directory, start_tag, end_tag, class_commits_w_comments):

    if os.path.isfile('Current_Commits'+end_tag+'.json'):
        with open('Current_Commits'+end_tag+'.json', 'r') as fp:
            commits = json.load(fp)
    else:
        commits = get_API_churn_per_commit(class_commits_w_comments, repository_directory)

        with open('Current_Commits'+end_tag+'.json', 'w') as fp:
            json.dump(commits, fp)

    return commits


def get_final_results(end_tag, method_objects, class_commits, all_API_methods):
    if os.path.isfile('apiary_results'+end_tag+'.json'):
        with open('apiary_results'+end_tag+'.json', 'r') as fp:
            results = json.load(fp)
    else:
        results = get_links(method_objects, class_commits, all_API_methods)

        with open('apiary_results'+end_tag+'.json', 'w') as fp:
            json.dump(results, fp)

    return results


def get_all_methods(repo_directory, s_tag, e_tag):
    if os.path.isfile("all_methods"+e_tag+".json"):
        method_list = []
        with open("all_methods" + e_tag + ".json", 'r') as fp:
            json_methods = json.load(fp)
        for method in json_methods:
            item = TargetMethod('temp')
            item.__dict__ = method
            method_list.append(item)
    else:
        method_list = get_all_current_methods(repo_directory, s_tag, e_tag)
        with open("all_methods"+e_tag+".json", 'w') as fp:
            item = []
            for o in method_list:
                temp = o.__dict__
                item.append(temp)

            json.dump(item, fp)

    return method_list


def save_suggestions(final_results, end_tag):
    suggestions = get_suggestion(final_results)
    with open("suggestions"+end_tag+".csv", 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["ID", "Kind", "Top Suggestion", "2nd", "3rd", "4th", "5th", "Links"])

        for key, value in suggestions.items():
            kind = suggestions[key].pop('Kind', None)
            links = suggestions[key].pop('Links', None)
            likely = suggestions[key].pop('Likely', None)

            # making the list of likely have only unique entries
            likely = list(set(likely))
            sorted_list = []

            remove_keys = []
            for item in suggestions[key]:
                if len(suggestions[key][item]) == 0:
                    remove_keys.append(item)
            for item in remove_keys:
                del suggestions[key][item]

            for item in sorted(suggestions[key], key=lambda k: suggestions[key][k][-1]):
                sorted_list.append(suggestions[key][item])

            to_write = [key, kind]
            # padding the list to make it the right length
            sorted_list = (sorted_list + ['NA'] + ['NA'] + ['NA'] + ['NA'])[:4]
            to_write.append(likely)
            to_write.extend(sorted_list)
            to_write.append(links)
            writer.writerow(to_write)


def save_final_results(final_results, end_tag):
    with open("final_results"+end_tag+".csv", 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["ID", "Kind", "Original_Doc_mention", "Final_Doc_mention", "Change in Doc", "Originally_called", "Finally_called:", "Commit_Link", "Commit_Message_Mention", "Implementation_changed_together"])
        for item, value in final_results["Methods"].items():

            writer.writerow([item,value["Kind"], value["Original_Doc_mention"], value["Final_Doc_mention"], value["Doc_diff"], value["Originally_called"], value["Finally_called:"], value["Commit_Link"], value["Commit_Message_Mention"], value["Implementation_changed_together"]])


def main():
    repository_directory = '/Users/max/Desktop/Release7'
    remote_repo_dir = '/home/release7/platform_frameworks_base'

    if os.path.exists(remote_repo_dir):
        repository_directory = remote_repo_dir

    start_tag_number = '5.1.1'  # input("Enter Start Tag Version number (with dots): ")
    end_tag_number = '6.0.0'  # input("Enter End Tag Version number (with dots): ")

    end_tag = 'android-'+str(end_tag_number)+'_r1'
    start_tag = 'android-'+str(start_tag_number)+'_r1'

    print("Processing from: "+start_tag+" to " + end_tag)

    method_changes = get_changed_methods(repository_directory, start_tag, end_tag)

    all_API_methods = get_all_methods(repository_directory, start_tag, end_tag)

    method_objects = scope(method_changes)

    class_commits = get_class_commits(repository_directory, start_tag, end_tag, method_objects)

    class_commits_w_comments = get_commit_comments(class_commits, repository_directory)

    rooted_method_objects = add_root_path(method_objects, class_commits_w_comments)

    method_objects_w_coms = get_method_tag_coms(repository_directory, start_tag, end_tag, rooted_method_objects)

    churned_class_commits = get_API_churn_per_com(repository_directory, start_tag, end_tag, class_commits_w_comments)

    print("Now getting final results: this part is the longest, saving/reload everyting in case of crash")

    saved_method_objects = get_method_tag_coms(repository_directory, start_tag, end_tag, rooted_method_objects)
    saved_churn = get_API_churn_per_com(repository_directory, start_tag, end_tag, class_commits_w_comments)

    commited_method_objects = save_affected_commits(repository_directory, end_tag, saved_method_objects, saved_churn)

    final_results = get_final_results(end_tag, commited_method_objects, churned_class_commits, all_API_methods)

    save_suggestions(final_results, end_tag)

    save_final_results(final_results, end_tag)

main()
