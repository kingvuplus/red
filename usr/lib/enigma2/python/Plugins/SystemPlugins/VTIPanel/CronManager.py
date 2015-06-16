# 2015.06.16 12:23:20 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/CronManager.py
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
from skin import loadSkin
#from plugin import checkvu
from os import path as os_path, mkdir as os_mkdir, listdir as os_listdir, walk as os_walk, access as os_access, W_OK as os_W_OK, X_OK, access, chmod, system
from __init__ import _
cronfile = '/etc/cron/crontabs/root'
cronupdate = '/etc/cron/crontabs/cron.update'
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


class ExtendedConfigTextTwo(ConfigText):

    def __init__(self, default = '', fixed_size = True, visible_width = False):
        ConfigText.__init__(self, default=default, fixed_size=fixed_size, visible_width=visible_width)
        mapping = self.mapping
        if mapping:
            mapping[1] = '1*-/,'
            mapping[2] = '2'
            mapping[3] = '3'
            mapping[4] = '4'
            mapping[5] = '5'
            mapping[6] = '6'
            mapping[7] = '7'
            mapping[8] = '8'
            mapping[9] = '9'
            mapping[0] = '0'


class SettingList:

    def __init__(self):
        self.entries = []
        self.cronFile = cronfile
        self.read()

    def read(self):
        global comment
        self.entries = []
        if not fileExists(self.cronFile):
            cmd = '/bin/mkdir -p /etc/cron/crontabs ; /bin/touch %s' % self.cronFile
            system(cmd)
            conf = open(self.cronFile, 'r')
        else:
            conf = open(self.cronFile, 'r')
        comment = ''
        for line in conf:
            line1 = line.strip()
            if line1.startswith('#'):
                comment += line1 + '\n'
            else:
                line1 = line1.replace('  ', ' ')
                linelength = line1
                counter = linelength.count(' ')
                while counter > 4:
                    linelength = linelength[:-1]
                    counter = linelength.count(' ')

                full = len(line1)
                front = len(linelength)
                short = full - front
                time2 = linelength.split(' ')
                command = line1[-short:].lstrip()
                minute = time2[0]
                hour = time2[1]
                day = time2[2]
                month = time2[3]
                weekday = time2[4]
                self.entries.append([command,
                 minute,
                 hour,
                 day,
                 month,
                 weekday])

        conf.close()

    def write(self):
        conf = open(self.cronFile, 'w')
        if comment:
            conf.write('%s' % comment)
        for entry in self.entries:
            conf.write('%s %s %s %s %s %s\n' % (entry[1],
             entry[2],
             entry[3],
             entry[4],
             entry[5],
             entry[0]))

        conf.close()

    def delete(self, cronjob):
        for entry in self.entries:
            if entry[0] + entry[1] + entry[2] + entry[3] + entry[4] + entry[5] == cronjob:
                self.entries.remove(entry)

    def get(self, cronjob):
        for entry in self.entries:
            if entry[0] + entry[1] + entry[2] + entry[3] + entry[4] + entry[5] == cronjob:
                command = entry[0]
                minute = entry[1]
                hour = entry[2]
                day = entry[3]
                month = entry[4]
                weekday = entry[5]
                return (command,
                 minute,
                 hour,
                 day,
                 month,
                 weekday)

    def modify(self, oldcommand, oldminute, oldhour, oldday, oldmonth, oldweekday, command, minute, hour, day, month, weekday):
        for entry in self.entries:
            if entry[0] == oldcommand and entry[1] == oldminute and entry[2] == oldhour and entry[3] == oldday and entry[4] == oldmonth and entry[5] == oldweekday:
                entry[0] = command
                entry[1] = minute
                entry[2] = hour
                entry[3] = day
                entry[4] = month
                entry[5] = weekday

    def add(self, command, minute, hour, day, month, weekday):
        self.entries.append([command,
         minute,
         hour,
         day,
         month,
         weekday])


settings = SettingList()

