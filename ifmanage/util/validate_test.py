import unittest

from .validate import is_ipv4, is_interface_addr_assigned


class TestValidate(unittest.TestCase):
    def test_is_ipv4(self):
        self.assertEqual(is_ipv4("192.168.0.1"), True)
        self.assertEqual(is_ipv4("192.168.0.999"), False)
        self.assertEqual(is_ipv4("192.168.0.2/24"), True)

    def test_is_interface_addr_assigned(self):
        self.assertEqual(is_interface_addr_assigned("lo", "127.0.0.1"), True)
        self.assertEqual(is_interface_addr_assigned("enp1s0", "fe80::a00:27ff:fec5:f821"), True)


if __name__ == '__main__':
    unittest.main()
