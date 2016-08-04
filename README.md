# Pinggu.org Referral Rewards Collector

The code provided is used to collect the referral rewards of "bbs.pinggu.org".
Technically, it will collect more than 1000 exp daily, which is equivalent to 100~190 coins.
A long waiting time is set to avoid abusing the forum.

The code is tested on Mac and Linux. But should works fine under Windows as long
as the PATH is set correctly.
Before running this script, please make sure that the following softwares
and packages are installed:
Python2, PhantomJS, requests, lxml, BeautifulSoup (bs4), selenium, firefox (not necessary)

Quick Start:
-----
    1) Modify the "_your_referral_url" link to your referral link
    2) Run the code, it will take less than 1 hour to collect the rewards.