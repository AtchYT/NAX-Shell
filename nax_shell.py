import os
import time
import importlib
import threading
from colorama import init, Fore

try:
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad, unpad
    
except ImportError:
    pass

modules_parallel = [
    ("rsa", None),
    ("secrets", None),
    ("base64", None),
    ("zlib", None),
    ("queue", None),
    ("re", None),
    ("sys", None),
    ("json", None),
    ("math", None),
    ("yaml", None),
    ("socket", None),
    ("psutil", None),
    ("shutil", None),
    ("getpass", None),
    ("tarfile", None),
    ("fnmatch", None),
    ("hashlib", None),
    ("zipfile", None),
    ("difflib", None),
    ("pyfiglet", None),
    ("markdown", None),
    ("datetime", None),
    ("platform", None),
    ("threading", None),
    ("subprocess", None),
    ("collections", None),    
    ("urllib.request", "urllib_request"),
]

modules_sequential = [
    ("prompt_toolkit", None),
    ("prompt_toolkit.styles", "prompt_toolkit_styles"),
    ("prompt_toolkit.history", "prompt_toolkit_history"),
    ("prompt_toolkit.shortcuts", "prompt_toolkit_shortcuts"),
    ("prompt_toolkit.completion", "prompt_toolkit_completion"),
    ("prompt_toolkit.formatted_text", "prompt_toolkit_formatted_text")
]

loaded_modules = {}

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

clear()

def load_module(module_name, alias):
    try:
        mod = importlib.import_module(module_name)
        key = alias if alias else module_name.split('.')[0]
        loaded_modules[key] = mod

    except Exception as e:
        print(f"Error loading {module_name}: {e}")

init(strip=False, autoreset=True)

RED, GREEN, YELLOW, CYAN, WHITE, ORANGE = Fore.RED, Fore.GREEN, Fore.LIGHTYELLOW_EX, Fore.LIGHTCYAN_EX, Fore.WHITE, Fore.YELLOW

threads = []

for mod_name, alias in modules_parallel:
    t = threading.Thread(target=load_module, args=(mod_name, alias))
    threads.append(t)
    t.start()

for t in threads:
    t.join()

for mod_name, alias in modules_sequential:
    try:
        mod = importlib.import_module(mod_name)
        key = alias if alias else mod_name.split('.')[0]
        loaded_modules[key] = mod

    except Exception as e:
        print(f"Error loading {mod_name}: {e}")

globals().update(loaded_modules)

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

nax_dir = os.path.join(os.path.expanduser("~"), ".NAX-Shell")
if not os.path.exists(nax_dir):
    os.makedirs(nax_dir)

HISTORY_FILE = os.path.join(nax_dir, ".nax_shell_history")
ALIAS_FILE = os.path.join(nax_dir, ".nax_shell_aliases")
AUTH_FILE = os.path.join(nax_dir, ".nax_shell_auth")
AUTH_DURATION = 30 * 60
AUTH_LAST_ACTIVE = None
PROCESSOR_NAME = None

def update_remaining_auth_time():
    try:
        if os.path.exists(AUTH_FILE) and AUTH_LAST_ACTIVE is not None:
            with open(AUTH_FILE, "r") as f:
                data = f.read().strip()
                
            parts = data.split(":")
            if len(parts) < 3:
                return
                
            stored_hash, last_timestamp, remaining_time = parts
            
            current_time = datetime.datetime.now().timestamp()
            session_duration = current_time - AUTH_LAST_ACTIVE
            
            new_remaining = max(0, float(remaining_time) - session_duration)
            
            with open(AUTH_FILE, "w") as f:
                f.write(f"{stored_hash}:{current_time}:{new_remaining}")
                
    except Exception as e:
        print(f"{RED}Auth time update error: {e}")
        pass

def update_auth_timestamp():
    try:
        system_user = getpass.getuser()
        user_hash = hashlib.sha256(system_user.encode()).hexdigest()
        current_time = datetime.datetime.now().timestamp()
        
        global AUTH_LAST_ACTIVE
        AUTH_LAST_ACTIVE = current_time
        
        with open(AUTH_FILE, "w") as f:
            f.write(f"{user_hash}:{current_time}:{AUTH_DURATION}")
            
    except Exception as e:
        print(f"{RED}Auth timestamp update error: {e}")
        pass

def get_api_url():
    def download_in_background():
        try:
            url = "https://raw.githubusercontent.com/AtchYT/NAX-Shell/main/README.md"
            readme_path = os.path.join(nax_dir, "README.md")

            with urllib_request.urlopen(url) as response:
                remote_content = response.read()

            if os.path.exists(readme_path):
                try:
                    with open(readme_path, 'rb') as f:
                        local_content = f.read()

                    if local_content != remote_content:
                        with open(readme_path, 'wb') as f:
                            f.write(remote_content)

                except Exception:
                    with open(readme_path, 'wb') as f:
                        f.write(remote_content)

            else:
                with open(readme_path, 'wb') as f:
                    f.write(remote_content)

        except Exception as e:
            print(f"{RED}API Error: {e}")

    download_thread = threading.Thread(target=download_in_background)
    download_thread.daemon = True
    download_thread.start()

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
        required = {'prompt_toolkit', 'colorama', 'pyfiglet', 'tqdm', 'rarfile', 'markdown', 'pyyaml', 'psutil', 'rsa'}
        
        try:
            import importlib.metadata as metadata

        except ImportError:
            import importlib_metadata as metadata

        if platform.system() == 'Windows':
            required.add('wmi')

        installed = {dist.metadata['Name'].lower() for dist in metadata.distributions() if dist.metadata.get('Name')}
        missing = {pkg for pkg in required if pkg.lower() not in installed}

        if missing:
            clear()
            print(f"{RED}Installing required packages: {', '.join(missing)}")
            thread = threading.Thread(target=install_missing_packages, args=(missing,))
            thread.start()
            thread.join()
            print(f"{GREEN}Packages installed successfully")
            print(f"{CYAN}Please run the script again to continue.")
            time.sleep(2)
            sys.exit(0)

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

