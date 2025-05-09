# Author: Mani Amoozadeh
# Email: mani.amoozadeh2@gmail.com

from scapy.all import Ether, IP, UDP, sendp

target_ip = "10.10.10.2"
source_ip = "10.10.10.1"

packet = Ether() / IP(src=source_ip, dst=target_ip) / UDP(sport=12345, dport=9999) / b"Hello from Scapy on eth1"
sendp(packet, iface="eth1", count=5)
