import gevent
import requests
import json
from datetime import datetime

from ajenti.api import *
from ajenti.api.sensors import Sensor
from ajenti.plugins.main.api import SectionPlugin
from ajenti.ui import on
import ajenti


ENDPOINT = 'http://ajenti.local.org:8080/docking-bay/receive/%i'
#ENDPOINT = None


@plugin
class AjentiOrgReporter (BasePlugin):
    default_classconfig = {'key': None}

    def init(self):
        self.last_report = None
        gevent.spawn(self.worker)

    @classmethod
    def classinit(cls):
        cls.get()

    def get_key(self):
        if not 'key' in self.classconfig:
            return None
        return self.classconfig['key']

    def set_key(self, key):
        self.classconfig['key'] = key
        self.save_classconfig()

    def worker(self):
        if not ENDPOINT:
            return
        while True:
            datapack = {'sensors': {}}

            for sensor in Sensor.get_all():
                data = {}
                for variant in sensor.get_variants():
                    data[variant] = sensor.value(variant)
                datapack['sensors'][sensor.id] = data

            gevent.sleep(3)
            url = ENDPOINT % ajenti.config.tree.installation_id

            if not self.get_key():
                continue

            try:
                requests.post(url, data={
                    'data': json.dumps(datapack),
                    'key': self.get_key()
                })
                self.last_report = datetime.now()
            except Exception, e:
                print e


@plugin
class AjentiOrgSection (SectionPlugin):
    def init(self):
        self.title = 'Ajenti.org'
        self.icon = 'group'
        self.category = ''
        self.order = 25
        self.append(self.ui.inflate('ajenti_org:main'))

    def on_page_load(self):
        self.refresh()

    def refresh(self):
        key = AjentiOrgReporter.get().get_key()
        self.find('pane-not-configured').visible = key is None
        self.find('pane-configured').visible = key is not None
        self.find('last-report').text = str(AjentiOrgReporter.get().last_report)

    @on('save-key', 'click')
    def on_save_key(self):
        AjentiOrgReporter.get().set_key(self.find('machine-key').value)
        self.refresh()