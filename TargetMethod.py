import re


class TargetMethod(object):

    def __init__(self, method_name, class_name=None, package_name=None, parameters=None, affected_commits={},
                 original_doc=None, final_doc=None, kind=None, repo_path=None, original_calls=[], final_calls=[],
                 return_type=None):

        self.method_name = method_name
        self.class_name = class_name
        self.package_name = package_name
        self.parameters = parameters
        self.affected_commits = affected_commits
        self.original_doc = original_doc
        self.original_calls = original_calls
        self.final_doc = final_doc
        self.final_calls = final_calls
        self.kind = kind
        self.repo_path = repo_path
        self.return_type = return_type

    def method_in_string(self, connected_method, sentence):
        if connected_method is not None and sentence is not None:
            in_sentence = re.search(r'\b' + connected_method.method_name + '\W', sentence)

            if in_sentence:
                return True
            else:
                return False
        else:
            return False

    def clean_params(self):
        clean_params = []

        if self.parameters is not None:
            for param in self.parameters:
                param.strip().strip('<>{}[]')

        return clean_params

    def filename(self):
        file_name = self.class_name + '.java'
        return file_name

    def pseudo_path(self):
        package = self.package_name.replace('.', '/')

        if '.' in self.class_name:
            class_name = self.class_name.split('.')[0] + '.java'
        else:
            class_name = self.filename()

        pseudo_path = package + '/' + class_name

        return pseudo_path

    def total_parameters(self):
        if self.parameters is None:
            return 0
        else:
            return len(self.parameters)

    def original_doc_mentions(self, connected_method):
        if self.original_doc is not None:
            if self.method_in_string(connected_method, self.original_doc):
                return True
        return False

    def final_doc_mentions(self, connected_method):
        if self.final_doc is not None:
            if self.method_in_string(connected_method, self.final_doc):
                return True
        return False

    def original_calls_contain(self, connected_method):
        if self.original_calls is not None:
            for call in self.original_calls:
                if str(call) == connected_method.method_name:
                    return True

        return False

    def final_calls_contain(self, connected_method):
        if self.final_calls is not None:
            for call in self.final_calls:
                if str(call) == connected_method.method_name:
                    return True

        return False

    def affected_commits_contain(self, connected_method):
        if self.affected_commits is not None:
            if id(self) != id(connected_method):
                for commit, mods in self.affected_commits.items():
                    if "Removals" in mods:
                        for item in mods["Removals"]:
                            for add, rem in item.items():
                                if self.method_in_string(connected_method, add) or \
                                        self.method_in_string(connected_method, rem):
                                    return True
        return False

    def implementation_changed_together(self, connected_method):
        if self.affected_commits is not None:
            if id(self) != id(connected_method):
                for commit, mods in self.affected_commits.items():
                    if "Changed Implementation" in mods:
                        if mods["Changed Implementation"]:

                            if commit in connected_method.affected_commits:
                                if "Changed Implementation" in connected_method.affected_commits[commit]:
                                    if connected_method.affected_commits[commit]["Changed Implementation"]:
                                        return True
        return False

    def get_unique_name(self):
        if self.repo_path is not None:

            unique_name = ""

            unique_name += self.repo_path + "_"
            unique_name += self.method_name

            if self.parameters is not None:
                param_string = '; '.join(self.parameters)
            else:
                param_string = ""
            unique_name += "(" + param_string + ")"
        else:
            return None

        return unique_name
