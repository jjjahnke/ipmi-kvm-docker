# Tiny Dashboard Specification

## Overview
Tiny Dashboard is a lightweight, Docker-based monitoring and management dashboard designed for home labs and small clusters. It aggregates access to Proxmox nodes and IPMI management interfaces into a single, easy-to-use UI using [homepage](https://github.com/gethomepage/homepage).

## Current Architecture
- **Orchestration**: `docker-compose` generated via Python script (`generate_dashboard.py`).
- **Frontend**: `ghcr.io/gethomepage/homepage`.
- **Backend/Middleware**: 
    - Custom `ipmi-kvm-docker` containers acting as HTML5-to-Java/KVM bridges for legacy IPMI devices.
- **Utilities**: 
    - `generate_dashboard.py`: Python script that handles network scanning (nmap), configuration generation, and Docker Compose file creation.

## Functional Requirements

### 1. Dashboard Generation
- **Primary Interface**: `Makefile`
- **Goal**: Consolidate all operations (build, run, generate) into a single entry point. The user runs `make dashboard NETWORK_CIDR=...` to perform the entire workflow.
- **Fault Tolerance**:
    - **Cleanup**: The process explicitly cleans up existing containers before starting new ones.
    - **Idempotency**: Re-running the generation safely overwrites existing configs.
- **Workflow**:
    1.  **Build**: Ensure the local `ipmi-kvm-docker` image is built (multi-arch support via `--platform linux/amd64` for Apple Silicon).
    2.  **Generate**: Execute `generate_dashboard.py` to scan the network and produce the configuration files.
    3.  **Launch**: Start the new dashboard stack using the generated `docker-compose.yml`.

### 2. IPMI/KVM Proxying
- **Problem**: Modern browsers do not support the Java applets required by older BMC/IPMI interfaces.
- **Solution**: Run `ipmi-kvm-docker` containers that bridge the KVM session to HTML5.
- **Target Hosts**: SuperMicro, ASUS, etc.
- **Configuration**: 
    - Uses `start_url` environment variable to launch the browser directly to the target management URL.
    - `IPMI_USER` and `IPMI_PASS` automation is bypassed in favor of direct browser interaction.

### 3. Dynamic Discovery & Dashboard Generation
- **Input**: Target network range (e.g., CIDR `192.168.1.0/24`).
- **Discovery Process**:
    - **IPMI**: Scan for UDP port 623.
    - **Proxmox**: Scan for TCP port 8006.
- **Auto-Configuration**:
    - **For IPMI Hosts (Port 623)**:
        - **Management Interface (Direct)**: Link to `https://<device_ip>` using `mdi-server` icon.
        - **KVM Console (Proxy)**: Link to `http://localhost:<proxy_port>` using `mdi-console` icon.
        - Generates a proxy container service in `docker-compose.yml`.
    - **For Proxmox Hosts (Port 8006)**:
        - Link to `https://<device_ip>:8006` using `proxmox` icon.
        - No proxy container required.

### 4. Custom Container Build
- **Requirement**: `Makefile` handles building the custom `ipmi-kvm-docker` image.
- **Platform Support**: Explicitly targets `linux/amd64` to support legacy software dependencies (Ubuntu 14.04), using Rosetta 2 emulation on ARM64 hosts.

## Deprecated / Removed
- `find_impi.sh`: Replaced by Python `nmap` integration.
- `tiny-dashboard.sh`: Replaced by `generate_dashboard.py` and `Makefile`.
- **Ping Widget**: Currently disabled due to configuration/compatibility issues with the Homepage container.

## Roadmap
- [ ] **Externalize Credentials**: Move any potential sensitive data to `.env`.
- [ ] **Re-enable Ping Widget**: Investigate and fix the "Missing Widget Type" error.
- [ ] **Grouping**: Logical grouping of nodes (e.g., by Cluster, by Rack).
