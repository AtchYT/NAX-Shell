import os
import re
import sys
import json
import time
import shutil
import getpass
import hashlib
import platform
import threading
import subprocess
import urllib.request
from pyfiglet import Figlet
from datetime import datetime
from colorama import init, Fore
from prompt_toolkit.styles import Style
from prompt_toolkit import PromptSession                              
from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import WordCompleter, PathCompleter, NestedCompleter
from prompt_toolkit.formatted_text import FormattedText

if os.name == 'nt':
    import wmi

else:
    wmi = None

init(autoreset=True)
RED, GREEN, BLUE, YELLOW, CYAN, WHITE, ORANGE = Fore.RED, Fore.GREEN, Fore.BLUE, Fore.LIGHTYELLOW_EX, Fore.CYAN, Fore.WHITE, Fore.YELLOW
AUTH_FILE = os.path.join(os.path.expanduser("~"), ".nax_shell_auth")
AUTH_DURATION = 10 * 60
PROCESSOR_NAME = None

def get_processor_name():
    global PROCESSOR_NAME
    if PROCESSOR_NAME is None:
        try:                                                                      
            if os.name == 'nt' and wmi:
                w = wmi.WMI()
                processor = w.Win32_Processor()[0]
                PROCESSOR_NAME = processor.Name

            elif os.name == 'posix':
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('model name'):
                            PROCESSOR_NAME = line.split(':', 1)[1].strip()
                            break

            if not PROCESSOR_NAME:
                PROCESSOR_NAME = platform.processor()

        except:
            PROCESSOR_NAME = platform.processor()

    return PROCESSOR_NAME

