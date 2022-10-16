#!/usr/bin/env python

# import normal packages
import platform
import os
import sys
import threading
import socket
import struct
import select


from gi.repository import GLib as gobject

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService




def sma_receiver_thread() :
    
    ipbind = '0.0.0.0'
    MCAST_GRP = '239.12.255.254'
    MCAST_PORT = 9522
            
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', MCAST_PORT))
    try:
        mreq = struct.pack("4s4s", socket.inet_aton(MCAST_GRP), socket.inet_aton(ipbind))
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    except BaseException:
        print('could not connect to mulicast group or bind to given interface')
        sys.exit(1)

    while True:
        ready = select.select([sock], [], [], 2)

        if ready[0] == []:
            _dbusservice['/Ac/L1/Power'] = 0 # set power to zero if timeout
            _dbusservice['/Ac/L2/Power'] = 0 # set power to zero if timeout
            _dbusservice['/Ac/L3/Power'] = 0 # set power to zero if timeout
            _dbusservice['/Ac/Power'] = 0 # set power to zero if timeout
            continue
 
        b = sock.recv(608)
            
        try:
            if len(b) < 500: # too short
                continue
                
            if int.from_bytes(b[16:18], byteorder='big') != 0x6069 : # wrong protocol?
                continue
                
            if int.from_bytes(b[20:24], byteorder='big') == 0xffffffff : # wrong serial?
                continue  
                
            _dbusservice['/Ac/Power'] = (int.from_bytes(b[32:36], byteorder='big') - int.from_bytes(b[52:56], byteorder='big')) / 10
            _dbusservice['/Ac/Energy/Forward'] = int.from_bytes(b[40:48], byteorder='big') / 3600 / 1000
            _dbusservice['/Ac/Energy/Reverse'] = int.from_bytes(b[60:68], byteorder='big') / 3600 / 1000
            
            offset = 164
            _dbusservice['/Ac/L1/Energy/Forward'] = int.from_bytes(b[offset + 12:offset + 20], byteorder='big') / 3600 / 1000
            _dbusservice['/Ac/L1/Energy/Reverse'] = int.from_bytes(b[offset + 32:offset + 40], byteorder='big') / 3600 / 1000
            _dbusservice['/Ac/L1/Power'] = (int.from_bytes(b[offset + 4:offset + 8], byteorder='big') - int.from_bytes(b[offset + 24:offset + 28], byteorder='big')) / 10
            _dbusservice['/Ac/L1/Voltage'] = int.from_bytes(b[offset + 132:offset + 136], byteorder='big') / 1000
            _dbusservice['/Ac/L1/Current'] = _dbusservice['/Ac/L1/Power'] / _dbusservice['/Ac/L1/Voltage']

            offset = 308
            _dbusservice['/Ac/L2/Energy/Forward'] = int.from_bytes(b[offset + 12:offset + 20], byteorder='big') / 3600 / 1000
            _dbusservice['/Ac/L2/Energy/Reverse'] = int.from_bytes(b[offset + 32:offset + 40], byteorder='big') / 3600 / 1000
            _dbusservice['/Ac/L2/Power'] = (int.from_bytes(b[offset + 4:offset + 8], byteorder='big') - int.from_bytes(b[offset + 24:offset + 28], byteorder='big')) / 10
            _dbusservice['/Ac/L2/Voltage'] = int.from_bytes(b[offset + 132:offset + 136], byteorder='big') / 1000
            _dbusservice['/Ac/L2/Current'] = _dbusservice['/Ac/L2/Power'] / _dbusservice['/Ac/L2/Voltage']
            
            offset = 452
            _dbusservice['/Ac/L3/Energy/Forward'] = int.from_bytes(b[offset + 12:offset + 20], byteorder='big') / 3600 / 1000
            _dbusservice['/Ac/L3/Energy/Reverse'] = int.from_bytes(b[offset + 32:offset + 40], byteorder='big') / 3600 / 1000
            _dbusservice['/Ac/L3/Power'] = (int.from_bytes(b[offset + 4:offset + 8], byteorder='big') - int.from_bytes(b[offset + 24:offset + 28], byteorder='big')) / 10
            _dbusservice['/Ac/L3/Voltage'] = int.from_bytes(b[offset + 132:offset + 136], byteorder='big') / 1000
            _dbusservice['/Ac/L3/Current'] = _dbusservice['/Ac/L3/Power'] / _dbusservice['/Ac/L3/Voltage']
            
            _dbusservice['/Ac/Current'] = _dbusservice['/Ac/L1/Current'] + _dbusservice['/Ac/L2/Current'] + _dbusservice['/Ac/L3/Current']
            
            _dbusservice['/Serial'] = int.from_bytes(b[20:24], byteorder='big')
        except:
            print('error parsing energy meter values')   
        
