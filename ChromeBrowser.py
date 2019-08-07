import mechanize
import http.cookiejar as cookielib
import os
from bs4 import BeautifulSoup
import re

from helpers import create_filename

USERNAME = os.environ['CATALYST_USERNAME']
PASSWORD = os.environ['CATALYST_PASSWORD']


class ChromeBrowser:
    def __init__(self, datetime_object):
        self.current_date_padded = '{d.month:02}/{d.day:02}/{d.year}'.format(d=datetime_object)
        self.current_date = '{d.month}/{d.day}/{d.year}'.format(d=datetime_object)
        cj = cookielib.LWPCookieJar()
        self.br = mechanize.Browser()
        self.br.set_cookiejar(cj)

        # Browser options
        self.br.set_handle_equiv(True)
        self.br.set_handle_gzip(True)
        self.br.set_handle_redirect(True)
        self.br.set_handle_referer(True)
        self.br.set_handle_robots(False)
        self.br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        self.br.addheaders = [('User-agent',
                          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.142 Safari/537.36')]

    def log_in(self):
        self.br.open("https://datafinch.com/")

        self.br.follow_link(text="Catalyst Login")

        self.br.select_form(nr=0)
        self.br.form['Username'] = USERNAME
        self.br.form['Password'] = PASSWORD
        self.br.submit()

        self.br.select_form(nr=0)
        self.br.submit()

    def get_recently_mastered(self):
        rm_list = []
        recently_mastered_response = self.br.open_novisit(
            url_or_request='https://secure.datafinch.com/Widget/RecentlyMasteredTargets?_=Evelyn%20Lehman')
        recently_mastered_soup = BeautifulSoup(recently_mastered_response.read(), 'html.parser')
        rm_tr_list = recently_mastered_soup.find_all('tr')
        for row in rm_tr_list:
            rm_td_list = row.find_all('td')
            if rm_td_list:
                rm_target = rm_td_list[0].text.strip()
                rm_date = rm_td_list[2].text.strip()
                if rm_date == self.current_date_padded:
                    rm_list.append(rm_target)
        return rm_list

    def get_trial_count(self):
        tc_list = []
        trial_count_response = self.br.open_novisit(
            url_or_request='https://secure.datafinch.com/Widget/TrialCounts?_=Evelyn%20Lehman')
        trial_count_soup = BeautifulSoup(trial_count_response.read(), 'html.parser')
        tc_tr_list = trial_count_soup.find_all('tr')
        for row in tc_tr_list[:6]:
            tc_td_list = row.find_all('td')
            if tc_td_list:
                tc_target = tc_td_list[0].text.strip()
                tc_list.append(tc_target)
        return tc_list

    def get_attachments(self):
        self.br.follow_link(text="Assessments")
        self.br.follow_link(text="Form Responses")

        soup = BeautifulSoup(self.br.response().read(), 'html.parser')

        tbody = soup.find("tbody")
        tr_list = tbody.find_all('tr')
        attachment_list = []
        for i, tr in enumerate(tr_list):
            td_list = tr.find_all('td')
            form_date = td_list[0].text
            form_type = td_list[1].text
            form_user = td_list[2].text
            row_date = re.findall(r"^[0-9/]+", form_date)
            if row_date[0] == self.current_date:
                links = tr.find_all('a')
                br_link = self.br.find_link(url=links[1]['href'])
                (filename, headers) = self.br.retrieve(
                    br_link.absolute_url
                )
                attachment_list.append(
                    {
                        'tmp_name': filename,
                        'friendly_name': create_filename(form_date, form_type, form_user)
                    })
                # os.remove(filename)
        return attachment_list