def install_missing_packages(missing):
    try:
        process = subprocess.Popen([sys.executable, '-m', 'pip', 'install', *missing], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            print(f"{RED}Error installing packages:\n{stderr}")

        else:
            print(stdout)

    except Exception as e:
        print(f"{RED}Error installing packages: {e}")

def install_requirements():
    try:
        try:
            import importlib.metadata as metadata

        except ImportError:
            import importlib_metadata as metadata

        required = {'prompt_toolkit', 'colorama', 'pyfiglet'}
        if os.name == 'nt':
            required.add('wmi')

        installed = {dist.metadata['Name'].lower() for dist in metadata.distributions() if dist.metadata.get('Name')}
        missing = {pkg for pkg in required if pkg.lower() not in installed}

        if missing:
            print(f"{RED}Installing required packages: {', '.join(missing)}")
            thread = threading.Thread(target=install_missing_packages, args=(missing,))
            thread.start()
            thread.join()
            return True
        return False

    except Exception as e:
        print(f"{RED}Error installing packages: {e}")
        sys.exit(1)

install_requirements()
commands, aliases = {}, {}

fitNAXShell = Figlet(font='mini')
fitNAXVers = Figlet(font='mini')

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def register_command(name, func):
    commands[name] = func

def process_command(cmd):
    parts = cmd.split()
    if not parts:
        return

    command, args = parts[0], parts[1:]
    if command in aliases:
        parts = aliases[command].split() + args
        command, args = parts[0], parts[1:]

    if command in commands:
        commands[command](args)

    else:
        print(f"{RED}{command}: command not found")

def get_prompt():
    current_user, hostname, cwd = os.getlogin(), platform.node(), os.getcwd()
    home = os.path.expanduser("~")
    if cwd.startswith(home):
        cwd = cwd.replace(home, "~", 1)

    return FormattedText([
        ('class:username', current_user), ('class:at', '@'),
        ('class:hostname', hostname), ('class:colon', ':'),
        ('class:path', cwd), ('class:prompt', '$ ')
    ])

style = Style.from_dict({
    'username': 'ansigreen',
    'hostname': 'ansigreen',
    'at': 'ansigreen',
    'colon': 'ansiwhite',
    'path': 'ansiblue',
    'prompt': 'ansiwhite',
})

def ls_command(args):
    path = args[0] if args else os.getcwd()
    try:
        for file in os.listdir(path):
            full_path = os.path.join(path, file)
            if os.path.isdir(full_path):
                print(f"{BLUE}{file}/", end="  ")

            elif os.access(full_path, os.X_OK):
                print(f"{GREEN}{file}*", end="  ")

            else:
                print(f"{WHITE}{file}", end="  ")
        print()

    except Exception as e:
        print(f"{RED}ls: cannot access '{path}': {str(e)}")

def cd_command(args):
    try:
        os.chdir(args[0] if args else os.path.expanduser("~"))

    except Exception as e:
        print(f"cd: {args[0] if args else '~'}: {e}")

def pwd_command(args):
    print(os.getcwd())

def clear_command(args):
    os.system('cls' if os.name == 'nt' else 'clear')

def cat_command(args):
    if not args:
        print("cat: usage: cat <file>")
        return

    try:
        with open(args[0], 'r') as f:
            print(f.read())

    except Exception as e:
        print(f"cat: {args[0]}: {e}")

def sysinfo_command(args):
    print(f"{YELLOW}OS: {platform.system()} {platform.release()}")
    print(f"{YELLOW}Machine: {platform.machine()}")
    print(f"{YELLOW}Processor: {get_processor_name()}")

    if os.name == 'posix':
        try:
            with open('/proc/meminfo', 'r') as f:
                mem_info = f.readline()
                print(f"{YELLOW}Memory: {mem_info.split(':')[1].strip()}")

        except:
            pass

def help_command(args):
    print("Available commands:")
    for cmd in sorted(commands.keys()):
        print(f"  {cmd}")
    print("\nUse 'exit' to quit the terminal")

def exit_command(args):
    raise SystemExit

def logout_command(args):
    if os.path.exists(AUTH_FILE):
        try:
            os.remove(AUTH_FILE)
            clear()
            print(f"{GREEN}Logged out successfully.")
            time.sleep(2)

        except Exception as e:
            print(f"{RED}Error during logout: {e}")

    else:
        print(f"{YELLOW}No active session to logout.")

    clear()
    sys.exit(0)

def get_api_password():
    try:
        url = "https://atchyt.github.io/api.html"
        with urllib.request.urlopen(url) as response:
            content = response.read().decode('utf-8')
        match = re.search(r'<div id="users"[^>]*>(.*?)</div>', content, re.DOTALL)
        if match:
            try:
                users = json.loads(match.group(1).strip())
                system_user = os.getlogin()
                return users.get(system_user, "")

            except json.JSONDecodeError as e:
                print(f"{RED}Invalid user data format: {e}")
                sys.exit(1)

        else:
            print(f"{RED}User data not found in API response")
            sys.exit(1)

    except Exception as e:
        print(f"{RED}API Error: {e}")
        sys.exit(1)

def is_recent_auth():
    try:
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, "r") as f:
                data = f.read().strip()
                if ":" not in data:
                    return False

                stored_hash, timestamp_str = data.split(":")
                last_auth = float(timestamp_str)

                system_user = getpass.getuser()
                user_hash = hashlib.sha256(system_user.encode()).hexdigest()

                if stored_hash == user_hash and (datetime.now().timestamp() - last_auth) < AUTH_DURATION:
                    return True
                    
    except Exception:
        pass

    return False

def update_auth_timestamp():
    try:
        system_user = getpass.getuser()
        user_hash = hashlib.sha256(system_user.encode()).hexdigest()

        with open(AUTH_FILE, "w") as f:
            f.write(f"{user_hash}:{datetime.now().timestamp()}")
            
    except Exception:
        pass

def login():
    try:
        if is_recent_auth():
            return True

        api_password = get_api_password()

        if not api_password:
            print(f"{RED}Error: Cannot get the user from the API")
            return False

        print(f"{ORANGE}Authentication Required")
        current_user = getpass.getuser()

        for _ in range(3):
            try:
                user_input = getpass.getpass(f"Password for {current_user}: ")

                if not user_input:
                    print(f"{RED}Sorry, try again.")
                    continue

                if user_input == api_password:
                    update_auth_timestamp()
                    return True

                print(f"{RED}Sorry, try again.")

            except KeyboardInterrupt:
                print(f"\n{RED}Login interrupted. Please try again.")
                continue

        clear()
        print(f"{RED} Exiting {CYAN}NAX-Shell{RED} | v1.0.0\n════════════════════════════\n")
        print(f"{RED}3 incorrect password attempts")
        return False

    except KeyboardInterrupt:
        print("\nLogin process interrupted.")
        return False