commands, aliases = {}, {}

fitNAXShell = pyfiglet.Figlet(font='mini')
fitNAXVers = pyfiglet.Figlet(font='mini')

def register_command(name, func):
    commands[name] = func

def process_command(cmd):
    if not cmd.strip():
        return

    if ';' in cmd:
        commands_to_run = cmd.split(';')
        for single_cmd in commands_to_run:
            if single_cmd.strip():
                process_command(single_cmd.strip())
        return

    if '&&' in cmd:
        commands_to_run = cmd.split('&&')
        for single_cmd in commands_to_run:
            if single_cmd.strip():
                result = execute_single_command(single_cmd.strip())
                if not result:
                    break
        return

    if '|' in cmd:
        commands_to_run = cmd.split('|')
        for single_cmd in commands_to_run:
            if single_cmd.strip():
                execute_single_command(single_cmd.strip())
        return

    execute_single_command(cmd)

def execute_single_command(cmd):
    parts = cmd.split()
    if not parts:
        return True

    command, args = parts[0], parts[1:]
    if command in aliases:
        parts = aliases[command].split() + args
        command, args = parts[0], parts[1:]

    if command in commands:
        try:
            commands[command](args)
            return True

        except Exception as e:
            print(f"{RED}Error executing '{command}': {str(e)}")
            return False

    else:
        print(f"{RED}{command}: command not found")
        return False

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

def update_completer():
    global completer, session
    completer = WordCompleter(list(commands.keys()) + list(aliases.keys()))
    
    if 'session' in globals():
        session = loaded_modules["prompt_toolkit_shortcuts"].PromptSession(
            get_prompt,
            style=style,
            completer=get_nested_completer(),
            history=FileHistory(HISTORY_FILE),
            complete_while_typing=True
        )

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
    if not args:
        os.chdir(os.path.expanduser("~"))
        update_completer()
        return
    
    try:
        path = os.path.normpath(args[0])
        os.chdir(path)
        update_completer()

    except Exception as e:
        print(f"{RED}cd: {e}")

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
            print(f"{WHITE}Done: {source} to {destination}")

        else:
            shutil.copy2(source, destination)
            print(f"{WHITE}Done: {source} to {destination}")

    except Exception as e:
        print(f"{RED}cp: error copying '{source}' to '{destination}': {e}")

def mv_command(args):
    if len(args) < 2:
        print("mv: usage: mv <source> <destination>")
        return

    source, destination = args[0], args[1]

    try:
        shutil.move(source, destination)
        print(f"{WHITE}Done {source} to {destination}")

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

    os_info = f"{YELLOW}OS: {platform.system()} {platform.release()}"
    kernel_info = f"{YELLOW}Kernel: {platform.version()}"
    machine_info = f"{YELLOW}Machine: {platform.machine()}"
    processor_info = f"{YELLOW}Processor: {get_processor_name()}"

    memory_info = ""
    if os.name == 'posix':
        try:
            with open('/proc/meminfo', 'r') as f:
                mem_total = int(f.readline().split()[1]) // 1024
                mem_free = int(f.readline().split()[1]) // 1024
                mem_used = mem_total - mem_free
                memory_info = f"{YELLOW}Memory: {mem_used}MB / {mem_total}MB"
        except:
            memory_info = f"{YELLOW}Memory: Not available"

    def get_uptime():
        if platform.system() == "Windows":
            try:
                import psutil
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                return uptime_seconds

            except ImportError:
                return None

        elif platform.system() in ["Linux", "Darwin"]:
            try:
                with open('/proc/uptime', 'r') as f:
                    uptime_seconds = float(f.readline().split()[0])
                    return uptime_seconds

            except (FileNotFoundError, PermissionError):
                try:
                    uptime_output = subprocess.check_output(['uptime', '-p']).decode('utf-8').strip()
                    if uptime_output.startswith("up"):
                        uptime_str = uptime_output[3:]
                        days, hours, minutes = 0, 0, 0
                        if "day" in uptime_str:
                            days = int(uptime_str.split(" day")[0])
                            uptime_str = uptime_str.split(", ")[1] if ", " in uptime_str else ""
                        if "hour" in uptime_str:
                            hours = int(uptime_str.split(" hour")[0])
                            uptime_str = uptime_str.split(", ")[1] if ", " in uptime_str else ""
                        if "minute" in uptime_str:
                            minutes = int(uptime_str.split(" minute")[0])
                        uptime_seconds = days * 86400 + hours * 3600 + minutes * 60
                        return uptime_seconds

                except Exception:
                    return None
        else:
            return None

    def format_uptime(uptime_seconds):
        if uptime_seconds is None:
            return "Not available"
        uptime_days = int(uptime_seconds // (3600 * 24))
        uptime_hours = int((uptime_seconds % (3600 * 24)) // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        return f"{uptime_days}d {uptime_hours}h {uptime_minutes}m"

    uptime_seconds = get_uptime()
    uptime_info = f"{YELLOW}Uptime: {format_uptime(uptime_seconds)}"

    resolution_info = ""
    if os.name == 'nt':
        try:
            import ctypes
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)
            resolution_info = f"{YELLOW}Resolution: {width}x{height}"

        except:
            resolution_info = f"{YELLOW}Resolution: Not available"
    elif os.name == 'posix':
        try:
            import subprocess
            output = subprocess.check_output(['termux-display']).decode('utf-8')
            for line in output.splitlines():
                if 'Physical size' in line:
                    resolution = line.split(':')[1].strip()
                    resolution_info = f"{YELLOW}Resolution: {resolution}"
                    break

        except:
            resolution_info = f"{YELLOW}Resolution: Not available"

    shell_info = f"{YELLOW}Shell: {os.environ.get('SHELL', 'Not available')}"
    terminal_info = f"{YELLOW}Terminal: {os.environ.get('TERM', 'Not available')}"

    print(f"{CYAN}════════════════════════════════════════════")
    print(f"{CYAN}NAX-Shell System Information")
    print(f"{CYAN}════════════════════════════════════════════")
    print(os_info)
    print(kernel_info)
    print(machine_info)
    print(processor_info)
    print(memory_info)
    print(uptime_info)
    print(resolution_info)
    print(shell_info)
    print(terminal_info)

def help_command(args):
    print("Available commands:")
    for cmd in sorted(commands.keys()):
        print(f"  {cmd}")

    print("\nUse 'exit' to quit the terminal")

def exit_command(args):
    update_remaining_auth_time()
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
                update_remaining_auth_time()
                sys.exit(1)

        else:
            print(f"{RED}User data not found in API response")
            update_remaining_auth_time()
            sys.exit(1)

    except Exception as e:
        print(f"{RED}API Error: {e}")
        update_remaining_auth_time()
        sys.exit(1)

def is_recent_auth():
    try:
        if os.path.exists(AUTH_FILE):
            with open(AUTH_FILE, "r") as f:
                data = f.read().strip()
                if ":" not in data:
                    return False
                
                parts = data.split(":")
                if len(parts) < 3:
                    return False
                    
                stored_hash, last_timestamp, remaining_time = parts
                last_auth = float(last_timestamp)
                remaining_seconds = float(remaining_time)
                
                system_user = getpass.getuser()
                user_hash = hashlib.sha256(system_user.encode()).hexdigest()
                
                if stored_hash == user_hash and remaining_seconds > 0:
                    global AUTH_LAST_ACTIVE
                    AUTH_LAST_ACTIVE = datetime.datetime.now().timestamp()
                    return True

    except Exception as e:
        print(f"{RED}Auth error: {e}")
        pass

    return False
    
def update_remaining_auth_time():
    try:
        if os.path.exists(AUTH_FILE) and AUTH_LAST_ACTIVE is not None:
            with open(AUTH_FILE, "r") as f:
                data = f.read().strip()
                
            parts = data.split(":")
            if len(parts) < 3:
                return
                
            stored_hash, last_timestamp, remaining_time = parts
            
            current_time = datetime.datetime.now().timestamp()
            session_duration = current_time - AUTH_LAST_ACTIVE
            
            new_remaining = max(0, float(remaining_time) - session_duration)
            
            with open(AUTH_FILE, "w") as f:
                f.write(f"{stored_hash}:{current_time}:{new_remaining}")
                
    except Exception as e:
        print(f"{RED}Auth time update error: {e}")
        pass

def login():
    try:
        if is_recent_auth():
            return True

        api_password = get_api_password()

        if not api_password:
            print(f"{RED}Error: Cannot get the user from the API")
            return False

        print(f"{CYAN}{fitNAXShell.renderText('NAX-Shell | BETA')}")
        print(f"{CYAN}{fitNAXVers.renderText('v 1.0.0')}")
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
        print(f"{RED} Exiting {CYAN}NAX-Shell · BETA{RED} | v1.0.0\n════════════════════════════\n")
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
        print(f"\n{YELLOW}╔════════════════════════════════════════════╗")
        print(f"{YELLOW}║ {CYAN}NAX-Shell{YELLOW} | Documentation and Information {YELLOW}║")
        print(f"{YELLOW}╠══════════════════════════════════════════════╣")
        print(f"{YELLOW}║ {GREEN}{url}{YELLOW}  ║")
        print(f"{YELLOW}╚═══════════════════════════════════════════╝\n")

def mkdir_command(args):
    if not args:
        print("mkdir: missing operand")

    else:
        for dir_name in args:
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"{WHITE}Directory created: {dir_name}")

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
                print(f"{WHITE}File created: {filename}")
            else:
                print(f"{YELLOW}File already exists: {filename}")

        except Exception as e:
            print(f"{RED}touch: cannot create '{filename}': {e}")

