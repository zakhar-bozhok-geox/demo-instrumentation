# Influx dependencies
import pprint
from mylogstash import getConfigsAndApplyToLogger
from influx import NaiveInfluxdbWrap

# OpenTelemetry dependencies
from open_telemetry import NaiveOoklaMetrics
from open_telemetry import NaiveWasabiMetrics
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import start_http_server
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource

# Common dependencies
from ookla import getOoklaSpeedtestResult
from wasabi import WasabiConfig, getWasabiSpeed
from environs import Env
from time import sleep

import logging
import sys

from pypprof.net_http import start_pprof_server
import mprofile

def configureOpenTelemetry():
    resource = Resource.create({'service.name': 'predictions-worker'})
    trace.set_tracer_provider(TracerProvider(
        resource=resource
    ))
    span_exporter = OTLPSpanExporter(endpoint="http://jaeger:4317")
    span_processor = BatchSpanProcessor(span_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    # Configure OpenTelemetry metrics
    metrics.set_meter_provider(
        MeterProvider(
            resource=resource, 
            metric_readers=[PrometheusMetricReader()], 
            views=NaiveWasabiMetrics.genereateViews(),
        ) 
    )
    start_http_server(port=8000, addr="0.0.0.0") # Prometheus metrics endpoint

def configurePhlare():
    # start memory profiling
    mprofile.start(sample_rate=128 * 1024)
    # enable pprof http server
    start_pprof_server(host='0.0.0.0', port=8081)

def main():
    configureOpenTelemetry()
    configurePhlare()
    tracer = trace.get_tracer("geox-test-tracer")
    env = Env()
    wasabiConfig = WasabiConfig.from_env(env)
    influxClient = NaiveInfluxdbWrap.from_env()

    logger = logging.getLogger("worker-logger")
    logger.setLevel(logging.INFO)
    sleepTime = env.int("SLEEP_TIME", 60)

    getConfigsAndApplyToLogger(env, logger)

    logger.info("Starting worker")
    with tracer.start_as_current_span("main"):
        wasabiMetrics = NaiveWasabiMetrics()
        ooklaMetrics = NaiveOoklaMetrics()
        while True:
            with tracer.start_as_current_span("getWasabiSpeedAndReport"):
                wasabiResults = getWasabiSpeed(
                    wasabiConfig.s3_endpoint_url,
                    wasabiConfig.access_key,
                    wasabiConfig.secret_access_key,
                    wasabiConfig.bucket_name
                )
                # Report using OpenTelemetry
                wasabiMetrics.recordMetrics(wasabiResults)
                # Report using InfluxDB
                influxClient.write(
                    "wasabi", 
                    {   "endpoint": wasabiResults.endpoint_url, 
                        "bucket": wasabiResults.bucket_name     }, 
                    {   "upload_speed_mbs": wasabiResults.upload_speed_mbs, 
                        "download_speed_mbs": wasabiResults.download_speed_mbs, 
                        "upload_time_s": wasabiResults.upload_time_s, 
                        "download_time_s": wasabiResults.download_time_s    }
                )
                logger.info(f"Wasabi: Upload speed: {round(wasabiResults.upload_speed_mbs,2)} MB/s, Download speed: {round(wasabiResults.download_speed_mbs,2)} MB/s, upload time: {round(wasabiResults.upload_time_s,2)}, download time: {round(wasabiResults.download_time_s,2)}, endpoint: {wasabiResults.endpoint_url}, bucket: {wasabiResults.bucket_name}")
            with tracer.start_as_current_span("getOoklaSpeedAndReport"):
                try:
                    ooklaResults = getOoklaSpeedtestResult()
                    # Report using OpenTelemetry
                    ooklaMetrics.recordMetrics(ooklaResults)
                    # Report using InfluxDB
                    influxClient.write(
                        "ookla", 
                        {   "server": ooklaResults.name, 
                            "country": ooklaResults.country     }, 
                        {   "upload_speed_mbs": ooklaResults.upload_speed_mbs, 
                            "download_speed_mbs": ooklaResults.download_speed_mbs, 
                            "ping_ms": ooklaResults.ping_ms    }
                    )
                    logger.info(f"Ookla: Upload speed: {round(ooklaResults.upload_speed_mbs,2)} MB/s, Download speed: {round(ooklaResults.download_speed_mbs,2)} MB/s, Ping: {round(ooklaResults.ping_ms,2)} ms, Server: {ooklaResults.name} ({ooklaResults.country})")
                except Exception as e:
                    logger.error(f"Ookla: Error: {e}")

            logger.info(f"Sleeping for {sleepTime} seconds")
            sleep(sleepTime)

if __name__ == "__main__":
    main()