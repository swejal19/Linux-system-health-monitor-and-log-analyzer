# Linux System Health Monitor & Log Analyzer

A Python-based Linux monitoring and diagnostic tool that collects live system metrics, evaluates configurable health thresholds, generates timestamped JSON reports, analyzes structured logs, detects recurring failures, and provides transparent rule-based probable root-cause diagnostics.

The project also includes Bash automation and Docker containerization for repeatable execution and reproducible runtime environments.

## Features

### Real-Time System Monitoring

Collects live metrics from the current Linux execution environment:

- CPU usage and physical/logical core count
- Memory usage and availability
- Disk utilization
- System uptime
- Top processes by memory usage
- Platform and kernel information

### Configurable Health Thresholds

Resource thresholds are defined in `config.json`.

The monitor evaluates:

- CPU utilization
- Memory utilization
- Disk utilization

Each resource receives a `HEALTHY` or `WARNING` status based on the configured threshold.

The overall health status currently reflects CPU, memory, and disk threshold evaluation.

### Network Connectivity Checks

Performs:

- DNS resolution
- TCP connectivity testing
- Connection-time measurement

Network failures are handled gracefully and reported without crashing the complete monitoring workflow.

### Timestamped JSON Reports

Every monitor execution generates a structured JSON report containing:

- Timestamp
- Overall health status
- Threshold violations
- Platform information
- CPU, memory, and disk metrics
- System uptime
- Top processes
- Network-check results
- Relevant configuration values

Generated reports are stored in the `reports/` directory and excluded from Git by default.

### Log Parsing and Severity Detection

Analyzes a controlled project-local sample log with the expected format:

```text
YYYY-MM-DD HH:MM:SS SEVERITY Message
