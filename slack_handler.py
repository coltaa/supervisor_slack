#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import slackweb
import os
from config import Config
import boto3
import requests
from time import sleep

aws_metadata_url = "http://169.254.169.254/latest/"
aws_metadata_iamCredentialsPath = "meta-data/iam/security-credentials/"
aws_metadata_AZPath = "meta-data/placement/availability-zone/"
aws_metadata_InstanceTypePath = "meta-data/instance-type/"
aws_metadata_InstanceIdentity = "dynamic/instance-identity/document"


f = file(os.path.join(os.path.dirname(__file__), 'conf/slack.cfg'))
cfg = Config(f)

try:
   os.environ["SLACK_URL"]
except KeyError:
   print "Please set the environment variable FOO"
   sys.exit(1)

slack_url = os.environ["SLACK_URL"]
slack = slackweb.Slack(url=slack_url)


def write_stdout(s):
    # only eventlistener protocol messages may be sent to stdout
    sys.stdout.write(s)
    sys.stdout.flush()

def write_stderr(s):
    sys.stderr.write(s)
    sys.stderr.flush()

def getInstanceRole():
    try:
        r = requests.get(aws_metadata_url + aws_metadata_iamCredentialsPath)
        if r.status_code == 200:
            response = r.text
        return response
    except:
        print("ERROR: Metadata not available.")
        return

def getMetaData(urlpath):
    try:
        r = requests.get(aws_metadata_url + urlpath)
        if r.status_code == 200:
            response = r.json()
        return response
    except:
        print("ERROR: Metadata not available.")
        return


def getIAMCredentials():
    try:
        InstanceRole = getInstanceRole()
        r = requests.get(aws_metadata_url + aws_metadata_iamCredentialsPath + InstanceRole)
        credentialsJson = r.json()

        return credentialsJson

    except:
        print("ERROR getting Credentials from Meta-data")

# # Initialize Credentials
aws_CredentialsData = getIAMCredentials()
aws_AccessKeyId = aws_CredentialsData.get("AccessKeyId")
aws_SecretAccessKey = aws_CredentialsData.get("SecretAccessKey")
aws_Token = aws_CredentialsData.get("Token")

# Get Instance Region
aws_InstanceData = getMetaData(aws_metadata_InstanceIdentity)
aws_region = aws_InstanceData.get("region")
aws_availabilityZone = aws_InstanceData.get("availabilityZone")
aws_instanceId = aws_InstanceData.get("instanceId")
aws_accountId = aws_InstanceData.get("accountId")
aws_privateIp = aws_InstanceData.get("privateIp")

ec2_resource = boto3.resource(region_name = aws_region, service_name ='ec2',
                    aws_access_key_id = aws_AccessKeyId,
                    aws_secret_access_key = aws_SecretAccessKey,
                    aws_session_token = aws_Token
                              )
ec2_client = boto3.client(region_name = aws_region, service_name ='ec2',
                    aws_access_key_id = aws_AccessKeyId,
                    aws_secret_access_key = aws_SecretAccessKey,
                    aws_session_token = aws_Token
                              )

route53_client = boto3.client(region_name = aws_region, service_name ='route53',
                    aws_access_key_id = aws_AccessKeyId,
                    aws_secret_access_key = aws_SecretAccessKey,
                    aws_session_token = aws_Token)

def getTags(resource, tagkey, retries = 0, wait = 0):
    if retries > 10: return
    try:
        sleep(wait)
        response = ec2_client.describe_tags(
            Filters=[
                {
                    'Name': 'resource-id',
                    'Values': [
                        resource,
                    ]
                },
                {
                    'Name': 'key',
                    'Values': [
                        tagkey,
                    ]
                },

            ]
        )
        tagValue = response.get('Tags')[0].get('Value')
        return tagValue

    except:
        print("ERROR getting tag " + tagkey)
        retries += 1
        wait = retries * 2
        getTags(resource, tagkey, retries, wait )

aws_instance_name = getTags(aws_instanceId, "Name")
aws_private_ip = getTags(aws_instanceId, "Name")


def main():
    while 1:
        # transition from ACKNOWLEDGED to READY
        write_stdout('READY\n')

        # read header line and print it to stderr
        line = sys.stdin.readline()

        # read event payload and print it to stderr
        headers = dict([ x.split(':') for x in line.split() ])
        data = sys.stdin.read(int(headers['len']))
        print(headers)
        if 'PROCESS_STATE_STARTING' == headers['eventname']:
            attachments = []
            attachment = {"title": cfg.messages.start.title, "color": "warning", "text": cfg.messages.start.text}
            attachments.append(attachment)
            slack.notify(attachments=attachments)

        elif 'PROCESS_STATE_STARTED' == headers['eventname'] or 'PROCESS_STATE_RUNNING' == headers['eventname']:
            attachments = []
            attachment = {"title": cfg.messages.running.title, "color": "good", "text": cfg.messages.running.text}
            attachments.append(attachment)
            slack.notify(attachments=attachments)

        elif 'PROCESS_STATE_EXITED' == headers['eventname'] or 'PROCESS_STATE_STOPPED' == headers['eventname']:
            attachments = []
            attachment = {"title": cfg.messages.stop.title, "color": "danger", "text": cfg.messages.stop.text}
            attachments.append(attachment)
            slack.notify(attachments=attachments)

        elif 'PROCESS_STATE_FATAL' == headers['eventname']:
            attachments = []
            attachment = {"title": cfg.messages.fatal.title, "color": "danger", "text": cfg.messages.fatal.text}
            attachments.append(attachment)
            slack.notify(attachments=attachments)

        # transition from READY to ACKNOWLEDGED
        write_stdout('RESULT 2\nOK')

if __name__ == '__main__':
    main()