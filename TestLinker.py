import Linker

def test_get_links(method_objects, commit_info, all_API_methods):
    links_dict = {"Methods": {}}

    all_API_methods = Linker.remove_repeats(method_objects, all_API_methods)
    method_objects = Linker.remove_high_link_commits(method_objects)
    second_level = method_objects.copy()

    total_methods = len(method_objects)

    viewed = ''

    for a in method_objects:
        if 'addGpsStatusListener' in a.get_unique_name():
            for b in second_level:
                if 'registerGnssStatusCallback' in b.get_unique_name():
                    viewing = a

                    if a.get_unique_name() != b.get_unique_name():
                        Linker.print_progress(links_dict, total_methods)

                        if not (a.get_unique_name() in links_dict["Methods"]):
                            links_dict["Methods"][a.get_unique_name()] = {"Kind": a.kind, "Original_Doc_mention": [], "Final_Doc_mention": [], "Originally_called": [], "Finally_called:": [], "Commit_Link": [], "Commit_Message_Mention": [], "Implementation_changed_together": []}

                        message_links = Linker.get_commit_message_links(a, b, commit_info)
                        if len(message_links) > 0:
                            if not (b.get_unique_name() in links_dict["Methods"][a.get_unique_name()]["Commit_Message_Mention"]):
                                links_dict["Methods"][a.get_unique_name()]["Commit_Message_Mention"].append(b.get_unique_name())
                        Linker.get_connections(a, b, links_dict["Methods"][a.get_unique_name()])

                        if a.kind == "Removed":
                            if viewed != viewing.get_unique_name():
                                print("Getting General links for: {}".format(a.get_unique_name()))
                                Linker.get_general_links(a, all_API_methods, links_dict, commit_info)
                                viewed = viewing.get_unique_name()

    links_dict = Linker.get_ori_final_diffs(links_dict)

    return links_dict