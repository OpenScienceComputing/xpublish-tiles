#!/usr/bin/env python3
"""Deploy FluxTilesStack with automatic Cloudflare DNS validation."""

import os
import subprocess
import sys
import time

import boto3
import requests

DOMAIN = "tiles.openscicomp.io"
CLOUDFLARE_ZONE_ID = "87c01c20b112503cd755cbdfaaf593b4"
AWS_REGION = "us-west-2"
POLL_INTERVAL = 10


def get_cf_token():
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        print("Error: CLOUDFLARE_API_TOKEN env var not set")
        sys.exit(1)
    return token


def cf_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def find_cert(acm):
    paginator = acm.get_paginator("list_certificates")
    for page in paginator.paginate(CertificateStatuses=["PENDING_VALIDATION", "ISSUED"]):
        for cert in page["CertificateSummaryList"]:
            if cert["DomainName"] == DOMAIN:
                return cert["CertificateArn"]
    return None


def get_validation_record(acm, cert_arn):
    detail = acm.describe_certificate(CertificateArn=cert_arn)
    for opt in detail["Certificate"]["DomainValidationOptions"]:
        if "ResourceRecord" in opt:
            rr = opt["ResourceRecord"]
            return rr["Name"], rr["Value"]
    return None, None


def cf_record_exists(token, name):
    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records"
    resp = requests.get(url, headers=cf_headers(token), params={"name": name})
    data = resp.json()
    return data["success"] and len(data["result"]) > 0


def create_cf_cname(token, name, value):
    url = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records"
    payload = {"type": "CNAME", "name": name, "content": value, "ttl": 60, "proxied": False}
    resp = requests.post(url, headers=cf_headers(token), json=payload)
    data = resp.json()
    if data["success"]:
        print(f"Created CNAME: {name} -> {value}")
    elif any(e.get("code") == 81053 for e in data.get("errors", [])):
        print(f"CNAME already exists: {name}")
    else:
        print(f"Failed to create CNAME: {data['errors']}")
        sys.exit(1)


def main():
    token = get_cf_token()
    acm = boto3.client("acm", region_name=AWS_REGION)

    print("Starting cdk deploy...")
    deploy_dir = os.path.dirname(os.path.abspath(__file__))
    cdk_proc = subprocess.Popen(
        ["cdk", "deploy", "--require-approval=never"],
        cwd=deploy_dir,
    )

    print(f"Polling ACM for certificate for {DOMAIN}...")
    cert_arn = None
    while cert_arn is None:
        cert_arn = find_cert(acm)
        if cert_arn is None:
            time.sleep(POLL_INTERVAL)
    print(f"Found cert: {cert_arn}")

    detail = acm.describe_certificate(CertificateArn=cert_arn)
    if detail["Certificate"]["Status"] == "ISSUED":
        print("Certificate already issued, skipping DNS validation.")
    else:
        print("Waiting for DNS validation record...")
        name, value = None, None
        while name is None:
            name, value = get_validation_record(acm, cert_arn)
            if name is None:
                time.sleep(POLL_INTERVAL)

        if cf_record_exists(token, name):
            print(f"CNAME already exists: {name}")
        else:
            create_cf_cname(token, name, value)

        print("Waiting for certificate to be issued...")
        while True:
            detail = acm.describe_certificate(CertificateArn=cert_arn)
            status = detail["Certificate"]["Status"]
            if status == "ISSUED":
                print("Certificate issued.")
                break
            elif status == "FAILED":
                print("Certificate validation failed.")
                cdk_proc.terminate()
                sys.exit(1)
            time.sleep(POLL_INTERVAL)

    print("Waiting for cdk deploy to complete...")
    cdk_proc.wait()
    if cdk_proc.returncode != 0:
        print(f"cdk deploy failed with exit code {cdk_proc.returncode}")
        sys.exit(cdk_proc.returncode)

    print("Deployment complete!")


if __name__ == "__main__":
    main()