def rm_command(args):
    if not args:
        print(f"{WHITE}rm: missing operand")
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
                    print(f"{WHITE}Removed directory: {target}")

                else:
                    print(f"{RED}rm: cannot remove '{target}': Is a directory (use -r to remove directories)")

            else:
                os.remove(target)
                print(f"{WHITE}Removed file: {target}")

        except Exception as e:
            print(f"{RED}rm: error removing '{target}': {e}")

def chmod_command(args):
    if len(args) < 2:
        print("chmod: usage: chmod <mode> <file>")
        return

    mode, *files = args

    try:
        if any(symbol in mode for symbol in ('+', '-', '=')):
            current_mode = os.stat(files[0]).st_mode

            if '+x' in mode:
                new_mode = current_mode | 0o111

            elif '-x' in mode:
                new_mode = current_mode & ~0o111

            else:
                print(f"{RED}chmod: unsupported symbolic mode: '{mode}'")
                return

            for file in files:
                try:
                    os.chmod(file, new_mode)
                    print(f"{WHITE}Mode changed for {file}")

                except Exception as e:
                    print(f"{RED}chmod: cannot change mode of '{file}': {e}")

        else:
            mode_int = int(mode, 8)
            for file in files:
                try:
                    os.chmod(file, mode_int)
                    print(f"{WHITE}Mode changed for {file}")

                except Exception as e:
                    print(f"{RED}chmod: cannot change mode of '{file}': {e}")

    except ValueError:
        print(f"{RED}chmod: invalid mode: '{mode}'")

def echo_command(args):
    print(" ".join(args))

def grep_command(args):
    if len(args) < 2:
        print("grep: usage: grep <pattern> <file>")
        return

    pattern = args[0]
    files = args[1:]

    try:
        regex = re.compile(pattern)
        for file in files:
            try:
                with open(file, 'r') as f:
                    for i, line in enumerate(f, 1):
                        if regex.search(line):
                            print(f"{file}:{i}: {line.rstrip()}")

            except Exception as e:
                print(f"{RED}grep: {file}: {e}")

    except re.error as e:
        print(f"{RED}grep: invalid pattern: {e}")

def find_command(args):
    if not args:
        args = ['.']

    root = args[0]
    pattern = args[1] if len(args) > 1 else '*'

    try:
        for path, dirs, files in os.walk(root):
            for item in dirs + files:
                if fnmatch.fnmatch(item, pattern):
                    print(os.path.join(path, item))

    except Exception as e:
        print(f"{RED}find: error: {e}")

