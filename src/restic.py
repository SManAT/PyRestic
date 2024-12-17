import atexit
import click
import os
import sys
from libs.TerminalColors import TerminalColors
from libs.Configuration import Configuration
from libs.CmdRunner import CmdRunner
from libs.CmdRunner_Terminal import CmdRunner_Terminal
from libs.Profiles import Profiles

from pathlib import Path


class Restic:

    def __init__(self):
        self.rootDir = Path(__file__).parent

        self.term = TerminalColors()
        self.term.set_BackgroundColor()

        self.configFile = os.path.join(self.rootDir, "config.yml")
        self.Configuration = Configuration(self.configFile)
        # Basic check
        self.checkForConfigFile()

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
        self.profiles = Profiles(self.Configuration)
        firstProfile = self.profiles.getFirstProfile()
        # load first profile
        self.config = self.profiles.loadProfile(firstProfile)

        self.storagePath = os.path.normpath(self.config["storage"])
        # exists?
        if os.path.isdir(self.storagePath) is False:
            self.term.print(f"{self.storagePath} does not exist ...", "RED")
            self.term.print("Please create Storage Path ...", "YELLOW")
            self.term.print("-exit-", "YELLOW")
            sys.exit(-1)

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
        files = self.search_files_in_dir(os.path.join(self.rootDir, "bin/"), [".exe"])
        return os.path.normpath(os.path.join(self.rootDir, files[0]))

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

    def createPwdFile(self):
        """create a password file from config"""
        fh = open(os.path.join("src", "bin", ".pwd"), "w")
        fh.write(self.config["password"])
        fh.close()

    def _checkInit(self):
        cmd = f'"{self.resticBin}" -r "{self.storagePath}" -p "{self.resticPwd}" cat config'
        self.runner.runCmd_Silent(cmd)
        return self.runner.getStdErr()

    def testRepoInit(self):
        """test if the repo is allready initialized"""
        res = self._checkInit()

        if "repository does not exist" in res:
            self.term.print("Repository is not initialized ...", "red")
            self.term.print(f"do {os.path.basename(__file__)} --init", "yellow")
            sys.exit()

        elif "unable to create lock in backend" in res:
            self.term.print("The repository is locked, trying to unlock it ...", "RED")
            self.removeLocks()
            return True
        else:
            return True

    def init(self, profile_name):
        """Initialze the repository"""
        self.term.print(f"Initialze the repository [{profile_name}]")

        config = self.profiles.loadProfile(profile_name)
        if config is not False:
            self.profiles.setConfig(config)
            self.createPwdFile()
            res = self._checkInit()
            if "repository does not exist" in res:
                cmd = f'"{self.resticBin}" init -r "{self.storagePath}" -p "{self.resticPwd}"'
                self.runner.runCmd_with_Spinner(cmd, "Initializing ")
                self.term.print("Repository has been initialized ...", "YELLOW")
                self.term.print(f"Path: {self.storagePath}")
            else:
                self.term.print("Repository is allready initialized ...", "RED")
                self.term.print("-exit-", "YELLOW")

    def removeLocks(self):
        """Remove Lock files from Restic"""
        cmd = f'"{self.resticBin}" -r "{self.storagePath}" unlock -p "{self.resticPwd}"'
        self.runner.runCmd_with_Spinner(cmd, "Unlock Repository ")
        res = self.runner.getStdErr()

        if "Fatal: wrong password or no key found" in res:
            self.term.print(f"{self.storagePath}")
            self.term.print("Error: There is another Repository stored ...", "RED")
            self.term.print("-exit-", "YELLOW")
            sys.exit()

        self.term.print("done ...", "YELLOW")

    def backup(self, profile_name):
        """do a restic backup"""
        config = self.profiles.loadProfile(profile_name)

        if config is not False:
            self.profiles.setConfig(config)
            self.term.print(f"Creating a backup [{profile_name}] with {self.profiles.getSnapshots()} snapshots")

            self.createPwdFile()
            if self.testRepoInit() is True:
                # remove Lock
                self.removeLocks()

                self.profiles.createIncludeExcludeFiles(self.includeFile, self.excludeFile)

                # backup
                cmd = f'"{self.resticBin}" -r "{self.storagePath}" backup --files-from "{self.includeFile}" --exclude-file "{self.excludeFile}" -p "{self.resticPwd}" -v'
                runner = CmdRunner_Terminal()
                runner.run_command(cmd)

                self.term.print("done ...", "YELLOW")

                # keep n snapshots
                snapshots = self.config["snapshots"]
                cmd = f'"{self.resticBin}" -r "{self.storagePath}" forget --keep-last {snapshots} -p "{self.resticPwd}"'

                self.runner.runCmd_with_Spinner(cmd, "Maintaince Snapshots  ")
                self.term.print("done ...", "YELLOW")

                # free space
                cmd = f'"{self.resticBin}" -r "{self.storagePath}" prune -p "{self.resticPwd}"'
                self.runner.runCmd(cmd, "Maintaince Snapshots  ")
                self.term.print("done ...", "YELLOW")

            else:
                self.term.print("Repository is not initialized ...", "RED")
                self.term.print("-exit-", "YELLOW")

    def stats(self, profile_name):
        """Statistics about Repo"""
        self.term.print("Get statistics from Repository")

        config = self.profiles.loadProfile(profile_name)
        if config is not False:
            self.profiles.setConfig(config)
            self.createPwdFile()
            if self.testRepoInit() is True:
                # stats
                cmd = f'"{self.resticBin}" stats -r "{self.storagePath}" -p "{self.resticPwd}"'
                runner = CmdRunner_Terminal()
                runner.run_command(cmd)

                self.term.print("done ...", "YELLOW")

    def check(self, profile_name):
        """Check s Repo"""
        self.term.print(f"Check Repository: {profile_name}")

        config = self.profiles.loadProfile(profile_name)
        if config is not False:
            self.profiles.setConfig(config)
            self.createPwdFile()
            if self.testRepoInit() is True:
                # stats
                cmd = f'"{self.resticBin}" check -r "{self.storagePath}" -p "{self.resticPwd}"'
                runner = CmdRunner_Terminal()
                runner.run_command(cmd)

                self.term.print("done ...", "YELLOW")

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
    "--stats",
    type=(str),
    required=False,
    help="Get some statistic about the Repository TEXT=Profile name",
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
def start(backup, restore, check, help, init, stats, profiles):
    restic = Restic()

    # debug
    # restic.profileManagement()
    #
    # restic.backup("profilXX")
    # sys.exit()

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

    elif check:
        profile_name = check
        restic.check(profile_name)
    else:
        # Display Help Informations and Usage
        ctx = click.get_current_context()
        click.echo(ctx.get_help())


if __name__ == "__main__":
    start()
