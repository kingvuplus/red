# 2015.06.16 12:49:13 CET
#Embedded file name: /usr/lib/enigma2/python/Plugins/SystemPlugins/VTIPanel/NewsCenter.py
from Components.ActionMap import ActionMap
from Components.Console import Console
from Components.config import config
from Components.GUIComponent import GUIComponent
from Components.Label import Label
from Components.Pixmap import Pixmap
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.Sources.List import List
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Tools.BoundFunction import boundFunction
from Tools.Directories import *
from Tools.LoadPixmap import LoadPixmap
from Tools.Notifications import AddNotificationWithCallback
from skin import loadSkin
from os import path as os_path, remove
from UpgradeVti import UpdatePlugin
from Tools.HardwareInfoVu import HardwareInfoVu
from enigma import getVTiVersionString, eTimer
import xml.dom.minidom
from xml.dom.minidom import Node
from cPickle import dump, load
import urllib2
from __init__ import _
packagetmpfile = '/tmp/.package.tmp'
cache_file = '/tmp/.updatecache'
vumodel = HardwareInfoVu().get_device_name()

def getHeader():
    imageversion = getVTiVersionString()
    ret = 'VTi ' + imageversion + ' (Vu+ '
    if vumodel == 'duo':
        ret += 'Duo)\n'
    elif vumodel == 'solo':
        ret += 'Solo)\n'
    elif vumodel == 'uno':
        ret += 'Uno)\n'
    elif vumodel == 'ultimo':
        ret += 'Ultimo)\n'
    elif vumodel == 'solo2':
        ret += 'Solo2)\n'
    elif vumodel == 'duo2':
        ret += 'Duo2)\n'
    elif vumodel == 'solose':
        ret += 'Solo SE)\n'
    elif vumodel == 'zero':
        ret += 'zero)\n'
    return ret


header = getHeader()

def write_cache(cache_data):
    if not os_path.isdir(os_path.dirname(cache_file)):
        try:
            mkdir(os_path.dirname(cache_file))
        except OSError:
            pass

    fd = open(cache_file, 'w')
    dump(cache_data, fd, -1)
    fd.close()


def load_cache():
    fd = open(cache_file)
    cache_data = load(fd)
    fd.close()
    return cache_data


def newsURL():
    f = open('/etc/opkg/all-feed.conf', 'r')
    news = f.readline().strip('src/gz VTi-all ')
    f.close()
    news = news.strip()
    news = news.replace('all', 'vtinews.xml')
    return news


def skip_entry(entry):
    if entry.hasAttribute('require'):
        require = entry.getAttribute('require').split(',')
        if len(require) and vumodel not in require:
            return True
    return False


def parse_xml():
    list = []
    xml_ok = True
    news_url = newsURL()
    try:
        news = urllib2.urlopen(news_url, None, 5.0).read()
    except urllib2.HTTPError:
        return 2
    except urllib2.URLError:
        return 3

    try:
        xmldoc = xml.dom.minidom.parseString(news)
    except xml.parsers.expat.ExpatError:
        return 3

    news = None
    for node in xmldoc.getElementsByTagName('update'):
        if skip_entry(node):
            continue
        update_type = 'normal'
        if node.hasAttribute('type'):
            update_type = node.getAttribute('type')
        title = node.getElementsByTagName('title')
        update_title = title[0].firstChild.data
        update_list = node.getElementsByTagName('item')
        p_item_list = []
        for entry in update_list:
            if skip_entry(entry):
                continue
            my_item = None
            for update_item in entry.getElementsByTagName('itemtext'):
                if update_item.firstChild:
                    my_item = update_item.firstChild.data

            p_subitem_list = []
            for topic in entry.getElementsByTagName('description'):
                if topic.firstChild:
                    if skip_entry(topic):
                        continue
                    topic_description = topic.firstChild.data
                    p_subitem_list.append(topic_description)

            p_item_list.append((my_item, p_subitem_list))

        list.append((update_title, p_item_list, update_type))

    xmldoc.unlink()
    write_cache(list)
    list = None
    return 1


