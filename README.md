# Supervisor to Slack
Little tool to help monitor server status

![repo at work](https://na.cx/i/UZK7p7.jpg)

## Prerequisites
Python 2.7 with pip

## Configuration
Refer to [supervisord.conf.sample](conf/supervisord.conf) and [slack.cfg.sample](conf/slack.cfg)

where slack_url is the API url of slack incoming webhook

## Installation and Usage
1. Install required python modules
```bash
pip install -r requirements.txt
```

2. Make sure `supervisord.conf` and `slack.cfg` exists

3. Run by starting
```bash
supervisord -c conf/supervisord.conf
```
