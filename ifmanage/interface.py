import os

from util.command import cmd


class Interface(object):
    def __init__(self, ifname, **kwargs):
        self.config = kwargs
        self.config.setdefault("ifname", ifname)
        self.ifname = ifname

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
        pass

    def set_dhcpv6(self, enable: bool):
        """
        Enable/Disable DHCPv6 client on a given interface.
        """
        pass

    def set_mtu(self, mtu:int):
        """
        Set interface mtu value.
        """
        cmd(f"ip link set {self.ifname} mtu {mtu}")