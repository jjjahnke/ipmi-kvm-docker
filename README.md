# IPMI-KVM-Docker & Tiny Dashboard

![Docker Image Size (tag)](https://img.shields.io/docker/image-size/solarkennedy/ipmi-kvm-docker/latest)
![Docker Pulls](https://img.shields.io/docker/pulls/solarkennedy/ipmi-kvm-docker)

This is a **customized fork** of [solarkennedy/ipmi-kvm-docker](https://github.com/solarkennedy/ipmi-kvm-docker). It extends the original project with **Tiny Dashboard**, a tool to automatically discover IPMI and Proxmox hosts on your network and generate a unified management dashboard.

## Features

*   **Original IPMI KVM Proxy:** Runs a containerized browser with Java support to access legacy IPMI KVM consoles via HTML5 (noVNC).
*   **Tiny Dashboard:**
    *   **Auto-Discovery:** Scans a network CIDR for IPMI (UDP 623) and Proxmox (TCP 8006) interfaces.
    *   **Unified UI:** Generates a [Homepage](https://github.com/gethomepage/homepage) dashboard linking to all discovered services.
    *   **Proxy Integration:** Automatically spins up local proxy containers for legacy IPMI hosts, allowing one-click access to their KVM consoles from modern browsers.
    *   **Apple Silicon Support:** Includes build fixes for running the legacy Ubuntu 14.04-based containers on ARM64 (M1/M2/M3) Macs via Rosetta 2.

## Quick Start: Tiny Dashboard

This is the primary way to use this fork.

### Prerequisites
*   Docker & Docker Compose
*   Python 3
*   `nmap` (requires root/sudo privileges for UDP scanning)

### Usage

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd ipmi-kvm-docker
    ```

2.  **Generate and Run:**
    Run the `make dashboard` command with your target network CIDR. This will build the local docker image, scan the network, generate the config, and start the dashboard.

    ```bash
    # Example
    make dashboard NETWORK_CIDR=192.168.1.0/24
    ```

3.  **Access:**
    *   **Dashboard:** Open [http://localhost:3000](http://localhost:3000)
    *   **Proxmox:** Click the tiles to open Proxmox directly.
    *   **IPMI Direct:** Click the "server" icon to open the BMC web interface directly.
    *   **IPMI Console:** Click the "console" icon to open the containerized KVM proxy.

## Manual / Original Usage

You can still use the container manually as a standalone KVM proxy.

### Build the Image
```bash
make build
```
*Note: On Apple Silicon, this automatically targets `linux/amd64`.*

### Run a Single Container
```bash
docker run -d -p 8080:8080 -e START_URL=https://<target-ipmi-ip> ipmi-kvm-docker:latest
```
Access via [http://localhost:8080](http://localhost:8080).

## Configuration

*   **Resolution:** Default is `1024x768x24`. Override with `-e RES=1600x900x24`.
*   **Images:** Mount a local folder to `/root/images` to access ISOs within the container.
    ```bash
    docker run -v /your/iso/folder:/root/images ...
    ```

## Original Project Credits
Based on work by [solarkennedy](https://github.com/solarkennedy).
*   Xvfb - X11 in a virtual framebuffer
*   x11vnc - VNC server
*   noVNC - HTML5 VNC viewer
*   Fluxbox - Window manager
*   Chromium/Firefox - Browser
*   Java-plugin - Legacy Java support for KVMs
