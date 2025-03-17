import os
import time
import importlib
import threading
from tqdm import tqdm
from colorama import init, Fore                                                      

modules_parallel = [
    ("re", None),
    ("sys", None),
    ("json", None),
    ("time", None),
    ("tqdm", None),
    ("math", None),
    ("shutil", None),
    ("pyfiglet", None),
    ("datetime", None),
    ("fnmatch", None),
    ("getpass", None),
    ("hashlib", None),
    ("platform", None),
    ("threading", None),                                                             
    ("subprocess", None),
    ("urllib.request", "urllib_request"),
]

modules_sequential = [
    ("prompt_toolkit", None),
    ("prompt_toolkit.styles", "prompt_toolkit_styles"),                              
    ("prompt_toolkit.history", "prompt_toolkit_history"),
    ("prompt_toolkit.shortcuts", "prompt_toolkit_shortcuts"),
    ("prompt_toolkit.completion", "prompt_toolkit_completion"),
    ("prompt_toolkit.completion", "prompt_toolkit_completion"),
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

    finally:
        pbar.update(1)

init(strip=False, autoreset=True)

RED, GREEN, YELLOW, CYAN, WHITE, ORANGE = Fore.RED, Fore.GREEN, Fore.LIGHTYELLOW_EX, Fore.LIGHTCYAN_EX, Fore.WHITE, Fore.YELLOW

desc_bar = f"{CYAN}NAX-Shell · v1.0.0{YELLOW}"

pbar = tqdm(
    total=16,
    desc=desc_bar,
    ncols=80,
    ascii="══",
    dynamic_ncols=True,
    bar_format="{desc} [{bar}] {percentage:3.0f}%"
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

AUTH_FILE = os.path.join(os.path.expanduser("~"), ".nax_shell_auth")
AUTH_DURATION = 30 * 60
PROCESSOR_NAME = None
ALIAS_FILE = os.path.join(os.path.expanduser("~"), ".nax_shell_aliases")

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
        print(f"{YELLOW}Pipe operator detected. Note: Piping is simulated in NAX-Shell.")
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
    global session
    nested_completer = get_nested_completer()
    session.completer = nested_completer

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
        with open(history_file, "r") as f:
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
    path_completer = PathCompleter()
    
    command_completers = {}

    for cmd in list(commands.keys()):
        command_completers[cmd] = None
    
    for alias in aliases.keys():
        command_completers[alias] = None
    
    file_commands = {
        "cat": PathCompleter(only_directories=False),
        "mkdir": PathCompleter(only_directories=True),
        "cd": PathCompleter(only_directories=True),
        "md": PathCompleter(only_directories=True),
        "ls": PathCompleter(),
        "grep": PathCompleter(),
        "cp": PathCompleter(),
        "mv": PathCompleter(),
        "rm": PathCompleter()
    }
    command_completers.update(file_commands)
    
    operators = {
        ";": NestedCompleter.from_nested_dict(command_completers),
        "&&": NestedCompleter.from_nested_dict(command_completers),
        "|": NestedCompleter.from_nested_dict(command_completers)
    }
    
    result = {}
    for cmd, completer in command_completers.items():
        if completer is None:
            result[cmd] = operators
        else:
            result[cmd] = completer
            
    return NestedCompleter.from_nested_dict(result)

history_file = os.path.join(os.path.expanduser("~"), ".terminal_history")
completer = WordCompleter(list(commands.keys()) + list(aliases.keys()))

session = loaded_modules["prompt_toolkit_shortcuts"].PromptSession(
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
    print(f"{GREEN}Type 'help' for available commands\nand 'web' for documentation\n")
    load_aliases()
    update_completer()

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
