import re

from ifmanage.interface import Interface


class Ethernet(Interface):
    def __init__(self, ifname, **kwargs):
        if re.match("(lan|eth|eno|ens|enp|enx)[0-9]+$", ifname):
            raise ValueError("The name of network card is not standard")

        default = {
            "type":"ethernet",
            "dhcp-options": {
                "default-route-distance": "210"
            },
            "dhcpv6-options": {
                "pd": {
                    "length": "64"
                }
            },
            "ip": {
                "arp-cache-timeout": "30"
            },
            "duplex": "auto",
            "mtu": "1500",
            "speed": "auto",
        }
        default.update(kwargs)
        super().__init__(ifname,  **default)
