import tomllib
import tomli_w
import subprocess
import pyright

from dataclasses import dataclass
from typing import Any
from collections.abc import Callable

@dataclass
class Stage:
    name: str
    function: Callable[[], bool]

def stage_str(event: str, stage_name: str) -> str:
    return f'[{event}] -----< {stage_name} >-----'

def stage_start(stage: Stage) -> str:
    return stage_str('START', stage.name)

def stage_error(stage: Stage) -> str:
    return stage_str('ERROR', stage.name)

@dataclass
class Version:
    major: int
    minor: int
    patch: int

def version_to_str(version: Version) -> str:
    return f'{version.major}.{version.minor}.{version.patch}'

def parse_version(s: str) -> Version:
    major, minor, patch = map(int, s.split('.'))
    return Version(major, minor, patch)

def increment_minor(version: Version) -> Version:
    return Version(version.major, version.minor + 1, version.patch)

def increment_major(version: Version) -> Version:
    return Version(version.major+1, version.minor, version.patch)

check_git_status_stage = Stage('check git status clean', lambda: (subprocess.run('test -z "$(git status --porcelain)"', shell=True).returncode == 0))

type_check_stage = Stage('type check', lambda: (pyright.main(['./src']) == 0))

def update_version(update: Callable[[Version], Version]) -> None:
    pyproject_toml = "pyproject.toml"
    with open(pyproject_toml, "rb") as f:
        project_config = tomllib.load(f)
    
    version = parse_version(project_config['project']['version'])
    new_version_str = version_to_str(update(version))
    project_config['project']['version'] = new_version_str

    with open(pyproject_toml, "wb") as f:
        tomli_w.dump(project_config, f)

    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", new_version_str], check=True)
    subprocess.run(['git', 'tag', new_version_str], check=True)

def bump_major() -> bool:
    update_version(increment_major)
    return True

def bump_minor() -> bool:
    update_version(increment_minor)
    return True

def set_initial_version() -> bool:
    update_version(lambda _: Version(1, 0, 0))
    return True

def clean_and_build() -> bool:
    subprocess.run(['rm', '-rf', 'dist'], check=True)
    return subprocess.run(['uv', 'build']).returncode == 0

uv_build_stage = Stage('uv build', clean_and_build)

def uv_publish_stage(pypi_token: str) -> Stage:
    return Stage(
        'uv publish',
        lambda: subprocess.run(['uv', 'publish', '--token', pypi_token]).returncode == 0
    )

def run_stages(stages: list[Stage]) -> None:
    if len(stages) == 0:
        return
    stage = stages[0]
    print(stage_start(stage))
    if stage.function():
        run_stages(stages[1:])
    else:
        print(stage_error(stage))

def release_version(pypi_token: str, version_change_description: str, change_version: Callable[[], bool]) -> None:
    run_stages([
        check_git_status_stage,
        type_check_stage,
        Stage(version_change_description, change_version),
        uv_build_stage,
        uv_publish_stage(pypi_token)
    ])

def minor(pypi_token: str) -> None:
    release_version(pypi_token, 'bump minor version', bump_minor)

def major(pypi_token: str) -> None:
    release_version(pypi_token, 'bump major version', bump_major)

def initial_publish(pypi_token: str) -> None:
    release_version(pypi_token, 'set initial version', set_initial_version)
