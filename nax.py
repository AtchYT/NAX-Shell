import importlib
import threading
import time
from tqdm import tqdm

modules_parallel = [
    ("os", None),
    ("re", None),
    ("sys", None),
    ("json", None),
    ("time", None),
    ("shutil", None),
    ("getpass", None),
    ("hashlib", None),
    ("platform", None),
    ("threading", None),                                                                 ("subprocess", None),
    ("urllib.request", "urllib_request"),
    ("tqdm", None),
    ("pyfiglet", None),
    ("datetime", None),
    ("colorama", None),
]

modules_sequential = [
    ("prompt_toolkit.styles", "prompt_toolkit_styles"),                                  ("prompt_toolkit", None),
    ("prompt_toolkit.history", "prompt_toolkit_history"),
    ("prompt_toolkit.completion", "prompt_toolkit_completion"),
    ("prompt_toolkit.formatted_text", "prompt_toolkit_formatted_text")
]

loaded_modules = {}

def load_module(module_name, alias):
    try:
        mod = importlib.import_module(module_name)
        key = alias if alias else module_name.split('.')[0]
        loaded_modules[key] = mod

    except Exception as e:
        print(f"Error loading {module_name}: {e}")

    finally:
        pbar.update(1)

from colorama import init, Fore

init(strip=False, autoreset=True)

CYANtqdm = Fore.LIGHTCYAN_EX
YELLOWtqdm = Fore.YELLOW
                                                                                     desc_bar = f"{CYANtqdm}NAX-Shell · v1.0.0{YELLOWtqdm}"

pbar = tqdm(
    total=16,
    desc=desc_bar,
    ncols=80,
    ascii=True,
    dynamic_ncols=True,
    bar_format="{desc} |{bar}| {percentage:3.0f}%"
)

threads = []
for mod_name, alias in modules_parallel:
    t = threading.Thread(target=load_module, args=(mod_name, alias))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

pbar.close()

for mod_name, alias in modules_sequential:
    try:
        mod = importlib.import_module(mod_name)
        key = alias if alias else mod_name.split('.')[0]
        loaded_modules[key] = mod
    except Exception as e:
        print(f"Error cargando {mod_name}: {e}")

globals().update(loaded_modules)

if "colorama" in loaded_modules:
    init = loaded_modules["colorama"].init
    Fore = loaded_modules["colorama"].Fore

if "prompt_toolkit_styles" in loaded_modules:
    Style = loaded_modules["prompt_toolkit_styles"].Style

if "prompt_toolkit_history" in loaded_modules:
    FileHistory = loaded_modules["prompt_toolkit_history"].FileHistory

if "prompt_toolkit_completion" in loaded_modules:
    WordCompleter = loaded_modules["prompt_toolkit_completion"].WordCompleter
    PathCompleter = loaded_modules["prompt_toolkit_completion"].PathCompleter
    NestedCompleter = loaded_modules["prompt_toolkit_completion"].NestedCompleter

if "prompt_toolkit_formatted_text" in loaded_modules:
    FormattedText = loaded_modules["prompt_toolkit_formatted_text"].FormattedText

init(autoreset=True)
RED, GREEN, YELLOW, CYAN, WHITE, ORANGE = Fore.RED, Fore.GREEN, Fore.LIGHTYELLOW_EX, Fore.LIGHTCYAN_EX, Fore.WHITE, Fore.YELLOW

AUTH_FILE = os.path.join(os.path.expanduser("~"), ".nax_shell_auth")
AUTH_DURATION = 10 * 60
PROCESSOR_NAME = None

