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


class ProposalFailure(ValueError):
    """A fixed, credential-safe reason for a proposal failure."""


class ProviderHTTPFailure(ProposalFailure):
    """Only a numeric HTTP status is safe to expose from a Provider error."""

    def __init__(self, status):
        self.status = status if isinstance(status, int) and 100 <= status <= 599 else 502
        super().__init__(f"Provider operation returned HTTP {self.status}")


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
        raise ProposalFailure("proposal must be a JSON object with supported fields")
    mount, path = request.get("mount"), request.get("path")
    for value in [mount, path]:
        if (
            not isinstance(value, str)
            or len(value) > 512
            or not re.fullmatch(r"[A-Za-z0-9_@.-]+(?:/[A-Za-z0-9_@.-]+)*", value)
            or any(p in (".", "..") for p in value.split("/"))
        ):
            raise ProposalFailure("use a canonical mount and relative endpoint")
    if mount not in mounts or mount.split("/")[0] in (
        "sys",
        "auth",
        "identity",
        "cubbyhole",
    ):
        raise ProposalFailure("select a discovered secrets backend")
    if path.split("/")[0] == "config":
        raise ProposalFailure("Provider seed configuration requires separate bootstrap")
    if request.get("method") not in ("GET", "POST", "PUT", "DELETE", "LIST"):
        raise ProposalFailure("unsupported method")
    if request.get("body") is not None and (
        request["method"] not in ("POST", "PUT")
        or not isinstance(request["body"], dict)
    ):
        raise ProposalFailure("only POST and PUT accept a JSON object body")
    if request.get("output", "status") not in ("status", "keys") or (
        request.get("output") == "keys" and request["method"] != "LIST"
    ):
        raise ProposalFailure("key-name output requires LIST")
    fields = request.get("env", {})
    if not isinstance(fields, dict) or len(fields) > 32:
        raise ProposalFailure("invalid environment mappings")
    for name, selector in fields.items():
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Z][A-Z0-9_]*", name)
            or name.startswith(("BAO_", "DYLD_"))
            or name
            in ("PATH", "HOME", "SHELL", "ENV", "BASH_ENV", "PYTHONPATH", "LD_PRELOAD")
        ):
            raise ProposalFailure("invalid credential environment name")
        if (
            not isinstance(selector, list)
            or not 1 <= len(selector) <= 8
            or any(not isinstance(k, str) or not k or len(k) > 128 for k in selector)
        ):
            raise ProposalFailure("invalid response field selector")
    if len(json.dumps(request).encode()) > 65536:
        raise ProposalFailure("proposal exceeds 64 KiB")
    return request


