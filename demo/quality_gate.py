"""A small synthetic release policy with explicit failure reasons."""

REQUIRED_CHECKS = ("tests", "lint", "security")


def check_release(results):
    """Return issues for required checks that are missing or did not pass."""
    issues = []
    for check in REQUIRED_CHECKS:
        if check not in results:
            issues.append(f"{check}: missing")
        elif results[check] != "pass":
            issues.append(f"{check}: {results[check]}")
    return issues


def main():
    sample = {"tests": "pass", "lint": "pass", "security": "pass"}
    issues = check_release(sample)
    print("Release blocked: " + ", ".join(issues) if issues else "Release gate passed")
    return bool(issues)


if __name__ == "__main__":
    raise SystemExit(main())
