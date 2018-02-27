import json
import os

import boto3


class ReleaseChannel(object):
    def __init__(self, name, tag, image):
        self.name = name
        self.tag = tag
        self.image = image


class ReleaseChannelFactory(object):
    def __call__(self, name, tag):
        s3 = boto3.resource('s3')
        content_object = s3.Object(os.environ['S3BUCKET'], '%s/%s.json' % (name, tag))
        file_content = content_object.get()['Body'].read().decode('utf-8')
        metadata = json.loads(file_content)
        return ReleaseChannel(name, tag, metadata['image'])
