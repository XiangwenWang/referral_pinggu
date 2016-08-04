'''
This code is for testing purpose only, and is provided AS-IS.

The code provided is used to collect the referral rewards of "bbs.pinggu.org".
Technically, it will collect more than 1000 exp daily, which is equivalent to 100~190 coins.
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
        driver.WebDriverWait(driver, 20)
    except:
        print("Skip loading main page due to slow connection")
    finally:
        if not os.path.isdir('screenshot'):
            os.mkdir('screenshot')
        driver.save_screenshot('screenshot/screen0.png')

    driver.get("http://bbs.pinggu.org/member.php?mod=regpinggu")
    driver.implicitly_wait(15)
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
    driver.find_element_by_name('secanswer').send_keys(
        find_verif_code(driver.page_source))
    # screenshot after filling forms
    driver.save_screenshot('screenshot/screen2.png')
    # submit
    driver.find_element_by_id("registerformsubmit").click()
    # screenshot of the results
    driver.save_screenshot('screenshot/screen3.png')
    driver.close()
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
                             proxies=_proxy, timeout=60)
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


def access_register(proxy=None):
    i = 0
    while i < _max_register_count:
        try:
            try_register(proxy=proxy)
            # print(try_register(proxy=proxy))
            i += 1
            print("SUCCESS")
        except:
            print("ERROR")


if __name__ == '__main__':
    access_referral(multi_attempts=True)  # visit reward
    access_register()  # register reward
    # while True: access_register(proxy=access_referral()); time.sleep(86000);
    # register with proxy, this is not necessary
