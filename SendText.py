import re
import sublime
import sublime_plugin
import subprocess
import string
import tempfile

settings = {}

class SendSelectionCommand(sublime_plugin.TextCommand):
    @staticmethod
    def escapeString(s):
        s = s.replace('\\', '\\\\')
        s = s.replace('"', '\\"')
        return s

    @staticmethod
    def send(selection):
        prog = settings.get('program')

        if prog == "Terminal.app":
            # Remove trailing newline
            selection = selection.rstrip('\n')
            # Split selection into lines
            selection = SendSelectionCommand.escapeString(selection)

            subprocess.call(['osascript', '-e',
                'tell app "Terminal" to do script "' + selection + '" in window 1'])

        elif prog == "iTerm":
            # Remove trailing newline
            selection = selection.rstrip('\n')

            # If it ends with a space, add a newline. iTerm has a quirk where
            # if the scripted command doesn't end with a space, it automatically
            # adds a newline. but if it does end with a space, it doesn't add a newline.
            if (selection[-1] == " "):
                selection = selection + "\n"

            selection = SendSelectionCommand.escapeString(selection)

            subprocess.call(['osascript', '-e', 'tell app "iTerm"',
                '-e', 'set mysession to current session of current terminal',
                '-e', 'tell mysession to write text "' + selection + '"',
                '-e', 'end tell'])

        elif prog == "tmux":
            # Get the full pathname of the tmux, if it's
            progpath = settings.get('paths').get('tmux')
            # If path isn't specified, just call without path
            if not progpath:
                progpath = 'tmux'

            subprocess.call([progpath, 'set-buffer', selection])
            subprocess.call([progpath, 'paste-buffer', '-d'])

        elif prog == "screen":
            # Get the full pathname of the tmux, if it's
            progpath = settings.get('paths').get('screen')
            # If path isn't specified, just call without path
            if not progpath:
                progpath = 'screen'

            if len(selection)<2000:
                subprocess.call([progpath, '-X', 'stuff', selection])
            else:
                with tempfile.NamedTemporaryFile() as tmp:
                    with open(tmp.name, 'w') as file:
                        file.write(selection)
                        subprocess.call([progpath, '-X', 'stuff', ". %s\n" % (file.name)])


    def run(self, edit):
        global settings
        settings = sublime.load_settings('SendText.sublime-settings')

        # get selection
        selection = ""
        for region in self.view.sel():
            if region.empty():
                selection += self.view.substr(self.view.line(region))
                selection = re.sub('^\t*', '', selection) # BKJ edit -- better for Python
                selection += "\n"
                # self.advanceCursor(region) # BKJ edit -- this functionality was dumb
            else:
                selection += self.view.substr(region) 
                # selection = selection.split('\n')
                # self.detab(selection)
                # selection = '\n'.join(selection)
                selection += "\n\n"

        # BKJ edit -- want to be able to send empty lines
        # only proceed if selection is not empty
        # if(selection == "" or selection == "\n"):
        #     return

        self.send(selection)

    # BKJ addition -- strip tabs from python
    def detab(self, selection):
        selection = [x for x in selection if x != '']
        mintabs = min([len(re.sub('(^\t*).*', '\\1', x)) for x in selection])
        for m in range(0, mintabs):
            selection = [re.sub('^\t', '', x) for x in selection]
        return selection

    # def advanceCursor(self, region):
    #     (row, col) = self.view.rowcol(region.begin())

    #     # Make sure not to go past end of next line
    #     nextline = self.view.line(self.view.text_point(row + 1, 0))
    #     if nextline.size() < col:
    #         loc = self.view.text_point(row + 1, nextline.size())
    #     else:
    #         loc = self.view.text_point(row + 1, col)

    #     # Remove the old region and add the new one
    #     self.view.sel().subtract(region)
    #     self.view.sel().add(sublime.Region(loc, loc))
