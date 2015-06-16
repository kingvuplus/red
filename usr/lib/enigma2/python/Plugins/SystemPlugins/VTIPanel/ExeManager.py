# 2015.06.16 12:44:06 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/ExeManager.py
from Screens.Screen import Screen
from Components.Label import Label
from Components.MenuList import MenuList
from Components.ActionMap import ActionMap
from Components.GUIComponent import GUIComponent
from Components.config import config, getConfigListEntry, ConfigInteger, ConfigSubsection, ConfigSelection, ConfigText, NoSave, ConfigDirectory
from Components.ConfigList import ConfigListScreen
from Tools.Directories import pathExists, fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_CURRENT_PLUGIN, SCOPE_CURRENT_SKIN, SCOPE_METADIR
from Components.Sources.StaticText import StaticText
from Screens.MessageBox import MessageBox
from Components.Pixmap import Pixmap
from Tools.LoadPixmap import LoadPixmap
from Components.FileList import FileList
from Screens.Console import Console
from skin import loadSkin
#from plugin import checkvu
from os import path as os_path, mkdir as os_mkdir, listdir as os_listdir, walk as os_walk, access as os_access, W_OK as os_W_OK, X_OK, access, chmod, system
from __init__ import _
exelist = '/etc/enigma2/exelist.conf'
startdirectory = '/usr/script'

class ExtendedConfigTextOne(ConfigText):

    def __init__(self, default = '', fixed_size = True, visible_width = False):
        ConfigText.__init__(self, default=default, fixed_size=fixed_size, visible_width=visible_width)
        mapping = self.mapping
        if mapping:
            if '<' not in mapping[1]:
                mapping[1] += '<'
            if '>' not in mapping[1]:
                mapping[1] += '>'


class SettingExe:

    def __init__(self):
        self.entries = []
        self.exeList = exelist
        self.read()

    def read(self):
        self.entries = []
        if not fileExists(self.exeList):
            cmd = '/bin/touch %s' % self.exeList
            system(cmd)
            conf = open(self.exeList, 'r')
        else:
            conf = open(self.exeList, 'r')
        for line in conf:
            line = line.strip()
            full = line.split('::')
            command = full[0]
            commandoption = full[1]
            showexe = full[2]
            self.entries.append([command, commandoption, showexe])

        conf.close()

    def write(self):
        conf = open(self.exeList, 'w')
        for entry in self.entries:
            conf.write('%s::%s::%s\n' % (entry[0], entry[1], entry[2]))

        conf.close()

    def delete(self, exejob):
        for entry in self.entries:
            if entry[0] + entry[1] + entry[2] == exejob:
                self.entries.remove(entry)

    def get(self, exejob):
        for entry in self.entries:
            if entry[0] + entry[1] + entry[2] == exejob:
                command = entry[0]
                commandoption = entry[1]
                showentry = entry[2]
                return (command, commandoption, showentry)

    def modify(self, oldcommand, oldcommandoption, oldshowentry, command, commandoption, showentry):
        for entry in self.entries:
            if entry[0] == oldcommand and entry[1] == oldcommandoption and entry[2] == oldshowentry:
                entry[0] = command
                entry[1] = commandoption
                entry[2] = showentry

    def add(self, command, commandoption, showentry):
        self.entries.append([command, commandoption, showentry])


settings = SettingExe()

