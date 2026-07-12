import json
import platform
import socket
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil
BYTES_PER_GB = 1024 ** 3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.json"
REPORTS_DIR = PROJECT_ROOT / "reports"

DEFAULT_CONFIG = {
    "thresholds": {
        "cpu_warning": 80,
        "memory_warning": 80,
        "disk_warning": 85,
    },
    "network": {
        "hostname": "example.com",
        "port": 443,
        "timeout_seconds": 3,
    },
    "monitoring": {
        "top_processes": 5,
    },
}

def bytes_to_gb(value_in_bytes):
    """Convert bytes to gibibytes and round to two decimal places."""
    return round(value_in_bytes / BYTES_PER_GB, 2)

def load_config():
    """
    Load configuration from config.json.

    Invalid or missing values fall back to safe defaults.
    """
    config = {
        "thresholds": DEFAULT_CONFIG["thresholds"].copy(),
        "network": DEFAULT_CONFIG["network"].copy(),
        "monitoring": DEFAULT_CONFIG["monitoring"].copy(),
    }

    try:
        with CONFIG_PATH.open("r", encoding="utf-8") as config_file:
            user_config = json.load(config_file)

    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return config

    if not isinstance(user_config, dict):
        return config

    thresholds = user_config.get("thresholds", {})
    if isinstance(thresholds, dict):
        for key in ("cpu_warning", "memory_warning", "disk_warning"):
            value = thresholds.get(key)

            if isinstance(value, (int, float)) and not isinstance(value, bool):
                if 0 <= value <= 100:
                    config["thresholds"][key] = value

    network = user_config.get("network", {})
    if isinstance(network, dict):
        hostname = network.get("hostname")
        port = network.get("port")
        timeout = network.get("timeout_seconds")

        if isinstance(hostname, str) and hostname.strip():
            config["network"]["hostname"] = hostname.strip()

        if isinstance(port, int) and not isinstance(port, bool):
            if 1 <= port <= 65535:
                config["network"]["port"] = port

        if isinstance(timeout, (int, float)) and not isinstance(timeout, bool):
            if 0.1 <= timeout <= 30:
                config["network"]["timeout_seconds"] = timeout

    monitoring = user_config.get("monitoring", {})
    if isinstance(monitoring, dict):
        top_processes = monitoring.get("top_processes")

        if isinstance(top_processes, int) and not isinstance(top_processes, bool):
            if 1 <= top_processes <= 20:
                config["monitoring"]["top_processes"] = top_processes

    return config

