import sys

from .types import Run


def generate_run_command(run: Run, args: list[str]) -> list[str]:
    command = [
        # 'echo',
        sys.executable,
        '-m',
        'automate',
    ]

    if run.stages is not None:
        command.append(",".join(run.stages))

    if run.config is not None:
        command.append(f'--config-file={run.config}')

    if run.include_official_mods:
        command.append('--include-official-mods')

    if run.mods is not None:
        command.append(f'--mods={",".join(run.mods)}')

    if run.maps is not None:
        command.append(f'--maps={",".join(run.maps)}')

    if args:
        command.extend(args)

    return command