def execute(request, command, environ):
    validate(request, [request.get("mount")] if isinstance(request, dict) else [])
    address, token = environ.get("BAO_ADDR", ""), environ.get("BAO_TOKEN", "")
    if not re.fullmatch(r"http://127\.0\.0\.1:[0-9]+", address) or not token:
        raise ProposalFailure("execute inside an Alicit Invocation")
    if bool(request.get("env")) != bool(command):
        raise ProposalFailure(
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
        raise ProposalFailure("Provider response exceeds limit")
    try:
        payload = json.loads(raw) if raw else {}
    except (ValueError, UnicodeError):
        raise ProposalFailure("Provider returned an invalid JSON response") from None
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
                raise ProposalFailure("response lacks a requested credential field")
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
        data = payload.get("data") if isinstance(payload, dict) else None
        keys = data.get("keys") if isinstance(data, dict) else None
        if not isinstance(keys, list) or any(not isinstance(k, str) for k in keys):
            raise ProposalFailure("Provider returned no key-name inventory")
        result["keys"] = keys
    print(json.dumps(result))
    return 0



def read_catalog(alicit):
    """Return the alicit configuration catalog from the installed CLI.

    A four-verb CLI answers `doctor --catalog`. An installed CLI from before
    ADR-0120 has no doctor verb, so fall back to its discover verb: a script
    must work beside the installed CLI as well as the next one (ADR-0124).
    """
    current = subprocess.run(
        [alicit, "doctor", "--catalog", "--json"], capture_output=True, text=True
    )
    if current.returncode == 0:
        return json.loads(current.stdout)
    legacy = [alicit, "discover", "--json"]  # ADR-0124 N-1: installed CLI before ADR-0120
    return json.loads(subprocess.check_output(legacy, text=True, stderr=subprocess.PIPE))


def catalog_mounts(catalog):
    if (
        not isinstance(catalog, dict)
        or not isinstance(catalog.get("profiles"), list)
        or not isinstance(catalog.get("providers"), list)
        or any(
            not isinstance(p, dict) or not isinstance(p.get("name"), str)
            for p in catalog["profiles"]
        )
        or any(
            not isinstance(p, dict) or not isinstance(p.get("path"), str)
            for p in catalog["providers"]
        )
    ):
        raise ProposalFailure("Alicit catalog must list profiles and Provider mounts")
    if not any(p["name"] == "operator-proposals" for p in catalog["profiles"]):
        raise ProposalFailure("operator-proposals is not deployed")
    return [p["path"] for p in catalog["providers"]]


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "_execute":
        if len(sys.argv) < 3 or len(sys.argv[2]) > 87384:
            raise ProposalFailure("missing or oversized frozen proposal")
        frozen = base64.b64decode(sys.argv[2], validate=True)
        if len(frozen) > 65536:
            raise ProposalFailure("proposal exceeds 64 KiB")
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
        raise ProposalFailure("proposal exceeds 64 KiB")
    try:
        request = json.loads(raw)
    except (ValueError, UnicodeError):
        raise ProposalFailure("proposal must contain valid JSON") from None
    # Check the declaration before even reading the catalog. Only a discovered
    # mount can proceed, but malformed local input needs no CLI call at all.
    request = validate(request, [request.get("mount")] if isinstance(request, dict) else [])
    if bool(request.get("env")) != bool(command):
        raise ProposalFailure(
            "credential mappings require a consumer command, and vice versa"
        )
    frozen = json.dumps(request, sort_keys=True, separators=(",", ":")).encode()
    digest = hashlib.sha256(frozen).hexdigest()
    justification = f"{args.justification} | {request['method']} {request['mount']}/{request['path']} | proposal SHA256 {digest}"
    if not 16 <= len(justification.encode()) <= 500:
        raise ProposalFailure(
            "expanded justification must be 16–500 bytes including the method/path and SHA256 suffix; shorten the justification or endpoint"
        )
    try:
        mounts = catalog_mounts(read_catalog(args.alicit))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        if isinstance(error, ProposalFailure):
            raise
        raise ProposalFailure("could not read a valid Alicit catalog") from None
    validate(request, mounts)
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
    # Request ID and any Provider HTTP status to this same stderr stream, so this
    # handler adds the proposal identity and the lookup instead of a replacement
    # message. It never repeats or interprets Provider response text.
    if code != 0:
        print(
            f"Invocation stage for proposal SHA256 {digest} did not complete; alicit exited {code}. "
            "If Alicit printed a Request ID above, run `alicit doctor --request <request-id>` "
            "to see its retained outcome; otherwise Request creation is unconfirmed. "
            "Inspect the outcome before retrying.",
            file=sys.stderr,
            flush=True,
        )
    return code


if __name__ == "__main__":
    native = sys.argv[1:2] == ["_execute"]
    try:
        sys.exit(main())
    except ProposalFailure as error:
        if native:
            sys.exit(f"Native Provider stage failed: {error}. Inspect the Request outcome before retrying.")
        sys.exit(f"Local preflight failed: {error}. No Alicit Request was created.")
    except (ValueError, OSError, subprocess.CalledProcessError):
        if native:
            sys.exit("Native Provider stage failed; inspect the Request outcome before retrying.")
        sys.exit("Local preflight failed: could not prepare or start the proposal Invocation. No Alicit Request was created.")
