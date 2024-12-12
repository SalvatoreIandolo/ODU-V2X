from scapy.all import *
import time, subprocess
import asn1tools as asn
import os
from time import sleep
import GeoNetworking
from datetime import timedelta

recipients_mac_adress= 'ff:ff:ff:ff:ff:ff'
your_mac_adress= 'b4:b5:b6:c4:11:49'
interface = 'wlan1'

latitude = 446351418
longitude = 108136683


cam = asn.compile_files('ITS-Container.asn','uper')
dict_to_send = {'header': {'protocolVersion': 2, 'messageID': 2, 'stationID': 10},
                 'cam': {'generationDeltaTime': int(time.time()), 'camParameters':
                          {'basicContainer': {'stationType': 5, 'referencePosition': {'latitude': 449224306, 'longitude': 109968809,
                         'positionConfidenceEllipse': {'semiMajorConfidence': 282, 'semiMinorConfidence': 280, 'semiMajorOrientation': 1138},
                           'altitude': {'altitudeValue': 6050, 'altitudeConfidence': 'alt-020-00'}}}, 'highFrequencyContainer': 
                           ('basicVehicleContainerHighFrequency', {'heading': {'headingValue': 62, 'headingConfidence': 8}, 'speed': 
                            {'speedValue': 1163, 'speedConfidence': 4}, 'driveDirection': 'forward', 'vehicleLength': 
                            {'vehicleLengthValue': 42, 'vehicleLengthConfidenceIndication': 'trailerPresenceIsUnknown'}, 'vehicleWidth': 18,
                              'longitudinalAcceleration': {'longitudinalAccelerationValue': -2, 'longitudinalAccelerationConfidence': 102},
                             'curvature': {'curvatureValue': 386, 'curvatureConfidence': 'onePerMeter-0-01'}, 'curvatureCalculationMode': 
                             'yawRateUsed', 'yawRate': {'yawRateValue': 2354, 'yawRateConfidence': 'unavailable'}, 'accelerationControl': (b'@', 7), 
                             'steeringWheelAngle': {'steeringWheelAngleValue': 57, 'steeringWheelAngleConfidence': 1}, 'lateralAcceleration': 
                             {'lateralAccelerationValue': 43, 'lateralAccelerationConfidence': 102}})}}}


cam_bytes = cam.encode('CAM', dict_to_send)

uper_string = cam_bytes.hex()






# Registra il nuovo livello di protocollo
#bind_layers(Dot11, GeoNetworking, type=0x8947)  # Usa il valore EtherType corretto





# Creare un pacchetto CAM personalizzato 
command = 'date +%3S%3N'

while True:

  time1 = time.perf_counter()
	
  # Creare un pacchetto CAM personalizzato 
  
  
	
  geo = GeoNetworking.GeoNetworking(version= 1,basic_next_header = 1, reserved = 0,
                        life_time_multiplier = 60, life_time_base = 1,
                        remaining_hop_limit = 1, common_next_header = 2, h_reserved = 0,
                        header_type = 5, header_sub_type = 0, traffic_story_carry_forward = 0,
                        traffic_channel_offload = 0, traffic_class_id = 2, mobility_flags = 0,
                        flags_reserved = 0, payload_lenght = 50, maximum_hop_limit = 1, Reserved = 0,
                        gn_addr_manual = 0, gn_addr_its_type = 15, gn_addr_its_country_code = 0,
                        gn_addr_address = your_mac_adress ,timestamp = int(subprocess.check_output(command, shell=True, text=True)),
                        latitude = latitude, longitude = longitude, position_accuracy_indicator = 0,
                        speed = 0, heading = 0,local_channel_busy_ratio = 0,max_neighbouring_cbr = 0,
                        output_power = 23,reserved_tsbp = 0,reserved_tsbp_2 = 0)


  



  print(geo)

  # Visualizza il pacchetto
  cam_raw = raw(cam_bytes)

  geo_raw = raw(geo)

  #print(b)

  btp_b_raw = b'\x07\xd1\x54\x00'

  
  dot11 = Dot11(subtype=8,type=2, proto=0, ID=0, addr1="ff:ff:ff:ff:ff:ff", addr2=your_mac_adress, addr3="ff:ff:ff:ff:ff:ff", SC=480)
  qos = Dot11QoS(A_MSDU_Present=0, Ack_Policy=1, EOSP=0, TID=3, TXOP=0 )
  llc = LLC(dsap=0xaa, ssap=0xaa, ctrl=3)
  snap = SNAP(OUI=0, code=0x8947)
  raww = Raw(load=geo_raw+btp_b_raw+cam_raw)
  mex = RadioTap(present = 0x400000, timestamp = int(time1),  ts_accuracy = 0,  ts_position = 0,ts_flags = None)/dot11/qos/llc/snap/raww

  

  answer = sendp(mex, iface=interface)

  print(timedelta(seconds=time.perf_counter()-time1))