def get_platform_info():
    """Return basic information about the Linux environment."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "platform": platform.platform(),
    }


def get_cpu_metrics():
    """Return CPU core counts and current utilization percentage."""
    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "usage_percent": psutil.cpu_percent(interval=1),
    }


def get_memory_metrics():
    """Return current virtual memory statistics."""
    memory = psutil.virtual_memory()

    return {
        "total_gb": bytes_to_gb(memory.total),
        "used_gb": bytes_to_gb(memory.used),
        "available_gb": bytes_to_gb(memory.available),
        "usage_percent": memory.percent,
    }


def get_disk_metrics():
    """Return disk usage statistics for the root filesystem."""
    disk = psutil.disk_usage("/")

    return {
        "total_gb": bytes_to_gb(disk.total),
        "used_gb": bytes_to_gb(disk.used),
        "available_gb": bytes_to_gb(disk.free),
        "usage_percent": disk.percent,
    }


def get_system_uptime():
    """Return system uptime as a human-readable duration."""
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time

    return str(timedelta(seconds=int(uptime.total_seconds())))

def get_top_processes(limit=5):
    """
    Return the top running processes sorted by memory usage.

    Process information is read-only. Processes that disappear or cannot
    be accessed are skipped safely.
    """
    processes = []

    for process in psutil.process_iter(
        attrs=["pid", "name", "cpu_percent", "memory_percent"]
    ):
        try:
            process_info = process.info

            processes.append(
                {
                    "pid": process_info["pid"],
                    "name": process_info["name"] or "Unknown",
                    "cpu_percent": round(process_info["cpu_percent"] or 0.0, 2),
                    "memory_percent": round(
                        process_info["memory_percent"] or 0.0, 2
                    ),
                }
            )

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda item: item["memory_percent"], reverse=True)

    return processes[:limit]

def check_network_connectivity(
    hostname="example.com",
    port=443,
    timeout_seconds=3
):
    """
    Safely check DNS resolution and outbound TCP connectivity
    for one explicitly configured hostname and port.
    """
    result = {
        "hostname": hostname,
        "port": port,
        "resolved_ip": None,
        "dns_status": "FAIL",
        "tcp_status": "NOT CHECKED",
        "connection_time_ms": None,
        "error": None,
    }

    try:
        resolved_ip = socket.gethostbyname(hostname)
        result["resolved_ip"] = resolved_ip
        result["dns_status"] = "PASS"

    except socket.gaierror as error:
        result["error"] = f"DNS resolution failed: {error}"
        return result

    try:
        start_time = time.perf_counter()

        with socket.create_connection(
            (hostname, port),
            timeout=timeout_seconds
        ):
            elapsed_seconds = time.perf_counter() - start_time

        result["tcp_status"] = "PASS"
        result["connection_time_ms"] = round(elapsed_seconds * 1000, 2)

    except (socket.timeout, TimeoutError) as error:
        result["tcp_status"] = "FAIL"
        result["error"] = f"Connection timed out: {error}"

    except OSError as error:
        result["tcp_status"] = "FAIL"
        result["error"] = f"TCP connection failed: {error}"

    return result

def evaluate_health(cpu, memory, disk, thresholds):
    """
    Compare current resource usage against configured warning thresholds.
    """
    violations = []

    resource_statuses = {
        "cpu": "HEALTHY",
        "memory": "HEALTHY",
        "disk": "HEALTHY",
    }

    if cpu["usage_percent"] >= thresholds["cpu_warning"]:
        resource_statuses["cpu"] = "WARNING"
        violations.append(
            f"CPU utilization ({cpu['usage_percent']}%) exceeded "
            f"configured threshold ({thresholds['cpu_warning']}%)."
        )

    if memory["usage_percent"] >= thresholds["memory_warning"]:
        resource_statuses["memory"] = "WARNING"
        violations.append(
            f"Memory utilization ({memory['usage_percent']}%) exceeded "
            f"configured threshold ({thresholds['memory_warning']}%)."
        )

    if disk["usage_percent"] >= thresholds["disk_warning"]:
        resource_statuses["disk"] = "WARNING"
        violations.append(
            f"Disk utilization ({disk['usage_percent']}%) exceeded "
            f"configured threshold ({thresholds['disk_warning']}%)."
        )

    overall_status = "WARNING" if violations else "HEALTHY"

    return resource_statuses, violations, overall_status

def build_health_report():
    """
    Collect system metrics, evaluate health, and return one structured report.
    """
    config = load_config()

    platform_info = get_platform_info()
    cpu = get_cpu_metrics()
    memory = get_memory_metrics()
    disk = get_disk_metrics()
    uptime = get_system_uptime()

    top_processes = get_top_processes(
        limit=config["monitoring"]["top_processes"]
    )

    network = check_network_connectivity(
        hostname=config["network"]["hostname"],
        port=config["network"]["port"],
        timeout_seconds=config["network"]["timeout_seconds"],
    )

    resource_statuses, violations, overall_status = evaluate_health(
        cpu=cpu,
        memory=memory,
        disk=disk,
        thresholds=config["thresholds"],
    )

    cpu["status"] = resource_statuses["cpu"]
    memory["status"] = resource_statuses["memory"]
    disk["status"] = resource_statuses["disk"]

    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "overall_status": overall_status,
        "threshold_violations": violations,
        "platform": platform_info,
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
        "uptime": uptime,
        "top_processes": top_processes,
        "network": network,
        "configuration": {
            "thresholds": config["thresholds"],
            "monitoring": config["monitoring"],
        },
    }

def save_json_report(report):
    """
    Save a health report as a timestamped JSON file inside reports/.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    filename_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = REPORTS_DIR / f"health_report_{filename_timestamp}.json"

    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=4)

    return report_path

