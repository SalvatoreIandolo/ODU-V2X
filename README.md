# ODU-V2X
This repository contains the documentation to make Linux talk IEEE 802.11p, an amendment to the popular IEEE 802.11 standard (aka Wi-Fi) aiming at wireless access in vehicular environments (WAVE), using as microprocessor the Raspberry Pi 5. We provide [here](https://drive.google.com/file/d/18nidumndKURn4lcGJB4QnWLtRST3PxBK/view?usp=sharing) a ready-to-use ISO that can be flashed and enables all the features descrived in the following sections.
## Hardware
To access the the 5.9Ghz band and support IEEE 802.11p, we equipped the Raspberry with a HAT (Hardware Attached on Top) enabling the support of MiniPCIe Wi-Fi cards and installed an "ath9k" Wi-Fi card, in our case the Mikrotik R11e-5HnD. This was done because the ath9k Wi-Fi driver is the only one capable of supporting both OCB (Outside the Context of a BSS) and the 5.9Ghz band. To sum up, the hardware needed is:
- Raspberry Pi 5
- Hat mPCIe for Raspberry Pi 5 (the one we used can be found [here](https://pineboards.io/products/hat-mpcie-for-raspberry-pi-5?_pos=2&_sid=b284f9774&_ss=r)
- Wi-Fi card [Mikrotik R11e-5HnD](https://mikrotik.com/product/R11e-5HnD)

## Software setup
Most changes for the components of the IEEE 802.11 stack are already in Linux mainline, but to get ready for the 802.11p we need few more steps. We used this [guide](https://gitlab.com/hpi-potsdam/osm/g5-on-linux/11p-on-linux) to implement the 802.11p and support the 5.9Ghz band, but with some little modifications that will be described.
First of all, we need to disable the in-build Wi-Fi of the Raspberry in order to use our PCIe Wi-Fi card. This is done by adding the following lines in the file /boot/firmware/config.txt
```
dtoverlay=disable-Wi-Fi
dtparam= pciex1
dtoverlay=pcie-32bit-dma
```
Important to note is that the Mikrotik R11e-5HnD has regdomain set in firmware/EEPROM, which dictates the limits of the device. The regdomain set is in our case "US", so this means that when we have to added the support for the 5.9Ghz frequencies, we cannot create another country code, as done in the guide liked above, but we need to expand the rescrictions in the "US" regdomain. This can be done updating the Linux' wireless-regdb  and modifing the file "db.txt" by adding to the "US" regulations these line:

```
(5855 - 5925 @ 10), (100)
```

Another step is, while we are patching the ath9k driver to support the 5.9Ghz frequencies, is to eliminate the "NL80211_RRF_NO_IR" flag. This flag means that we cannot initiate radiation on those frequencies. Since the scope of this project is not only to receive but also transmit vehicular messages, the "NL80211_RRF_NO_IR" flag is just replaced with a "0" value. The line should look like this and has to effect the file located in drivers/net/wireless/ath/regd.c


```
#define ATH_5GHZ_5470_5925	REG_RULE(5470-10, 5925+10, 80, 0, 30, 0)

#define ATH_5GHZ_5725_5925	REG_RULE(5725-10, 5925+10, 80, 0, 30, 0)
```
After compiling the kernel and signing the new regulatory data with the Central Regulatory Domain Agent (CRDA), we are ready to put the interface in IEEE 802.11p band, OCB mode and assing an IP address:

```
sudo ip link set wlan0 down
sudo iw dev wlan0 set type ocb
sudo ip link set wlan0 up
sudo iw dev wlan0 ocb join 5900 10MHZ
sudo ip address add 10.1.1.13/24 brd + dev wlan0
sudo iw dev wlan0 interface add wlan1 type monitor
sudo ifconfig wlan1 up
```
To receive messages we recommend either tshark or tcpdump:

```
sudo tshark -i wlan1
sudo tcpdump -i wlan1
```
To send messages CAM/GEONW messages, we provide in this repo some python scripts that serve this scope. In order to use them, you need to install the following libraries:
-asn1tools
-scapy

```
sudo python3 send_CAM_mex.py
sudo python3 send_GEONW_mex.py
```

