# Author: Mani Amoozadeh
# Email: mani.amoozadeh2@gmail.com

from scapy.all import sniff, IP, Raw

def handle_packet(packet):
    if IP in packet and packet[IP].src.startswith("10.10.10."):  # Filter out DHCP, etc.
        payload = packet[Raw].load if Raw in packet else b"<no payload>"
        print(f"Received packet: {packet[IP].src} → {packet[IP].dst}")
        print(f"Payload: {payload.decode(errors='replace')}")
        print("-" * 40)

print("[*] Listening for IP packets on eth1...")
sniff(iface="eth1", filter="ip and src host 10.10.10.1", prn=handle_packet)