calc_safe = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'pow': pow,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'pi': math.pi,
    'e': math.e,
    'factorial': math.factorial,
}

calc_completer = WordCompleter(list(calc_safe.keys()) + ['+', '-', '*', '/', '**', '(', ')', '[', ']', '{', '}', '==', '!=', '<', '>', '<=', '>='])

def calc_command(args):
    session_calc = loaded_modules["prompt_toolkit_shortcuts"].PromptSession("calc> ", completer=calc_completer)
    while True:
        try:
            expr = session_calc.prompt()
            if expr.strip().lower() in ['exit', 'quit']:
                break

            if not expr.strip():
                continue

            parts = expr.split()
            if parts:
                if parts[0] not in calc_safe:
                    print(f"{RED}calc: error: '{parts[0]}' is not a valid function or constant")
                    continue

                func_name = parts[0]
                func = calc_safe[func_name]

                if callable(func):
                    if len(parts) == 1:
                        print(f"{RED}calc: error: Function '{func_name}' requires arguments")
                        continue
                    else:
                        args_str = ", ".join(parts[1:])
                        expr = f"{func_name}({args_str})"
                else:
                    expr = func_name

            result = eval(expr, {"__builtins__": None}, calc_safe)
            print(result)

        except SyntaxError:
            print(f"{RED}calc: error: Invalid syntax")

        except Exception as e:
            print(f"{RED}calc: error: {e}")

def history_command(args):
    try:
        with open(HISTORY_FILE, "r") as f:
            print(f.read())

    except Exception as e:
        print(f"history: error reading history: {e}")

def curl_command(args):
    if not args:
        print("curl: usage: curl <url>")
        return

    url = args[0]
    try:
        with urllib_request.urlopen(url) as response:
            content = response.read().decode('utf-8')
            print(content)
    except Exception as e:
        print(f"{RED}curl: error: {e}")

def ping_command(args):
    if not args:
        print("ping: usage: ping <host>")
        return

    host = args[0]
    count = 4

    if "-c" in args and args.index("-c") < len(args) - 1:
        try:
            count = int(args[args.index("-c") + 1])
        except ValueError:
            print(f"{RED}ping: invalid count value")
            return

    try:
        ip_address = None
        try:
            with urllib_request.urlopen(f"http://{host}", timeout=2) as response:
                ip_address = response.geturl().split('/')[2].split(':')[0]

        except:
            pass

        if not ip_address or ip_address == host:
            import socket
            ip_address = socket.gethostbyname(host)

        print(f"PING {host} ({ip_address})")
    except Exception as e:
        print(f"PING {host} ({host})")

    success = 0
    for i in range(count):
        try:
            start_time = time.time()
            urllib_request.urlopen(f"http://{host}", timeout=2)
            elapsed = (time.time() - start_time) * 1000
            print(f"64 bytes from {host}: icmp_seq={i+1} ttl=64 time={elapsed:.2f} ms")
            success += 1
            time.sleep(1)

        except Exception:
            print(f"Request timeout for icmp_seq {i+1}")

    print(f"\n--- {host} ping statistics ---")
    loss = 100 - (success / count * 100)
    print(f"{count} packets transmitted, {success} received, {loss:.1f}% packet loss")

def wget_command(args):
    if not args:
        print("wget: usage: wget <url> [output_file]")
        return

    url = args[0]
    output_file = args[1] if len(args) > 1 else url.split('/')[-1]
    if not output_file:
        output_file = "index.html"

    try:
        print(f"Downloading {url} to {output_file}...")
        with urllib_request.urlopen(url) as response:
            content = response.read()
            with open(output_file, 'wb') as f:
                f.write(content)
            print(f"{GREEN}Download complete: {output_file}")

    except Exception as e:
        print(f"{RED}wget: error: {e}")

def kill_command(args):
    if not args:
        print("kill: usage: kill <pid>")
        return

    try:
        pid = int(args[0])
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(pid), '/F'], check=True)
            print(f"{GREEN}Process with PID {pid} terminated")

        else:
            os.kill(pid, 9)
            print(f"{GREEN}Process with PID {pid} terminated")

    except ValueError:
        print(f"{RED}kill: invalid process id: {args[0]}")

    except subprocess.CalledProcessError as e:
        print(f"{RED}kill: error: {e}")

    except Exception as e:
        print(f"{RED}kill: error: {e}")

def whoami_command(args):
    try:
        print(os.getlogin())

    except Exception as e:
        print(f"{RED}whoami: error: {e}")

def date_command(args):
    try:
        print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    except Exception as e:
        print(f"{RED}date: error: {e}")

def df_command(args):
    try:
        if os.name == 'nt':
            process = subprocess.Popen(['wmic', 'logicaldisk', 'get', 'deviceid,size,freespace'],
                                      stdout=subprocess.PIPE, text=True)
            output, _ = process.communicate()
            print(output)

        else:
            process = subprocess.Popen(['df', '-h'], stdout=subprocess.PIPE, text=True)
            output, _ = process.communicate()
            print(output)

    except Exception as e:
        print(f"{RED}df: error: {e}")

def ps_command(args):
    try:
        if os.name == 'nt':
            process = subprocess.Popen(['tasklist'], stdout=subprocess.PIPE, text=True)
            output, _ = process.communicate()
            print(output)

        else:
            process = subprocess.Popen(['ps', 'aux'], stdout=subprocess.PIPE, text=True)
            output, _ = process.communicate()
            print(output)

    except Exception as e:
        print(f"{RED}ps: error: {e}")

