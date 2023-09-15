import tarfile, os, re, shutil, json
from datetime import datetime
from os import path
from colorama import Fore
from colorama import Style

global debug_status

# World of Warcraft root directory
#root = '/mnt/c/Program Files (x86)/World of Warcraft/'
#root = '/mnt/c/Blizzard/World of Warcraft/'
#root = '/mnt/d/Blizzard/World of Warcraft/'

# path to output directory
# path_output = '/mnt/c/Users/alane/OneDrive/Documents/WoW BackUps'
# path_output = '/mnt/d/My Drive/Applications/WoW BackUps'
path_configuration = '/home/humplebert/wowi-configuration.json'

template_configuration = {
    'path_wow_root': '',
    'path_output': '',
}

# game versions
versions = {
    'Retail': '_retail_',
    'Classic Era': '_classic_era_',
    'Classic': '_classic_'
}

# menu
menu_options = {
    '1': 'Archive WTF',
    '2': 'Archive WTF & Interface',
    '3': 'Rename Interface',
    '4': 'Restore Interface',
    'p': 'Update Paths',
    'q': 'Quit'
}

menu_options_versions = {
    '1': 'Retail',
    '2': 'Classic Era',
    '3': 'Classic',
    'q': 'Quit'
}

menu_options_path_wow_root = {
    '1': '/mnt/c/Program Files (x86)/World of Warcraft/',
    '2': '/mnt/c/Blizzard/World of Warcraft/',
    '3': '/mnt/d/Blizzard/World of Warcraft/',
    'o': 'Other (manually define)',
    'q': 'Quit'
}

menu_options_path_output = {
    '1': '/mnt/d/My Drive/Applications/WoW BackUps',
    '2': '/mnt/c/Users/alane/OneDrive/Documents/WoW BackUps',
    'o': 'Other (manually define)',
    'q': 'Quit'
}

def run_manager(show_header=False):
    if show_header:
        print("World of Warcraft Interface Management System")
        print_configuration('path_wow_root','Current Root Path')
        print_configuration('path_output','Current BackUp Path')

    debug_status = True
    debug_label = f"{Fore.GREEN}ON{Style.RESET_ALL}"

    if not bool(get_configuration('path_wow_root')):
        set_path(menu_options_path_wow_root, 'Select path to World of Warcraft root directory... ', 'path_wow_root')
        run_manager(True)

    if not bool(get_configuration('path_output')):
        set_path(menu_options_path_output, 'Select path to WoW BackUps output directory... ', 'path_output')
        run_manager(True)

    path_wow_root = get_configuration('path_wow_root')

    # set Debug Mode
    action = input('Debug Mode? (y/n/q) [y] ')
    exit_program(action)

    if action == 'n':
        debug_status = False
        debug_label = f"{Fore.RED}OFF{Style.RESET_ALL}"

    print(f"Debug Mode is {debug_label}\n\n")

    # build menu
    print(build_menu(menu_options))
    action = input('Select Action: ')

    if action in menu_options.keys():
        exit_program(action)

        if action == 'p':
            set_path(menu_options_path_wow_root, 'Select path to World of Warcraft root directory... ', 'path_wow_root')
            set_path(menu_options_path_output, 'Select path to WoW BackUps output directory... ', 'path_output')
            run_manager(True)

        if action == '3':
            print(f"\n{build_menu(menu_options_versions)}")
            action = input('Select Rename Action: ')

            if action == 'q':
                print("\n")
                run_manager()

            do_interface_rename(versions[menu_options_versions[action]], path_wow_root, debug_status)
            run_manager()

        if action == '4':
            do_interface_restore(debug_status, path_wow_root)

        folders=['WTF']
        if action != '1':
            folders.append('Interface')

        directories = {}
        directories_failed = {}

        for version in versions:
            for folder in folders:
                paths = build_paths(versions[version], path_wow_root, folder)

                if os.path.exists(paths['path_folder']):
                    directories[paths['path_folder']] = paths['path_rel']
                else:
                    directories_failed.append(paths['path_folder'])

        if directories:
            print_summary("Folders added to archive", directories)

        if directories_failed:
            print_summary("Folders NOT added to archive (path is invalid)", directories_failed)

        do_interface_archive(directories, debug_status)

        print(f"{Fore.GREEN}Backup complete!{Style.RESET_ALL}\n\n")
        run_manager()
    else:
        print(f"{Fore.RED}Invalid Selection!{Style.RESET_ALL}\n\n")
        run_manager()


def exit_program(action):
    if action == 'q':
        quit()

