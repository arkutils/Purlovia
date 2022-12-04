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

    if run.appid is not None:
        command.append(f'--appid={run.appid}')

    if run.include_official_mods:
        command.append('--include-official-mods')

    if run.mods is not None:
        command.append(f'--mods={",".join(run.mods)}')

    if run.maps is not None:
        command.append(f'--maps={",".join(run.maps)}')

    if run.output_path:
        command.append(f'--output-path={run.output_path}')

    if args:
        command.extend(args)

    return command
