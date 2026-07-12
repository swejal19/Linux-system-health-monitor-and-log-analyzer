DIAGNOSTIC_RULES = [
    {
        "name": "Database Connection Failure",
        "keywords": (
            "database connection refused",
            "database connection failed",
            "unable to connect to database",
        ),
        "probable_cause": (
            "The database service may be unavailable, the configured host or "
            "port may be incorrect, or network connectivity may be failing."
        ),
        "recommended_checks": [
            "Verify that the database service is running.",
            "Check the configured database hostname and port.",
            "Test network connectivity to the database endpoint.",
            "Review database service logs for additional evidence.",
        ],
    },
    {
        "name": "DNS Resolution Failure",
        "keywords": (
            "dns resolution failed",
            "temporary failure in name resolution",
            "name or service not known",
        ),
        "probable_cause": (
            "The hostname may be invalid, the DNS resolver may be unavailable "
            "or misconfigured, or a temporary name-resolution failure occurred."
        ),
        "recommended_checks": [
            "Verify that the hostname is correct.",
            "Check the system DNS resolver configuration.",
            "Test hostname resolution with getent hosts.",
            "Check whether the configured DNS service is reachable.",
        ],
    },
    {
        "name": "Permission Failure",
        "keywords": (
            "permission denied",
            "access denied",
        ),
        "probable_cause": (
            "The current user or process may not have sufficient permissions, "
            "or file ownership and permission settings may not match the "
            "application's requirements."
        ),
        "recommended_checks": [
            "Inspect file or directory permissions.",
            "Check file ownership.",
            "Verify which user is running the process.",
            "Avoid changing permissions broadly without understanding the cause.",
        ],
    },
    {
        "name": "Disk Space Exhaustion",
        "keywords": (
            "disk space exhausted",
            "no space left on device",
            "disk full",
        ),
        "probable_cause": (
            "The target filesystem may have insufficient free space, or "
            "application data and logs may have consumed available capacity."
        ),
        "recommended_checks": [
            "Check filesystem usage with df -h.",
            "Identify large files or directories before taking action.",
            "Review log-retention and cleanup policies.",
            "Do not delete files automatically without operator review.",
        ],
    },
]

def diagnose_entries(entries):
    """
    Apply transparent keyword-based diagnostic rules to ERROR and CRITICAL
    log entries and return probable causes with supporting evidence.
    """
    diagnoses = []

    for rule in DIAGNOSTIC_RULES:
        matched_entries = []

        for entry in entries:
            if entry["severity"] not in ("ERROR", "CRITICAL"):
                continue

            normalized_message = entry["message"].lower()

            if any(
                keyword in normalized_message
                for keyword in rule["keywords"]
            ):
                matched_entries.append(entry)

        if matched_entries:
            diagnoses.append(
                {
                    "rule": rule["name"],
                    "probable_cause": rule["probable_cause"],
                    "recommended_checks": rule["recommended_checks"],
                    "match_count": len(matched_entries),
                    "evidence": [
                        {
                            "line_number": entry["line_number"],
                            "timestamp": entry["timestamp"],
                            "severity": entry["severity"],
                            "message": entry["message"],
                        }
                        for entry in matched_entries
                    ],
                }
            )

    return diagnoses
