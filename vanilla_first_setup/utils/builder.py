# builder.py
#
# Copyright 2022 mirkobrombin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundationat version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import logging
import json

from gi.repository import Gio

from vanilla_first_setup.utils.recipe import RecipeLoader

from vanilla_first_setup.defaults.welcome import VanillaDefaultWelcome
from vanilla_first_setup.defaults.theme import VanillaDefaultTheme

from vanilla_first_setup.layouts.preferences import VanillaLayoutPreferences
from vanilla_first_setup.layouts.yes_no import VanillaLayoutYesNo


logger = logging.getLogger("FirstSetup::Builder")


templates = {
    "welcome": VanillaDefaultWelcome,
    "theme": VanillaDefaultTheme,
    "preferences": VanillaLayoutPreferences,
    "yes-no": VanillaLayoutYesNo
}


class Builder:

    def __init__(self, window):
        self.__window = window
        self.__recipe = RecipeLoader()
        self.__register_widgets = []
        self.__register_finals = []
        self.__load()

    def __load(self):
        # here we create a temporary file to store the output of the commands
        # the log path is defined in the recipe
        if "log_file" not in self.__recipe.raw:
            logger.critical("Missing 'log_file' in the recipe.")
            sys.exit(1)

        log_path = self.__recipe.raw["log_file"]

        if not os.path.exists(log_path):
            try:
                open(log_path, 'a').close()
            except OSError:
                logger.critical("failed to create log file: %s" % log_path)
                sys.exit(1)

        for key, step in self.__recipe.raw["steps"].items():
            if step["template"] in templates:
                _widget = templates[step["template"]](self.__window, self.distro_info, key, step)
                self.__register_widgets.append(_widget)

    def get_finals(self):
        self.__register_finals = []

        for widget in self.__register_widgets:
            self.__register_finals.append(widget.get_finals())

        return self.__register_finals

    @property
    def widgets(self):
        return self.__register_widgets

    @property
    def recipe(self):
        return self.__recipe.raw
    
    @property
    def distro_info(self):
        return {
            "name": self.__recipe.raw["distro_name"],
            "logo": self.__recipe.raw["distro_logo"]
        }