class ExeManager(Screen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        skin_path = plugin_path
        self.session = session
#       checkvu.runcheck()
        self.list = []
        settings.read()
        for exe in settings.entries:
            command = exe[0]
            commandoption = exe[1]
            showentry = exe[2]
            self.list.append((_('Execute: ') + command + ' ' + commandoption, command + commandoption + showentry))

        self.title = _('VTI ExeManager')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['showexe'] = MenuList(self.list)
        self['key_red'] = StaticText(_('Delete'))
        self['key_green'] = StaticText(_('Add'))
        self['key_yellow'] = StaticText(_('Modify'))
        self['key_blue'] = StaticText(_('Execute'))
        self['myActionMap'] = ActionMap(['OkCancelActions', 'ColorActions'], {'ok': self.modify,
         'cancel': self.cancel,
         'green': self.add,
         'red': self.remove,
         'yellow': self.modify,
         'blue': self.execute}, -1)

    def add(self):
        self.session.openWithCallback(self.updateList, addExe, self.skin_path)

    def modify(self):
        try:
            returnValue = self['showexe'].l.getCurrentSelection()[1]
        except:
            returnValue = None

        if returnValue is not None:
            exejob = returnValue
            self.session.openWithCallback(self.updateList, modifyExe, self.skin_path, exejob)

    def execute(self):
        try:
            returnValue = self['showexe'].l.getCurrentSelection()[1]
        except:
            returnValue = None

        if returnValue is not None:
            exejob = returnValue
            self.exeentryexecute = settings.get(exejob)
            self.command = self.exeentryexecute[0]
            self.commandoption = self.exeentryexecute[1]
            self.showentry = self.exeentryexecute[2]
            self.space = ' '
            cmd = self.command + self.space + self.commandoption
            if not fileExists(self.command):
                self.session.open(MessageBox, _('File %s was not found') % self.command, MessageBox.TYPE_ERROR, timeout=5)
            elif not access(self.command, X_OK):
                self.session.open(MessageBox, _('File %s is not executable') % self.command, MessageBox.TYPE_ERROR, timeout=5)
            elif self.showentry == 'showok':
                self.session.open(Console, _('VTI ExeManager'), [cmd])
            else:
                system(cmd)
                self.session.open(MessageBox, _('Command: %s was executed') % cmd, MessageBox.TYPE_INFO, timeout=5)

    def remove(self):
        try:
            returnValue = self['showexe'].l.getCurrentSelection()[1]
        except:
            returnValue = None

        if returnValue is not None:
            exejob = returnValue
            settings.delete(exejob)
            settings.write()
            self.updateList()

    def updateList(self, ret = None):
        settings.read()
        self.list = []
        for exe in settings.entries:
            command = exe[0]
            commandoption = exe[1]
            showentry = exe[2]
            self.list.append((_('Execute: ') + command + ' ' + commandoption, command + commandoption + showentry))

        self['showexe'].l.setList(self.list)

    def cancel(self):
        self.close(None)


class addExe(Screen, ConfigListScreen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.input_command = NoSave(ConfigDirectory(default=_('your executable')))
        self.input_option = NoSave(ExtendedConfigTextOne(default='', visible_width=50, fixed_size=False))
        self.input_showentry = NoSave(ConfigSelection(default='shownok', choices=[('shownok', _('no')), ('showok', _('yes'))]))
        self.title = _('Add a executable to ExeManager')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Save'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'InputActions'], {'ok': self.keySelect,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keySave}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session)
        self.createSetup()

    def createSetup(self):
        self.list = []
        self.exemanagerAddExecutable = getConfigListEntry(_('Command to execute : '), self.input_command)
        self.exemanagerAddOption = getConfigListEntry(_('Additional command options : '), self.input_option)
        self.exemanagerAddShowentry = getConfigListEntry(_('Show command output : '), self.input_showentry)
        self.list.append(self.exemanagerAddExecutable)
        self.list.append(self.exemanagerAddOption)
        self.list.append(self.exemanagerAddShowentry)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keySelect(self):
        sel = self['config'].getCurrent()
        if sel == self.exemanagerAddExecutable:
            self.session.openWithCallback(self.selectedFile, ExeManagerFile, startdirectory, self.skin_path)

    def selectedFile(self, res):
        if res is not None:
            self.input_command.value = res

    def keyCancel(self):
        self.close()

    def keySave(self):
        self.command = self.input_command.value
        self.commandoption = self.input_option.value
        self.showentry = self.input_showentry.value
        settings.add(self.command, self.commandoption, self.showentry)
        settings.write()
        self.close()


class modifyExe(Screen, ConfigListScreen):

    def __init__(self, session, plugin_path, exejob, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.exeentry = settings.get(exejob)
        self.command = self.exeentry[0]
        self.commandoption = self.exeentry[1]
        self.showentry = self.exeentry[2]
        self.input_command = NoSave(ConfigDirectory(default=self.command))
        self.input_commandoption = NoSave(ExtendedConfigTextOne(default=self.commandoption, visible_width=50, fixed_size=False))
        self.input_showentry = NoSave(ConfigSelection(default=self.showentry, choices=[('shownok', _('no')), ('showok', _('yes'))]))
        self.title = _('Modify execute command')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Save'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'InputActions'], {'ok': self.keySelect,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keySave}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session)
        self.createSetup()

    def createSetup(self):
        self.list = []
        self.exemanagerAddExecutable = getConfigListEntry(_('Command to execute : '), self.input_command)
        self.exemanagerAddOption = getConfigListEntry(_('Additional command options : '), self.input_commandoption)
        self.exemanagerAddShowentry = getConfigListEntry(_('Show command output : '), self.input_showentry)
        self.list.append(self.exemanagerAddExecutable)
        self.list.append(self.exemanagerAddOption)
        self.list.append(self.exemanagerAddShowentry)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keySelect(self):
        sel = self['config'].getCurrent()
        if sel == self.exemanagerAddExecutable:
            self.session.openWithCallback(self.selectedFile, ExeManagerFile, startdirectory, self.skin_path)

    def selectedFile(self, res):
        if res is not None:
            self.input_command.value = res

    def keyCancel(self):
        self.close()

    def keySave(self):
        self.oldcommand = self.command
        self.oldcommandoption = self.commandoption
        self.oldshowentry = self.showentry
        self.command = self.input_command.value
        self.commandoption = self.input_commandoption.value
        self.showentry = self.input_showentry.value
        settings.modify(self.oldcommand, self.oldcommandoption, self.oldshowentry, self.command, self.commandoption, self.showentry)
        settings.write()
        self.close()


class ExeManagerFile(Screen):

    def __init__(self, session, initDir, plugin_path):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self['filelist'] = FileList(initDir, inhibitMounts=False, inhibitDirs=False, showMountpoints=False)
        self['executable'] = Label()
        self['keyblue'] = Label()
        self['actions'] = ActionMap(['WizardActions',
         'DirectionActions',
         'ColorActions',
         'EPGSelectActions'], {'back': self.cancel,
         'left': self.left,
         'right': self.right,
         'up': self.up,
         'down': self.down,
         'ok': self.ok,
         'green': self.green,
         'blue': self.blue,
         'red': self.cancel}, -1)
        self.title = _('Select a file to execute')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('OK'))

    def cancel(self):
        self.close(None)

    def green(self):
        if self['filelist'].getSelection()[1] == True:
            self['executable'].setText(_('Invalid Choice'))
        else:
            directory = self['filelist'].getCurrentDirectory()
            if directory.endswith('/'):
                self.fullpath = self['filelist'].getCurrentDirectory() + self['filelist'].getFilename()
            else:
                self.fullpath = self['filelist'].getCurrentDirectory() + '/' + self['filelist'].getFilename()
            if not access(self.fullpath, X_OK):
                self['executable'].setText(_('File is not executable'))
            else:
                self.close(self.fullpath)

    def blue(self):
        notexec = self['keyblue'].getText()
        if notexec == 'chmod 755':
            directory = self['filelist'].getCurrentDirectory()
            if directory.endswith('/'):
                self.fullpath = self['filelist'].getCurrentDirectory() + self['filelist'].getFilename()
            else:
                self.fullpath = self['filelist'].getCurrentDirectory() + '/' + self['filelist'].getFilename()
            chmod(self.fullpath, 493)
            self['keyblue'].setText(_(' '))
            self['executable'].setText(self['filelist'].getFilename())

    def up(self):
        self['filelist'].up()
        self.updateFile()

    def down(self):
        self['filelist'].down()
        self.updateFile()

    def left(self):
        self['filelist'].pageUp()
        self.updateFile()

    def right(self):
        self['filelist'].pageDown()
        self.updateFile()

    def ok(self):
        if self['filelist'].canDescent():
            self['filelist'].descent()
            self.updateFile()

    def updateFile(self):
        currFolder = self['filelist'].getSelection()[0]
        if self['filelist'].getFilename() is not None:
            directory = self['filelist'].getCurrentDirectory()
            if directory.endswith('/'):
                self.fullpath = self['filelist'].getCurrentDirectory() + self['filelist'].getFilename()
            else:
                self.fullpath = self['filelist'].getCurrentDirectory() + '/' + self['filelist'].getFilename()
            if not access(self.fullpath, X_OK):
                if self['filelist'].getSelection()[1] == True:
                    self['executable'].setText(currFolder)
                    self['keyblue'].setText(_(' '))
                else:
                    self['executable'].setText(_('File is not executable'))
                    self['keyblue'].setText(_('chmod 755'))
            else:
                self['executable'].setText(self['filelist'].getFilename())
                self['keyblue'].setText(_(' '))
        else:
            currFolder = self['filelist'].getSelection()[0]
            if currFolder is not None:
                self['executable'].setText(currFolder)
                self['keyblue'].setText(_(' '))
            else:
                self['executable'].setText(_('Invalid Choice'))
                self['keyblue'].setText(_(' '))
