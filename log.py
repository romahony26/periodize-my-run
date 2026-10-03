"""Logging for every task the tool performs, with secrets scrubbed.

Log file: state/logs/periodize.log (rotated at 1 MB, five kept). Passwords
are never passed to the logger; as a second line of defence every record is
run through a filter that blanks anything that looks like a credential.
"""
import logging
import logging.handlers
import os
import re
import sys

log = logging.getLogger("periodize")

_PATTERNS = [
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]+"), "[redacted-key]"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]+"), "Bearer [redacted]"),
    (re.compile(r"(?i)(pass(?:word|wd)?|secret|token|cookie|mfa[_ ]?code)(\"?\s*[:=]\s*\"?)[^\s\",}]+"), r"\1\2[redacted]"),
    (re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}"), "[redacted-jwt]"),
    (re.compile(r"[A-Za-z0-9._%+\-]{1,64}@[A-Za-z0-9\-]{1,63}(?:\.[A-Za-z0-9\-]{1,63}){1,6}"), "[email]"),
    (re.compile(r"(?i)(refresh_token|client_secret|access_token|api[_-]?key)(\"?\s*[:=]\s*\"?)[^\s\",}]+"), r"\1\2[redacted]"),
    (re.compile(r"GOCSPX-[A-Za-z0-9_\-]+|1//[A-Za-z0-9_\-]{8,}"), "[redacted]"),
    (re.compile(r"\b[A-Za-z0-9_\-]{40,}\b"), "[redacted]"),
]


MAX_LEN = 8000      # nothing the app logs is longer; a cap keeps the filter fast whatever it is fed


_CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f\u2028\u2029\u202a-\u202e]")


def scrub(text):
    text = text if len(text) <= MAX_LEN else text[:MAX_LEN] + " [cut]"
    for pat, rep in _PATTERNS:
        text = pat.sub(rep, text)
    return text


class Redact(logging.Filter):
    def filter(self, record):
        # a line break inside a logged value (a race name, say) could forge a log entry, so breaks and other control characters are neutralised
        record.msg, record.args = _CONTROL.sub("?", scrub(record.getMessage()).replace("\n", "\\n")), None
        if record.exc_info:
            record.exc_text = scrub(logging.Formatter().formatException(record.exc_info))
            record.exc_info = None
        return True


def setup(state_dir, verbose=False):
    if log.handlers:
        return log
    d = os.path.join(state_dir, "logs")
    os.makedirs(d, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    os.chmod(d, 0o700)  # nosemgrep: insecure-file-permissions - owner-only on a directory is the strictest setting
    path = os.path.join(d, "periodize.log")
    if not os.path.exists(path):
        os.close(os.open(path, os.O_WRONLY | os.O_CREAT, 0o600))
    os.chmod(path, 0o600)       # the log names races and health values: this user only
    fh = logging.handlers.RotatingFileHandler(path, maxBytes=1_000_000, backupCount=5)
    sh = logging.StreamHandler(sys.stdout)
    for h in (fh, sh):
        h.setFormatter(fmt)
        h.addFilter(Redact())
        log.addHandler(h)
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    sh.setLevel(logging.INFO)
    # the Garmin library's own warnings go to the same file, also scrubbed
    lib = logging.getLogger("garminconnect")
    lib.setLevel(logging.WARNING)
    lib.addHandler(fh)
    return log
