# Tiny HTTP Honeypot

A small, low-interaction web decoy for a home lab or a network you are authorised to monitor. It serves a fictional operations portal and records basic request metadata so you can see which paths were touched.

**Author:** Jason Santos Ritchie

This is a learning project. It is not a production honeypot platform, firewall, or way to secure a server.

## How it works

- `honeypot.py` serves a fictional page and a generic response to form submissions.
- `gui.py` starts and stops the service and displays request events.
- The default bind address is `127.0.0.1`, keeping the demo on this computer.
- Each event records time, source IP and port, method, path, and submitted body size.
- Form contents are never read or saved. Query strings are removed from logged paths.

## Run the graphical demo

Requires Python 3.10 or newer. No third-party packages are needed.

```sh
python3 gui.py
```

Keep the bind address at `127.0.0.1`, then select **Start local decoy**. If port 8080 is already in use, choose another local port, such as 18080. See [docs/DEMO.md](docs/DEMO.md) for the request walkthrough and expected results.

## Run a live check

This script starts the service locally, sends a page request and a form submission using clearly fake values, verifies HTTP 200 and 401, checks that the fake values are absent from the event log, and then cleans up the temporary log:

```sh
bash scripts/live_demo.sh
```

Choose another port if 18080 is occupied:

```sh
PORT=18081 bash scripts/live_demo.sh
```

## Live demo evidence

See [docs/DEMO.md](docs/DEMO.md) for visual evidence from a fresh loopback run: the fictional portal response, the generic 401 response, and the event records emitted by the server. The images are rendered from the actual HTTP response bodies and event lines observed during that run; they are not raw desktop screenshots.

## Run the unit tests

```sh
python3 -m unittest -v
```

## Data handling

The server does not record usernames, passwords, cookies, authorization headers, query-string values, or browser details. A form submission returns a generic 401 response. The event log contains source addresses, so treat it as private operational data and apply your usual retention rules.

## Safety and limits

- Use it only on systems and networks you own or are authorised to monitor.
- Keep the portal title fictional; do not imitate a real company without approval.
- Use synthetic form values only. Never enter a real account password.
- Do not forward the port from a router or expose the service to the public internet.
- The service uses basic HTTP, has no TLS, does not persist logs, and cannot determine whether a request is malicious. A request is an observation to investigate, not proof of an attack.
