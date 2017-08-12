from wetland import config
import pygeoip

geoip = pygeoip.GeoIP(config.cfg.get("wetland", "geoipdb"))
