import csv
import re

def get_matches():
    with open('matches.csv') as matches:
        reader = csv.DictReader(matches)
        result = {}
        for row in reader:
            key = row.pop('Target')
            if key in result:
                # implement your duplicate row handling here
                pass
            result[key] = row
    return result


# must have removed links manually from suggestions right now fix later
def get_suggestions():
    result = {}
    with open('suggestions.csv') as suggestions:
        next(suggestions)
        for line in suggestions:
            clean_line = line.strip()
            fully_def_parameters = re.compile(",(?![^<>]*>)").split(clean_line)

            key = fully_def_parameters.pop(0)
            result[key] = count(fully_def_parameters)

    return result


def count(items):
    tally = 0
    for item in items:
        if item != '[]' and item != 'NA':
            tally += 1
    return tally


def add_tally_to_matches(matches, suggestions):
    for item in matches:
        new_item = item.replace(',', ';')

        try:
            guesses = suggestions[new_item]
        except:
            print('can\'t find guess {}'.format(new_item))
            guesses = 'NA'
        matches[item]['Guesses'] = str(guesses)

    return matches


def clean_to_print_csv(current_dict):
    for key, value in current_dict.items():
        current_dict[key] = value.replace(',',';')

    return current_dict


def print_guesses_with_tally(tallied_matches):
    with open('tallied_matches.csv', 'w') as matches:
        headings = 'Target,Comment replacement,Suggested Replacement,Found replacement,Changed param type,Changed Parameter #,Guesses,Position,Replacement,Note\n'
        matches.write(headings)

        for item in tallied_matches:
            current_dict = tallied_matches[item]
            current_dict = clean_to_print_csv(current_dict)

            to_write = item.replace(',',';')+','+current_dict['Comment replacement']+','+current_dict['Suggested Replacement']\
            +','+current_dict['Found replacement']+','+current_dict['Changed param type']+','+current_dict['Changed Parameter #']\
            +','+current_dict['Guesses']+'\n'
            matches.write(to_write)


def load_uses():

    with open('consolidated_uses.csv') as matches:
        reader = csv.DictReader(matches)
        result = {}
        viewed_packages = []
        for row in reader:
            if int(row[' In Version'].replace('\'', '').replace(' ', '')) == 22:
                key = row['Package'].strip('[').replace('.', '/') + '.java' + '_' + row.pop(' Method')
                key = key.replace('\'', '').replace(' ', '')

                project = row[' projectVersion'].replace('\'', '').replace(' ', '').split('/')
                file = row[' File'].replace('\'', '').replace(' ', '')
                viewing = project[1] + '/' + project[2] + '/' + file
                if viewing not in viewed_packages:

                    if key in result:
                        result[key] += int(row[' #Times'].replace('\'', '').replace(' ', ''))
                    else:
                        result[key] = int(row[' #Times'].replace('\'', '').replace(' ', ''))

                    viewed_packages.append(viewing)
    return result


def print_successes(uses):
    with open('project_total_uses_22.csv', 'w') as matches:
        headings = 'Target, Use_count\n'
        matches.write(headings)

        for item in uses:
            to_write = item + ',' + str(uses[item]) + '\n'
            matches.write(to_write)


def load_final_matches():
    file_name = 'final_resultsandroid-7.1.0_r1.csv'
    with open(file_name) as matches:
        reader = csv.DictReader(matches)
        result = {"Methods": {}}
        for row in reader:
            if row['Kind'] != 'Added':
                items = tabulate_methods_links(row)
                items.update({"Kind": row["Kind"]})
                result["Methods"][row["ID"]] = items

    save_tabulated_final_results(result, file_name)


def tabulate_methods_links(row):
    tabulated_uses = {}
    for item in row:
        if item != "ID" and item != "Kind":
            uses = tabulate_uses(row[item])
            tabulated_uses[item] = uses

    return tabulated_uses


def tabulate_uses(item):
    all_uses = re.compile(",(?![^<>]*>)").split(item)

    if "[]" in all_uses:
        all_uses.remove("[]")

    return len(all_uses)


def save_tabulated_final_results(final_results, file_name):
    with open("tabulated_"+file_name, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["ID", "Kind", "Original_Doc_mention", "Final_Doc_mention", "Change in Doc", "Originally_called", "Finally_called:", "Commit_Link", "Commit_Message_Mention", "Implementation_changed_together"])
        for item, value in final_results["Methods"].items():

            writer.writerow([item, value["Kind"], value["Original_Doc_mention"], value["Final_Doc_mention"], value["Change in Doc"], value["Originally_called"], value["Finally_called:"], value["Commit_Link"], value["Commit_Message_Mention"], value["Implementation_changed_together"]])


def main():
    load_final_matches()
    # matches = get_matches()
    # suggestions = get_suggestions()
    # tallied_matches = add_tally_to_matches(matches, suggestions)
    # print_guesses_with_tally(tallied_matches)
    # uses = load_uses()
    # print_successes(uses)

main()
