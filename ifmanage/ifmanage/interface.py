import json
import os

import jmespath

from util.command import cmd, is_systemd_service_active, popen
from util.template import render
from util.validate import is_interface_addr_assigned
from util.dictutil import dict_merge


class Interface(object):
    def __init__(self, ifname, **kwargs):
        self.config = kwargs
        self.config.setdefault("ifname", ifname)
        self.ifname = ifname
        self.info = {}

    def get_info(self) -> dict:
        return {}

    def exist(self) -> bool:
        return os.path.exists(f'/sys/class/net/{self.ifname}')

    def create(self):
        """
       Create interface from operating system.
       """
        cmd('ip link add dev {ifname} type {type}'.format(**self.config))

    def delete(self):
        """
        Remove interface from operating system.
        """
        cmd('ip link del dev {ifname}'.format(**self.config))

    def remove(self):
        """
        Remove interface from operating system. Removing the interface
        configure all assigned IP addresses and clear possible DHCP(v6)
        client processes.
        """

        # remove all assigned IP addresses from interface - this is a bit redundant
        # as the kernel will remove all addresses on interface deletion, but we
        # can not delete ALL interfaces, see below
        self.flush_addrs()

        # Delete network connection
        self.delete()

    def flush_addrs(self):
        """
        Flush all addresses from an interface, including DHCP.
        """
        self.set_dhcp(False)
        self.set_dhcpv6(False)
        cmd(f'ip addr flush dev "{self.ifname}"')

    def set_dhcp(self, enable: bool):
        """
        Enable/Disable DHCP client on a given interface.
        """
        ifname = self.ifname
        config_base = r'/var/lib/dhcp/dhcp-client'
        config_file = f'{config_base}_{ifname}.conf'
        options_file = f'{config_base}_{ifname}.options'
        pid_file = f'{config_base}_{ifname}.pid'
        lease_file = f'{config_base}_{ifname}.leases'
        systemd_service = f'dhcp-client@{ifname}.service'

        if enable:
            with open('/etc/hostname', 'r') as f:
                hostname = f.read().rsplit('\n')
                self.info = dict_merge({'dhcp_options': {'host_name': hostname}}, self.info)

            render(options_file, 'dhcp-client/daemon-options.j2', self.info)
            render(config_file, 'dhcp-client/ipv4.j2', self.info)
            cmd(f'systemctl restart {systemd_service}')
        else:
            if is_systemd_service_active(systemd_service):
                cmd(f'systemctl stop {systemd_service}')

            for file in [config_file, options_file, pid_file, lease_file]:
                if os.path.isfile(file):
                    os.remove(file)

    def set_dhcpv6(self, enable: bool):
        """
        Enable/Disable DHCPv6 client on a given interface.
        """
        ifname = self.ifname
        config_file = f"/run/dhcp6c/dhcp6c.{ifname}.conf"
        systemd_service = f"dhcp6c@{ifname}.service"

        if enable:
            render(config_file, 'dhcp-client/ipv6.j2', self.info)
            # We must ignore any return codes. This is required to enable
            # DHCPv6-PD for interfaces which are yet not up and running.
            popen(f'systemctl restart {systemd_service}')
        else:
            if is_systemd_service_active(systemd_service):
                cmd(f'systemctl stop {systemd_service}')

            if os.path.isfile(config_file):
                os.remove(config_file)

    def set_mtu(self, mtu: int):
        """
        Set interface mtu value.
        """
        cmd(f"ip link set {self.ifname} mtu {mtu}")

    def set_state(self, enable: bool):
        cmd("ip link set dev {} {}".format(self.ifname, "up" if enable else "down"))

    def set_alias(self, name: str):
        if not name:
            raise ValueError("Alias cannot be empty")
        cmd(f'ip link set dev {self.ifname} alias "{name}')

    def set_mac(self, mac: str):
        split = mac.split(':')
        size = len(split)

        # a mac address consits out of 6 octets
        if size != 6:
            raise ValueError(f'wrong number of MAC octets ({size}): {mac}')

        octets = []
        try:
            for octet in split:
                octets.append(int(octet, 16))
        except ValueError:
            raise ValueError(f'invalid hex number "{octet}" in : {mac}')

        # validate against the first mac address byte if it's a multicast
        # address
        if octets[0] & 1:
            raise ValueError(f'{mac} is a multicast MAC address')

        # overall mac address is not allowed to be 00:00:00:00:00:00
        if sum(octets) == 0:
            raise ValueError('00:00:00:00:00:00 is not a valid MAC address')

        if octets[:5] == (0, 0, 94, 0, 1):
            raise ValueError(f'{mac} is a VRRP MAC address')

        cmd(f"ip link set dev {self.ifname} address {mac}")

    def add_addr(self, addr: str):
        """
        Add IP(v6) address to interface. Address is only added if it is not
        already assigned to that interface. Address format must be validated
        and compressed/normalized before calling this function.
        """

        if addr.lower() == 'dhcp':
            self.set_dhcp(True)
        elif addr.lower() == 'dhcpv6':
            self.set_dhcpv6(True)
        elif not is_interface_addr_assigned(self.ifname, addr):
            cmd(f"ip addr add {addr} dev {self.ifname}")

    def del_addr(self, addr: str):
        """
        Delete IP(v6) address from interface. Address is only deleted if it is
        assigned to that interface. Address format must be exactly the same as
        was used when adding the address.

        addr: can be an IPv4 address, IPv6 address, dhcp or dhcpv6!
        IPv4: delete IPv4 address from interface
        IPv6: delete IPv6 address from interface
        DHCP: stop dhcp-client (IPv4) on interface
        DHCPv6: stop dhcp-client (IPv6) on interface
        """

        if not addr:
            raise ValueError("The deletion address cannot be empty")

        if addr.lower() == "dhcp":
            self.set_dhcp(False)
        elif addr.lower() == 'dhcpv6':
            self.set_dhcpv6(False)
        elif is_interface_addr_assigned(self.ifname, addr):
            cmd(f'ip addr del {addr} dev {self.ifname}')

    def get_state(self) -> bool:
        out = cmd(f"ip -json link show dev {self.ifname}")
        return True if 'UP' in jmespath.search('[*].flags | [0]', json.loads(out)) else False

    def get_alias(self) -> str:
        out = cmd(f"ip -json -detail link list dev {self.ifname}")
        return jmespath.search('[*].ifalias | [0]', json.loads(out)) or ''

    def get_mac(self) -> str:
        out = cmd(f"ip -json -detail link list dev {self.ifname}")
        return jmespath.search('[*].address | [0]', json.loads(out))
