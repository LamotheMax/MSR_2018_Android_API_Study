import git
import logging


def get_project_repository(repo_dir):

    repository = git.Repo(repo_dir)
    assert not repository.bare
    return repository


def follow_file(file_name, repo, latest_tag, earliest_tag):
    g = repo.git

    # look into git log -- path also, see the benefits of each and chose one
    hexshas = g.log('{}..{}'.format(earliest_tag, latest_tag), '--pretty=%H', '--follow', '--', file_name).split('\n')
    print("Looking at : ", file_name)

    return hexshas


def secondary_path_finder(pseudo_path, repo, tag1, tag2):

        removed_index = git.IndexFile.from_tree(repo, tag1)
        path = None
        for entry, value in removed_index.entries.items():
            potential_path = value.path
            if pseudo_path in potential_path:
                if potential_path.endswith(".java"):
                    return potential_path

        added_index = git.IndexFile.from_tree(repo, tag2)
        for entry, value in added_index.entries.items():
            potential_path_2 = value.path
            if pseudo_path in potential_path_2:
                if potential_path_2.endswith(".java"):
                    return potential_path_2

        return path


def create_file_path(pseudo_path, diff):

    for file in diff:
        if pseudo_path in file.a_path:
            return file.a_path

        elif pseudo_path in file.b_path:
            return file.b_path

    return None


def get_diff_file_list(repo, start_tag, end_tag):
    start_commit = repo.tags[start_tag].commit
    end_commit = repo.tags[end_tag].commit
    diff = end_commit.diff(start_commit, create_patch=False)

    return diff


def extract_methods(repo_dir, start_tag, end_tag, methods_dict):
    repo = get_project_repository(repo_dir)
    commits_dict = {}

    logging.basicConfig(level=logging.DEBUG, filename='error.log')

    diff = get_diff_file_list(repo, start_tag, end_tag)

    for pseudo_path in methods_dict:

            file_name = create_file_path(pseudo_path, diff)
            if file_name is None:
                file_name = secondary_path_finder(pseudo_path, repo, start_tag, end_tag)
            try:
                if file_name is not None:
                    commit_list = follow_file(file_name, repo, end_tag, start_tag)
                    commits_dict[file_name] = {'Commits': commit_list}
                else:
                    commits_dict[pseudo_path] = {'Commits': []}
            except:
                logging.exception("Failed to follow: " + str(file_name) + " in pseudo_path: " + str(pseudo_path))

    return commits_dict
