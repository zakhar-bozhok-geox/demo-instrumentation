
from dataclasses import dataclass
import speedtest

@dataclass
class OoklaSpeedtestResult:
    download_speed_mbs: float = None
    upload_speed_mbs: float = None
    ping_ms: float = None
    country: str = None
    name: str = None
    lat: float = None
    lon: float = None

def getOoklaSpeedtestResult() -> OoklaSpeedtestResult:
    s = speedtest.Speedtest()
    s.get_servers([])
    s.get_best_server()

    s.download(threads=None)
    s.upload(threads=None)
    ooklaRes = s.results.dict()

    res = OoklaSpeedtestResult()
    res.download_speed_mbs = ooklaRes["download"] / 1024 / 1024 / 8
    res.upload_speed_mbs = ooklaRes["upload"] / 1024 / 1024 / 8
    res.ping_ms = ooklaRes["ping"]
    res.country = ooklaRes["server"]["country"]
    res.name = ooklaRes["server"]["name"]
    res.lat = ooklaRes["server"]["lat"]
    res.lon = ooklaRes["server"]["lon"]

    return res
