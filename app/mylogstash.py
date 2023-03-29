from dataclasses import dataclass
import logging
from dataclasses_json import dataclass_json
from environs import Env
import marshmallow.validate
import logstash

@dataclass_json
@dataclass
class LogStashConfig:
    host: str = None
    port: int = None

    @staticmethod
    def from_env(env: Env) -> "LogStashConfig":
        with env.prefixed('LOGSTASH_'):
            config = LogStashConfig()
            config.host = env.str("HOST", "logstash", validate=marshmallow.validate.Length(min=1))
            config.port = env.int("PORT", validate=marshmallow.validate.Range(min=1))
            return config

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: \n{self.to_json(indent=4, sort_keys=True)}"

def configureLogStashLogging(logger: logging.Logger, logStashConfig: LogStashConfig):
    logger.addHandler(logstash.TCPLogstashHandler(logStashConfig.host, logStashConfig.port, version=1, tags=['worker_tag_example']))

def getConfigsAndApplyToLogger(env: Env, logger: logging.Logger):
    logStashConfig = LogStashConfig.from_env(env)
    configureLogStashLogging(logger, logStashConfig)