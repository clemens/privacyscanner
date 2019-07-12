from privacyscanner.scanmodules.chromedevtools.extractors.base import Extractor
from datetime import datetime


class CookieSyncExtractor(Extractor):

    def extract_information(self):
        cookies_synced = dict(cookie_sync_occured=None, sync_occurence_counter=0, sync_relation=[], sync_companies=[])
        tracker_requests = []
        tracker_cookies = []

        for request in self.page.request_log:
            if request['is_thirdparty']:
                tracker_requests.append(request)

        for cookie in self.result['cookies']:
            if cookie['is_tracker']:
                tracker_cookies.append(cookie)

        if len(tracker_cookies) == 0:
            cookies_synced['cookie_sync_occured'] = False

        for cookie in tracker_cookies:
            for request in tracker_requests:
                if len(cookie['value']) > 6:
                    if cookie['value'] in request['url']:
                        cookie_domain = cookie['domain'].split('.')[len(cookie['domain'].split('.'))-2]
                        if cookie_domain not in request['url']:

                            try:
                                t_url = request['url'].split('/')[2]
                                d_name = t_url.split('.')
                                target_company_name = d_name[len(d_name)-2]
                            except IndexError:
                                target_company_name = request['url']
                            if target_company_name not in cookies_synced['sync_companies']:
                                cookies_synced['sync_companies'].append(target_company_name)

                            try:
                                origin_company_name = cookie['domain'].split('.')[len(cookie['domain'].split('.'))-2]
                            except IndexError:
                                origin_company_name = cookie['domain']
                            if origin_company_name not in cookies_synced['sync_companies']:
                                cookies_synced['sync_companies'].append(origin_company_name)

                            strikeout_count = 0
                            if len(cookies_synced) > 0:
                                for element in cookies_synced['sync_relation']:
                                    strikeout_subcount = 0
                                    if target_company_name in element['cookie_sync_target']:
                                        strikeout_subcount += 1
                                    if origin_company_name in element['cookie_sync_target']:
                                        strikeout_subcount += 1
                                    if origin_company_name in element['cookie_sync_origin']:
                                        strikeout_subcount += 1
                                    if strikeout_subcount > 1:
                                        strikeout_count = 1

                            if len(cookie['value']) == 10:
                                possible_time_cookie = None
                                utcstamp = None
                                try:
                                    possible_time_cookie = datetime.utcfromtimestamp(int(cookie['value']))
                                    utcstamp = datetime.utcnow()
                                except ValueError:
                                    strikeout_count += 0
                                if possible_time_cookie is not None:
                                    if possible_time_cookie.date().year == utcstamp.date().year:
                                        if possible_time_cookie.date().month == utcstamp.date().month:
                                            strikeout_count += 1

                            if strikeout_count == 0:
                                cookies_synced['cookie_sync_occurred'] = True
                                cookies_synced['sync_relation'].append({'cookie_sync_origin': cookie['domain'],
                                                                        'cookie_sync_target': request['url'],
                                                                        'cookie_sync_value': cookie['value']})

        if cookies_synced['cookie_sync_occurred'] is None:
            cookies_synced['cookie_sync_occurred'] = False

        cookies_synced['sync_occurrence_counter'] = len(cookies_synced['sync_relation'])

        self.result['cookiesync'] = cookies_synced
