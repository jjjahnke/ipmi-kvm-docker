#!/usr/bin/env python3
import sys
import os
import subprocess
import xml.etree.ElementTree as ET
import ipaddress
import argparse

# Configuration
COMPOSE_FILE = "tiny-dashboard/docker-compose.yml"
CONFIG_DIR = "tiny-dashboard/config"
SERVICES_FILE = f"{CONFIG_DIR}/services.yaml"
SETTINGS_FILE = f"{CONFIG_DIR}/settings.yaml"
WIDGETS_FILE = f"{CONFIG_DIR}/widgets.yaml"
BOOKMARKS_FILE = f"{CONFIG_DIR}/bookmarks.yaml"

# Constants
IPMI_PORT = 623
PROXMOX_PORT = 8006
PROXY_START_PORT = 8081

def scan_network(cidr):
    """
    Scans the given CIDR for IPMI (UDP 623) and Proxmox (TCP 8006) hosts.
    Returns a dictionary of found hosts and their types.
    """
    print(f"Scanning {cidr} for IPMI (UDP:{IPMI_PORT}) and Proxmox (TCP:{PROXMOX_PORT})...")
    
    # Construct nmap command
    # -sU: UDP Scan (for IPMI)
    # -sS: TCP SYN Scan (for Proxmox) - requires root/sudo usually. 
    # If not sudo, -sT (Connect scan) is used for TCP.
    # Note: UDP scan without sudo might fail or be slow.
    # We will try a combined scan.
    
    cmd = [
        "sudo", "nmap", 
        "-p", f"U:{IPMI_PORT},T:{PROXMOX_PORT}",
        "-sU", "-sS", # UDP and TCP SYN scan
        "--open",
        "-oX", "-", # Output to stdout as XML
        cidr
    ]
    
    # Fallback to non-sudo connect scan if sudo fails or not available? 
    # UDP scan really needs raw socket access (sudo). 
    # For now, we assume sudo access or running as root is acceptable given the nature of the tool. 
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        xml_output = result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running nmap: {e}")
        print("Ensure you have sudo privileges for UDP scanning.")
        sys.exit(1)

    hosts = []
    try:
        root = ET.fromstring(xml_output)
        for host in root.findall("host"):
            ip_addr = host.find("address").get("addr")
            host_info = {"ip": ip_addr, "type": []}
            
            ports = host.findall("ports/port")
            for port in ports:
                port_id = int(port.get("portid"))
                protocol = port.get("protocol")
                state = port.find("state").get("state")
                
                if state == "open":
                    if protocol == "udp" and port_id == IPMI_PORT:
                        host_info["type"].append("IPMI")
                    elif protocol == "tcp" and port_id == PROXMOX_PORT:
                        host_info["type"].append("PROXMOX")
            
            if host_info["type"]:
                hosts.append(host_info)
                print(f"Found {host_info['type']} at {ip_addr}")
                
    except ET.ParseError as e:
        print(f"Error parsing nmap XML: {e}")
        sys.exit(1)
        
    return hosts

def generate_configs(hosts, image_name):
    """Generates the docker-compose.yml and homepage config files."""
    
    # Ensure config directory exists
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # --- Docker Compose ---
    compose_content = """services:
  homepage:
    image: ghcr.io/gethomepage/homepage:latest
    container_name: homepage
    ports:
      - 3000:3000
    volumes:
      - ./config:/app/config
      - /var/run/docker.sock:/var/run/docker.sock
"""
    
    # --- Services YAML (Homepage) ---
    services_yaml = "---\n"
    
    proxmox_hosts = [h for h in hosts if "PROXMOX" in h["type"]]
    ipmi_hosts = [h for h in hosts if "IPMI" in h["type"]]
    
    # 1. Proxmox Group
    if proxmox_hosts:
        services_yaml += "- Proxmox Cluster:\n"
        for host in proxmox_hosts:
            ip = host["ip"]
            safe_ip = ip.replace(".", "-")
            services_yaml += f"    - Node {safe_ip}:\n"
            services_yaml += f"        icon: proxmox\n"
            services_yaml += f"        href: https://{ip}:{PROXMOX_PORT}\n"
            services_yaml += f"        description: \"Proxmox Node\"\n"
            # widget:
            #     type: ping
            #     ip: {ip}

    # 2. Management Plane Group (IPMI)
    if ipmi_hosts:
        services_yaml += "\n- Management Plane:\n"
        current_port = PROXY_START_PORT
        
        for host in ipmi_hosts:
            ip = host["ip"]
            safe_ip = ip.replace(".", "-")
            
            # A. Direct Link
            services_yaml += f"    - IPMI {safe_ip} (Direct):\n"
            services_yaml += f"        icon: mdi-server\n"
            services_yaml += f"        href: https://{ip}\n"
            services_yaml += f"        description: \"Direct Management\"\n"
            # widget:
            #     type: ping
            #     ip: {ip}
            
            # B. Proxy Link & Container
            proxy_service_name = f"kvm-{safe_ip}"
            
            # Add to Docker Compose
            compose_content += f"\n  {proxy_service_name}:\n"
            compose_content += f"    image: {image_name}\n"
            compose_content += f"    container_name: {proxy_service_name}\n"
            compose_content += f"    environment:\n"
            compose_content += f"      - start_url=https://{ip}\n"
            compose_content += f"    ports:\n"
            compose_content += f"      - {current_port}:8080\n"
            
            # Add to Services YAML
            services_yaml += f"    - IPMI {safe_ip} (Console):\n"
            services_yaml += f"        icon: mdi-console\n"
            services_yaml += f"        href: http://localhost:{current_port}\n"
            services_yaml += f"        description: \"KVM Console (Proxy)\"\n"
            
            current_port += 1

    # Write files
    with open(COMPOSE_FILE, "w") as f:
        f.write(compose_content)
    print(f"Generated {COMPOSE_FILE}")
    
    with open(SERVICES_FILE, "w") as f:
        f.write(services_yaml)
    print(f"Generated {SERVICES_FILE}")
    
    # --- Settings YAML ---
    settings_yaml = """--- 
title: \"Tiny Dashboard\" 
layout:
  Proxmox Cluster:
    style: row
    columns: 3
  Management Plane:
    style: row
    columns: 4
"""
    with open(SETTINGS_FILE, "w") as f:
        f.write(settings_yaml)
    print(f"Generated {SETTINGS_FILE}")
    
    # --- Touch other files ---
    with open(WIDGETS_FILE, "a"): 
        os.utime(WIDGETS_FILE, None)
    with open(BOOKMARKS_FILE, "a"):
        os.utime(BOOKMARKS_FILE, None)

def main():
    parser = argparse.ArgumentParser(description="Generate Tiny Dashboard configuration.")
    parser.add_argument("cidr", help="Network CIDR to scan (e.g., 192.168.1.0/24)")
    parser.add_argument("--image", default="ipmi-kvm-docker:latest", help="Docker image to use for KVM proxies")
    args = parser.parse_args()

    hosts = scan_network(args.cidr)
    
    if not hosts:
        print("No IPMI or Proxmox hosts found.")
        # We might still want to generate an empty dashboard or one with manual entries? 
        # For now, let's proceed to generate (it will just be empty groups).
    
    generate_configs(hosts, args.image)
    print("Dashboard generation complete.")
if __name__ == "__main__":
    main()