def do_interface_archive(directories, debug_status=True):
    path_output = get_configuration('path_output')
    filename = f"{path_output}/{get_datetime()}.tar.gz"
    print(f"Creating archive {Fore.CYAN}{filename}{Style.RESET_ALL} ...")

    if debug_status == False:
        with tarfile.open(filename, 'w') as archive:

            for value in directories:
                if os.path.exists(value):
                    archive.add(value, arcname=directories[value])

        archive.close()

def do_interface_rename(version, root, debug_status=True):
    folders = ['WTF','Interface']
    filename = get_datetime()
    renames = {}
    paths_new = []

    action = re.sub(r'\W+', '', input(f"Interface Name? [{filename}] "))

    if action:
        filename = action[:35]

    path_archives = os.path.join(root, version, 'archives')
    if os.path.exists(path_archives) == False:
        print_summary("Create /archives directory", {path_archives})

        if debug_status == False:
            os.mkdir(path_archives)

    for folder in folders:
        paths = build_paths(version, root, folder)
        path_new = os.path.join(path_archives, f"{filename}/{folder}")

        if os.path.exists(paths['path_folder']):
            if os.path.exists(path_new):
                print(f"Could not rename {paths['path_rel']} to {path_new} because the folder already exists. Process aborted.\n")
                run_manager()
            else:
                renames[paths['path_folder']] = path_new
                paths_new.append(path_new)
        else:
            print(f"Could not rename {paths['path_rel']} because the path to the folder was invalid! Process aborted.\n")
            run_manager()

    if renames:
        print("\nRename process initiated. This may take some time...\n")
        for k in renames:
            if debug_status == False:
                shutil.move(k, renames[k])

        print_summary("Interface folders moved to archives", paths_new)
        print('Rename process complete!\n')

def do_interface_restore(version, root, debug_status=True):
    #TODO: check if /archives folder exists for the _version_
    path_archives = os.path.join(root, version, 'archives')
    if check_archive_path() == False:
        print("Archives directory not found. Process aborted.\n")
        run_manager()

    #TODO: print a list of folders in the /archives folder grouped by timestamp with timestamp converted to y-m-d h:ma format
    #TODO: run archive for current WTF/Interface in _version_
    #TODO: rename /archives folders to _version_ folders
    print('\nNYI! Goodbye!')
    run_manager()

def build_path_archives(version, root, archives_foldername='archives'):
    return os.path.join(root, version, archives_foldername)

def check_archive_path(path_archives):
    return os.path.exists(path_archives)

def get_datetime():
    now = datetime.now()
    return now.strftime("%Y%m%d%H%M%S")

def print_summary(header,collection):
    merged_collection = "\n    ".join(collection)
    print(f"{header}:\n    {merged_collection}")

def build_menu(options):
    menu = []

    for k, v in options.items():
        menu.append(f"[{k}] {v}")

    return "\n".join(menu)

def build_paths(version, root, folder='WTF'):
    path_version = os.path.join(root,version)
    path_folder = os.path.join(path_version, folder)
    path_rel = f"{version}/{folder}"

    return {
        'path_version': path_version,
        'path_folder': path_folder,
        'path_rel': path_rel
    }

def check_path_configuration():
    if not bool(os.path.exists(path_configuration)):
        write_configuration_file(template_configuration)

def check_path_wow_root():
    if get_configuration('path_wow_root'):
        return True

    return False

def write_configuration_file(configuration_json):
    configuration_file = open(path_configuration, 'w')
    configuration_file.write(json.dumps(configuration_json))
    configuration_file.close()

def get_configuration(configuration_key='ALL'):
    check_path_configuration()

    configuration_file = open(path_configuration,)
    configuration = json.load(configuration_file)

    if configuration_key == 'ALL':
        return configuration

    if configuration_key in configuration:
        return configuration[configuration_key]

    return

def print_configuration(configuration_key, label):
    print(f"{label}: {Fore.YELLOW}{get_configuration(configuration_key)}{Style.RESET_ALL}")

def set_path(menu_options, menu_prompt, configuration_key):
    check_path_configuration()
    configuration = get_configuration()

    print(f"{menu_prompt}")
    print(build_menu(menu_options))
    action = input('Select Option: ')
    exit_program(action)

    if 'o' == action:
        path_value = input('Enter Full Path: ')
    else:
        path_value = menu_options[action]

    if not bool(os.path.exists(path_value)):
        print(f"{Fore.RED}Path '{path_value}' is INVALID!{Style.RESET_ALL}")
        set_path(menu_options, menu_prompt, configuration_key)
    else:
        print(f"{Fore.GREEN}Path is VALID!{Style.RESET_ALL}")
        configuration[configuration_key] = path_value
        write_configuration_file(configuration)

run_manager(True)