class AllNews(Screen):

    def __init__(self, session, plugin_path, args = 0):
        Screen.__init__(self, session)
        self.skinName = ['AllNews', 'BackupSuite']
        self.skin_path = plugin_path
        self.session = session
        self.title = _('News about VTI')
        try:
            self['title'] = StaticText(self.title)
        except:
            pass

        self.png_normal = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/update_normal.png'))
        self.png_info = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/update_info.png'))
        self.png_urgent = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, 'SystemPlugins/VTIPanel/pictures/update_urgent.png'))
        self.list = [('loading', _('Please wait ...'), self.png_info)]
        self['menu'] = List(self.list)
        self['status'] = Label()
        self['header'] = Label(header)
        self['key_red'] = StaticText(_('Exit'))
        self['key_green'] = StaticText(_('Update'))
        self['key_blue'] = StaticText(_('show Updates'))
        self['key_yellow'] = StaticText()
        self['key_info'] = StaticText()
        self['shortcuts'] = ActionMap(['SetupActions', 'ColorActions'], {'ok': self.runMenuEntry,
         'cancel': self.keyCancel,
         'green': self.greenKey,
         'red': self.keyCancel,
         'blue': self.blueKey}, -2)
        self.onLayoutFinish.append(self.setMenu)

    def greenKey(self):
        self.session.open(UpdatePlugin)

    def blueKey(self):
        self.runMenuEntry(show_upgradable=True)

    def setMenu(self):
        self.delayTimer = eTimer()
        self.delayTimer.start(100, True)
        self.delayTimer.callback.append(self.createMenu)

    def createMenu(self):
        self.list = []
        res = parse_xml()
        if res == 1:
            list = load_cache()
            for item in list:
                update_type = str(item[2])
                png = self.png_normal
                if update_type == 'urgent':
                    png = self.png_urgent
                elif update_type == 'info':
                    png = self.png_info
                self.list.append((item, str(item[0]), png))

            list = None
        elif res == 2:
            message = _('It seems that your Internet connection is not ok, please check it')
        elif res == 3:
            message = _('The news file can not be analyzed, please be patient and try again later')
        self['menu'].updateList(self.list)
        if res > 1:
            self.session.open(MessageBox, message, MessageBox.TYPE_ERROR, timeout=30)

    def runMenuEntry(self, show_upgradable = False):
        idx = self['menu'].getIndex()
        if idx or len(self.list):
            self.session.openWithCallback(self.setMenuIndex, VTiUpdateInfo, idx, show_upgradable)

    def setMenuIndex(self, idx = 0):
        self['menu'].setIndex(idx)

    def keyCancel(self):
        self.list = None
        for f in (packagetmpfile, cache_file):
            if fileExists(f):
                remove(f)

        self.close()