def get_processor_name():
    global PROCESSOR_NAME
    if PROCESSOR_NAME is None:
        try:
            if os.name == 'nt' and 'wmi' in globals() and wmi:
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
        process = subprocess.Popen([sys.executable, '-m', 'pip', 'install', *missing],
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
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

        required = {'prompt_toolkit', 'colorama', 'pyfiglet', 'tqdm'}
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

if install_requirements():
    sys.exit(0)

if os.name == 'nt':
    try:
        import wmi
    except ImportError:
        wmi = None
else:
    wmi = None

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

commands, aliases = {}, {}

fitNAXShell = pyfiglet.Figlet(font='mini')
fitNAXVers = pyfiglet.Figlet(font='mini')

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
                print(f"{CYAN}{file}/", end="  ")
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

def cp_command(args):
    if len(args) < 2:
        print("cp: usage: cp <source> <destination>")
        return
    source, destination = args[0], args[1]
    try:
        if os.path.isdir(source):
            if os.path.exists(destination) and not os.path.isdir(destination):
                print(f"{RED}cp: cannot overwrite non-directory '{destination}' with directory '{source}'")
                return
            shutil.copytree(source, destination)
            print(f"{GREEN}Done: {source} to {destination}")
        else:
            shutil.copy2(source, destination)
            print(f"{GREEN}Done: {source} to {destination}")
    except Exception as e:
        print(f"{RED}cp: error copying '{source}' to '{destination}': {e}")

def mv_command(args):
    if len(args) < 2:
        print("mv: usage: mv <source> <destination>")
        return
    source, destination = args[0], args[1]
    try:
        shutil.move(source, destination)
        print(f"{GREEN}Done {source} to {destination}")
    except Exception as e:
        print(f"{RED}mv: error moving '{source}' to '{destination}': {e}")

def pwd_command(args):
    print(os.getcwd())

def clear_command(args):
    clear()

def cat_command(args):
    if not args:
        print("cat: missing file operand")
        return
    for file in args:
        try:
            with open(file, 'r') as f:
                print(f.read())
        except Exception as e:
            print(f"cat: {file}: {e}")

def sysinfo_command(args):
    if PROCESSOR_NAME is None:
        print(f"{YELLOW}Loading information...\n", end='', flush=True)
        get_processor_name()
        print('\033[1A\033[K', end='')
    else:
        get_processor_name()
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
        with urllib_request.urlopen(url) as response:
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
                if stored_hash == user_hash and (datetime.datetime.now().timestamp() - last_auth) < AUTH_DURATION:
                    return True
    except Exception:
        pass
    return False

def update_auth_timestamp():
    try:
        system_user = getpass.getuser()
        user_hash = hashlib.sha256(system_user.encode()).hexdigest()
        with open(AUTH_FILE, "w") as f:
            f.write(f"{user_hash}:{datetime.datetime.now().timestamp()}")
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
                print(f"\n{RED}Sorry, try again.")
                continue
        clear()
        print(f"{RED} Exiting {CYAN}NAX-Shell{RED} | v1.0.0\n════════════════════════════\n")
        print(f"{RED}3 incorrect password attempts")
        return False
    except KeyboardInterrupt:
        print("\nLogin process interrupted.")
        return False

def web_command(args):
    url = "https://atchyt.github.io/nax_shell.html"
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
            print(f"{GREEN}Opening {CYAN}{url}{GREEN} in your browser...")
            webbrowser.open(url)
        except Exception as e:
            print(f"{RED}Could not open browser: {e}")
            print(f"{YELLOW}You can visit manually: {url}")
    else:
        print(f"\n{YELLOW}╔═══════════════════════════════════════════╗")
        print(f"{YELLOW}║ {CYAN}NAX-Shell{YELLOW} | Documentation and Information {YELLOW}║")
        print(f"{YELLOW}╠═══════════════════════════════════════════╣")
        print(f"{YELLOW}║ {GREEN}{url}{YELLOW}  ║")
        print(f"{YELLOW}╚═══════════════════════════════════════════╝\n")

def mkdir_command(args):
    if not args:
        print("mkdir: missing operand")
    else:
        for dir_name in args:
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"{GREEN}Directory created: {dir_name}")
            except Exception as e:
                print(f"{RED}mkdir: cannot create directory '{dir_name}': {e}")

def touch_command(args):
    if not args:
        print("touch: missing file operand")
        return
    for filename in args:
        try:
            if not os.path.exists(filename):
                open(filename, 'a').close()
                print(f"{GREEN}File created: {filename}")
            else:
                os.utime(filename, None)
                print(f"{GREEN}Timestamp updated: {filename}")
        except Exception as e:
            print(f"{RED}touch: cannot create or update '{filename}': {e}")

