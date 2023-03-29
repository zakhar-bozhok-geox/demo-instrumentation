from opentelemetry import metrics
import socket
from ookla import OoklaSpeedtestResult
from wasabi import WasabiSpeedtestResult
from opentelemetry.sdk.metrics.view import View, ExplicitBucketHistogramAggregation


class NaiveWasabiMetrics:
    downloadTimeName: str = "wasabi.download_time"
    uploadTimeName: str = "wasabi.upload_time"
    downloadSpeedMBsName: str = "wasabi.download_speed_mbs"
    uploadSpeedMBsName: str = "wasabi.upload_speed_mbs"
    def __init__(self) -> None:
        self.__meter = metrics.get_meter("wasabi")
        self.downloadTimeHistogram = self.__meter.create_histogram(self.downloadTimeName)
        self.uploadTimeHistogram = self.__meter.create_histogram(self.uploadTimeName)
        self.__lastDownloadSpeedObservation = [] #metrics.Observation(0)
        self.__lastUploadSpeedObservation = [] #metrics.Observation(0)
        self.__downloadSpeedMBsGauge = self.__meter.create_observable_gauge(self.downloadSpeedMBsName, callbacks=[lambda x: [self.__lastDownloadSpeedObservation]])
        self.__uploadSpeedMBsGauge = self.__meter.create_observable_gauge(self.uploadSpeedMBsName, callbacks=[lambda x: [self.__lastUploadSpeedObservation]])

    def recordMetrics(self, speedTestResult: WasabiSpeedtestResult):
        attrs = {
            "bucket_name" : speedTestResult.bucket_name,
            "endpoint_url" : speedTestResult.endpoint_url,
            "hostname" : socket.gethostname()
        }
        self.downloadTimeHistogram.record(speedTestResult.download_time_s, attrs)
        self.uploadTimeHistogram.record(speedTestResult.upload_time_s, attrs)
        self.__lastDownloadSpeedObservation = metrics.Observation(speedTestResult.download_speed_mbs, attrs)
        self.__lastUploadSpeedObservation = metrics.Observation(speedTestResult.upload_speed_mbs, attrs)
    
    @staticmethod
    def genereateViews():
        histogramBuckets = [0, 0.1, 0.2, 0.4, 0.6, 0.8, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 5.0, 10.0, 50.0, 100.0]
        return [
            View(instrument_name=NaiveWasabiMetrics.downloadTimeName, aggregation=ExplicitBucketHistogramAggregation(histogramBuckets)),
            View(instrument_name=NaiveWasabiMetrics.uploadTimeName, aggregation=ExplicitBucketHistogramAggregation(histogramBuckets))
        ]

class NaiveOoklaMetrics:
    downloadSpeedMBsName: str = "ookla.download_speed_mbs"
    uploadSpeedMBsName: str = "ookla.upload_speed_mbs"
    pingMsName: str = "ookla.ping_ms"
    
    def __init__(self) -> None:
        self.__meter = metrics.get_meter("ookla")
        self.__downloadSpeedHistogram = self.__meter.create_histogram(self.downloadSpeedMBsName)
        self.__uploadSpeedHistogram = self.__meter.create_histogram(self.uploadSpeedMBsName)
        self.__pingMsHistogram = self.__meter.create_histogram(self.pingMsName)
        self.__lastDownloadSpeedObservation = [] 
        self.__lastUploadSpeedObservation = [] 
        self.__lastPingMsObservation = [] 
        self.__downloadSpeedMBsGauge = self.__meter.create_observable_gauge(self.downloadSpeedMBsName, callbacks=[lambda x: self.__lastDownloadSpeedObservation])
        self.__uploadSpeedMBsGauge = self.__meter.create_observable_gauge(self.uploadSpeedMBsName, callbacks=[lambda x: self.__lastUploadSpeedObservation])
        self.__pingMsGauge = self.__meter.create_observable_gauge(self.pingMsName, callbacks=[lambda x: self.__lastPingMsObservation])

    def recordMetrics(self, speedTestResult: OoklaSpeedtestResult):
        attrs = {
            "country" : speedTestResult.country,
            "name" : speedTestResult.name,
            "lat" : speedTestResult.lat,
            "lon" : speedTestResult.lon,
        }
        self.__downloadSpeedHistogram.record(speedTestResult.download_speed_mbs, attrs)
        self.__uploadSpeedHistogram.record(speedTestResult.upload_speed_mbs, attrs)
        self.__pingMsHistogram.record(speedTestResult.ping_ms, attrs)
        self.__lastDownloadSpeedObservation = [metrics.Observation(speedTestResult.download_speed_mbs, attrs)]
        self.__lastUploadSpeedObservation = [metrics.Observation(speedTestResult.upload_speed_mbs, attrs)]
        self.__lastPingMsObservation = [metrics.Observation(speedTestResult.ping_ms, attrs)]

    @staticmethod
    def generateViews() -> View:
        speedHistogramBuckets = [0,20,40,60,80,100,130,160,190,220,270,350,500]
        pingHistogramBuckets = [0, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
        return [
            View(instrument_name=NaiveOoklaMetrics.downloadSpeedMBsName, aggregation=ExplicitBucketHistogramAggregation(speedHistogramBuckets)),
            View(instrument_name=NaiveOoklaMetrics.uploadSpeedMBsName, aggregation=ExplicitBucketHistogramAggregation(speedHistogramBuckets)),
            View(instrument_name=NaiveOoklaMetrics.pingMsName, aggregation=ExplicitBucketHistogramAggregation(pingHistogramBuckets))
        ]