class VTiUpdateInfo(Screen):

    def __init__(self, session, idx = 0, show_upgradable = False):
        self.session = session
        Screen.__init__(self, session)
        self.skinName = ['VTiUpdateInfo']
        self.title = _('News about VTI')
        try:
            self['title'] = StaticText(self.title)
        except:
            pass

        self.Console = None
        self.list = load_cache()
        self.idx = idx
        self.infotxt = self.list[self.idx]
        self['update'] = ScrollLabel(self.getNews())
        self['header'] = Label(self.getHeaderWithDate())
        self['key_red'] = StaticText(_('Close'))
        self['key_green'] = StaticText(_('Update'))
        self['key_yellow'] = StaticText(_(' '))
        self['key_blue'] = StaticText(_('show Updates'))
        self['actions'] = ActionMap(['ColorActions', 'SetupActions', 'EventViewActions'], {'red': self.closeNews,
         'green': self.greenPressed,
         'yellow': self.yellowPressed,
         'blue': self.bluePressed,
         'cancel': self.closeNews,
         'nextEvent': self.prevUpdate,
         'prevEvent': self.nextUpdate,
         'pageUp': self.pageUp,
         'pageDown': self.pageDown}, -1)
        if show_upgradable:
            self.bluePressed()

    def getText(self, what):
        self.what = what
        if self.what == 'news':
            ret = self.getNews()
        elif self.what == 'updates':
            ret = self.getUpdates()
        elif self.what == 'header':
            ret = self.getHeaderWithDate()
        return ret

    def bluePressed(self):
        try:
            self['title'].setText(_('Upgradable Packages'))
        except Exception as e:
            pass

        self['key_blue'].setText(_(' '))
        self['key_yellow'].setText(_('show News'))
        self['update'].setText(_('Please wait ...'))
        self.getUpdates()

    def yellowPressed(self):
        try:
            self['title'].setText(_('News about VTI'))
        except Exception as e:
            pass

        self['key_blue'].setText(_('show Updates'))
        self['key_yellow'].setText(_(' '))
        self['update'].setText(self.getText('news'))

    def pageUp(self):
        self['update'].pageUp()

    def pageDown(self):
        self['update'].pageDown()

    def nextUpdate(self):
        if self.idx + 1 < len(self.list):
            self.idx += 1
            self.updateText()

    def prevUpdate(self):
        if self.idx != 0:
            self.idx += -1
            self.updateText()

    def updateText(self):
        self.infotxt = self.list[self.idx]
        self['update'].setText(self.getNews())
        self['header'].setText(self.getHeaderWithDate())
        self['key_blue'].setText(_('show Updates'))
        self['key_yellow'].setText(_(' '))

    def greenPressed(self):
        self.session.open(UpdatePlugin)

    def closeNews(self):
        if self.Console is not None:
            if len(self.Console.appContainers):
                for name in self.Console.appContainers.keys():
                    self.Console.kill(name)

        self.list = None
        self.close(self.idx)

    def getNews(self):
        ret = ''
        if len(self.infotxt[1]):
            for item in self.infotxt[1]:
                ret += '* ' + str(item[0]) + '\n'
                if len(item[1]):
                    for desc in item[1]:
                        ret += '    - ' + str(desc) + '\n'

                    ret += '\n'

        return ret

    def getHeaderWithDate(self):
        ret = header + self.infotxt[0]
        return str(ret)

    def getUpdates(self):
        if not fileExists(packagetmpfile):
            self.Console = Console()
            cmd = 'opkg update'
            self.Console.ePopen(cmd, self.opkg_update_finished)
        else:
            self.opkg_upgrade_finished(result=None, retval=0)

    def opkg_update_finished(self, result, retval, extra_args = None):
        if not self.Console:
            self.Console = Console()
        cmd = 'opkg list-upgradable > %s' % packagetmpfile
        self.Console.ePopen(cmd, self.opkg_upgrade_finished)

    def opkg_upgrade_finished(self, result, retval, extra_args = None):
        if fileExists(packagetmpfile):
            f = open(packagetmpfile, 'r')
            updates = f.readlines()
            f.close()
            txt = ''
            for line in updates:
                line = line.split(' - ')
                if len(line) >= 3:
                    packagename = line[0].strip()
                    oldversion = line[1].strip()
                    newversion = line[2].strip()
                    if not packagename == '':
                        txt += _('\nPackage : %s \nold version : %s \nnew version : %s\n') % (packagename, oldversion, newversion)

            checkempty = len(txt)
            if checkempty == 0:
                txt = _('\nYour System is up to date')
            else:
                config.usage.update_available.value = True
        else:
            txt = _('It seems that your Internet connection is not ok, please check it')
        self['update'].setText(txt)


class UpdateNotification:

    def setSession(self, session, plugin_path):
        self.session = session
        self.plugin_path = plugin_path

    def show_NewsCenter(self, res = None):
        if config.usage.check_for_updates.value > 0:
            intervall = config.usage.check_for_updates.value * 1000 * 3600
            self.update_timer.start(intervall, True)
        if res:
            f = open(packagetmpfile, 'w+')
            f.write(self.upgradable_packages)
            f.close
            self.session.open(AllNews, self.plugin_path)

    def check_updates(self):
        self.Console = Console()
        cmd = 'opkg update'
        self.Console.ePopen(cmd, self.opkg_update_finished)

    def opkg_update_finished(self, result, retval, extra_args = None):
        if not self.Console:
            self.Console = Console()
        cmd = 'opkg list-upgradable'
        self.Console.ePopen(cmd, self.opkg_upgrade_finished)

    def opkg_upgrade_finished(self, result, retval, extra_args = None):
        is_update = False
        if len(result):
            check_result = result.split('\n', 10)
            if len(check_result):
                for line in check_result:
                    line = line.split(' - ')
                    if len(line) >= 3:
                        is_update = True
                        break

        if is_update:
            self.upgradable_packages = result
            config.usage.update_available.value = True
            if config.usage.show_notification_for_updates.value:
                message = _('There are updates available.\nDo you want to open Software Update menu ?')
                AddNotificationWithCallback(boundFunction(self.show_NewsCenter), MessageBox, message, timeout=0)
            else:
                self.show_NewsCenter(res=None)
        else:
            config.usage.update_available.value = False
            if config.usage.check_for_updates.value > 0:
                intervall = config.usage.check_for_updates.value * 1000 * 3600
                self.update_timer.start(intervall, True)

    def init_timer(self):
        self.update_timer = eTimer()
        self.update_timer.callback.append(self.check_updates)
        self.update_timer.start(60000, True)


update_notification = UpdateNotification()
