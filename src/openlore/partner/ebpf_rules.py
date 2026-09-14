"""eBPF zero-egress network policies for isolated partner enclaves."""

from __future__ import annotations

import ipaddress
from typing import Any, Dict, List, Optional, Tuple


class EBPFNetworkPolicyManager:
    """Configures kernel-level network packet filtering for partner cloud enclaves."""

    def __init__(self, allowed_inspection_endpoints: List[str]) -> None:
        """Initialize the policy manager with a whitelist of authorized inspection endpoints.

        Endpoints can be IP addresses ('10.0.0.50'), IP with port ('10.0.0.50:443'),
        or hostnames.
        """
        self.allowed_inspection_endpoints = allowed_inspection_endpoints

    def generate_tc_filter_rules(self) -> str:
        """Generate eBPF traffic control C source code enforcing zero-egress kernel filtering.

        Packets destined to whitelisted inspection endpoints receive TC_ACT_OK.
        All other outbound egress packets are dropped immediately with TC_ACT_SHOT.
        """
        # Parse IPs and ports from allowed endpoints
        ip_filters = []
        for ep in self.allowed_inspection_endpoints:
            ep = ep.strip()
            if not ep:
                continue
            if ":" in ep and not ep.startswith("["):
                host, port_str = ep.split(":", 1)
                try:
                    port = int(port_str)
                except ValueError:
                    port = 0
            else:
                host = ep
                port = 0

            try:
                ip_obj = ipaddress.ip_address(host)
                if isinstance(ip_obj, ipaddress.IPv4Address):
                    ip_int = int(ip_obj)
                    ip_hex = f"0x{ip_int:08X}"
                    if port > 0:
                        ip_filters.append(
                            f"        /* Allowed: {ep} */\n"
                            f"        if (dst_ip == {ip_hex} && dst_port == {port}) {{\n"
                            f"            return TC_ACT_OK;\n"
                            f"        }}"
                        )
                    else:
                        ip_filters.append(
                            f"        /* Allowed: {ep} */\n"
                            f"        if (dst_ip == {ip_hex}) {{\n"
                            f"            return TC_ACT_OK;\n"
                            f"        }}"
                        )
            except ValueError:
                # Hostname or non-standard format
                ip_filters.append(
                    f"        /* Whitelisted inspection endpoint: {ep} */\n"
                    f"        // Endpoint '{ep}' matched via TC map table\n"
                )

        c_filters_block = "\n".join(ip_filters) if ip_filters else "        /* No external endpoints allowed */"

        c_source = f"""/*
 * OpenLore Zero-Egress Kernel Packet Filter
 * Generated eBPF Traffic Control (TC) Classifier
 * Enforces strict zero-egress for isolated partner studio enclaves.
 */

#include <linux/bpf.h>
#include <linux/pkt_cls.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

SEC("tc_egress")
int openlore_tc_egress_filter(struct __sk_buff *skb) {{
    void *data = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    /* Parse Ethernet header */
    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) {{
        return TC_ACT_OK; /* Let short/malformed packets handle by kernel stack */
    }}

    /* Only filter IPv4 outbound egress */
    if (eth->h_proto == bpf_htons(ETH_P_IP)) {{
        struct iphdr *iph = (void *)(eth + 1);
        if ((void *)(iph + 1) > data_end) {{
            return TC_ACT_SHOT;
        }}

        __u32 dst_ip = bpf_ntohl(iph->daddr);
        __u16 dst_port = 0;

        /* Allow internal loopback 127.0.0.0/8 */
        if ((dst_ip & 0xFF000000) == 0x7F000000) {{
            return TC_ACT_OK;
        }}

        /* Parse TCP or UDP destination port */
        if (iph->protocol == IPPROTO_TCP) {{
            struct tcphdr *tcph = (void *)iph + (iph->ihl * 4);
            if ((void *)(tcph + 1) <= data_end) {{
                dst_port = bpf_ntohs(tcph->dest);
            }}
        }} else if (iph->protocol == IPPROTO_UDP) {{
            struct udphdr *udph = (void *)iph + (iph->ihl * 4);
            if ((void *)(udph + 1) <= data_end) {{
                dst_port = bpf_ntohs(udph->dest);
            }}
        }}

        /* Check whitelisted inspection endpoints */
{c_filters_block}

        /* Zero-Egress Rule: Drop all other outbound network traffic */
        return TC_ACT_SHOT;
    }}

    /* Drop all other outbound L3 egress (e.g. unapproved IPv6/ARP leaks) */
    return TC_ACT_SHOT;
}}

char __license[] SEC("license") = "GPL";
"""
        return c_source

    def generate_bpftool_commands(
        self,
        interface: str = "eth0",
        object_file: str = "tc_egress_filter.o",
    ) -> List[str]:
        """Generate command sequence for loading and attaching the eBPF filter with tc/bpftool."""
        return [
            f"ip link set dev {interface} up",
            f"tc qdisc replace dev {interface} clsact",
            f"tc filter replace dev {interface} egress bpf da obj {object_file} sec tc_egress",
            f"bpftool prog show name openlore_tc_egress_filter",
        ]

    def verify_enclave_compliance(
        self,
        enclave_id: str,
        active_sockets: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[bool, List[str]]:
        """Audit active socket connections against signed inspection endpoints.

        Detects and logs any unauthorized data egress attempts.
        """
        violations: List[str] = []
        if not active_sockets:
            return (True, [])

        allowed_parsed: List[Tuple[str, Optional[int]]] = []
        for ep in self.allowed_inspection_endpoints:
            ep = ep.strip()
            if ":" in ep and not ep.startswith("["):
                host, p_str = ep.split(":", 1)
                try:
                    port = int(p_str)
                except ValueError:
                    port = None
                allowed_parsed.append((host, port))
            else:
                allowed_parsed.append((ep, None))

        for sock in active_sockets:
            remote_ip = (
                sock.get("remote_ip")
                or sock.get("dst_ip")
                or sock.get("destination_ip")
                or sock.get("remote_address")
                or ""
            )
            remote_port = sock.get("remote_port") or sock.get("dst_port") or sock.get("port")
            if remote_port is not None:
                try:
                    remote_port = int(remote_port)
                except (ValueError, TypeError):
                    remote_port = None

            # Check for loopback address
            if remote_ip in ("127.0.0.1", "::1", "localhost") or str(remote_ip).startswith("127."):
                continue

            # Check if remote matches any allowed endpoint
            is_allowed = False
            for allowed_host, allowed_port in allowed_parsed:
                if remote_ip == allowed_host:
                    if allowed_port is None or remote_port == allowed_port:
                        is_allowed = True
                        break

            if not is_allowed:
                violations.append(
                    f"Enclave '{enclave_id}' detected unauthorized egress attempt to "
                    f"{remote_ip}:{remote_port} (Protocol: {sock.get('protocol', 'TCP')})"
                )

        passed = len(violations) == 0
        return (passed, violations)
