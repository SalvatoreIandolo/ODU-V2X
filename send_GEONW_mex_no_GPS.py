from scapy.all import *
import time, subprocess
import asn1tools as asn
import os
import GeoNetworking
from datetime import timedelta
import datetime

recipients_mac_adress= 'ff:ff:ff:ff:ff:ff'
your_mac_adress= 'b4:b5:b6:c4:11:49'
interface = 'wlan1'


# Connect to the local gpsd
#gpsd.connect()


# Command to get timestamp in secs and nanosecs
command = 'date +%3S%3N'

try:

  

    while True:

        start_time = time.perf_counter()

        # Creare un pacchetto CAM personalizzato 

        # Get the current position
        #packet = gpsd.get_current()

        # Get data from the gps
        latitude = 446351418
        longitude = 108136683
        speed = 50
        heading = 0
        timestamp = 10000
        altitude = 0


        geo = GeoNetworking.GeoNetworking(version= 1,basic_next_header = 1, reserved = 0,
                                    life_time_multiplier = 60, life_time_base = 1,
                                    remaining_hop_limit = 1, common_next_header = 0, h_reserved = 0,
                                    header_type = 1, header_sub_type = 0, traffic_story_carry_forward = 0,
                                    traffic_channel_offload = 0, traffic_class_id = 3, mobility_flags = 0,
                                    flags_reserved = 0, payload_lenght = 0, maximum_hop_limit = 1, Reserved = 0,
                                    gn_addr_manual = 0, gn_addr_its_type = 15, gn_addr_its_country_code = 0,
                                    gn_addr_address = your_mac_adress ,timestamp = 10000,
                                    latitude = latitude, longitude = longitude, position_accuracy_indicator = 0,
                                    speed = speed, heading = heading)


        geo_raw = raw(geo)

        btp_b_raw = b'\x07\xd1\x54\x00'

        # Create all layers necessary for a CAM packet

        dot11 = Dot11(subtype=8,type=2, proto=0, ID=0, addr1="ff:ff:ff:ff:ff:ff", addr2=your_mac_adress, addr3="ff:ff:ff:ff:ff:ff", SC=480)
        qos = Dot11QoS(A_MSDU_Present=0, Ack_Policy=1, EOSP=0, TID=3, TXOP=0 )
        llc = LLC(dsap=0xaa, ssap=0xaa, ctrl=3)
        snap = SNAP(OUI=0, code=0x8947)
        raww = Raw(load=geo_raw+btp_b_raw)
        mex = RadioTap(present = 0x400000, timestamp = int(start_time),  ts_accuracy = 0,  ts_position = 0,ts_flags = None)/dot11/qos/llc/snap/raww

        # Send packet
        answer = sendp(mex, iface=interface)

        # Send a packet every 100 ms
        while (timedelta(seconds=time.perf_counter()-start_time) <= timedelta(milliseconds=100)):
            continue

        print(timedelta(seconds=time.perf_counter()-start_time))

except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print ("\nKilling Thread...")
    print ("Done.\nExiting.")