def rm_command(args):
    if not args:
        print("rm: missing operand")
        return

    recursive = False
    targets = []

    for arg in args:
        if arg == "-r":
            recursive = True
        else:
            targets.append(arg)

    if not targets:
        print("rm: missing operand")
        return

    for target in targets:
        if not os.path.exists(target):
            print(f"{RED}rm: cannot remove '{target}': No such file or directory")
            continue
        try:
            if os.path.isdir(target):
                if recursive:
                    shutil.rmtree(target)
                    print(f"{GREEN}Removed directory: {target}")
                else:
                    print(f"{RED}rm: cannot remove '{target}': Is a directory (use -r to remove directories)")
            else:
                os.remove(target)
                print(f"{GREEN}Removed file: {target}")
        except Exception as e:
            print(f"{RED}rm: error removing '{target}': {e}")

def notepad_command(args):
    if not args:
        print("notepad: missing file operand")
        return
    filename = args[0]
    # Cargar contenido existente si el archivo existe
    content = ""
    if os.path.exists(filename):
        try:
            with open(filename, "r") as f:
                content = f.read()
        except Exception as e:
            print(f"{RED}notepad: cannot open file '{filename}': {e}")
            return

    # Importar las funciones necesarias de prompt_toolkit
    from prompt_toolkit import PromptSession
    from prompt_toolkit.key_binding import KeyBindings

    kb = KeyBindings()
    saved_flag = [False]  # Lista mutable para poder modificarla en el handler

    @kb.add("c-s")
    def _(event):
        "Guarda el archivo mientras editas (Ctrl+S)"
        text = event.app.current_buffer.text
        try:
            with open(filename, "w") as f:
                f.write(text)
            saved_flag[0] = True
            print(f"\n{GREEN}File saved: {filename}")
        except Exception as e:
            print(f"\n{RED}Error saving file '{filename}': {e}")

    @kb.add("c-q")
    def _(event):
        "Sale del editor (Ctrl+Q)"
        event.app.exit(result=event.app.current_buffer.text)

    # Crear la sesión de edición con prompt_toolkit en modo multilinea
    session_editor = PromptSession(
        message=f"{YELLOW}Editing {filename} (Ctrl+S to save, Ctrl+Q to exit)\n",
        key_bindings=kb,
        multiline=True,
        default=content
    )
    try:
        edited_text = session_editor.prompt()
        # Si no se guardó previamente, se guarda al salir
        if not saved_flag[0]:
            with open(filename, "w") as f:
                f.write(edited_text)
            print(f"{GREEN}File saved: {filename}")
    except Exception as e:
        print(f"{RED}notepad: error editing file '{filename}': {e}")

register_command("notepad", notepad_command)
register_command("rm", rm_command)
register_command("touch", touch_command)
register_command("mkdir", mkdir_command)
register_command("md", mkdir_command)
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
register_command("cp", cp_command)
register_command("mv", mv_command)

def set_window_title(title):
    if os.name == 'nt':
        os.system(f'title {title}')
    else:
        print(f'\033]0;{title}\007', end='')

def get_nested_completer():
    path_completer = PathCompleter()
    completer_dict = {cmd: None for cmd in commands.keys()}
    completer_dict.update({
        "cd": PathCompleter(only_directories=True),
        "mkdir": PathCompleter(only_directories=True),
        "md": PathCompleter(only_directories=True),
        "ls": PathCompleter(),
        "cat": PathCompleter(only_directories=False),
        "rm": PathCompleter()
    })
    return NestedCompleter.from_nested_dict(completer_dict)

history_file = os.path.join(os.path.expanduser("~"), ".terminal_history")
completer = WordCompleter(list(commands.keys()) + list(aliases.keys()))

session = loaded_modules["prompt_toolkit"].PromptSession(
    get_prompt,
    style=style,
    completer=get_nested_completer(),
    history=FileHistory(history_file),
    complete_while_typing=True
)

def main():
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
    time.sleep(0.15)
    print(f"{YELLOW}Initializing shell environment...")
    time.sleep(0.15)
    clear()
    print(f"{YELLOW} Loading {CYAN}NAX-Shell{YELLOW} | v1.0.0\n════════════════════════════\n")
    time.sleep(0.08)
    main()