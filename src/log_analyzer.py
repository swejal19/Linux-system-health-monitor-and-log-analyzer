import re
from collections import Counter
from pathlib import Path
from diagnostics import diagnose_entries

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG_PATH = PROJECT_ROOT / "logs" / "sample_system.log"

SEVERITY_LEVELS = ("INFO", "WARNING", "ERROR", "CRITICAL")

LOG_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) "
    r"(?P<severity>INFO|WARNING|ERROR|CRITICAL) "
    r"(?P<message>.+)$"
)

def parse_log_line(line, line_number):
    """
    Parse one log line into structured fields.

    Return None when the line does not match the expected format.
    """
    match = LOG_PATTERN.match(line.strip())

    if not match:
        return None

    return {
        "line_number": line_number,
        "timestamp": match.group("timestamp"),
        "severity": match.group("severity"),
        "message": match.group("message"),
    }

def analyze_log_file(log_path=DEFAULT_LOG_PATH):
    """
    Read a project-local log file and return structured analysis results.
    """
    log_path = Path(log_path)

    result = {
        "log_file": str(log_path),
        "total_lines": 0,
        "parsed_lines": 0,
        "malformed_lines": [],
        "severity_counts": {
            severity: 0 for severity in SEVERITY_LEVELS
        },
        "entries": [],
    }

    try:
        with log_path.open("r", encoding="utf-8") as log_file:
            for line_number, line in enumerate(log_file, start=1):
                result["total_lines"] += 1

                if not line.strip():
                    continue

                parsed_entry = parse_log_line(line, line_number)

                if parsed_entry is None:
                    result["malformed_lines"].append(
                        {
                            "line_number": line_number,
                            "content": line.rstrip("\n"),
                        }
                    )
                    continue

                result["parsed_lines"] += 1
                result["entries"].append(parsed_entry)

                severity = parsed_entry["severity"]
                result["severity_counts"][severity] += 1

    except FileNotFoundError:
        result["error"] = f"Log file not found: {log_path}"
        return result

    except PermissionError:
        result["error"] = f"Permission denied while reading: {log_path}"
        return result

    except OSError as error:
        result["error"] = f"Unable to read log file: {error}"
        return result

    result["recurring_errors"] = detect_recurring_errors(result["entries"])
    result["diagnoses"] = diagnose_entries(result["entries"])
    result["error"] = None
    return result

def detect_recurring_errors(entries, minimum_occurrences=2):
    """
    Detect repeated ERROR and CRITICAL messages.

    Messages are normalized to lowercase for comparison so that trivial
    capitalization differences do not create separate error groups.
    """
    error_messages = []

    for entry in entries:
        if entry["severity"] in ("ERROR", "CRITICAL"):
            normalized_message = entry["message"].strip().lower()
            error_messages.append(normalized_message)

    message_counts = Counter(error_messages)

    recurring_errors = []

    for message, count in message_counts.items():
        if count >= minimum_occurrences:
            recurring_errors.append(
                {
                    "message": message,
                    "occurrences": count,
                }
            )

    recurring_errors.sort(
        key=lambda item: item["occurrences"],
        reverse=True,
    )

    return recurring_errors

def display_log_analysis(result):
    """Display a human-readable summary of log analysis results."""
    print("=" * 60)
    print("                    LOG ANALYSIS REPORT")
    print("=" * 60)
    print(f"Log File: {result['log_file']}")

    if result.get("error"):
        print(f"Status: FAILED")
        print(f"Error: {result['error']}")
        print("=" * 60)
        return

    print(f"Total Lines: {result['total_lines']}")
    print(f"Successfully Parsed: {result['parsed_lines']}")
    print(f"Malformed Lines: {len(result['malformed_lines'])}")

    print("\nSEVERITY COUNTS")
    for severity in SEVERITY_LEVELS:
        print(f"{severity}: {result['severity_counts'][severity]}")

    recurring_errors = result.get("recurring_errors", [])

    print("\nRECURRING ERRORS")

    if recurring_errors:
        for error in recurring_errors:
            print(
                f"- {error['message']} "
                f"(occurrences: {error['occurrences']})"
            )
    else:
        print("No recurring errors detected.")

    if result["malformed_lines"]:
        print("\nMALFORMED LINES")
        for malformed in result["malformed_lines"]:
            print(
                f"Line {malformed['line_number']}: "
                f"{malformed['content']}"
            )

    print("=" * 60)

    diagnoses = result.get("diagnoses", [])

    print("\nPROBABLE ROOT-CAUSE DIAGNOSTICS")

    if diagnoses:
        for diagnosis in diagnoses:
            print(f"\nRule: {diagnosis['rule']}")
            print(f"Matched Events: {diagnosis['match_count']}")
            print(f"Probable Cause: {diagnosis['probable_cause']}")

            print("Evidence:")
            for evidence in diagnosis["evidence"]:
                print(
                    f"  - Line {evidence['line_number']} | "
                    f"{evidence['timestamp']} | "
                    f"{evidence['severity']} | "
                    f"{evidence['message']}"
                )

            print("Recommended Checks:")
            for check in diagnosis["recommended_checks"]:
                print(f"  - {check}")
    else:
        print("No diagnostic rules matched.")


def main():
    result = analyze_log_file()
    display_log_analysis(result)


if __name__ == "__main__":
    main()
