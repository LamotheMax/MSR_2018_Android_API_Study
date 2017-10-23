from collections import Counter


def count_suggestion_occurrence(suggestion_link_dict):

    suggestion_list = []
    for link_kind, links in suggestion_link_dict.items():
        if link_kind != "Kind":
            suggestion_list.extend(links)

    counted_suggestions = Counter(suggestion_list)

    return counted_suggestions


def order_suggestions_by_occurence(suggestions):
    ordered_suggestions = {}
    for item in suggestions:
        if not (suggestions[item] in ordered_suggestions):
            ordered_suggestions[suggestions[item]] = [item]
        else:
            ordered_suggestions[suggestions[item]].append(item)

    return ordered_suggestions


def bin_suggestions(suggestions):

    for method, suggestion in suggestions.items():
        links = []
        same_class = []
        method_class = method.split('_')[0]

        for rank, items in suggestion.items():
            if rank != "Kind":
                for item in items:
                    item_class = item.split('_')[0]
                    if item == method:
                        suggestion[rank].remove(item)
                    elif item in suggestions:
                        if suggestions[item]["Kind"] == "Removed":
                            links.append(item)
                            suggestion[rank].remove(item)
                        elif item_class == method_class:
                            same_class.append(item)
                            suggestion[rank].remove(item)

        suggestion.update({"Links": links})
        suggestion.update({"Likely": same_class})

    return suggestions


def get_suggestion(final_link_results):
    suggestions = {}

    for method in final_link_results["Methods"]:
        suggestions[method] = {"Kind": final_link_results["Methods"][method]["Kind"]}

        suggestion_occurence = count_suggestion_occurrence(final_link_results["Methods"][method])
        suggestions[method].update(order_suggestions_by_occurence(suggestion_occurence))

    bin_suggestions(suggestions)
    return suggestions
