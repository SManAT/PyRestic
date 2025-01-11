import questionary
import logging
from questionary.prompts.common import Separator
from questionary import Style

from libs.TerminalColors import TerminalColors


class Profiles:
    """Manage Profiles with Restic"""

    dict = {
        "Q1": "LIST all profiles ...",
        "Q2": "CREATE a profile ...",
        "Q3": "RENAME a profile ...",
        "Q5": "SHOW a profile ...",
        "Q4": "DELETE a profile ...",
    }

    custom_style_fancy = Style(
        [
            ("qmark", "fg:#00ff00 bold"),  # token in front of the question
            ("question", "fg:#c0c0c0 bold"),  # question text
            ("answer", "fg:#c0c0c0 bold"),  # submitted answer text behind the question
            (
                "pointer",
                "fg:#00ff00 bold",
            ),  # pointer used in select and checkbox prompts
            (
                "highlighted",
                "fg:#00ff00 bold",
            ),  # pointed-at choice in select and checkbox prompts
            ("selected", "fg:#c0c0c0"),  # style for a selected item of a checkbox
            ("separator", "fg:#c0c0c0"),  # separator in lists
            (
                "instruction",
                "fg:#c0c0c0",
            ),  # user instructions for select, rawselect, checkbox
            ("text", "fg:#c0c0c0"),  # plain text
            (
                "disabled",
                "fg:#858585 italic",
            ),  # disabled choices for select and checkbox prompts
        ]
    )

    def __init__(self, Configuration):
        self.logger = logging.getLogger(__name__)
        self.Configuration = Configuration
        self.configDict = self.Configuration.load_yml()
        # actual config data
        self.config = None

        self.term = TerminalColors()
        self.term.set_BackgroundColor("BACKGROUND")

    # questionary.select("Welche CSV Datei?", choices=flist, style=self.custom_style_fancy).ask()
    def confirm(self, msg):
        response = questionary.confirm(
            msg,
            default=False,
            qmark="?",
            style=None,
            auto_enter=True,
            instruction=None,
        ).ask()
        return response

    def MainMenue(self):
        a = questionary.select(
            "Profiles Management:",
            choices=[
                self.dict["Q1"],
                self.dict["Q2"],
                self.dict["Q3"],
                self.dict["Q5"],
                Separator(),
                self.dict["Q4"],
            ],
            style=self.custom_style_fancy,
        ).ask()

        if a == self.dict["Q1"]:
            return "profile-list"
        if a == self.dict["Q2"]:
            return "profile-create"
        if a == self.dict["Q3"]:
            return "profile-rename"
        if a == self.dict["Q4"]:
            return "profile-delete"
        if a == self.dict["Q5"]:
            return "profile-show"

    def showInfo(self):
        self.term.print("Profile Management", "YELLOW")
        self.term.print("All Profiles are stored in the files config.yml", "YELLOW")

    def getProfiles(self):
        """get all profile names"""
        return self.configDict.keys()

    def getSnapshots(self):
        """get all profile names"""
        dict_items = self.config.items()
        data = dict(dict_items)
        return data["snapshots"]

    def setConfig(self, config):
        """set actual config data"""
        self.config = config

    def getFirstProfile(self):
        """get the first listet key in dict"""
        return next(iter(self.configDict))

    def setConfigDict(self, new_config):
        self.configDict = {}
        self.configDict.update(new_config)

    def loadProfile(self, profile):
        """
        load all data from a specific profile
        :param profile: the name of the profile
        """
        try:
            return self.configDict[profile]
        except Exception as e:
            self.logger.error(f"This profile does not exist: {str(e)}")
            # show Profile List
            self.ProfileList()
            return False

    def ProfileList(self, txt="Profiles in config.yml"):
        """list all Profiles"""
        profiles = self.getProfiles()
        self.term.print(f"\n{txt}", "yellow")
        line = ""
        for i in range(len(txt)):
            line += "-"
        self.term.print(line, "yellow")
        for p in profiles:
            self.term.print(p)
        self.term.print("\n")

    def existsProfile(self, pname, log=False):
        """
        check if a profile exists
        :param pname: name of the profile
        :param log: write some log messages and exit?
        """
        # check if profile exists
        profiles = self.getProfiles()
        found = False
        for p in profiles:
            if p.lower() == pname.lower():
                found = True
                break
        if log:
            if found:
                self.term.print(f"Profile {pname} allready exists ...", "red")
                self.term.print("-exit-", "yellow")
        return found

    def createProfile(self):
        """create a new profile"""
        self.term.print("Creating a new profil", "yellow")
        pname = questionary.text("Profile name?").ask()

        self.existsProfile(pname, True)

        # append default Config to existing config
        config_dict = self.Configuration.getDefaultConfig(pname)
        new_config = self.Configuration.appendConfigFile(config_dict)
        self.Configuration.save_config(new_config, self.Configuration.getConfigFilePath())
        self.term.print(f"Profile [{pname}] created ...", "yellow")
        # neu einlesen
        self.configDict = self.Configuration.load_yml()
        self.showProfileInfos(pname)

    def showProfiles_Infos(self):
        """select a profile and show infos about it"""
        plist = []
        plist = self.getProfiles()
        pname = questionary.select("Which profile?", choices=plist, style=self.custom_style_fancy).ask()
        self.showProfileInfos(pname)

    def showProfileInfos(self, pname):
        """show some Informations about the profile"""
        self.term.print(f"\nProfile [{pname}]")
        data = self.loadProfile(pname)
        for key, data in data.items():
            print(f"  {key}: {data}")

        self.term.print("\nEdit the profile direct in config.yml file!", "yellow")

    def msgProfileNotExists(self, pname):
        """show basic Information, that the given profile doese not exists"""
        self.term.print(f"Repository {pname} does not exists ...", "RED")
        self.ProfileList()
        self.term.print("-exit-", "YELLOW")

    def renameProfile(self):
        plist = []
        plist = self.getProfiles()
        pname = questionary.select("Which profile to rename?", choices=plist, style=self.custom_style_fancy).ask()
        new_name = questionary.text("What is the new name?", style=self.custom_style_fancy).ask()

        new_config = {}
        for key, data in self.configDict.items():
            if key.lower() == pname.lower():
                new_config[new_name] = data
            else:
                new_config[key] = data

        return new_config, pname, new_name

    def deleteProfile(self):
        plist = []
        plist = self.getProfiles()
        pname = questionary.select("Which profile to DELETE?", choices=plist, style=self.custom_style_fancy).ask()

        new_config = {}
        for key, data in self.configDict.items():
            if key.lower() != pname.lower():
                new_config[key] = data
        return new_config, pname

    def createIncludeExcludeFiles(self, incFile, exFile):
        """create include.txt and exclude.txt from Profile"""
        # use actual config
        dict_items = self.config.items()
        data = dict(dict_items)
        file = open(incFile, "w")
        for item in data["include"]:
            file.write(f"{item}\n")
        file.close()

        file = open(exFile, "w")
        for item in data["exclude"]:
            file.write(f"{item}\n")
        file.close()
