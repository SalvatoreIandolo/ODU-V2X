import re
import serial
import socket
from scapy.all import *
import time, subprocess
import asn1tools as asn
import os
import GeoNetworking
from datetime import timedelta, datetime
import gpsd
import datetime
import threading
import time
import psutil


def get_mac_address():
    for interface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == psutil.AF_LINK:
                return addr.address

recipients_mac_adress= 'ff:ff:ff:ff:ff:ff'
your_mac_adress= get_mac_address()
print(your_mac_adress)
interface = 'wlan1'

denm = asn.compile_files('ETSI-ITS-CDD.asn','uper')

# Command to get timestamp in secs and nanosecs
command = 'date +%3S%3N'

def convert_time_to_datetime(time_str, date_str):
    hours = int(time_str[:2])
    minutes = int(time_str[2:4])
    seconds = float(time_str[4:])
    day = int(date_str[:2])
    month = int(date_str[2:4])
    year = int("20" + date_str[4:])  # Convert two-digit year to four-digit
    return datetime.datetime(year, month, day, hours, minutes, int(seconds), int((seconds % 1) * 1e6))

def convert_to_decimal(degrees, minutes, direction):
    decimal = float(degrees) + float(minutes) / 60
    if direction in ['S', 'W']:
        decimal = -decimal
    decimal_no_dot = str(decimal).replace('.', '')
    decimal_no_dot = decimal_no_dot.ljust(9, '0')[:9]  # Ensure exactly 9 digits
    return int(decimal_no_dot)

def parse_gprmc(sentence):
    pattern = r'\$GPRMC,(\d{6}\.\d+),([AV]),(\d{2})(\d{2}\.\d+),([NS]),(\d{3})(\d{2}\.\d+),([EW]),([\d\.]*),([\d\.]*),(\d{6}),?,?,([A-Z])?\*(\w{2})'
    match = re.match(pattern, sentence)
    
    if not match:
        return None
    
    time_utc = convert_time_to_datetime(match.group(1), match.group(11) if match.group(11) else "")
    status = match.group(2)
    latitude = convert_to_decimal(match.group(3), match.group(4), match.group(5))
    longitude = convert_to_decimal(match.group(6), match.group(7), match.group(8))
    speed_knots = float(match.group(9)) if match.group(9) else 0.0
    speed_kmh = int(speed_knots * 1.852 )  # Convert knots to km/h
    date_utc = match.group(10)
    course_over_ground = int(float(match.group(10))) if match.group(10) else 0
    mode = match.group(11) if match.group(11) else "N/A"
    checksum = match.group(12)

    # generationDeltaTime = TimestampIts mod 65 536 TimestampIts represents an integer value in milliseconds since 2004-01-01T00:00:00:000Z
    past = datetime.datetime(2004, 1, 1, 0, 0, 0) # to match the EITS generation delta time specification
    diff = time_utc - past
    seconds = int(diff.total_seconds() * 1000)
    generationDeltaTime = seconds % 65536 #final value to put in CAM packet

    
    parsed_data = {
        'Time (UTC)': time_utc,
        'Status': 'Active' if status == 'A' else 'Void',
        'Latitude': latitude,
        'Longitude': longitude,
        'Speed (knots)': speed_knots,
        'Speed_kmh': round(speed_kmh, 2),
        'Date (UTC)': date_utc,
        "Heading": course_over_ground,
        'Mode': mode,
        'Checksum': checksum,
        'Generation_delta_time':generationDeltaTime
    }
    
    return parsed_data

# Serial port settings
GPS_PORT = "/dev/ttyACM0"  # Adjust based on your system
BAUD_RATE = 9600  # Common baud rate for GPS modules

# UDP settings
UDP_IP = "10.1.1.255"  # Broadcast address
UDP_PORT = 5005  # Port to send data
BUFFER_SIZE = 1024

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # Enable broadcast


with serial.Serial(GPS_PORT, BAUD_RATE, timeout=1) as ser:
    try:
        while True:
            start_time = time.perf_counter()
            
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if line.startswith("$GPRMC"):  # Extract only GPRMC sentences
                parsed_output = parse_gprmc(line)
                print("Broadcasting:", line)
                #print(parsed_output["Latitude"])
                
                #sock.sendto(line.encode(), (UDP_IP, UDP_PORT))  # Send via UDP

                #create geonetworking part, timestamp with the command date inserted, can be removed 

                geo = GeoNetworking.GeoNetworking(version= 1,basic_next_header = 1, reserved = 0,
                                    life_time_multiplier = 60, life_time_base = 1,
                                    remaining_hop_limit = 1, common_next_header = 2, h_reserved = 0,
                                    header_type = 5, header_sub_type = 0, traffic_story_carry_forward = 0,
                                    traffic_channel_offload = 0, traffic_class_id = 2, mobility_flags = 0,
                                    flags_reserved = 0, payload_lenght = 50, maximum_hop_limit = 1, Reserved = 0,
                                    gn_addr_manual = 0, gn_addr_its_type = 15, gn_addr_its_country_code = 0,
                                    gn_addr_address = your_mac_adress ,timestamp = int(subprocess.check_output(command, shell=True, text=True)),
                                    latitude = 0, longitude = 0, position_accuracy_indicator = 0,
                                    speed = 0, heading = 0,local_channel_busy_ratio = 0,max_neighbouring_cbr = 0,
                                    output_power = 23,reserved_tsbp = 0,reserved_tsbp_2 = 0)


                dict_to_send = {'header': {'protocolVersion': 2, 'messageId': 1, 'stationId': 4316}, 'denm': {'management': {'actionID': 
                {'originatingStationId': 999, 'sequenceNumber': 101}, 'detectionTime': parsed_output["Generation_delta_time"], 'referenceTime': parsed_output["Generation_delta_time"],
             'eventPosition': {'latitude': parsed_output["Latitude"], 'longitude': parsed_output["Longitude"], 'positionConfidenceEllipse': {'semiMajorConfidence': 100,
             'semiMinorConfidence': 100, 'semiMajorOrientation': 0}, 'altitude': {'altitudeValue': 100, 'altitudeConfidence': 'alt-000-01'}},
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