def load_aliases():
    global aliases
    try:
        if os.path.exists(ALIAS_FILE):
            with open(ALIAS_FILE, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and '=' in line:
                        alias, command = line.split('=', 1)
                        aliases[alias] = command
    except Exception as e:
        print(f"{RED}Error loading aliases: {e}")

def save_aliases():
    try:
        with open(ALIAS_FILE, 'w') as f:
            for alias, command in aliases.items():
                f.write(f"{alias}={command}\n")
    except Exception as e:
        print(f"{RED}Error saving aliases: {e}")

def alias_command(args):
    if not args:
        if not aliases:
            print("No aliases defined")
            print("Use alias terminal=replace to define an alias")
        else:
            for alias, command in aliases.items():
                print(f"{alias}='{command}'")
        return

    if len(args) == 1 and '=' not in args[0]:
        alias = args[0]
        if alias in aliases:
            print(f"{alias}='{aliases[alias]}'")
        else:
            print(f"alias: {alias}: not found")
        return

    for arg in args:
        if '=' in arg:
            alias, command = arg.split('=', 1)
            aliases[alias] = command
            print(f"Alias set: {alias}='{command}'")
            save_aliases()
            update_completer()

        else:
            print(f"alias: invalid format: {arg}")

def unalias_command(args):
    if not args:
        print("unalias: usage: unalias <name>")
        print("Use unalias terminal=replace to define an alias")
        return

    for alias in args:
        if alias in aliases:
            del aliases[alias]
            print(f"Alias removed: {alias}")
            save_aliases()
            update_completer()

        else:
            print(f"unalias: {alias}: not found")

def diff_command(args):
    if len(args) != 2:
        print("diff: usage: diff <file1> <file2>")
        return
    
    file1, file2 = args[0], args[1]
    try:
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            diff = difflib.unified_diff(
                f1.readlines(),
                f2.readlines(),
                fromfile=file1,
                tofile=file2,
            )
            for line in diff:
                print(line, end='')
    except Exception as e:
        print(f"{RED}diff error: {e}")

def netinfo_command(args):
    try:
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        print(f"{CYAN}Network Information")
        print(f"{YELLOW}Hostname: {hostname}")
        print(f"{YELLOW}IP Address: {ip_address}")
    except Exception as e:
        print(f"{RED}netinfo error: {e}")

def monitor_command(args):
    try:
        import psutil
        print(f"{CYAN}System Monitoring")
        print(f"{YELLOW}CPU Usage: {psutil.cpu_percent()}%")
        print(f"{YELLOW}Memory Usage: {psutil.virtual_memory().percent}%")
        print(f"{YELLOW}Disk Usage: {psutil.disk_usage('/').percent}%")
    except ImportError:
        print(f"{RED}psutil package not installed. Run 'pip install psutil'")
    except Exception as e:
        print(f"{RED}monitor error: {e}")

def zip_command(args):
    if len(args) < 2:
        print("zip: usage: zip <output> <file1> [file2 ...]")
        return
    
    output = args[0]
    files = args[1:]
    
    try:
        if output.endswith('.zip'):
            with zipfile.ZipFile(output, 'w') as zipf:
                for file in files:
                    if os.path.isdir(file):
                        for root, dirs, files in os.walk(file):
                            for f in files:
                                zipf.write(os.path.join(root, f))
                    else:
                        zipf.write(file)
        elif output.endswith('.tar.gz') or output.endswith('.tgz'):
            with tarfile.open(output, 'w:gz') as tarf:
                for file in files:
                    tarf.add(file)
        elif output.endswith('.tar'):
            with tarfile.open(output, 'w:') as tarf:
                for file in files:
                    tarf.add(file)
        else:
            print(f"{RED}Unsupported output format: {output}")
            return
            
        print(f"{GREEN}Created {output} successfully")
    except Exception as e:
        print(f"{RED}Error creating archive: {e}")

def unzip_command(args):
    if len(args) < 1:
        print("unzip: usage: unzip <archive> [destination]")
        return
    
    archive = args[0]
    destination = args[1] if len(args) > 1 else os.path.splitext(archive)[0]
    
    try:
        if archive.endswith('.zip'):
            with zipfile.ZipFile(archive, 'r') as zip_ref:
                zip_ref.extractall(destination)
        elif archive.endswith('.tar.gz') or archive.endswith('.tgz'):
            with tarfile.open(archive, 'r:gz') as tar_ref:
                tar_ref.extractall(destination)
        elif archive.endswith('.tar'):
            with tarfile.open(archive, 'r:') as tar_ref:
                tar_ref.extractall(destination)
        elif archive.endswith('.rar'):
            try:
                import rarfile
                with rarfile.RarFile(archive) as rar_ref:
                    rar_ref.extractall(destination)
            except ImportError:
                print(f"{RED}rarfile package not installed. Run 'pip install rarfile'")
                return
        else:
            print(f"{RED}Unsupported archive format: {archive}")
            return
            
        print(f"{GREEN}Extracted {archive} to {destination}")
    except Exception as e:
        print(f"{RED}Error extracting {archive}: {e}")

def search_command(args):
    if len(args) < 2:
        print("search: usage: search <directory> <pattern>")
        return
    
    directory, pattern = args[0], args[1]
    try:
        for root, dirs, files in os.walk(directory):
            for name in files + dirs:
                if fnmatch.fnmatch(name, pattern):
                    print(os.path.join(root, name))
    except Exception as e:
        print(f"{RED}search error: {e}")

def checksum_command(args):
    if len(args) < 1:
        print("checksum: usage: checksum <file> [algorithm]")
        print("Available algorithms: md5, sha1, sha256 (default)")
        return
    
    file = args[0]
    algorithm = args[1] if len(args) > 1 else "sha256"
    
    try:
        hash_func = getattr(hashlib, algorithm)()
        with open(file, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        print(f"{algorithm.upper()} checksum: {hash_func.hexdigest()}")
    except AttributeError:
        print(f"{RED}Invalid algorithm: {algorithm}")
    except Exception as e:
        print(f"{RED}Error calculating checksum: {e}")

def convert_command(args):
    if len(args) < 2:
        print("convert: usage: convert <input> <output>")
        print("Supported conversions: txt -> md, md -> html, json -> yaml, yaml -> json")
        return
    
    input_file, output_file = args[0], args[1]
    
    try:
        if input_file.endswith('.txt') and output_file.endswith('.md'):
            with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
                for line in infile:
                    outfile.write(line)
            print(f"{GREEN}Converted {input_file} to {output_file}")
        elif input_file.endswith('.md') and output_file.endswith('.html'):
            try:
                import markdown
                with open(input_file, 'r') as infile:
                    html = markdown.markdown(infile.read())
                with open(output_file, 'w') as outfile:
                    outfile.write(html)
                print(f"{GREEN}Converted {input_file} to {output_file}")
            except ImportError:
                print(f"{RED}markdown package not installed. Run 'pip install markdown'")
        elif (input_file.endswith('.json') and output_file.endswith('.yaml')) or \
             (input_file.endswith('.yaml') and output_file.endswith('.json')):
            try:
                import yaml
                with open(input_file, 'r') as infile:
                    if input_file.endswith('.json'):
                        data = json.load(infile)
                        with open(output_file, 'w') as outfile:
                            yaml.dump(data, outfile)
                    else:
                        data = yaml.safe_load(infile)
                        with open(output_file, 'w') as outfile:
                            json.dump(data, outfile, indent=2)
                print(f"{GREEN}Converted {input_file} to {output_file}")
            except ImportError:
                print(f"{RED}yaml package not installed. Run 'pip install pyyaml'")
        else:
            print(f"{RED}Unsupported conversion: {input_file} -> {output_file}")
    except Exception as e:
        print(f"{RED}Error during conversion: {e}")

def fileinfo_command(args):
    if len(args) < 1:
        print("fileinfo: usage: fileinfo <file>")
        return
    
    file = args[0]
    
    try:
        stat = os.stat(file)
        print(f"{CYAN}File Information:")
        print(f"{YELLOW}Path: {os.path.abspath(file)}")
        print(f"{YELLOW}Size: {stat.st_size} bytes")
        print(f"{YELLOW}Created: {datetime.datetime.fromtimestamp(stat.st_ctime)}")
        print(f"{YELLOW}Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}")
        print(f"{YELLOW}Permissions: {oct(stat.st_mode)[-3:]}")
    except Exception as e:
        print(f"{RED}Error getting file info: {e}")

def memory_usage_command(args):
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        print(f"{CYAN}Memory Usage:")
        print(f"{YELLOW}Total: {mem.total // (1024 * 1024)} MB")
        print(f"{YELLOW}Available: {mem.available // (1024 * 1024)} MB")
        print(f"{YELLOW}Used: {mem.used // (1024 * 1024)} MB")
        print(f"{YELLOW}Percentage: {mem.percent}%")
        
        print(f"\n{CYAN}Swap Usage:")
        print(f"{YELLOW}Total: {swap.total // (1024 * 1024)} MB")
        print(f"{YELLOW}Used: {swap.used // (1024 * 1024)} MB")
        print(f"{YELLOW}Free: {swap.free // (1024 * 1024)} MB")
        print(f"{YELLOW}Percentage: {swap.percent}%")
    except Exception as e:
        print(f"{RED}Error getting memory usage: {e}")

def cpu_temp_command(args):
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            print(f"{YELLOW}No temperature sensors found")
            return
            
        print(f"{CYAN}CPU Temperatures:")
        for name, entries in temps.items():
            for entry in entries:
                print(f"{YELLOW}{entry.label or name}: {entry.current}°C")
    except Exception as e:
        print(f"{RED}Error getting CPU temperature: {e}")

def disk_usage_command(args):
    path = args[0] if args else os.getcwd()
    try:
        usage = psutil.disk_usage(path)
        print(f"{CYAN}Disk Usage for {path}:")
        print(f"{YELLOW}Total: {usage.total // (1024 * 1024)} MB")
        print(f"{YELLOW}Used: {usage.used // (1024 * 1024)} MB")
        print(f"{YELLOW}Free: {usage.free // (1024 * 1024)} MB")
        print(f"{YELLOW}Percentage Used: {usage.percent}%")
    except Exception as e:
        print(f"{RED}Error getting disk usage: {e}")

def generate_keys(num_keys=4, key_size=1024, prefix="key"):
    keys = []
    for i in range(num_keys):
        pub_key, priv_key = rsa.newkeys(key_size)
        with open(f"{prefix}_{i}_private.pem", "wb") as priv_file:
            priv_file.write(priv_key.save_pkcs1())
        with open(f"{prefix}_{i}_public.pem", "wb") as pub_file:
            pub_file.write(pub_key.save_pkcs1())
        keys.append((pub_key, priv_key))
    return keys

def load_keys(num_keys=4, prefix="key"):
    keys = []
    for i in range(num_keys):
        try:
            with open(f"{prefix}_{i}_private.pem", "rb") as priv_file:
                priv_key = rsa.PrivateKey.load_pkcs1(priv_file.read())
            with open(f"{prefix}_{i}_public.pem", "rb") as pub_file:
                pub_key = rsa.PublicKey.load_pkcs1(pub_file.read())
            keys.append((pub_key, priv_key))
        except FileNotFoundError:
            break
    return keys

def encrypt_with_multi_keys(data, keys):
    result = data
    key_info = []
    for pub_key, _ in keys:
        aes_key = secrets.token_bytes(32)
        iv = secrets.token_bytes(16)
        encrypted_key_info = rsa.encrypt(aes_key + iv, pub_key)
        key_info.append(encrypted_key_info)
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        result = cipher.encrypt(pad(result, AES.block_size))
    return result, key_info

def decrypt_with_multi_keys(encrypted_data, key_info, keys):
    result = encrypted_data
    for i in range(len(keys) - 1, -1, -1):
        _, priv_key = keys[i]
        encrypted_key_info = key_info[i]
        decrypted_key_info = rsa.decrypt(encrypted_key_info, priv_key)
        aes_key = decrypted_key_info[:32]
        iv = decrypted_key_info[32:]
        cipher = AES.new(aes_key, AES.MODE_CBC, iv)
        result = unpad(cipher.decrypt(result), AES.block_size)
    return result

def encrypt_file(input_file, output_file, keys):
    if not os.path.exists(input_file):
        print(f"{RED}error: File {input_file} does not exist.")
        return False
    try:
        with open(input_file, "rb") as f:
            plaintext = f.read()
        compressed = zlib.compress(plaintext)
        encrypted_data, key_info = encrypt_with_multi_keys(compressed, keys)
        with open(output_file, "wb") as f:
            f.write(len(keys).to_bytes(4, byteorder='big'))
            for info in key_info:
                f.write(len(info).to_bytes(4, byteorder='big'))
                f.write(info)
            f.write(encrypted_data)
        print(f"{GREEN}encrypt: Encrypted file saved as: {output_file}")
        return True
    except Exception as e:
        print(f"{RED}error: Failed to encrypt file: {str(e)}")
        return False

def decrypt_file(input_file, output_file, keys):
    if not os.path.exists(input_file):
        print(f"{RED}error: File {input_file} does not exist.")
        return False
    try:
        with open(input_file, "rb") as f:
            num_keys = int.from_bytes(f.read(4), byteorder='big')
            if num_keys > len(keys):
                print(f"{RED}error: Need {num_keys} keys to decrypt this file, but only found {len(keys)}.")
                return False
            key_info = []
            for _ in range(num_keys):
                info_len = int.from_bytes(f.read(4), byteorder='big')
                key_info.append(f.read(info_len))
            encrypted_data = f.read()
        decrypted_data = decrypt_with_multi_keys(encrypted_data, key_info, keys[:num_keys])
        decompressed = zlib.decompress(decrypted_data)
        with open(output_file, "wb") as f:
            f.write(decompressed)
        print(f"{GREEN}decrypt: Decrypted file saved as: {output_file}")
        return True
    except Exception as e:
        print(f"{RED}error: Failed to decrypt file: {str(e)}")
        return False

def genkeys_command(args):
    try:
        num_keys = 4
        key_size = 1024
        prefix = "key"
        
        i = 0
        while i < len(args):
            if args[i] == "-n" and i + 1 < len(args):
                try:
                    num_keys = int(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"{RED}genkeys: invalid number of keys: {args[i + 1]}")
                    return
            elif args[i] == "-s" and i + 1 < len(args):
                try:
                    key_size = int(args[i + 1])
                    i += 2
                except ValueError:
                    print(f"{RED}genkeys: invalid key size: {args[i + 1]}")
                    return
            elif args[i] == "-p" and i + 1 < len(args):
                prefix = args[i + 1]
                i += 2
            else:
                print(f"{RED}genkeys: unknown option: {args[i]}")
                print("Usage: genkeys [-n num_keys] [-s key_size] [-p prefix]")
                return
        
        print(f"{YELLOW}Generating {num_keys} RSA keys with size {key_size}...")
        keys = generate_keys(num_keys, key_size, prefix)
        print(f"{GREEN}Successfully generated {len(keys)} key pairs with prefix '{prefix}'")
    
    except Exception as e:
        print(f"{RED}Error generating keys: {e}")
        print(f"{YELLOW}Make sure you have the 'rsa' package installed.")

def encrypt_command(args):
    if len(args) < 2:
        print(f"{WHITE}encrypt: usage: encrypt <input_file> <output_file> [-n num_keys] [-p prefix]")
        return
    
    input_file = args[0]
    output_file = args[1]
    num_keys = 4
    prefix = "key"
    
    i = 2
    while i < len(args):
        if args[i] == "-n" and i + 1 < len(args):
            try:
                num_keys = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"{RED}encrypt: invalid number of keys: {args[i + 1]}")
                return
        elif args[i] == "-p" and i + 1 < len(args):
            prefix = args[i + 1]
            i += 2
        else:
            print(f"{RED}encrypt: unknown option: {args[i]}")
            print("Usage: encrypt <input_file> <output_file> [-n num_keys] [-p prefix]")
            return
    
    try:
        keys = load_keys(num_keys, prefix)
        if not keys:
            print(f"{RED}No keys found with prefix '{prefix}'. Generate keys first with 'genkeys'.")
            return
        
        print(f"{YELLOW}Encrypting {input_file} with {len(keys)} keys...")
        if encrypt_file(input_file, output_file, keys):
            print(f"{GREEN}File encrypted successfully.")
    
    except Exception as e:
        print(f"{RED}Error encrypting file: {e}")
        print(f"{YELLOW}Make sure you have the 'rsa' and 'pycryptodome' packages installed.")

def decrypt_command(args):
    if len(args) < 2:
        print(f"{WHITE}decrypt: usage: decrypt <input_file> <output_file> [-n num_keys] [-p prefix]")
        return
    
    input_file = args[0]
    output_file = args[1]
    num_keys = 4
    prefix = "key"
    
    i = 2
    while i < len(args):
        if args[i] == "-n" and i + 1 < len(args):
            try:
                num_keys = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"{RED}decrypt: invalid number of keys: {args[i + 1]}")
                return
        elif args[i] == "-p" and i + 1 < len(args):
            prefix = args[i + 1]
            i += 2
        else:
            print(f"{RED}decrypt: unknown option: {args[i]}")
            print("Usage: decrypt <input_file> <output_file> [-n num_keys] [-p prefix]")
            return
    
    try:
        keys = load_keys(num_keys, prefix)
        if not keys:
            print(f"{RED}No keys found with prefix '{prefix}'. Generate keys first with 'genkeys'.")
            return
        
        print(f"{YELLOW}Decrypting {input_file} with {len(keys)} keys...")
        if decrypt_file(input_file, output_file, keys):
            print(f"{GREEN}File decrypted successfully.")
    
    except Exception as e:
        print(f"{RED}Error decrypting file: {e}")
        print(f"{YELLOW}Make sure you have the 'rsa' and 'pycryptodome' packages installed.")

