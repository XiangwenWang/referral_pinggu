# Pinggu.org Referral Rewards Collector

The code provided is used to collect the referral rewards of "bbs.pinggu.org". Technically, it will collect 1900 exp daily, which is equivalent to 190 coins.
A long waiting time is set to avoid abusing the forum.

The code is tested on Mac and Linux. But it should work fine under Windows as long
as the PATH is correctly set.

Requirements:
-----
Python2, PhantomJS, requests, lxml, BeautifulSoup (bs4), selenium, Firefox (not necessary)

Quick Start:
-----
    1) Modify the "_your_referral_url" link to your referral link
    2) Run the code, "python referral_pinggu.py". It will take less than 1 hour to collect the rewards.