class CronManager(Screen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.session = session
#       checkvu.runcheck()
        self.list = []
        settings.read()
        for job in settings.entries:
            command = job[0]
            minute = job[1]
            hour = job[2]
            day = job[3]
            month = job[4]
            weekday = job[5]
            self.list.append(('CronJob: ' + command, command + minute + hour + day + month + weekday))

        self.title = _('VTI CronManager')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['showjobs'] = MenuList(self.list)
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
        self.session.openWithCallback(self.updateList, addJob, self.skin_path)

    def modify(self):
        try:
            returnValue = self['showjobs'].l.getCurrentSelection()[1]
        except:
            returnValue = None

        if returnValue is not None:
            cronjob = returnValue
            self.session.openWithCallback(self.updateList, modifyJob, self.skin_path, cronjob)

    def execute(self):
        try:
            returnValue = self['showjobs'].l.getCurrentSelection()[1]
        except:
            returnValue = None

        if returnValue is not None:
            cronjob = returnValue
            self.jobentryexecute = settings.get(cronjob)
            cmd = self.jobentryexecute[0]
            system(cmd)
            self.session.open(MessageBox, _('Command: %s was executed') % cmd, MessageBox.TYPE_INFO, timeout=5)

    def remove(self):
        try:
            returnValue = self['showjobs'].l.getCurrentSelection()[1]
        except:
            returnValue = None

        if returnValue is not None:
            cronjob = returnValue
            settings.delete(cronjob)
            settings.write()
            self.updateList()

    def updateList(self, ret = None):
        settings.read()
        self.list = []
        for job in settings.entries:
            command = job[0]
            minute = job[1]
            hour = job[2]
            day = job[3]
            month = job[4]
            weekday = job[5]
            self.list.append(('CronJob: ' + command, command + minute + hour + day + month + weekday))

        self['showjobs'].l.setList(self.list)

    def cancel(self):
        cmd = '/bin/echo "root" > %s' % cronupdate
        system(cmd)
        self.close(None)


class addJob(Screen, ConfigListScreen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.input_option = NoSave(ExtendedConfigTextOne(default='', visible_width=50, fixed_size=False))
        self.input_executable = NoSave(ConfigDirectory(default=_('your cronjob')))
        self.input_minute = NoSave(ExtendedConfigTextTwo(default='', visible_width=50, fixed_size=False))
        self.input_hour = NoSave(ExtendedConfigTextTwo(default='', visible_width=50, fixed_size=False))
        self.input_day = NoSave(ExtendedConfigTextTwo(default='', visible_width=50, fixed_size=False))
        self.input_month = NoSave(ExtendedConfigTextTwo(default='', visible_width=50, fixed_size=False))
        self.input_weekday = NoSave(ExtendedConfigTextTwo(default='', visible_width=50, fixed_size=False))
        self.title = _('Add a job to CronManager')
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
        self.cronmanagerAddExecutable = getConfigListEntry(_('Command to execute : '), self.input_executable)
        self.cronmanagerAddOption = getConfigListEntry(_('Additional command options : '), self.input_option)
        self.cronmanagerAddMinute = getConfigListEntry(_('Input minute : '), self.input_minute)
        self.cronmanagerAddHour = getConfigListEntry(_('Input hour : '), self.input_hour)
        self.cronmanagerAddDay = getConfigListEntry(_('Input day : '), self.input_day)
        self.cronmanagerAddMonth = getConfigListEntry(_('Input month : '), self.input_month)
        self.cronmanagerAddYear = getConfigListEntry(_('Input weekday : '), self.input_weekday)
        self.list.append(self.cronmanagerAddExecutable)
        self.list.append(self.cronmanagerAddOption)
        self.list.append(self.cronmanagerAddMinute)
        self.list.append(self.cronmanagerAddHour)
        self.list.append(self.cronmanagerAddDay)
        self.list.append(self.cronmanagerAddMonth)
        self.list.append(self.cronmanagerAddYear)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keySelect(self):
        sel = self['config'].getCurrent()
        if sel == self.cronmanagerAddExecutable:
            self.session.openWithCallback(self.selectedFile, CronManagerFile, startdirectory, self.skin_path)

    def selectedFile(self, res):
        if res is not None:
            self.input_executable.value = res

    def keyCancel(self):
        self.close()

    def keySave(self):
        if self.input_option.value is not ' ':
            self.command = self.input_executable.value + ' ' + self.input_option.value
        else:
            self.command = self.input_executable.value
        if self.input_minute.value == '':
            self.minute = '*'
        else:
            self.minute = self.input_minute.value
        if self.input_hour.value == '':
            self.hour = '*'
        else:
            self.hour = self.input_hour.value
        if self.input_day.value == '':
            self.day = '*'
        else:
            self.day = self.input_day.value
        if self.input_month.value == '':
            self.month = '*'
        else:
            self.month = self.input_month.value
        if self.input_weekday.value == '':
            self.weekday = '*'
        else:
            self.weekday = self.input_weekday.value
        settings.add(self.command, self.minute, self.hour, self.day, self.month, self.weekday)
        settings.write()
        self.close()


class modifyJob(Screen, ConfigListScreen):

    def __init__(self, session, plugin_path, cronjob, args = 0):
        Screen.__init__(self, session)
        self.skin_path = plugin_path
        self.jobentry = settings.get(cronjob)
        self.oldcommand = self.jobentry[0]
        self.command = self.jobentry[0]
        self.minute = self.jobentry[1]
        self.hour = self.jobentry[2]
        self.day = self.jobentry[3]
        self.month = self.jobentry[4]
        self.weekday = self.jobentry[5]
        if self.minute == '*':
            self.minute_clean = ''
        else:
            self.minute_clean = self.minute
        if self.hour == '*':
            self.hour_clean = ''
        else:
            self.hour_clean = self.hour
        if self.day == '*':
            self.day_clean = ''
        else:
            self.day_clean = self.day
        if self.month == '*':
            self.month_clean = ''
        else:
            self.month_clean = self.month
        if self.weekday == '*':
            self.weekday_clean = ''
        else:
            self.weekday_clean = self.weekday
        self.input_command = NoSave(ExtendedConfigTextOne(default=self.command, visible_width=50, fixed_size=False))
        self.input_minute = NoSave(ExtendedConfigTextTwo(default=self.minute_clean, visible_width=50, fixed_size=False))
        self.input_hour = NoSave(ExtendedConfigTextTwo(default=self.hour_clean, visible_width=50, fixed_size=False))
        self.input_day = NoSave(ExtendedConfigTextTwo(default=self.day_clean, visible_width=50, fixed_size=False))
        self.input_month = NoSave(ExtendedConfigTextTwo(default=self.month_clean, visible_width=50, fixed_size=False))
        self.input_weekday = NoSave(ExtendedConfigTextTwo(default=self.weekday_clean, visible_width=50, fixed_size=False))
        self.title = _('Modify a CronManager job')
        try:
            self['title'] = StaticText(self.title)
        except:
            print 'self["title"] was not found in skin'

        self['key_red'] = StaticText(_('Cancel'))
        self['key_green'] = StaticText(_('Save'))
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions', 'InputActions'], {'ok': self.keySave,
         'cancel': self.keyCancel,
         'red': self.keyCancel,
         'green': self.keySave}, -1)
        self.list = []
        ConfigListScreen.__init__(self, self.list, session=session)
        self.createSetup()

    def createSetup(self):
        self.list = []
        self.cronmanagerAddCommand = getConfigListEntry(_('Command to execute : '), self.input_command)
        self.cronmanagerAddMinute = getConfigListEntry(_('Input minute : '), self.input_minute)
        self.cronmanagerAddHour = getConfigListEntry(_('Input hour : '), self.input_hour)
        self.cronmanagerAddDay = getConfigListEntry(_('Input day : '), self.input_day)
        self.cronmanagerAddMonth = getConfigListEntry(_('Input month : '), self.input_month)
        self.cronmanagerAddYear = getConfigListEntry(_('Input weekday : '), self.input_weekday)
        self.list.append(self.cronmanagerAddCommand)
        self.list.append(self.cronmanagerAddMinute)
        self.list.append(self.cronmanagerAddHour)
        self.list.append(self.cronmanagerAddDay)
        self.list.append(self.cronmanagerAddMonth)
        self.list.append(self.cronmanagerAddYear)
        self['config'].list = self.list
        self['config'].l.setList(self.list)

    def keyCancel(self):
        self.close()

    def keySave(self):
        self.oldcommand = self.oldcommand
        self.oldminute = self.minute
        self.oldhour = self.hour
        self.oldday = self.day
        self.oldmonth = self.month
        self.oldweekday = self.weekday
        self.command = self.input_command.value
        if self.input_minute.value == '':
            self.minute = '*'
        else:
            self.minute = self.input_minute.value
        if self.input_hour.value == '':
            self.hour = '*'
        else:
            self.hour = self.input_hour.value
        if self.input_day.value == '':
            self.day = '*'
        else:
            self.day = self.input_day.value
        if self.input_month.value == '':
            self.month = '*'
        else:
            self.month = self.input_month.value
        if self.input_weekday.value == '':
            self.weekday = '*'
        else:
            self.weekday = self.input_weekday.value
        settings.modify(self.oldcommand, self.oldminute, self.oldhour, self.oldday, self.oldmonth, self.oldweekday, self.command, self.minute, self.hour, self.day, self.month, self.weekday)
        settings.write()
        self.close()


class CronManagerFile(Screen):

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
        self.title = _('Select a executable file for a cronjob')
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