register_command("genkeys", genkeys_command)
register_command("encrypt", encrypt_command)
register_command("decrypt", decrypt_command)
register_command("disk", disk_usage_command)
register_command("cputemp", cpu_temp_command)
register_command("memory", memory_usage_command)
register_command("checksum", checksum_command)
register_command("convert", convert_command)
register_command("fileinfo", fileinfo_command)
register_command("zip", zip_command)
register_command("unzip", unzip_command)
register_command("search", search_command)
register_command("monitor", monitor_command)
register_command("netinfo", netinfo_command)
register_command("diff", diff_command)
register_command("alias", alias_command)
register_command("unalias", unalias_command)
register_command("ps", ps_command)
register_command("kill", kill_command)
register_command("df", df_command)
register_command("whoami", whoami_command)
register_command("date", date_command)
register_command("curl", curl_command)
register_command("ping", ping_command)
register_command("wget", wget_command)
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
register_command("chmod", chmod_command)
register_command("echo", echo_command)
register_command("grep", grep_command)
register_command("find", find_command)
register_command("calc", calc_command)
register_command("history", history_command)

def set_window_title(title):
    if os.name == 'nt':
        os.system(f'title {title}')

    else:
        print(f'\033]0;{title}\007', end='')

def get_nested_completer():
    class DirectoryPathCompleter(PathCompleter):
        def get_completions(self, document, complete_event):
            for completion in super().get_completions(document, complete_event):
                try:
                    path = os.path.join(os.getcwd(), completion.text)
                    
                    if os.path.isdir(path) and not completion.text.endswith('/'):
                        completion.text += '/'
                        completion.display_meta = "Directory"
                        
                    completion.start_position = document.cursor_position - len(document.get_word_before_cursor())

                except Exception as e:
                    pass
                yield completion
    
    class CaseInsensitivePathCompleter(PathCompleter):
        def __init__(self, only_directories=False, **kwargs):
            super().__init__(**kwargs)
            self.only_directories = only_directories
            
        def get_completions(self, document, complete_event):
            word_before_cursor = document.get_word_before_cursor().lower()
            current_dir = os.getcwd()
            
            try:
                items = os.listdir(current_dir)
                
                for item in items:
                    if item.lower().startswith(word_before_cursor):
                        path = os.path.join(current_dir, item)
                        is_dir = os.path.isdir(path)
                        
                        if self.only_directories and not is_dir:
                            continue
                        
                        from prompt_toolkit.completion import Completion
                        display = f"{item}/" if is_dir else item
                        text = f"{item}/" if is_dir else item
                        meta = "Directory" if is_dir else "File"
                        
                        yield Completion(
                            text=text,
                            start_position=-len(word_before_cursor),
                            display=display,
                            display_meta=meta
                        )
            except Exception as e:
                for completion in super().get_completions(document, complete_event):
                    yield completion
    
    path_completer = CaseInsensitivePathCompleter()
    dir_completer = CaseInsensitivePathCompleter(only_directories=True)
    
    command_completers = {}

    for cmd in list(commands.keys()):
        command_completers[cmd] = None

    for alias in aliases.keys():
        command_completers[alias] = None

    operators = {
        ";": NestedCompleter.from_nested_dict(command_completers),
        "&&": NestedCompleter.from_nested_dict(command_completers),
        "|": NestedCompleter.from_nested_dict(command_completers)
    }

    file_commands = [
        "cd", "mv", "cp", "cat", "mkdir", "md", "ls", "grep", "rm", 
        "fileinfo", "checksum", "unzip", "search", "touch", "find",
        "diff", "convert", "zip", "encrypt", "decrypt"
    ]
    
    multi_arg_commands = ["mv", "cp", "diff", "convert", "zip", "encrypt", "decrypt"]
    
    for cmd in multi_arg_commands:
        try:
            file_dict = {word: path_completer for word in [""] + list(os.listdir("."))}
            command_completers[cmd] = file_dict

        except Exception:
            command_completers[cmd] = path_completer
    
    single_arg_commands = {
        "cat": PathCompleter(only_directories=False),
        "mkdir": dir_completer,
        "cd": dir_completer,
        "md": dir_completer,
        "ls": dir_completer,
        "grep": PathCompleter(),
        "rm": PathCompleter(),
        "fileinfo": PathCompleter(),
        "checksum": PathCompleter(),
        "unzip": PathCompleter(),
        "search": dir_completer,
        "touch": PathCompleter(),
        "find": dir_completer,
    }
    
    command_completers.update(single_arg_commands)
    
    option_completers = {
        "genkeys": {
            "-n": None,
            "-s": None,
            "-p": None,
        },
        "encrypt": {
            "-n": None,
            "-p": None,
        },
        "decrypt": {
            "-n": None,
            "-p": None,
        },
        "checksum": {
            word: WordCompleter(["md5", "sha1", "sha256"]) for word in list(os.listdir("."))
        },
        "chmod": {
            "-r": PathCompleter(),
            "+x": PathCompleter(),
            "-x": PathCompleter(),
        },
    }
    
    for cmd, completer in option_completers.items():
        if cmd not in multi_arg_commands:
            command_completers[cmd] = completer

    result = {}
    for cmd, completer in command_completers.items():
        if completer is None and cmd not in file_commands:
            result[cmd] = operators
        else:
            result[cmd] = completer

    return NestedCompleter.from_nested_dict(result)

completer = WordCompleter(list(commands.keys()) + list(aliases.keys()))

session = loaded_modules["prompt_toolkit_shortcuts"].PromptSession(
    get_prompt,
    style=style,
    completer=get_nested_completer(),
    history=FileHistory(HISTORY_FILE),
    complete_while_typing=True
)

def main():
    global session
    if not login():
        return

    clear()
    set_window_title('NAX-Shell · BETA · v1.0.0')
    print(f"{CYAN}{fitNAXShell.renderText('NAX-Shell | BETA')}")
    print(f"{CYAN}{fitNAXVers.renderText('v 1.0.0')}")
    print(f"{YELLOW}Platform: {platform.system()} {platform.release()}")
    print(f"{GREEN}Type 'help' for available commands\nand 'web' for documentation\n")
    load_aliases()
    update_completer()
    get_api_url()

    try:
        while True:
            try:
                process_command(session.prompt())

            except (KeyboardInterrupt, EOFError, SystemExit):
                update_remaining_auth_time()
                break

            except Exception as e:
                print(f"{RED}An error occurred: {str(e)}")

    finally:
        update_remaining_auth_time()

if __name__ == "__main__":    
    clear()
    main()
