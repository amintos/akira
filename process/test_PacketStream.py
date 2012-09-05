import unittest
from random import shuffle

from PacketStream import *

class MyError(Exception):
    pass

class PacketWriterTest(unittest.TestCase):

    def setUp(self):
        self.l = []
        self.error = False
        def write(s):
            if self.error:
                raise MyError('error')
            self.l.append(s)

        self.w = PacketWriter(write, 5)

    def test_write_nothing(self):
        self.w.write('')
        self.assertEquals(self.l, [])

    def test_write_less(self):
        self.w.write('4444')
        self.assertEquals(self.l, [])
        
    def test_write_less_then_more(self):
        self.w.write('333')
        self.w.write('55555')
        self.assertEquals(self.l, ['33355'])
        self.w.flush()
        self.assertEquals(self.l, ['33355', '555'])

    def test_write_much(self):
        self.w.write('1' * 1111)
        self.assertEquals(self.l, ['11111'] * (1111 // 5))
        self.w.write('1' * 1111)
        self.assertEquals(self.l, ['11111'] * (2222 // 5))
        self.w.flush()
        self.assertEquals(self.l[-1], '11')

    def test_write_packet_size(self):
        self.w.write('55555')
        self.assertEquals(self.l, ['55555'])

    def test_write_with_error(self):
        self.w.write('4444')
        self.error = True
        self.assertRaises(MyError, lambda: self.w.write('333'))
        self.error = False
        self.w.write('4444')
        self.assertEquals(self.l, ['44443', '33444'])
        self.w.flush()
        self.assertEquals(self.l[-1], '4')
        
    def test_flush_with_error(self):
        self.w.write('4444')
        self.error = True
        self.assertRaises(MyError, lambda: self.w.flush())
        self.error = False
        self.w.flush()
        self.assertEquals(self.l, ['4444'])

class CacheTest(unittest.TestCase):

    def setUp(self):
        self.c = Cache()

    def test_cache_somethiing(self):
        c = self.c
        c.cache('4444')
        self.assertEquals(c.size, 4)
        c.cache('4444')
        self.assertEquals(c.size, 8)

    def test_read(self):
        c = self.c
        c.cache('88888888')
        self.assertEquals(c.read(5), '8' * 5)
        self.assertEquals(c.size, 3)
        self.assertEquals(c.read(5), '8' * 3)
        self.assertEquals(c.size, 0)

    def test_read_wiht_error(self):
        def r(s):
            raise MyError('error!')
        c = self.c
        c.cache('55555')
        self.assertRaises(MyError, lambda: c.readTo(r, 5))
        self.assertEquals(c.read(10), '55555')


class SecretTest(unittest.TestCase):

    def setUp(self):
        self.s1 = Secret('1')
        self.s2 = Secret('2')

    def test_sign(self):
        a1 = self.s1.sign('a')
        a2 = self.s2.sign('a')
        self.assertNotEquals(a1, a2)
        self.assertTrue(self.s1.isSigned(a1))
        self.assertTrue(self.s2.isSigned(a2))
        self.assertFalse(self.s1.isSigned(a2))
        self.assertFalse(self.s2.isSigned(a1))

    def test_test_sign_on_bad_data(self):
        self.assertFalse(self.s1.isSigned('123321312312'))
        self.assertFalse(self.s1.isSigned(self.s1.sign('asadsf') + '1'))
        self.assertFalse(self.s1.isSigned(self.s1.sign('asadsf')[:-1]))

    def test_get_value_from_signed_stuff(self):
        s = self.s1.sign('abc')
        self.assertNotEqual(s, 'abc')
        self.assertEquals(self.s1.signedPart(s), 'abc')
        self.assertIn(self.s1.signaturePart(s), s)
        self.assertEquals(self.s1.signaturePart(s), self.s1.hmac('abc'))


class HmacStreamTest(unittest.TestCase):

    def setUp(self):
        self.l_12 = [] # connection from 1 to 2
        self.l_21 = []
        self.secret = Secret('test')
        self.h1 = HmacStream(self.secret, \
                             lambda:self.l_21.pop(0), self.l_12.append)
        self.h2 = HmacStream(self.secret, \
                             lambda:self.l_12.pop(0), self.l_21.append)
        self.hx = HmacStream(Secret('intruder'), \
                             lambda:self.l_12.pop(0), self.l_21.append)
        
    def test_write_and_read(self):
        self.h1.write('hello!')
        self.assertEquals(self.h2.read(6), 'hello!')

    def test_writeTwiceAndRead(self):
        self.h1.write('hello!')
        self.h1.write('55555')
        self.assertEquals(self.h2.read(4), 'hell')
        self.assertEquals(self.h2.read(2), 'o!')
        self.assertEquals(self.h2.read(5), '55555')

    def test_intrude(self):
        self.hx.write('intrusion')
        self.h2.write('its okay!')
        self.assertEquals(self.h1.read(9), 'its okay!')

    def test_h1_writes_to_l_12(self):
        self.h1.write('a')
        self.assertNotEquals(self.l_12, [])
        self.assertEquals(self.l_21, [])

    def test_vary_order(self):
        self.h1.write('a')
        self.h1.write('b')
        self.l_12 = list(reversed(self.l_12))
        self.assertEquals(self.h2.read(1), 'a')
        self.assertEquals(self.h2.read(1), 'b')

    def test_manyPacketsShuffled(self):
        s = ''
        for i in range(256):
            self.h1.write(chr(i))
            s+= chr(i)
        shuffle(self.l_12)
        self.assertEquals(self.h2.read(len(s)), s)

    def communicate(self, times = -1):
        while times != 0:
            if self.l_21:
                self.h1.communicate()
            elif self.l_12:
                self.h2.communicate()
            else:
                break
            times -= 1

    def test_lost_packet(self):
        self.h1.write('1')
        self.h1.write('2')
        self.h1.write('3')
        self.assertEquals(len(self.l_12), 3)
        p = self.l_12.pop(1)
        self.communicate(10)
        self.assertEquals(self.h1.read(3), '123')

    

if __name__ == '__main__':
    unittest.main(exit = False)
        
