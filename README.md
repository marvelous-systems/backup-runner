# backup-runner
Container to backup kubernetes deployments

# Development

## Python Environment

```bash
$ virtualenv .venv --python=python3
$ . .venv/bin/activate
$ pip install -r requirements.txt
```

## Adding a new Dependency

While virtualenv is activated, install the new dependency using pip.
Freeze the list of requirements and compare it to the previous revision, since
dependencies might be downgraded by `pip freeze`.

```bash
$ pip install some-dependency
$ pip freeze > app/requirements.txt.new && diff app/requirements.txt*
```

# Building

```bash
$ docker build -t backup-runner .
```

# Usage

## Running locally using a kubeconfig file

```bash
$ docker run -v ~/.kube/config:/kube/config backup-runner
usage: main.py [-h] [-b BACKUP [BACKUP ...] | -r RESTORE [RESTORE ...]]
               namespace deployment store
```