def web_command(args):
    url = "https://atchyt.github.com/nax_shell.html"

    is_windows = os.name == 'nt'
    is_termux = 'com.termux' in os.environ.get('PREFIX', '')

    has_gui = False

    if is_windows:
        has_gui = True
        try:
            if wmi:
                w = wmi.WMI()
                os_info = w.Win32_OperatingSystem()[0]
                if 'Core' in os_info.Caption and 'Server' in os_info.Caption:
                    has_gui = False
        except:
            pass
    elif is_termux:
        has_gui = os.environ.get('DISPLAY', '') != '' or os.environ.get('XDG_SESSION_TYPE', '') != ''

    else:
        has_gui = os.environ.get('DISPLAY', '') != '' or os.environ.get('WAYLAND_DISPLAY', '') != ''

    if has_gui:
        try:
            import webbrowser
            print(f"{GREEN}Opening {url} in your browser...")
            webbrowser.open(url)

        except Exception as e:
            print(f"{RED}Could not open browser: {e}")
            print(f"{YELLOW}You can visit manually: {url}")

    else:
        print(f"\n{CYAN}╔═══════════════════════════════════════════╗")
        print(f"{CYAN}║ {YELLOW}NAX Shell - Documentation and Information {CYAN}║")
        print(f"{CYAN}╠═══════════════════════════════════════════╣")
        print(f"{CYAN}║ {GREEN}{url}{CYAN}  ║")
        print(f"{CYAN}╚═══════════════════════════════════════════╝\n")

register_command("ls", ls_command)
register_command("cd", cd_command)
register_command("pwd", pwd_command)
register_command("cat", cat_command)
register_command("cls", clear_command)
register_command("clear", clear_command)
register_command("sysinfo", sysinfo_command)
register_command("web", web_command)
register_command("help", help_command)
register_command("exit", exit_command)
register_command("logout", logout_command)

def set_window_title(title):
    if os.name == 'nt':
        os.system(f'title {title}')

    else:
        print(f'\033]0;{title}\007', end='')

def get_nested_completer():
    path_completer = PathCompleter(only_directories=True)

    completer_dict = {cmd: None for cmd in commands.keys()}
    completer_dict.update({alias: None for alias in aliases.keys()})

    completer_dict['cd'] = path_completer

    completer_dict['ls'] = path_completer

    return NestedCompleter.from_nested_dict(completer_dict)

history_file = os.path.join(os.path.expanduser("~"), ".terminal_history")
completer = WordCompleter(list(commands.keys()) + list(aliases.keys()))

session = PromptSession(
    get_prompt,
    style=style,
    completer=get_nested_completer(),
    history=FileHistory(history_file),
    complete_while_typing=True
)

def main():
    get_processor_name()
    global session
    if not login():
        return

    clear()
    set_window_title('NAX-Shell · v1.0.0')
    print(f"{CYAN}{fitNAXShell.renderText('NAX-Shell')}")
    print(f"{CYAN}{fitNAXVers.renderText('v 1.0.0')}")
    print(f"{YELLOW}Platform: {platform.system()} {platform.release()}")
    print(f"{GREEN}Type 'help' for available commands")
    print(f"{GREEN}For more help, type 'web'\n")

    while True:
        try:
            process_command(session.prompt())

        except (KeyboardInterrupt, EOFError, SystemExit):
            break

        except Exception as e:
            print(f"{RED}An error occurred: {str(e)}")

if __name__ == "__main__":
    clear()
    print(f"{YELLOW}Starting {CYAN}NAX-Shell{YELLOW} | v1.0.0")
    time.sleep(0.75)
    print(f"{YELLOW}Initializing shell environment...")
    time.sleep(0.75)
    clear()
    print(f"{YELLOW} Loading {CYAN}NAX-Shell{YELLOW} | v1.0.0\n════════════════════════════\n")
    time.sleep(0.25)
    main()
