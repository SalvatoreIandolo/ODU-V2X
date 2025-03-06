from scapy.all import *
import time, subprocess
import asn1tools as asn
import os
import GeoNetworking
from datetime import timedelta
import gpsd
import datetime

recipients_mac_adress= 'ff:ff:ff:ff:ff:ff'
your_mac_adress= 'b4:b5:b6:c4:11:49'
interface = 'wlan1'


denm = asn.compile_files('ETSI-ITS-CDD.asn','uper')

# Connect to the local gpsd
gpsd.connect()

packet = gpsd.get_current()

timestamp = packet.time
timestamp_gps_parsed = datetime.datetime.strptime(timestamp[:-5],"%Y-%m-%dT%H:%M:%S")
milliseconds = int(timestamp.replace("Z","")[-3:])
timestamp_gps_parsed =timestamp_gps_parsed.replace(microsecond=milliseconds * 1000)
past = datetime.datetime(2004, 1, 1, 0, 0, 0) # to match the EITS generation delta time specification
diff = timestamp_gps_parsed - past
seconds = int(diff.total_seconds() * 1000)
eventDetectionTime = seconds % 65536 #final value to put in CAM packet

# Command to get timestamp in secs and nanosecs
command = 'date +%3S%3N'

try:

  

  while True:

    start_time = time.perf_counter()
    
    # Creare un pacchetto CAM personalizzato 
    
    # Get the current position
    packet = gpsd.get_current()

    # Get data from the gps
    latitude = int(int(str(packet.lat).replace(".",'')) / 100)
    longitude = int(int(str(packet.lon).replace(".",'')) / 100)
    speed = int(packet.hspeed *100)
    heading = int(packet.track * 10)
    timestamp = packet.time
    altitude = int(packet.alt * 100)

    # parse timestamp took from gps from string type to datetime 
    print(packet.time)
    timestamp_gps_parsed = datetime.datetime.strptime(timestamp[:-5],"%Y-%m-%dT%H:%M:%S")
    milliseconds = int(timestamp.replace("Z","")[-3:])
    timestamp_gps_parsed =timestamp_gps_parsed.replace(microsecond=milliseconds * 1000)
    # generationDeltaTime = TimestampIts mod 65 536 TimestampIts represents an integer value in milliseconds since 2004-01-01T00:00:00:000Z

    past = datetime.datetime(2004, 1, 1, 0, 0, 0) # to match the EITS generation delta time specification
    diff = timestamp_gps_parsed - past
    seconds = int(diff.total_seconds() * 1000)
    generationDeltaTime = seconds % 65536 #final value to put in CAM packet


    
    print(speed)
    print(packet.track)
    print(heading)
    print(generationDeltaTime)
    print(timestamp_gps_parsed)

    #create geonetworking part, timestamp with the command date inserted, can be removed 

    geo = GeoNetworking.GeoNetworking(version= 1,basic_next_header = 1, reserved = 0,
                          life_time_multiplier = 60, life_time_base = 1,
                          remaining_hop_limit = 1, common_next_header = 2, h_reserved = 0,
                          header_type = 5, header_sub_type = 0, traffic_story_carry_forward = 0,
                          traffic_channel_offload = 0, traffic_class_id = 2, mobility_flags = 0,
                          flags_reserved = 0, payload_lenght = 50, maximum_hop_limit = 1, Reserved = 0,
                          gn_addr_manual = 0, gn_addr_its_type = 15, gn_addr_its_country_code = 0,
                          gn_addr_address = your_mac_adress ,timestamp = generationDeltaTime,
                          latitude = latitude, longitude = longitude, position_accuracy_indicator = 0,
                          speed = 0, heading = 0,local_channel_busy_ratio = 0,max_neighbouring_cbr = 0,
                          output_power = 23,reserved_tsbp = 0,reserved_tsbp_2 = 0)

    


    
    dict_to_send = {'header': {'protocolVersion': 2, 'messageId': 1, 'stationId': 4316}, 'denm': {'management': {'actionID': 
                {'originatingStationId': 999, 'sequenceNumber': 101}, 'detectionTime': eventDetectionTime, 'referenceTime': generationDeltaTime,
             'eventPosition': {'latitude': latitude, 'longitude': longitude, 'positionConfidenceEllipse': {'semiMajorConfidence': 100,
             'semiMinorConfidence': 100, 'semiMajorOrientation': 0}, 'altitude': {'altitudeValue': altitude, 'altitudeConfidence': 'alt-000-01'}},
               'relevanceDistance': 'lessThan1000m', 'relevanceTrafficDirection': 'upstreamTraffic', 'validityDuration': 59, 'stationType': 15},
                 'situation': {'informationQuality': 6, 'eventType': {'causeCode': 3, 'subCauseCode': 0}}}}


    denm_bytes = denm.encode('DENM', dict_to_send)

    uper_string = denm_bytes.hex()

    # Visualizza il pacchetto
    denm_raw = raw(denm_bytes)

    geo_raw = raw(geo)

    btp_b_raw = b'\x07\xd1\x54\x00'

    # Create all layers necessary for a CAM packet

    dot11 = Dot11(subtype=8,type=2, proto=0, ID=0, addr1="ff:ff:ff:ff:ff:ff", addr2=your_mac_adress, addr3="ff:ff:ff:ff:ff:ff", SC=480)
    qos = Dot11QoS(A_MSDU_Present=0, Ack_Policy=1, EOSP=0, TID=3, TXOP=0 )
    llc = LLC(dsap=0xaa, ssap=0xaa, ctrl=3)
    snap = SNAP(OUI=0, code=0x8947)
    raww = Raw(load=geo_raw+btp_b_raw+denm_raw)
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
