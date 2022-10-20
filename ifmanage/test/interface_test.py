import unittest

from ifmanage.interface import Interface


class TestInterface(unittest.TestCase):
    def test_exist(self):
        obj = Interface("enp1s0")
        self.assertEqual(obj.exist(), True)

        obj = Interface("lo")
        self.assertEqual(obj.exist(), True)

        obj = Interface("esfd")
        self.assertEqual(obj.exist(), False)


if __name__ == '__main__':
    unittest.main()
