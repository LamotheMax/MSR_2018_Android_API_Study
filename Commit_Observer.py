from collections import Counter


def get_top_churn_commits(method_objects, percentile):
    counted_commits_dict = count_modifications_per_commit(method_objects)

    most_common = counted_commits_dict.most_common(len(counted_commits_dict)//int(percentile))

    most_common_list = []
    for item in most_common:
        most_common_list.append(item[0])

    return most_common_list


def remove_top_churn_commits(counted_commits_dict, most_common):

    for item in most_common:
        del counted_commits_dict[item]

    return counted_commits_dict


def is_worthwhile_commit(commit):

    if count_commit_files(commit) > 20:
        return False


def is_in_top_churn_commits(commit_sha, method_objects):
    most_common = get_top_churn_commits(method_objects, 10)

    if commit_sha in most_common:
        return True
    else:
        return False


def count_commit_files(commit):
    commit_files = 0

    for item in commit:
        commit_files += 1

    return commit_files


def count_modifications_per_commit(method_objects):
    commits_mods = []

    for method_object in method_objects:
        for commit, mods in method_object.affected_commits.items():
            if "Changed Implementation" in mods:
                commits_mods.append(commit)

    commits_count = Counter(commits_mods)
    return commits_count
