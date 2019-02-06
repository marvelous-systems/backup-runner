# backup-runner
Container to backup kubernetes deployments

# Development

## Python Environment

```bash
$ virtualenv .venv --python=python3
$ . .venv/bin/activate
$ pip install -r requirements.txt
```

## Running locally using kubeconfig

```bash
$ docker run -v ~/.kube/config:/kube/config backup-runner
```

# Building

```bash
$ docker build -t backup-runner .
```

# Usage