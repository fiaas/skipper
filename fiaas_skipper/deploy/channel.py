#!/usr/bin/env python
# -*- coding: utf-8
import boto3
import json
from botocore.handlers import disable_signing


class ReleaseChannel(object):
    def __init__(self, name, tag, image):
        self.name = name
        self.tag = tag
        self.image = image


class ReleaseChannelFactory(object):
    def __init__(self, config):
        self.s3bucket = config.s3bucket

    def __call__(self, name, tag):
        s3 = boto3.resource('s3')
        # Use anonymous mode
        s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
        content_object = s3.Object(self.s3bucket, '%s/%s.json' % (name, tag))
        file_content = content_object.get()['Body'].read().decode('utf-8')
        metadata = json.loads(file_content)
        return ReleaseChannel(name, tag, metadata['image'])
