def is_interface_addr_assigned(ifname: str, address: str) -> bool:
    import netifaces
    from netifaces import AF_INET, AF_INET6

    netmask = None
    if '/' in address:
        address, netmask = address.split('/')

    try:
        ifaces = netifaces.ifaddresses(ifname)
    except ValueError:
        return False

    addr_type = AF_INET if is_ipv4(address) else AF_INET6

    for ip in ifaces.get(addr_type, []):
        # ip can have the interface name in the 'addr' field, we need to remove it
        # {'addr': 'fe80::f84f:28ff:fee7:4400%enp1s0', 'netmask': 'ffff:ffff:ffff:ffff::'}
        ip_addr = ip['addr'].split('%')[0]

        if not are_same_address(address, ip_addr):
            continue

        if not netmask:
            return True

        if is_ipv4(ip_addr):
            prefix = sum([bin(int(_)).count('1') for _ in ip['netmask'].split('.')])
        else:
            prefix = sum([bin(int(_, 16)).count('1') for _ in ip['netmask'].split('/')[0].split(':') if _])

        if prefix == int(netmask):
            return True

    return False


def is_ipv4(address: str) -> bool:
    import IPy

    netmask = None
    if '/' in address:
        address, netmask = address.split('/')

    try:
        ip = IPy.IP(address)

        if netmask and int(netmask) > 24:
            return False
        return ip.version() == 4
    except ValueError:
        return False


def are_same_address(addr1: str, addr2: str) -> bool:
    from socket import AF_INET
    from socket import AF_INET6
    from socket import inet_pton

    # compare the binary representation of the IP
    addr1_type = AF_INET if is_ipv4(addr1) else AF_INET6
    addr2_type = AF_INET if is_ipv4(addr2) else AF_INET6
    return inet_pton(addr1_type, addr1) == inet_pton(addr2_type, addr2)
