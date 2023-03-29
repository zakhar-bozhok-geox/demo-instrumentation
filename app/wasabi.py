
from dataclasses import dataclass
import uuid
import boto3
import time

from dataclasses_json import dataclass_json
from environs import Env
import marshmallow

@dataclass
class WasabiSpeedtestResult:
    bucket_name: str = None
    endpoint_url: str = None
    download_speed_mbs: float = None
    upload_speed_mbs: float = None
    download_time_s: float = None
    upload_time_s: float = None

@dataclass
@dataclass_json
class WasabiConfig:
    access_key: str = None
    secret_access_key: str = None
    bucket_name: str = None
    s3_endpoint_url: str = None

    @staticmethod
    def from_env(env: Env) -> 'WasabiConfig':
        with env.prefixed("WASABI_"):
            config = WasabiConfig()
            config.access_key = env.str(
                "ACCESS_KEY", validate=marshmallow.validate.Length(min=1))
            config.secret_access_key = env.str(
                "SECRET_ACCESS_KEY", validate=marshmallow.validate.Length(min=1))
            config.bucket_name = env.str(
                "BUCKET_NAME", validate=marshmallow.validate.Length(min=1))
            config.s3_endpoint_url = env.str(
                "S3_ENDPOINT_URL", validate=marshmallow.validate.Length(min=1))
            return config

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: \n{self.to_json(indent=4, sort_keys=True)}"


def getWasabiSpeed(endpoint_url: str, access_key: str, secret_access_key: str, bucket_name: str, object_name: str = None):
    s3 = boto3.client('s3',
                      endpoint_url=endpoint_url,
                      aws_access_key_id=access_key,
                      aws_secret_access_key=secret_access_key)

    if object_name is None:
        object_name = uuid.uuid4().hex

    # Upload 1MB of 'A' to the Wasabi bucket and measure the time it takes
    content = b'A' * (1024 * 1024)
    start_time = time.time()
    s3.put_object(Bucket=bucket_name, Key=object_name, Body=content)
    upload_time = time.time() - start_time
    upload_speed = len(content) / (upload_time) / 1024 / 1024

    # Download the object from the Wasabi bucket and measure the time it takes
    start_time = time.time()
    response = s3.get_object(Bucket=bucket_name, Key=object_name)
    content = response['Body'].read()
    download_time = time.time() - start_time
    download_speed = len(content) / (download_time) / 1024 / 1024

    s3.delete_object(Bucket=bucket_name, Key=object_name)

    res = WasabiSpeedtestResult()
    res.bucket_name = bucket_name
    res.endpoint_url = endpoint_url
    res.download_speed_mbs = download_speed
    res.upload_speed_mbs = upload_speed
    res.download_time_s = download_time
    res.upload_time_s = upload_time

    return res