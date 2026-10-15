#!/usr/bin/env python3
"""Ubuntu-only worker: fixed commands, validated domains, no Docker socket in the API."""
import argparse
import base64
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request


DOMAIN = re.compile(r"(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def checked_domain(domain):
    if not DOMAIN.fullmatch(domain):
        raise ValueError("Domínio público inválido")
    return domain


def verify_dns(domain, allowed_ips):
    checked_domain(domain)
    actual = {ipaddress.ip_address(record[4][0]) for record in socket.getaddrinfo(domain, 443, type=socket.SOCK_STREAM)}
    expected = {ipaddress.ip_address(ip.strip()) for ip in allowed_ips.split(",") if ip.strip()}
    if not actual or not actual.issubset(expected):
        raise ValueError("DNS não corresponde ao servidor")


def execute(command, *, timeout=120):
    # Never shell=True and never echo stderr: it can include API/database credentials.
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                            errors="surrogateescape", timeout=timeout)
    if result.returncode:
        raise RuntimeError(f"Comando falhou: {command[0]}")
    return result.stdout


class Worker:
    def __init__(self, api_dir, allowed_ips, email, compose_files):
        self.api_dir = Path(api_dir).resolve()
        self.allowed_ips, self.email = allowed_ips, email
        self.compose = ["docker", "compose", "--project-directory", str(self.api_dir)]
        for filename in compose_files.split(","):
            path = (self.api_dir / filename.strip()).resolve()
            if path.parent != self.api_dir or not path.is_file():
                raise ValueError("Arquivo Compose inválido")
            self.compose += ["-f", str(path)]
        self.runtime = self.api_dir / "tenant-runtime"
        self.nginx_root = Path("/etc/nginx")
        self.runtime.mkdir(mode=0o700, exist_ok=True)

    def api(self, action, job_id=None, step=None):
        command = self.compose + ["exec", "-T", "api", "python", "-m", "scripts.tenant_provision", action]
        if job_id:
            command.append(job_id)
        if step:
            command += ["--step", step]
        return json.loads(execute(command, timeout=1800))

    def configure_nginx(self, job):
        domain = checked_domain(job["domain"])
        job_id = job["id"]
        if not re.fullmatch(r"[a-f0-9]{32}", job_id):
            raise ValueError("Identificador inválido")
        name = f"tenant-auto-{job_id}.conf"
        available = self.nginx_root / "sites-available" / name
        enabled = self.nginx_root / "sites-enabled" / name
        marker = f"# tenant-provision:{job_id}"
        for path in (self.nginx_root / "sites-enabled").iterdir():
            if path == enabled or not path.is_file():
                continue
            # Existing virtual hosts may contain comments saved with legacy encodings.
            content = path.read_text(encoding="utf-8", errors="surrogateescape")
            for directive in re.findall(r"server_name\s+([^;]+);", content):
                if domain in directive.split():
                    raise ValueError("Domínio já configurado em outro virtual host")
        if available.exists():
            if marker not in available.read_text(encoding="utf-8", errors="surrogateescape"):
                raise ValueError("Virtual host não pertence a esta criação")
        else:
            content = f"""{marker}
server {{
    listen 80;
    listen [::]:80;
    server_name {domain};
    location = /.well-known/tenant-provision {{
        default_type text/plain;
        return 200 '{job_id}';
    }}
    location / {{
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }}
}}
"""
            # Exclusive creation refuses accidental overwrite; retries retain Certbot changes.
            with available.open("x", encoding="utf-8") as output:
                output.write(content)
        if enabled.is_symlink():
            if enabled.resolve() != available.resolve():
                raise ValueError("Link do Nginx aponta para outro arquivo")
        elif enabled.exists():
            raise ValueError("Destino do Nginx já existe")
        else:
            enabled.symlink_to(available)
        try:
            execute(["nginx", "-t"])
        except Exception:
            # Remove only our link. Nginx keeps its last valid active configuration.
            if enabled.is_symlink() and enabled.resolve() == available.resolve():
                enabled.unlink()
            raise
        execute(["systemctl", "reload", "nginx"])

    def certificate(self, job):
        execute(["certbot", "--nginx", "--non-interactive", "--agree-tos", "--email", self.email,
                 "--redirect", "--keep-until-expiring", "--cert-name", f"tenant-{job['id']}",
                 "-d", checked_domain(job["domain"])], timeout=600)

    def verify(self, job):
        verify_dns(job["domain"], self.allowed_ips)
        base = f"https://{job['domain']}"
        # No redirects to an unverified destination, including during certificate checks.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(NoRedirect())
        with opener.open(base + "/.well-known/tenant-provision", timeout=30) as response:
            if response.read(128).decode().strip() != job["id"]:
                raise ValueError("Domínio não atende a nova empresa")
        with opener.open(base + "/", timeout=30) as response:
            if "<html" not in response.read(65536).decode().lower():
                raise ValueError("Frontend não está disponível")
        self.api("activate", job["id"])
        request = urllib.request.Request(base + "/api/v1/auth/login",
            data=urllib.parse.urlencode({"username": "Admin", "password": "Admin"}).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"})
        with opener.open(request, timeout=30) as response:
            result = json.loads(response.read(65536))
            if not result.get("access_token"):
                raise ValueError("Login inicial não foi validado")
            # Confirm the shared API routed this login to the intended business database.
            encoded_claims = result["access_token"].split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(encoded_claims + "=" * (-len(encoded_claims) % 4)))
            if claims.get("tenant_id") != job["tenant_id"]:
                raise ValueError("Login foi direcionado a outra empresa")

    def process(self, job):
        step = "dns"
        try:
            for step, action in (
                ("dns", lambda: verify_dns(job["domain"], self.allowed_ips)),
                ("database", lambda: self.api("prepare", job["id"])),
                ("nginx", lambda: self.configure_nginx(job)),
                ("certificate", lambda: self.certificate(job)),
                ("verification", lambda: self.verify(job)),
            ):
                self.api("step", job["id"], step)
                print(f"Tenant {job['tenant_id']}: {step}", flush=True)
                action()
            self.api("finish", job["id"])
        except Exception as exc:
            print(f"Tenant {job['tenant_id']}: falha em {step} ({type(exc).__name__})", flush=True)
            self.api("fail", job["id"], step)

    def serve(self):
        import fcntl
        with (self.runtime / "worker.lock").open("w") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            stop = threading.Event()
            def heartbeat():
                while not stop.is_set():
                    (self.runtime / "worker-heartbeat").touch()
                    stop.wait(15)
            thread = threading.Thread(target=heartbeat, daemon=True)
            thread.start()
            try:
                while True:
                    try:
                        job = self.api("next")
                        if job:
                            self.process(job)
                        else:
                            time.sleep(5)
                    except Exception as exc:
                        print(f"Provisionador aguardando API ({type(exc).__name__})", flush=True)
                        time.sleep(10)
            finally:
                stop.set()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    ips = os.environ["TENANT_PUBLIC_IPS"]
    email = os.environ["TENANT_CERTBOT_EMAIL"]
    if not ips.strip() or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        raise SystemExit("Configure IPs públicos e email do certificado")
    for ip in ips.split(","):
        ipaddress.ip_address(ip.strip())
    worker = Worker(os.environ.get("TENANT_API_DIR", "/var/www/apicontratos/ContratosN/API"), ips, email,
                    os.environ.get("TENANT_COMPOSE_FILES", "docker-compose.yml,docker-compose.tenant.yml"))
    if args.check:
        execute(["nginx", "-t"])
        execute(["certbot", "--version"])
        execute(worker.compose + ["config", "--quiet"])
        print("Configuração do provisionador conferida.")
    else:
        worker.serve()


if __name__ == "__main__":
    main()
