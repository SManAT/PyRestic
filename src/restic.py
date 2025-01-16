import atexit
import click
import os
import sys
import questionary
import re
from datetime import datetime
from libs.TerminalColors import TerminalColors
from libs.Configuration import Configuration
from libs.CmdRunner import CmdRunner
from libs.CmdRunner_Terminal import CmdRunner_Terminal
from libs.Profiles import Profiles
from libs.OSDetector import OSDetector

from pathlib import Path


class Restic:

    output_cache = []

    def __init__(self):
        self.rootDir = Path(__file__).parent

        self.term = TerminalColors()
        self.term.set_BackgroundColor()

        self.configFile = os.path.join(self.rootDir, "config.yml")
        self.Configuration = Configuration(self.configFile)
        # Basic check
        self.checkForConfigFile()

        # Dirs?
        self.createDir(os.path.join(self.rootDir, "bin"))

        self.resticBin = self.getResticPath()
        self.resticPwd = os.path.normpath(os.path.join(self.rootDir, "bin", ".pwd"))

        self.includeFile = os.path.normpath(os.path.join(self.rootDir, "bin", "include.txt"))
        self.excludeFile = os.path.normpath(os.path.join(self.rootDir, "bin", "exclude.txt"))

        self.runner = CmdRunner()
        # connect Callback events
        self.runner.add_stdout_listener(self.on_stdout)
        self.runner.add_stderr_listener(self.on_stderr)
        self.runner.add_completion_listener(self.on_completion)

        self.configDict = self.load_yml()
        self.profiles = Profiles(self.Configuration, self.includeFile, self.excludeFile, self.resticPwd)
        firstProfile = self.profiles.getFirstProfile()
        # load first profile
        self.config = self.profiles.loadProfile_and_setVariables(firstProfile)

        # catch terminating Signal
        atexit.register(self.exit_handler)

        # Standard Informations
        self._basicInfos()

    def exit_handler(self):
        """do something on sys.exit()"""
        pass

    def checkForConfigFile(self):
        """Basic check for config file"""
        if os.path.exists(self.configFile) is False:
            self.createEmptyConfigFile()

    def load_yml(self):
        """Load the yaml file config.yml"""
        if os.path.exists(self.configFile) is False:
            self.createEmptyConfigFile()

        config = self.Configuration.load_yml()
        if config is None or len(config) == 0:
            self.createEmptyConfigFile()

        return config

    def search_files_in_dir(self, directory=".", pattern=""):
        """
        search for pattern in directory NOT recursive
        :param directory: path where to search. relative or absolute
        :param pattern: a list e.g. ['.jpg', '.gif']
        """
        data = []
        for child in Path(directory).iterdir():
            if child.is_file():
                # print(f"{child.name}")
                if pattern == "":
                    data.append(os.path.join(directory, child.name))
                else:
                    for p in pattern:
                        if child.name.endswith(p):
                            data.append(os.path.join(directory, child.name))
        return data

    def getResticPath(self):
        """get path to exe file"""
        if OSDetector.is_windows():
            files = self.search_files_in_dir(os.path.join(self.rootDir, "bin/"), [".exe"])
            return os.path.normpath(os.path.join(self.rootDir, files[0]))
        if OSDetector.is_linux():
            return "restic"

    def createEmptyConfigFile(self):
        """will create an Empty Config File"""
        self.Configuration.createEmptyConfigFile()
        self.term.print("New config.yml File created ...", "RED")
        self.term.print("Profile [Default] was created ...", "YELLOW")
        self.term.print("Please edit config.yml as needed ...", "YELLOW")
        sys.exit(-1)

    def _basicInfos(self):
        self.term.print("Restic Python Wrapper, (c) Mag. Stefan Hagmann", "YELLOW")
        self.term.print("-----------------------------------------------", "YELLOW")

    def help(self):
        """print info text"""
        self.term.print("config.yml")
        self.term.print("     snapshots: 4, how many snapshots will be stored\n")
        self.term.print("     password: <a strong secret, don't lose it!>\n")
        self.term.print("     storage: absolute Path to the target Storage\n")
        self.term.print("     include: filename.txt of the include Patterns")
        self.term.print("              e.g: /data")
        self.term.print("                   /files/*.jpg\n")
        self.term.print("     exclude: filename.txt of the exclude Patterns")

    # Callback Wrapper --------------
    def on_stdout(self, line):
        print(line.strip())

    def on_stderr(self, line):
        print(line.strip())

    def on_completion(self):
        print("Command completed!")

    # Callback Wrapper --------------
    def modifyforOS(self, cmd):
        """win/unix cmd"""
        if OSDetector.is_windows():
            return cmd
        if OSDetector.is_linux():
            cmd = cmd.replace(f"{self.resticBin}", "restic")
            cmd = cmd.replace('"', "'")
        return cmd

    def _checkInit(self):
        cmd = f'"{self.resticBin}" cat config -r "{self.profiles.getStoragePath()}" -p "{self.resticPwd}"'
        cmd = self.modifyforOS(cmd)
        self.runner.runCmd_Silent(cmd)
        return self.runner.getStdErr()

    def createDir(self, path):
        """create dir if it not exists"""
        try:
            os.makedirs(path, exist_ok=True)
            # print(f"Successfully created path: {path}")
        except Exception as e:
            print(f"Error creating path: {str(e)}")

    def testRepoInit(self):
        """test if the repo is allready initialized"""
        res = self._checkInit()

        if ("repository does not exist" in res) or ("Fatal: unable to open config file" in res) or ("Fatal: unable to open repository" in res):
            self.term.print("Repository is not initialized ...", "red")
            self.term.print(f"do {os.path.basename(__file__)} --init [profil name]", "yellow")
            sys.exit()

        elif "unable to create lock in backend" in res:
            self.term.print("The repository is locked, trying to unlock it ...", "RED")
            self.removeLocks()
            return True
        else:
            return True

    def init(self, profile_name="default"):
        """Initialze the repository"""
        self.term.print(f"Initialze the repository [{profile_name}]")

        config = self.profiles.loadProfile_and_setVariables(profile_name)
        if config is not False:
            if self.testRepoInit() is False:
                cmd = f'"{self.resticBin}" init -r "{self.profiles.getStoragePath()}" -p "{self.resticPwd}"'
                cmd = self.modifyforOS(cmd)
                self.runner.runCmd_with_Spinner(cmd, "Initializing ")
                self.term.print("Repository has been initialized ...", "YELLOW")
                self.term.print(f"Path: {self.profiles.getStoragePath()}")
            else:
                self.term.print("Repository is allready initialized ...", "RED")
                self.term.print("-exit-", "YELLOW")

    def removeLocks(self):
        """Remove Lock files from Restic"""
        cmd = f'"{self.resticBin}" -r "{self.profiles.getStoragePath()}" unlock -p "{self.resticPwd}"'
        cmd = self.modifyforOS(cmd)
        self.runner.runCmd_with_Spinner(cmd, "Unlock Repository ")
        res = self.runner.getStdErr()

        if "Fatal: wrong password or no key found" in res:
            self.term.print(f"{self.profiles.getStoragePath()}")
            self.term.print("Error: There is another Repository stored ...", "RED")
            self.term.print("-exit-", "YELLOW")
            sys.exit()

        self.term.print("done ...", "YELLOW")

    def backup(self, profile_name="default"):
        """do a restic backup"""
        config = self.profiles.loadProfile_and_setVariables(profile_name)

        if config is not False:
            self.term.print(f"Creating a backup [{profile_name}] with {self.profiles.getSnapshots()} snapshots")
            if self.testRepoInit() is True:
                # remove Lock
                self.removeLocks()

                # backup
                cmd = f'"{self.resticBin}" -r "{self.profiles.getStoragePath()}" backup --files-from "{self.includeFile}" --exclude-file "{self.excludeFile}" -p "{self.resticPwd}" -v'
                print(cmd)
                cmd = self.modifyforOS(cmd)
                runner = CmdRunner_Terminal()
                runner.run_command(cmd)

                self.term.print("done ...", "YELLOW")

                # keep n snapshots
                snapshots = config["snapshots"]
                cmd = f'"{self.resticBin}" -r "{self.profiles.getStoragePath()}" forget --keep-last {snapshots} -p "{self.resticPwd}"'
                cmd = self.modifyforOS(cmd)

                self.runner.runCmd_with_Spinner(cmd, "Maintaince Snapshots  ")
                self.term.print("done ...", "YELLOW")

                # free space
                cmd = f'"{self.resticBin}" -r "{self.profiles.getStoragePath()}" prune -p "{self.resticPwd}"'
                cmd = self.modifyforOS(cmd)
                self.runner.runCmd(cmd, "Maintaince Snapshots  ")
                self.term.print("done ...", "YELLOW")

            else:
                self.term.print("Repository is not initialized ...", "RED")
                self.term.print("-exit-", "YELLOW")

    def stats(self, profile_name="default"):
        """Statistics about Repo"""
        self.term.print("Get statistics from Repository")

        config = self.profiles.loadProfile_and_setVariables(profile_name)
        if config is not False:
            if self.testRepoInit() is True:
                # stats
                cmd = f'"{self.resticBin}" stats -r "{self.profiles.getStoragePath()}" -p "{self.resticPwd}"'
                cmd = self.modifyforOS(cmd)
                runner = CmdRunner_Terminal()
                runner.run_command(cmd)

                self.term.print("done ...", "YELLOW")

    def check(self, profile_name="default"):
        """Check s Repo"""
        self.term.print(f"Check Repository: {profile_name}")

        config = self.profiles.loadProfile_and_setVariables(profile_name)
        if config is not False:
            if self.testRepoInit() is True:
                # stats
                cmd = f'"{self.resticBin}" check -r "{self.profiles.getStoragePath()}" -p "{self.resticPwd}"'
                cmd = self.modifyforOS(cmd)
                runner = CmdRunner_Terminal()
                runner.run_command(cmd)

                self.term.print("done ...", "YELLOW")

    def snapshots(self, profile_name="default"):
        """list all snapshots"""
        self.term.print(f"Snapshots stored in Repository: {profile_name}")

        config = self.profiles.loadProfile_and_setVariables(profile_name)
        if config is not False:
            if self.testRepoInit() is True:
                # stats
                cmd = f'"{self.resticBin}" snapshots -r "{self.profiles.getStoragePath()}" -p "{self.resticPwd}"'
                cmd = self.modifyforOS(cmd)
                runner = CmdRunner_Terminal()
                runner.run_command(cmd)

                self.term.print("done ...", "YELLOW")

    def process_output(self, line):
        # Process each line as it comes
        self.term.print(line.strip())
        self.output_cache.append(line.strip())

    def list(self, profile_name="default"):
        """list all snapshots"""
        self.term.print(f"List all files stored in Repository: {profile_name}")

        config = self.profiles.loadProfile(profile_name)
        if config is not False:
            self.profiles.setConfig(config)
            self.createPwdFile()
            if self.testRepoInit() is True:
                # stats
                cmd = f'"{self.resticBin}" ls latest -r "{self.profiles.getStoragePath()}" -p "{self.resticPwd}"'
                cmd = self.modifyforOS(cmd)

                runner = CmdRunner()
                runner.add_stdout_listener(self.process_output)
                runner.runCmd(cmd)

                # store to file
                filename = os.path.normpath(os.path.join(self.rootDir, "..", "files_stored.txt"))
                cache = self.reduce_list(self.output_cache)
                with open(filename, "w", encoding="utf-8") as fh:
                    fh.write(f"All filenames are deleted, showing only directories...\n\n")
                    fh.close()

                try:
                    with open(filename, "w", encoding="utf-8") as fh:
                        for line in cache:
                            fh.write(f"{line}\n")
                    fh.close()
                except UnicodeEncodeError:
                    with open(filename, "w", encoding="utf-8-sig") as fh:  # Try with BOM
                        for line in cache:
                            fh.write(f"{line}\n")
                    fh.close()

                self.term.print("done ...", "YELLOW")
                self.term.print(f"Output stored to: {filename}", "YELLOW")

    def reduce_list(self, paths):
        """delete filenames and reduce"""
        paths = [path.rstrip("/") for path in paths]  # Remove trailing slashes
        unique_dirs = set()
        unique_dirs = {str(Path(path).parent) if Path(path).is_file() else path for path in paths}

        # Print sorted results
        return sorted(unique_dirs)

    def profileManagement(self):
        a = self.profiles.MainMenue()
        if a == "profile-list":
            self.profiles.ProfileList()
        if a == "profile-create":
            self.profiles.createProfile()
        if a == "profile-delete":
            new_config, old_name = self.profiles.deleteProfile()
            self.term.print(f"Profile [{old_name}] deleted ...", "yellow")
            self.Configuration.save_config(new_config, self.Configuration.getConfigFilePath())
            self.configDict = self.load_yml()

        if a == "profile-show":
            self.profiles.showProfiles_Infos()
        if a == "profile-rename":
            new_config, old_name, new_name = self.profiles.renameProfile()
            self.Configuration.save_config(new_config, self.Configuration.getConfigFilePath())
            self.configDict = self.load_yml()

            self.term.print(f"Profile renamed [{old_name}] -> [{new_name}]", "yellow")
            self.profiles.setConfigDict(self.configDict)
            self.profiles.showProfileInfos(new_name)

    def extract_backup_info(self, input_list):
        """get desired infos"""
        result = []
        current_entry = None

        for line in input_list:
            # Skip empty lines and header/separator lines
            if not line.strip():
                continue

            # If line starts with an ID (8 hex characters)
            if line[:8].strip() and all(c in "0123456789abcdef" for c in line[:8].strip()):
                parts = line.split()
                if len(parts) >= 7:  # Make sure we have enough parts
                    backup_id = parts[0]
                    date = f"{parts[1]} {parts[2]}"
                    size = parts[-2] + " " + parts[-1]
                    current_entry = {"id": backup_id, "date": date, "size": size}
                    result.append(current_entry)

        return result

    def extract_id(self, line):
        # Pattern for ID, date, and size
        pattern = r"id=([a-z0-9]{8,})"  # matches 8 or more characters
        match = re.search(pattern, line)
        return match.group(1) if match else None

    def loadSnapshots(self, config):
        """get all snapshots from Repository"""
        self.createPwdFile()
        if self.testRepoInit() is True:
            # stats
            cmd = f'"{self.resticBin}" snapshots -r "{self.profiles.getStoragePath()}" -p "{self.resticPwd}"'
            cmd = self.modifyforOS(cmd)
            runner = CmdRunner()
            runner.runCmd(cmd)

            lines = runner.getStdOutLines()
            lines = self.extract_backup_info(lines)
            snappys = []
            for line in lines:
                dt = datetime.strptime(line["date"], "%Y-%m-%d %H:%M:%S")
                date = dt.strftime("%d.%m.%Y-%H:%M")

                sstr = f"{date}: id={line['id']} ({line['size']})"
                snappys.append(sstr)

                snappys = list(reversed(snappys))

            id = questionary.select("Choose a snapshot to restore?", choices=snappys).ask()
            return self.extract_id(id)

    def get_desktop_path(self):
        """Get the user's Desktop path"""
        # Try standard user profile desktop
        desktop = os.path.join(os.getenv("USERPROFILE"), "Desktop")
        if os.path.exists(desktop):
            return desktop

    def path_exists(self, path):
        return os.path.exists(path)

    def restore(self, profile_name="default"):
        """restore a snapshot"""
        self.term.print(f"Restoring snapshot from Repository: {profile_name}")
        self.term.print("Loading snaphots ...\n", "YELLOW")

        config = self.profiles.loadProfile_and_setVariables(profile_name)
        if config is not False:
            if self.testRepoInit() is True:
                # load snapshots
                id = self.loadSnapshots(config)
                target = questionary.path("What's the path to restore the Repository to (use TAB)?", default=self.get_desktop_path(), validate=self.path_exists, only_directories=True).ask()

                answ = questionary.confirm("Are you sure?").ask()
                if answ is True:
                    # restic -r <path> restore <id>  --target /tmp/restore-work -p $PWDFILE
                    cmd = f'"{self.resticBin}" -r "{self.profiles.getStoragePath()}" restore {id} --target {target} -p "{self.resticPwd}"'
                    print(cmd)
                    cmd = self.modifyforOS(cmd)
                    runner = CmdRunner_Terminal()
                    runner.run_command(cmd)

                    self.term.print("done ...", "YELLOW")
                else:
                    self.term.print("Aborted ...", "YELLOW")


