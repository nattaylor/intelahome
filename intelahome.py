import requests
import xml.etree.ElementTree
import re
import datetime
import logging
import os
import enum


class Report(enum.Enum):
    LiveDemandReport = {
        'url': 'https://www.intelahome.com/plugins/live_demand/live_demand.asp',
        'attr': 'name',
        'type': 'time',
        'format': '%I:%M:%S %p',
    }
    
    UsageReport = {
        'url': 'https://www.intelahome.com/plugins/meter_usage/meter_usage.asp',
        'attr': 'label',
        'type': 'time',
        'format': '%I %p',
    }
    
    UsageComparisonReportWeek = {
        'url': 'https://www.intelahome.com/plugins/meter_usage/meter_usage_week.asp',
        'attr': 'label',
        'type': 'date',
        'format': '%m/%d',
    }
    
    UsageReportMonth = {
        'url': 'https://www.intelahome.com/plugins/meter_usage/meter_usage_month.asp',
        'attr': 'label',
        'format': '%m/%d',
        'type': 'date',
    }


class Intelahome:
    """Retrieve Intelahome structured electricity usage and demand data
    
    Usage:
    >>> %env CREDS=login=user%40domain.com&password=abc123
    >>> I = Intelahome()
    >>> I.report('UsageReport')
    {'2023-01-02T16:00:00': 0.123}
    
    Their web portal responds with HTML documents containing XML documents.
    This code parses that XML and makes the data consistent
    """
    
    def __init__(self):
        """Set up an Intelahome session"""
        self.s = requests.Session()
        self._login()
    
    def __del__(self):
        self.s.close()
    
    def _login(self):
        login = self.s.request(
            "POST", 
            "https://www.intelahome.com/index.asp",
            data=f'action=LOG-IN&{os.getenv("IHCREDS")}&I1.x=15&I1.y=15&RM=ON',
            headers = {'Content-Type': 'application/x-www-form-urlencoded'},
        )
        if not 'intelahome' in self.s.cookies:
            raise RuntimeError('Error.  Login Failed.  Did you set $IHCREDS?')
    
    def _parse(self, response):
        self.yesterday = True
        # This is an XML document included in the HTML response
        data = re.search('"dataSource": "(.*?)"', response.text).group(1).replace('&', '&amp;')
        root = xml.etree.ElementTree.fromstring(data)
        report = getattr(Report, root.get('exportfilename')).value
        # Some reports use 'label' but others use 'name'
        categories = iter([x.get(report['attr']) for x in root.iter('category')])
        ts = {}
        for s in root.iter('set'):
            v = float(s.attrib.get('value')) if s.attrib.get('value') != '' else 0
            t = self._parse_datetime(next(categories), report)
            ts[t.isoformat()] = v
        return ts
    
    def _parse_datetime(self, t, report):
        if report['type'] == 'time':
            if '/' in t:
                t = '12:00:00 AM'
                self.yesterday = False
            if t == '12 AM':
                self.yesterday = False
            if self.yesterday:
                day = (datetime.datetime.now() - datetime.timedelta(days = 1)).strftime("%Y-%m-%d")
            else:
                day = datetime.datetime.now().strftime("%Y-%m-%d")
            return datetime.datetime.strptime(f'{day} {t}', f'%Y-%m-%d {report["format"]}')
        elif report['type'] == 'date':
            return datetime.datetime.strptime(f'{datetime.datetime.now().year}/{t}', f'%Y/{report["format"]}')
    
    def report(self, report: Report)->dict:
        """Retrieve a report"""
        return self._parse(self.s.get(report.value['url']))

