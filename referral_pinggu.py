'''
This code is for testing purpose only, and is provided AS-IS.

The code provided is used to collect the referral rewards of "bbs.pinggu.org".
Technically, it will collect more than 1900 exp daily, which is equivalent to 190 coins.
A long waiting time is set to avoid abusing the forum.

The code is tested on Mac and Linux. But should works fine under Windows as long
as the PATH is set correctly.

Before running this script, please make sure that the following softwares
and packages are installed:
Python2, PhantomJS, requests, lxml, BeautifulSoup (bs4), selenium, firefox (not necessary)

Quick Start:
    1) Modify the "_your_referral_url" link to your referral link
    2) Run the code, it will take less than 1 hour to collect the rewards.

@ Author:  Xiangwen Wang
@ Date:    08/02/2016
@ License: Apache 2.0

Copyright 2016 Xiangwen Wang
'''

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import random
import string
import re
import os
import platform
import requests
import time
import multiprocessing
import traceback
import gc


# ------------change below to your referral link--------------
_your_referral_url = 'http://bbs.pinggu.org/?fromuid=8822244'
# ------------change above to your referral link--------------

_max_visit_count = 30  # number of visit rewards per day
_max_register_count = 10  # number of register rewards per day
_userAgents = [{'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:5.0) Gecko/20100101 Firefox/5.0'},
               {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:16.0) Gecko/20121026 Firefox/16.0"},
               {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0.1) Gecko/20100101"}]


def update_proxy():
    '''
    Update proxy list from incloak.com
    '''
    _max_lag = 900

    def check_proxy(hostname, waiting_time):
        '''
        Calling system ping function to verify the proxies
        '''
        if platform.system() == 'Windows':
            response = os.system("ping -n 1 -w %d %s" % (waiting_time, hostname))
        else:
            response = os.system("ping -c 1 -t %d %s" % (waiting_time, hostname))
        return True if response == 0 else False

    def add_port(port):
        response = requests.get('https://incloak.com/proxy-list/?maxtime=%d&ports=%d&type=h' %
                                (_max_lag, port), headers=random.choice(_userAgents))
        ip_s = re.findall('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', response.content)
        ip_s = [x for x in ip_s if check_proxy(x, _max_lag / 1000 + 1)]
        return map(lambda x: {'http': 'http://' + x + ':%d' % port}, ip_s)

    proxy = []
    proxy += add_port(80)
    proxy += add_port(3128)
    proxy += add_port(8080)
    print '%d Proxies updated' % len(proxy)
    return proxy


def try_register(proxy=None):
    '''
    Register reward. Reward is calculated by number of registers.
    Here, I used selenium + PhantomJS/Firefox when registering.
    '''
    def generate_random_str():
        '''
        generate a 9 to 12 characters random string as the username and password
        '''
        first_char = random.choice(string.ascii_letters)
        rest_char = ''.join(random.choice(string.ascii_letters + string.digits)
                            for _ in range(random.randint(9, 12)))
        return first_char + rest_char

    def find_verif_code(html_raw):
        '''
        find the verification code, on pinggu, it's the color text
        '''
        tag = re.findall(r'(secqaa_\w*)\"', html_raw)[0]
        html = BeautifulSoup(html_raw, 'lxml')
        return html.findAll('span', {'id': tag})[0].findAll('font')[0].getText()

    def set_proxy(host=None, port=None):
        '''
        set proxy for the selenium (will use firefox)
        '''
        profile = webdriver.FirefoxProfile()
        if host is not None:
            # set proxy
            profile.set_preference("network.proxy.type", 1)
            profile.set_preference("network.proxy.http", host)
            profile.set_preference("network.proxy.http_port", int(port))
        else:
            # reset proxy to SYSTEM
            # Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
            profile.set_preference("network.proxy.type", 5)
        profile.update_preferences()
        return webdriver.Firefox(firefox_profile=profile)

    random_str = generate_random_str()
    _waiting_time = 20
    if proxy is None:
        driver = webdriver.PhantomJS()
    else:
        # when choosing to use proxy
        # will use the firefox since it's easier to config proxies
        _proxy_host, _proxy_port = random.choice(proxy)['http'].split(':')
        driver = set_proxy(_proxy_host, int(_proxy_port))

    # visit the referral page first, then register
    driver.get(_your_referral_url)
    try:
        driver.WebDriverWait(driver, _waiting_time)
    except:
        print("Skip loading,"),
    finally:
        print("Cookie acquired, "),
        if not os.path.isdir('screenshot'):
            os.mkdir('screenshot')
        driver.save_screenshot('screenshot/screen0.png')

    driver.get("http://bbs.pinggu.org/member.php?mod=regpinggu")
    driver.implicitly_wait(_waiting_time)
    # driver.add_cookie(cookie)
    # screenshot before filling forms
    driver.save_screenshot('screenshot/screen1.png')
    # username
    driver.find_element_by_name('pgname221a').send_keys(random_str)
    # password
    driver.find_element_by_name('pgpass1121a').send_keys(random_str)
    # confirming password
    driver.find_element_by_name('pgpass1221a').send_keys(random_str)
    # email
    driver.find_element_by_name('pgemail4521a').send_keys(
        random_str + r'@gemail.com')
    # field of interests
    driver.find_element_by_name('field7[]').click()
    # verification code
    try:
        driver.find_element_by_name('secanswer').send_keys(
            find_verif_code(driver.page_source))
    except Exception as e:
        driver.quit()
        raise e
    # screenshot after filling forms
    driver.save_screenshot('screenshot/screen2.png')
    # submit
    driver.find_element_by_id("registerformsubmit").click()
    # screenshot of the results
    driver.save_screenshot('screenshot/screen3.png')
    driver.quit()
    return random_str


def access_referral(multi_attempts=True, skip_proxy=False):
    '''
    Visit reward. Reward is calculated by number of unique IP's.
    Here, requests package is used for timing concerns.
    '''
    if not skip_proxy:
        proxy = update_proxy()
        count = 0
        for _proxy in proxy:
            if count >= _max_visit_count:
                break
            try:
                requests.get(_your_referral_url, headers=random.choice(_userAgents),
                             proxies=_proxy, timeout=20)
                count += 1
                print("Visit %d finished" % count)
                time.sleep(3)
            except:
                time.sleep(1)

    # following are two site-availability-check service providers, but they can be used
    # to increase the visit IPs of our referral link. However, this could be potentailly
    # imcrease the stress of the forum, therefore try not to use it.
    try:
        assert multi_attempts
        testing_url1 = 'http://www.host-tracker.com/'
        driver = webdriver.PhantomJS()
        driver.get(testing_url1)
        driver.find_element_by_name('InstantCheckUrl').send_keys(_your_referral_url)
        driver.find_element_by_tag_name('button').click()
        driver.implicitly_wait(120)
        # driver.save_screenshot('screenshot/site_check1.png')
        driver.close()
    except:
        time.sleep(1)

    try:
        assert multi_attempts
        testing_url2 = 'http://www.17ce.com/'
        driver = webdriver.PhantomJS()
        driver.get(testing_url2)
        driver.find_element_by_name('url').send_keys(_your_referral_url, Keys.RETURN)
        driver.implicitly_wait(120)
        # driver.save_screenshot('screenshot/site_check2.png')
        driver.close()
    except:
        time.sleep(1)

    return proxy


class Process(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._cconn.send(None)
        except Exception as e:
            self._cconn.send((e, traceback.format_exc()))

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception


class TimeoutError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class TimeoutTracker():
    """
    Multiprocessing timeout checker
    """
    _timeout_threshold = 360  # seconds. Max timeout threshold for registration.

    def __init__(self, function):
        self.function = function

    def __call__(self, *args, **kargs):

        def function_process(pipe, function, args, kargs):
            pipe.send(function(*args, **kargs))  # A: result got from function process

        p_pipe, c_pipe = multiprocessing.Pipe()
        p = Process(target=function_process, args=(c_pipe, self.function, args, kargs))
        p.start()
        p.join(self._timeout_threshold)  # Wait

        if p.exception:
            # if there is other Error
            raise RuntimeError
        elif p.is_alive():
            # if passes the timeout threshold, terminate function process
            p.terminate()
            raise TimeoutError('Timeout')
        else:
            return p_pipe.recv()  # return result from A


def access_register(proxy=None, timeout_check=True):
    i = 0
    while i < _max_register_count:
        try:
            if timeout_check:
                TimeoutTracker(try_register)(proxy=proxy)
            else:
                print(try_register(proxy=proxy))
            i += 1
            print("SUCCESS %d" % i)
        except Exception as e:
            print(str(e) + 'Error , retrying')
        finally:
            for p in multiprocessing.active_children():
                p.terminate()
            gc.collect()


if __name__ == '__main__':
    access_referral(multi_attempts=True, skip_proxy=False)  # farm visitation rewards
    access_register(proxy=None, timeout_check=True)  # farm register rewards
    # while True: access_register(proxy=access_referral()); time.sleep(86000);
    # register with proxy, this is not necessary
