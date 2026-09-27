#!/usr/bin/env python3
"""Submit a frozen native Provider operation through Alicit approval."""

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


class ProviderHTTPFailure(ValueError):
    """Only a numeric HTTP status is safe to expose from a Provider error."""

    def __init__(self, status):
        self.status = status if isinstance(status, int) and 100 <= status <= 599 else 502
        super().__init__(
            f"Provider operation returned HTTP {self.status}; inspect outcome before retrying"
        )


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def validate(request, mounts):
    if not isinstance(request, dict) or set(request) - {
        "mount",
        "path",
        "method",
        "body",
        "env",
        "output",
    }:
        raise ValueError("invalid proposal fields")
    mount, path = request.get("mount"), request.get("path")
    for value in [mount, path]:
        if (
            not isinstance(value, str)
            or len(value) > 512
            or not re.fullmatch(r"[A-Za-z0-9_@.-]+(?:/[A-Za-z0-9_@.-]+)*", value)
            or any(p in (".", "..") for p in value.split("/"))
        ):
            raise ValueError("use a canonical mount and relative endpoint")
    if mount not in mounts or mount.split("/")[0] in (
        "sys",
        "auth",
        "identity",
        "cubbyhole",
    ):
        raise ValueError("select a discovered secrets backend")
    if path.split("/")[0] == "config":
        raise ValueError("Provider seed configuration requires separate bootstrap")
    if request.get("method") not in ("GET", "POST", "PUT", "DELETE", "LIST"):
        raise ValueError("unsupported method")
    if request.get("body") is not None and (
        request["method"] not in ("POST", "PUT")
        or not isinstance(request["body"], dict)
    ):
        raise ValueError("only POST and PUT accept a JSON object body")
    if request.get("output", "status") not in ("status", "keys") or (
        request.get("output") == "keys" and request["method"] != "LIST"
    ):
        raise ValueError("key-name output requires LIST")
    fields = request.get("env", {})
    if not isinstance(fields, dict) or len(fields) > 32:
        raise ValueError("invalid environment mappings")
    for name, selector in fields.items():
        if (
            not re.fullmatch(r"[A-Z][A-Z0-9_]*", name)
            or name.startswith(("BAO_", "DYLD_"))
            or name
            in ("PATH", "HOME", "SHELL", "ENV", "BASH_ENV", "PYTHONPATH", "LD_PRELOAD")
        ):
            raise ValueError("invalid credential environment name")
        if (
            not isinstance(selector, list)
            or not 1 <= len(selector) <= 8
            or any(not isinstance(k, str) or not k or len(k) > 128 for k in selector)
        ):
            raise ValueError("invalid response field selector")
    if len(json.dumps(request).encode()) > 65536:
        raise ValueError("proposal exceeds 64 KiB")
    return request


