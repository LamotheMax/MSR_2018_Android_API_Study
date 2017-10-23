from TargetMethod import TargetMethod


def add_root_path(method_objects, commit_messages):
    new_method_objects = {}

    for pseudo_path, value in method_objects.items():
        for item in commit_messages:
            if pseudo_path in item:
                new_method_objects[item] = {'Methods': []}
                for key, methods in value.items():
                    for method in methods:
                        method.repo_path = item
                        new_method_objects[item]['Methods'].append(method)
                break

    return new_method_objects


def get_targets(method_list, target_methods, type):
    for package, value in method_list[type]['Methods'].items():
        for class_name, methods in value.items():
            for method_dict in methods:

                target = TargetMethod(method_dict['method_name'])
                target.return_type = method_dict['return_type']
                target.class_name = class_name
                target.package_name = package
                target.kind = type
                if len(method_dict['parameters']) > 0 and method_dict['parameters'][0] != '':
                    target.parameters = method_dict['parameters']
                target_methods.append(target)

    return target_methods


def sort_by_class(target_methods):
    method_dict = {}

    for item in target_methods:
        pseudo_path = item.pseudo_path()

        if not (pseudo_path in method_dict):
            method_dict[pseudo_path] = {'Methods': [item]}
        else:
            method_dict[pseudo_path]['Methods'].append(item)

    return method_dict


def clean_methods(methods):
    keys = list(methods.keys())

    for path in keys:
        if '/icu' in path:
            del methods[path]
    return methods


def scope(method_items):
    target_methods = []

    target_methods = get_targets(method_items, target_methods, 'Removed')
    target_methods = get_targets(method_items, target_methods, 'Added')
    target_methods = get_targets(method_items, target_methods, 'Changed')
    target_methods = get_targets(method_items, target_methods, 'Deprecated')

    methods = sort_by_class(target_methods)
    methods = clean_methods(methods)

    return methods

