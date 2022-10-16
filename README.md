# SMA Energy Meter driver for VenusOS
Simple python script that reads values from SMA Energy Meter and pushes them into VenusOS

If no values are received for more than 2 seconds it will go into "0 watt" mode to avoid that your battery goes crazy
# Installation
Download the *sma_energy_meter.py* file and put it into any folder on the venus device e.g. to */home/root*
Add *python /home/root/sma_energy_meter.py &* to your */data/rc.local* for autostart
# How it works
The python script simply subscribes to multicast group 239.12.255.254 port 9522 which is the broadcast group of the SMA Energy Meter in your ethernet network
# Special thanks to
https://github.com/mitchese/shm-et340
https://github.com/RalfZim/venus.dbus-fronius-smartmeter