def execute(request, command, environ):
    validate(request, [request.get("mount")])
    address, token = environ.get("BAO_ADDR", ""), environ.get("BAO_TOKEN", "")
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]+", address) or not token:
        raise ValueError("execute inside an Alicit Invocation")
    if bool(request.get("env")) != bool(command):
        raise ValueError(
            "credential mappings require a consumer command, and vice versa"
        )
    body = request.get("body")
    operation = urllib.request.Request(
        address + "/v1/" + request["mount"] + "/" + request["path"],
        method=request["method"],
        data=None
        if body is None
        else json.dumps(body, sort_keys=True, separators=(",", ":")).encode(),
        headers={"X-Vault-Token": token, "Content-Type": "application/json"},
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(operation, timeout=1200) as response:
            raw = response.read(1048577)
    except urllib.error.HTTPError as error:
        status = error.code
        error.close()
        raise ProviderHTTPFailure(status) from None
    if len(raw) > 1048576:
        raise ValueError(
            "Provider response exceeds limit; inspect outcome before retrying"
        )
    payload = json.loads(raw) if raw else {}
    if command:
        env = {
            k: v
            for k, v in environ.items()
            if k not in ("BAO_ADDR", "BAO_TOKEN", "GH_TOKEN", "GITHUB_TOKEN")
            and not k.startswith("AWS_")
        }
        for name, selector in request["env"].items():
            value = payload
            for key in selector:
                value = value.get(key) if isinstance(value, dict) else None
            if not isinstance(value, str) or not value or "\x00" in value:
                raise ValueError("response lacks a requested credential field")
            env[name] = value
        if any(k.startswith("AWS_") for k in request["env"]):
            env.update(
                AWS_EC2_METADATA_DISABLED="true",
                AWS_CONFIG_FILE=os.devnull,
                AWS_SHARED_CREDENTIALS_FILE=os.devnull,
            )
        return subprocess.call(command, env=env)
    result = {
        "status": "completed",
        "mount": request["mount"],
        "path": request["path"],
        "method": request["method"],
    }
    if request.get("output") == "keys":
        keys = payload.get("data", {}).get("keys")
        if not isinstance(keys, list) or any(not isinstance(k, str) for k in keys):
            raise ValueError("Provider returned no key-name inventory")
        result["keys"] = keys
    print(json.dumps(result))
    return 0


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_execute":
        if len(sys.argv) < 3 or len(sys.argv[2]) > 87384:
            raise ValueError("missing or oversized frozen proposal")
        frozen = base64.b64decode(sys.argv[2], validate=True)
        if len(frozen) > 65536:
            raise ValueError("proposal exceeds 64 KiB")
        return execute(
            json.loads(frozen), sys.argv[3:], dict(os.environ)
        )
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("proposal", type=Path)
    parser.add_argument("--justification", required=True)
    parser.add_argument("--alicit", default="alicit")
    own, command = sys.argv[1:], []
    if "--" in own:
        split = own.index("--")
        command = own[split + 1 :]
        own = own[:split]
    args = parser.parse_args(own)
    raw = args.proposal.read_bytes()
    if len(raw) > 65536:
        raise ValueError("proposal exceeds 64 KiB")
    catalog = json.loads(subprocess.check_output([args.alicit, "discover", "--json"]))
    if not any(p["name"] == "operator-proposals" for p in catalog["profiles"]):
        raise ValueError("operator-proposals is not deployed")
    request = validate(json.loads(raw), [p["path"] for p in catalog["providers"]])
    if bool(request.get("env")) != bool(command):
        raise ValueError(
            "credential mappings require a consumer command, and vice versa"
        )
    frozen = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(frozen).hexdigest()
    justification = f"{args.justification} | {request['method']} {request['mount']}/{request['path']} | proposal SHA256 {digest}"
    if not 16 <= len(justification.encode()) <= 500:
        raise ValueError(
            "shorten justification or endpoint to fit the 500-byte approval limit"
        )
    print("Submitting proposal SHA256 " + digest, flush=True)
    code = subprocess.run(
        [
            args.alicit,
            "run",
            "--profile",
            "operator-proposals",
            "--justification",
            justification,
            "--",
            sys.executable,
            str(Path(__file__).resolve()),
            "_execute",
            base64.b64encode(frozen).decode("ascii"),
            *command,
        ],
        check=False,
    ).returncode
    # Keep the diagnostic that the Invocation already printed. Alicit writes the
    # Mint ID and any Provider HTTP status to this same stderr stream, so this
    # handler adds the proposal identity and the lookup instead of a replacement
    # message. It never repeats or interprets Provider response text.
    if code != 0:
        print(
            f"Proposal SHA256 {digest} did not complete; alicit exited {code}. "
            "Read the Mint ID above and run `alicit status <mint-id>` to see its "
            "retained outcome. Do not retry before you read that outcome.",
            file=sys.stderr,
            flush=True,
        )
    return code


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ProviderHTTPFailure as error:
        sys.exit(str(error))
    except (ValueError, OSError, subprocess.CalledProcessError):
        sys.exit(
            "Proposal failed; inspect its Alicit outcome and non-secret proposal file before retrying."
        )
