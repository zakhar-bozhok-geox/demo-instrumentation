from dataclasses import dataclass
import socket
from dataclasses_json import dataclass_json
from environs import Env
import marshmallow.validate
from influxdb_client import InfluxDBClient, Point

@dataclass_json
@dataclass
class InfluxDbConfig:
    bucket: str = None
    org: str = None
    token: str = None
    url: str = None
    optionalTags: dict = None

    @staticmethod
    def from_env(env: Env) -> "InfluxDbConfig":
        with env.prefixed('INFLUXDB_'):
            config = InfluxDbConfig()
            config.bucket = env.str(
                "BUCKET_NAME", validate=marshmallow.validate.Length(min=1))
            config.org = env.str("ORGANISATION", "geox",
                                 validate=marshmallow.validate.Length(min=1))
            config.token = env.str(
                "TOKEN", validate=marshmallow.validate.Length(min=1))
            config.url = env.str(
                "URL", validate=marshmallow.validate.Length(min=1))
            config.optionalTags = env.dict("OPTIONAL_TAGS", None)
            return config

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: \n{self.to_json(indent=4, sort_keys=True)}"

class NaiveInfluxdbWrap:
    def __init__(self, influxConfig: InfluxDbConfig):
        self.influxConfig = influxConfig
        self.influxClient = InfluxDBClient(url=influxConfig.url, token=influxConfig.token, org=influxConfig.org)
        self.influxWriteApi = self.influxClient.write_api()
    
    @staticmethod
    def from_env() -> "NaiveInfluxdbWrap":
        return NaiveInfluxdbWrap(InfluxDbConfig.from_env(Env()))

    def write(self, measurement: str, tags: dict, fields: dict):
        try:
            if self.influxConfig.optionalTags:
                tags.update(self.influxConfig.optionalTags)

            p = Point(measurement)
            p.tag("hostname", socket.gethostname())
            for key, value in tags.items():
                p.tag(key, value)
            for key, value in fields.items():
                p.field(key, value)

            self.influxWriteApi.write(self.influxConfig.bucket, self.influxConfig.org, p)
        except Exception as e:
            print(f"Error writing to influxdb: {e}")