@click.command(no_args_is_help=False)
@click.option(
    "--init",
    type=(str),
    required=False,
    help="Initialize the Repository TEXT=Profile name",
)
@click.option(
    "--backup",
    type=(str),
    required=False,
    help="Backup with Restic TEXT=Profile name",
)
@click.option(
    "--restore",
    required=False,
    type=(str),
    help="Restore a Backup TEXT=Profile name",
)
@click.option(
    "--check",
    type=(str),
    required=False,
    help="Check a Backup TEXT=Profile name",
)
@click.option(
    "--snapshots",
    type=(str),
    required=False,
    help="List all snapshots in repository TEXT=Profile name",
)
@click.option(
    "--list",
    type=(str),
    required=False,
    help="List all stored files in repository, and saves it to a text file, TEXT=Profile name",
)
@click.option(
    "--stats",
    type=(str),
    required=False,
    help="Get some statistic about the repository TEXT=Profile name",
)
@click.option(
    "--profiles",
    required=False,
    is_flag=True,
    help="Manage your Profiles",
)
@click.option(
    "--help",
    required=False,
    is_flag=True,
    help="Display some Informations about a Backup TEXT=Profile name",
)
def start(backup, restore, check, help, init, stats, profiles, snapshots, list):
    restic = Restic()

    # debug
    # restic.profileManagement()
    #

    restic.init("profil")
    sys.exit()

    if profiles:
        restic.profileManagement()

    elif init:
        profile_name = init
        restic.init(profile_name)

    elif backup:
        profile_name = backup
        restic.backup(profile_name)

    elif help:
        restic.help()

    elif stats:
        profile_name = stats
        restic.stats(profile_name)

    elif snapshots:
        profile_name = snapshots
        restic.snapshots(profile_name)

    elif list:
        profile_name = list
        restic.list(profile_name)

    elif restore:
        profile_name = restore
        restic.restore(profile_name)

    elif check:
        profile_name = check
        restic.check(profile_name)
    else:
        # Display Help Informations and Usage
        ctx = click.get_current_context()
        click.echo(ctx.get_help())


if __name__ == "__main__":
    start()