def display_health_report(report):
    config = load_config()

    """Collect system metrics and display a terminal health report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    timestamp = report["timestamp"]
    platform_info = report["platform"]
    cpu = report["cpu"]
    memory = report["memory"]
    disk = report["disk"]
    uptime = report["uptime"]
    top_processes = report["top_processes"]
    network = report["network"]
    violations = report["threshold_violations"]
    overall_status = report["overall_status"]

    config = load_config()

    resource_statuses, violations, overall_status = evaluate_health(
       cpu=cpu,
       memory=memory,
       disk=disk,
       thresholds=config["thresholds"],
    )

    print("=" * 60)
    print("              LINUX SYSTEM HEALTH REPORT")
    print("=" * 60)
    print(f"Timestamp: {timestamp}")

    print("\nPLATFORM")
    print(f"System: {platform_info['system']}")
    print(f"Release: {platform_info['release']}")
    print(f"Machine: {platform_info['machine']}")
    print(f"Platform: {platform_info['platform']}")

    print("\nCPU")
    print(f"Physical Cores: {cpu['physical_cores']}")
    print(f"Logical Cores: {cpu['logical_cores']}")
    print(f"Usage: {cpu['usage_percent']}%")
    print(f"Status: {cpu['status']}")

    print("\nMEMORY")
    print(f"Total: {memory['total_gb']} GB")
    print(f"Used: {memory['used_gb']} GB")
    print(f"Available: {memory['available_gb']} GB")
    print(f"Usage: {memory['usage_percent']}%")
    print(f"Status: {memory['status']}")

    print("\nDISK")
    print(f"Total: {disk['total_gb']} GB")
    print(f"Used: {disk['used_gb']} GB")
    print(f"Available: {disk['available_gb']} GB")
    print(f"Usage: {disk['usage_percent']}%")
    print(f"Status: {disk['status']}")

    print("\nUPTIME")
    print(f"Uptime: {uptime}")
    print(
         f"\nTOP {config['monitoring']['top_processes']} "
         "PROCESSES BY MEMORY USAGE"
    )
    print(f"{'PID':<10} {'NAME':<30} {'CPU %':>10} {'MEMORY %':>12}")
    print("-" * 65)

    if top_processes:
         for process in top_processes:
             print(
                f"{process['pid']:<10} "
                f"{process['name'][:30]:<30} "
                f"{process['cpu_percent']:>10.2f} "
                f"{process['memory_percent']:>12.2f}"
             )
    else:
         print("No accessible process information available.")

    print("\nNETWORK CONNECTIVITY")
    print(f"Target: {network['hostname']}:{network['port']}")
    print(f"DNS Resolution: {network['dns_status']}")

    if network["resolved_ip"]:
        print(f"Resolved IP: {network['resolved_ip']}")

    print(f"TCP Connectivity: {network['tcp_status']}")

    if network["connection_time_ms"] is not None:
        print(f"Connection Time: {network['connection_time_ms']} ms")

    if network["error"]:
        print(f"Error: {network['error']}")

    print("\nOVERALL SYSTEM HEALTH")
    print(f"Overall Status: {overall_status}")

    if violations:
        print("Threshold Violations:")
        for violation in violations:
            print(f"- {violation}")
    else:
        print("Reason: No configured resource thresholds were exceeded.")

    print("=" * 60)


def main():
    report = build_health_report()
    display_health_report(report)

    report_path = save_json_report(report)
    print(f"\nJSON report saved to: {report_path}")

if __name__ == "__main__":
    main()
