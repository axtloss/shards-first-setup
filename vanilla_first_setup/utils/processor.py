# processor.py
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
import shutil
import logging
import tempfile
import subprocess


logger = logging.getLogger("FirstSetup::Processor")


class Processor:

    @staticmethod
    def get_setup_commands(log_path, pre_run, post_run, commands):
        commands = pre_run + commands + post_run
        out_run = ""
        next_boot = []
        next_boot_script_path = os.path.expanduser("/etc/org.vanillaos.FirstSetup.nextBoot")
        next_boot_autostart_path = os.path.expanduser("/etc/xdg/autostart/org.vanillaos.FirstSetup.nextBoot.desktop")
        done_file = "/etc/vanilla-first-setup-done"
        abroot_bin = shutil.which("abroot")

        logger.info("processing the following commands: \n%s" %
                    '\n'.join(commands))

        # Collect all the commands that should be run at the next boot
        for command in commands:
            if command.startswith("!nextBoot"):
                next_boot.append(command.replace("!nextBoot", ""))
                continue

        # generating a temporary file to store all the commands so we can
        # run them all at once
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("#!/bin/sh\n")
            f.write("# This file was created by FirstSetup\n")
            f.write("# Do not edit this file manually\n\n")

            # fake the process if VANILLA_FAKE is set
            if "VANILLA_FAKE" in os.environ:
                f.write("echo 'VANILLA_FAKE is set, not running commands'\n")
                f.write("exit 0\n")

            # connection test
            f.write("wget -q --spider cloudflare.com\n")
            f.write("if [ $? != 0 ]; then\n")
            f.write("echo 'No internet connection!'\n")
            f.write("exit 1\n")
            f.write("fi\n")

            # nextBoot commands are collected in /etc/org.vanillaos.FirstSetup.nextBoot
            # and executed at the next boot by a desktop entry
            if len(next_boot) > 0:
                f.write("cat <<EOF > "+next_boot_script_path+"\n")
                f.write("#!/bin/sh\n")
                f.write("# This file was created by FirstSetup\n")
                f.write("# Do not edit this file manually\n\n")
                for command in next_boot:
                    f.write(f"{command}\n")
                f.write("cat <<2EOF > ~/.local/share/applications/org.vanillaos.FirstSetup.desktop")
                f.write("[Desktop Entry]\n")
                f.write("Name=FirstSetup\n")
                f.write("Comment=FirstSetup\n")
                f.write("Exec=vanilla-first-setup\n")
                f.write("Terminal=false\n")
                f.write("Type=Application\n")
                f.write("NoDisplay=true\n")
                f.write("2EOF\n")
                f.write("EOF\n")

                f.write("chmod +x "+next_boot_script_path+"\n")
                f.write("cat <<EOF > "+next_boot_autostart_path+"\n")
                f.write("[Desktop Entry]\n")
                f.write("Name=FirstSetup Next Boot\n")
                f.write("Comment=Run FirstSetup commands at the next boot\n")
                f.write("Exec=vanilla-first-setup --run-post-script 'sh %s'\n" % next_boot_script_path)
                f.write("Terminal=false\n")
                f.write("Type=Application\n")
                f.write("X-GNOME-Autostart-enabled=true\n")
                f.write("EOF\n")

            for command in commands:
                if command.startswith("!nextBoot"):
                    continue

                if command.startswith("!noSudo"):
                    command = command.replace("!noSudo", "sudo -u $USER")

                # outRun band is used to run a command outside of the main
                # shell script.
                if command.startswith("!outRun"):
                    out_run += command.replace("!outRun", "") + "\n"

                f.write(f"{command}\n")

            # run the outRun commands
            if out_run:
                f.write("if [ $? -eq 0 ]; then")
                f.write(f"{out_run}\n")
                f.write("fi")

            # create the done file
            f.write("if [ $? -eq 0 ]; then\n")
            f.write(f"touch {done_file}\n")
            f.write("fi\n")

            f.flush()
            f.close()

            # setting the file executable
            os.chmod(f.name, 0o755)

        cmd = ["pkexec", "sh", f.name]
        if abroot_bin := shutil.which("abroot"):
            cmd = ["pkexec", abroot_bin, "exec", "-f", "-s", "sh", f.name]
        return cmd

    @staticmethod
    def hide_first_setup(user: str=None):
        if user is None:
            user = os.environ.get("USER")

        autostart_file = "/home/%s/.config/autostart/org.vanillaos.FirstSetup.desktop" % user

        if os.path.exists(autostart_file):
            os.remove(autostart_file)
