from scapy.all import *
import time, subprocess
import asn1tools as asn
import os
from time import sleep

# Definisci il livello di protocollo GeoNetworking
class GeoNetworking(Packet):
    name = "GeoNetworking"
    fields_desc = [
        #BASIC HEADER
        BitField("version", 1,4),
        BitField("basic_next_header", 0,4),
        BitField("reserved", 0,8),
        # The LTMultiplier is a 6 bit unsigned integer, which represents a multiplier range from 0 to 26 - 1 = 63. Nel pacchetti GWONW di movyon è 60
        BitField("life_time_multiplier", 60,6,8), 
        # The LTBase sub-field represents a two bit unsigned selector that chooses one out of four predefined values -->
        #0 50 ms
        #1 1 s
        #2 10 s
        #3 100 s
        BitField("life_time_base", 0,2), 
        BitField("remaining_hop_limit", 0, 8),

        #COMMON HEADER
        #0 (usato da movyon) UNSPECIFIED
        #1 BTP-A
        #2 BTP-B
        #3 IPV6
        BitField("common_next_header", 1,4), 
        BitField("h_reserved", 0,4), #set to 0
        BitField("header_type", 0,4), # 0 unspecified, 1 BEACON etc.
        BitField("header_sub_type", 0,4),
        BitField("traffic_story_carry_forward", 0,1),
        BitField("traffic_channel_offload", 0,1),
        BitField("traffic_class_id", 0,6),
        BitField("mobility_flags", 0,1),
        BitField("flags_reserved", 0,7), #reserved to 0
        BitField("payload_lenght", 0,16),
        BitField("maximum_hop_limit", 1,8),
        BitField("Reserved", 0,8), #set to 0

        #BEACON HEADER
        #GN_ADDR
        
        ConditionalField(BitField("gn_addr_manual", 0,1),lambda pkt: pkt.header_type == 1),
        ConditionalField(BitField("gn_addr_its_type", 0,5),lambda pkt: pkt.header_type == 1),
        ConditionalField(BitField("gn_addr_its_country_code", 0,10),lambda pkt: pkt.header_type == 1),
        ConditionalField(MACField("gn_addr_address", "78:5e:e8:50:08:a2"),lambda pkt: pkt.header_type == 1),
        ConditionalField(BitField("timestamp", 0,32),lambda pkt: pkt.header_type == 1), #number of elapsed TAI milliseconds since 2004-01-01 00:00:00.000 UTC
        ConditionalField(BitField("latitude", 0,32),lambda pkt: pkt.header_type == 1),
        ConditionalField(BitField("longitude", 0,32),lambda pkt: pkt.header_type == 1),
        #Set to 1 (i.e. True) if the semiMajorConfidence
        #of the PosConfidenceEllipse as specified in
        #ETSI TS 102 894-2 [11] is smaller than the GN
        #protocol constant itsGnPaiInterval / 2
        #Set to 0 (i.e. False) otherwise

        ConditionalField(BitField("position_accuracy_indicator", 0,1),lambda pkt: pkt.header_type == 1),
        ConditionalField(BitField("speed", 0,15),lambda pkt: pkt.header_type == 1),
        ConditionalField(BitField("heading", 0,16),lambda pkt: pkt.header_type == 1),
        

        #TOPOLOGICALLY SCOPED PACKET 

        ConditionalField(BitField("gn_addr_manual_top", 0,1), lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField("gn_addr_its_type_top", 0,5), lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField("gn_addr_its_country_code_top", 0,10), lambda pkt: pkt.header_type == 5),
        ConditionalField(MACField("gn_addr_address_top", "78:5e:e8:50:08:a2"), lambda pkt: pkt.header_type == 5),

        ConditionalField(BitField("timestamp_top", 0,32),lambda pkt: pkt.header_type == 5), #number of elapsed TAI milliseconds since 2004-01-01 00:00:00.000 UTC
        ConditionalField(BitField("latitude_top", 0,32), lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField("longitude_top", 0,32),lambda pkt: pkt.header_type == 5),
        #Set to 1 (i.e. True) if the semiMajorConfidence
        #of the PosConfidenceEllipse as specified in
        #ETSI TS 102 894-2 [11] is smaller than the GN
        #protocol constant itsGnPaiInterval / 2
        #Set to 0 (i.e. False) otherwise

        ConditionalField(BitField("position_accuracy_indicator_top", 0,1),lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField("speed_top", 0,15),lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField("heading_top", 0,16),lambda pkt: pkt.header_type == 5),

        ConditionalField(BitField('local_channel_busy_ratio',0,8),lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField('max_neighbouring_cbr',0,8),lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField('output_power',0,5),lambda pkt: pkt.header_type == 5),
        ConditionalField(BitField('reserved_tsbp',0,3),lambda pkt: pkt.header_type == 5),
	    ConditionalField(BitField('reserved_tsbp_2',0,8),lambda pkt: pkt.header_type == 5),
    ]
    
