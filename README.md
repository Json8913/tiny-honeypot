# Tiny HTTP Honeypot

This is a small, low-interaction decoy web portal for a home lab or a network you are authorised to monitor. It serves a believable fictional operations sign-in page and records basic connection metadata so you can review which paths were touched.

**Author:** Jason Santos Ritchie

It is an early learning project. It is not a production honeypot platform, a firewall, or a way to secure a server.

## What it records

Each request produces one JSON line with the time, source IP and port, HTTP method, path, and submitted body size.

The honeypot deliberately does not read or save form contents. It does not record usernames, passwords, cookies, authorization headers, query-string values, or browser details. The sign-in form is only a decoy; a submission returns a generic failure.

## Desktop control panel

Run:

    python3 gui.py

The window starts and stops the local server and displays request metadata as events arrive. It defaults to `127.0.0.1:8080`. Keep the portal title fictional and use an authorised, isolated test network.

## Run it

Requires Python 3.10 or newer. No third-party packages are needed.

    python3 honeypot.py

Open http://127.0.0.1:8080 in your browser. Stop the server with Ctrl+C.

To listen on a lab interface, first choose an approved host address and restrict access with your network firewall. Then run:

    python3 honeypot.py --host 192.168.1.40 --port 8080

The default is loopback so the service is not exposed to the local network by accident. Do not forward the port from a router or expose it to the internet.

## Keep it safe

- Use it only on systems and networks you own or are authorised to monitor.
- Keep the title fictional; do not impersonate a real company or service without its approval.
- Do not enter real account credentials into a decoy. The code does not store submitted values.
- Treat the event log as private operational data because it includes source addresses.
- Review and delete local logs according to your organisation's retention rules.

## Current limits

The service speaks basic HTTP only. It does not emulate a real application, validate logins, provide TLS, persist logs to a file, or detect whether activity is malicious. A request is an observation to investigate, not proof of an attack.

## Checks

Run the included tests with:

    python3 -m unittest -v