from dbus.mainloop.glib import DBusGMainLoop
# Have a mainloop, so we can send/receive asynchronous calls to and from dbus
DBusGMainLoop(set_as_default=True)

# formatting
_kwh = lambda p, v: (str(round(v, 2)) + 'kWh')
_a = lambda p, v: (str(round(v, 1)) + 'A')
_w = lambda p, v: (str(round(v, 1)) + 'W')
_v = lambda p, v: (str(round(v, 1)) + 'V')
_degC = lambda p, v: (str(v) + ' C')
_s = lambda p, v: (str(v) + 's')

# start our main-service

servicename='com.victronenergy.grid.SMA-EM'
paths={
    '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh},
    '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
    '/Ac/Power': {'initial': 0, 'textformat': _w},
    '/Ac/Current': {'initial': 0, 'textformat': _a},
    '/Ac/Voltage': {'initial': 0, 'textformat': _v},
    
    '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
    '/Ac/L1/Energy/Forward': {'initial': 0, 'textformat': _kwh},
    '/Ac/L1/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
    '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
    '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},

    '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
    '/Ac/L2/Energy/Forward': {'initial': 0, 'textformat': _kwh},
    '/Ac/L2/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
    '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
    '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},
    
    '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
    '/Ac/L3/Energy/Forward': {'initial': 0, 'textformat': _kwh},
    '/Ac/L3/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
    '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
    '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
    
    '/DeviceType': {'initial': 0, 'textformat': _w},
    '/ErrorCode': {'initial': 0, 'textformat': _w},                

}


deviceinstance = 55
productname='Sma Energy Meter'

_dbusservice = VeDbusService("{}.http_{:02d}".format(servicename, deviceinstance))


# Create the management objects, as specified in the ccgx dbus-api document
_dbusservice.add_path('/Mgmt/ProcessName', __file__)
_dbusservice.add_path('/Mgmt/ProcessVersion',
                           'Unkown version, and running on Python ' + platform.python_version())
_dbusservice.add_path('/Mgmt/Connection', 'UDP Multicast')

# Create the mandatory objects
_dbusservice.add_path('/DeviceInstance', deviceinstance)
_dbusservice.add_path('/ProductId', 45058)  #
_dbusservice.add_path('/ProductName', productname)
_dbusservice.add_path('/CustomName', productname)
_dbusservice.add_path('/FirmwareVersion', 0)
_dbusservice.add_path('/HardwareVersion', 0)
_dbusservice.add_path('/Serial', 1)
_dbusservice.add_path('/Connected', 1)
_dbusservice.add_path('/UpdateIndex', 0)


# add path values to dbus
for path, settings in paths.items():
    _dbusservice.add_path(
        path, settings['initial'], gettextcallback=settings['textformat'], writeable=True)


receive_thread = threading.Thread(target=sma_receiver_thread)
receive_thread.daemon = True
receive_thread.start() 

    
mainloop = gobject.MainLoop()
mainloop.run()
