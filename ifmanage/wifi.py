import os.path
import socket
import stat

from ifmanage.interface import Interface

CTRL_IFACE_DIR = '/var/run/wpa_supplicant'
BUFF_SIZE = 4096

PING = 'PING'
SCAN = 'SCAN'
SCAN_RESULTS = 'SCAN_RESULTS'
ADD_NETWORK = 'ADD_NETWORK'
SET_NETWORK = 'SET_NETWORK'
SELECT_NETWORK = 'SELECT_NETWORK'
LIST_NETWORKS = 'LIST_NETWORKS'
DISCONNECT = 'DISCONNECT'
REMOVE_NETWORK = 'REMOVE_NETWORK'

# Define auth key mgmt types.
WPA_PSK = 'WPA-PSK'
WPA2_PSK = 'WPA2-PSK'
WPA_EAP = 'WPA-EAP'
WPA2_EAP = 'WPA2-EAP'


class Profile(object):
    def __init__(self, **kwargs):
        self._ssid = kwargs["ssid"]
        self._rssi = kwargs["RSSI"]
        self._frequency = kwargs["frequency"]
        self._akm = kwargs["akm"]
        self._password = ""

    @property
    def ssid(self) -> str:
        return self._ssid

    @property
    def RSSI(self) -> int:
        return self._rssi

    @property
    def frequency(self) -> list:
        return self._frequency

    @frequency.setter
    def frequency(self, freq: list):
        self._frequency = freq

    @property
    def akm(self) -> list:
        return self._akm

    @property
    def password(self) -> str:
        return self.password

    @password.setter
    def password(self, pwd: str):
        self._password = pwd


class WiFi(Interface):
    def __init__(self, ifname, **kwargs):
        super().__init__(ifname, **kwargs)
        self.ifname = ifname
        self._sock = self._init_socket()

    def _init_socket(self) -> socket.socket:
        sock_file = '{}/{}_{}'.format("/tmp", "ifmanage", self.ifname)
        control_file = "{}/{}".format(CTRL_IFACE_DIR, self.ifname)
        self._remove_existed_sock(sock_file)
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(sock_file)
        sock.connect(control_file)

        sock.send(PING.encode("utf-8"))
        retry = 0
        while retry <= 5:
            reply = sock.recv(BUFF_SIZE)
            if reply == '':
                raise ConnectionError(f"Connection to '{control_file}' is broken!")

            if reply.startswith(b'PONG'):
                print("init complete")
                return sock

        raise ConnectionError(f"Connection to '{control_file}' is broken!")

    def scan(self) -> list[Profile]:
        self._send_cmd(SCAN)
        print("wait scan...")
        profile_dict = {}
        reply = self._send_cmd(SCAN_RESULTS, decode=True)
        for line in reply[:-1].split('\n')[1:]:
            values = line.split('\t')
            ssid = values[4]
            freq = []
            if 2412 <= int(values[1]) <= 2484:
                freq.append("2.4GHz")
            elif 4915 <= int(values[1]) <= 5825:
                freq.append("5GHz")

            akm = []
            if WPA_PSK in values[3]:
                akm.append(WPA_PSK)
            if WPA2_PSK in values[3]:
                akm.append(WPA2_PSK)
            if WPA_EAP in values[3]:
                akm.append(WPA_EAP)
            if WPA2_EAP in values[3]:
                akm.append(WPA2_EAP)

            p = profile_dict.get(ssid)
            if p:
                freq.extend(p.frequency)
                akm.extend(p.akm)
                profile_dict[ssid] = Profile(**{
                    "ssid": ssid,
                    "frequency": freq,
                    "akm": akm,
                    "RSSI": max(p.RSSI, int(values[2]))
                })
            else:
                profile_dict[ssid] = Profile(**{
                    "ssid": ssid,
                    "frequency": freq,
                    "akm": akm,
                    "RSSI": int(values[2]),
                })

        return list(profile_dict.values())

    def connect(self, profile: Profile):
        networks = self.list_network()
        for n in networks:
            if n["ssid"] == profile.ssid:
                self._send_cmd("{} {}".format(SELECT_NETWORK, n["id"]))

    def disconnect(self):
        self._send_cmd(DISCONNECT)

    def add_profile(self, profile: Profile):
        reply = self._send_cmd(ADD_NETWORK, True)
        nid = reply.strip()

        self._send_cmd('{} {} ssid "{}"'.format(SET_NETWORK, nid, profile.ssid))

        akms = {
            WPA_PSK: ['WPA-PSK', 'WPA'],
            WPA2_PSK: ['WPA-PSK', 'WPA'],
            WPA_EAP: ['WPA-EAP', 'RSN'],
            WPA2_EAP: ['WPA-EAP', 'RSN'],
        }

        key_mgmt = akms.get(profile.akm[-1], ['None', ''])[0]
        self._send_cmd('{} {} key_mgmt {}'.format(SET_NETWORK, nid, key_mgmt))

        proto = akms.get(profile.akm[-1], ['None', ''])[1]
        if proto:
            self._send_cmd('{} {} proto {}'.format(SET_NETWORK, nid, proto))

        if profile.akm[-1] in [WPA2_PSK, WPA2_PSK]:
            self._send_cmd('{} {} psk "{}"'.format(SET_NETWORK, nid, profile.ssid))

    def remove_profile(self, nid):
        flag = False
        for i in self.list_network():
            if i["id"] == nid:
                flag = True
                break

        if flag:
            self._send_cmd("{} {}".format(REMOVE_NETWORK, nid))
        else:
            raise ValueError("Unknown network id")

    def list_network(self) -> list[dict]:
        networks = self._send_cmd(LIST_NETWORKS, decode=True)
        networks = networks[:-1].split('\n')
        if len(networks) == 1:
            return []

        res = []
        for n in networks[1:]:
            values = n.split('\t')
            res.append({
                "id": int(values[0]),
                "ssid": values[1],
                "bssid": values[2],
                "flags": values[3]
            })

        return res

    def _send_cmd(self, cmd: str, decode=False):
        self._sock.send(cmd.encode("utf-8"))
        reply = self._sock.recv(BUFF_SIZE)

        if decode:
            return reply.decode("utf-8")
        else:
            return reply

    def _remove_existed_sock(self, file):
        if os.path.exists(file):
            mode = os.stat(file).st_mode
            if stat.S_ISSOCK(mode):
                os.remove(file)


