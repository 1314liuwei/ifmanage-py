import socket
from ifmanage.wifi import WiFi


def wifi_test(name):
    ifs = WiFi("wlan0")
    res = ifs.scan()
    for i in res:
        print(i.ssid)
        print(i.RSSI)

    ifs.connect(res[0])

    print(len(res))
    print(len(set(res)))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    wifi_test("wlan0")
