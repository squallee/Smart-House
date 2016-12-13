import socket
import time
import sys
from optparse import OptionParser,OptionGroup



class BulbScanner():
    def __init__(self):
        self.found_bulbs = []

    def getBulbInfoByID(self, id):
        bulb_info = None
        for b in self.found_bulbs:
            if b['id'] == id:
                return b
        return b

    def getBulbInfo(self):
        return self.found_bulbs

    def scan(self, timeout=10):

        DISCOVERY_PORT = 48899

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', DISCOVERY_PORT))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        msg = "HF-A11ASSISTHREAD"

        # set the time at which we will quit the search
        quit_time = time.time() + timeout

        response_list = []
        # outer loop for query send
        while True:
            if time.time() > quit_time:
                break
            # send out a broadcast query
            sock.sendto(msg, ('<broadcast>', DISCOVERY_PORT))

            # inner loop waiting for responses
            while True:

                sock.settimeout(1)
                try:
                    data, addr = sock.recvfrom(64)
                except socket.timeout:
                    data = None
                    if time.time() > quit_time:
                        break

                if data is not None and data != msg:
                    # tuples of IDs and IP addresses
                    item = dict()
                    item['ipaddr'] = data.split(',')[0]
                    item['id'] = data.split(',')[1]
                    item['model'] = data.split(',')[2]
                    response_list.append(item)

        self.found_bulbs = response_list
        return response_list


def scan():
    # my code here
    print('hello')
    scanner = BulbScanner()
    scanner.scan(timeout=2)
    bulb_info_list = scanner.getBulbInfo()
    # we have a list of buld info dicts
    addrs = []
    if len(bulb_info_list) > 0:
        for b in bulb_info_list:
            addrs.append(b['ipaddr'])
    else:
        print
        "{} bulbs found".format(len(bulb_info_list))
        for b in bulb_info_list:
            print
            "  {} {}".format(b['id'], b['ipaddr'])
        sys.exit(0)
    return addrs

class WifiLedBulb():
    def __init__(self, ipaddr, port=5577):
        self.ipaddr = ipaddr
        self.port = port
        self.__is_on = False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.ipaddr, self.port))
        self.__state_str = ""

    def __str__(self):
        return self.__state_str


    def turnOn(self, on=True):
        if on:
            msg = bytearray([0x71, 0x23, 0x0f])
        else:
            msg = bytearray([0x71, 0x24, 0x0f])

        self.__write(msg)
        self.__is_on = on

    def isOn(self):
        return self.__is_on

    def turnOff(self):
        self.turnOn(False)

    def setRgb(self, r, g, b, persist=True):
        if persist:
            msg = bytearray([0x31])
        else:
            msg = bytearray([0x41])
        msg.append(r)
        msg.append(g)
        msg.append(b)
        msg.append(0x00)
        msg.append(0xf0)
        msg.append(0x0f)
        self.__write(msg)

    def __writeRaw(self, bytes):
        self.socket.send(bytes)

    def __write(self, bytes):
        # calculate checksum of byte array and add to end
        csum = sum(bytes) & 0xFF
        bytes.append(csum)
        # print "-------------",utils.dump_bytes(bytes)
        self.__writeRaw(bytes)


def parseArgs():
    parser = OptionParser()
    power_group = OptionGroup(parser, 'Power options (mutually exclusive)')
    mode_group = OptionGroup(parser, 'Mode options (mutually exclusive)')
    other_group = OptionGroup(parser, 'Other options')

    parser.add_option("-s", "--scan",
                      action="store_true", dest="scan", default=False,
                      help="Search for bulbs on local network")
    power_group.add_option("-1", "--on",
                           action="store_true", dest="on", default=False,
                           help="Turn on specified bulb(s)")
    power_group.add_option("-0", "--off",
                           action="store_true", dest="off", default=False,
                           help="Turn off specified bulb(s)")
    parser.add_option_group(power_group)

    mode_group.add_option("-c", "--color", dest="color", default=None,
                          help="Set single color mode.  Can be either color name, web hex, or comma-separated RGB triple",
                          metavar='COLOR')
    parser.add_option_group(mode_group)

    other_group.add_option("-v", "--volatile",
                           action="store_true", dest="volatile", default=False,
                           help="Don't persist mode setting with hard power cycle (RGB and WW modes only).")
    parser.add_option_group(other_group)

    (options, args) = parser.parse_args()
    return (options, args)

if __name__ == "__main__":
    (options, args) = parseArgs()
    addrs = []

    rst = scan()
    bulb_ip = rst[0]
    print(bulb_ip)
    if bulb_ip:
        bulb = WifiLedBulb(bulb_ip)
        bulb.setRgb(100, 0, 100)

    if options.scan:
        scan()
    else:
        addrs = args
        for addr in args:
            bulb = WifiLedBulb(addr)
    if options.on:
        bulb.turnOn()
    elif options.off:
        bulb.turnOff()
    if options.color is not None:
        bulb.setRgb(options.color[0], options.color[1], options.color[2])
