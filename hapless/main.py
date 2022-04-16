import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from hapless import config
from hapless.hap import Hap

"""
paused
running
finished
* finished(failed) non-zero rc
* finished(success) zero rc
💀
"""
console = Console()


class Hapless(object):
    def __init__(self):
        tmp_dir = Path(tempfile.gettempdir())
        self._hapless_dir = tmp_dir / "hapless"
        if not self._hapless_dir.exists():
            self._hapless_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def stats(haps: List[Hap]):
        if not haps:
            console.print("🔴 No haps are currently running")
            return

        table = Table(show_header=True, header_style="bold magenta", box=box.HEAVY_EDGE)
        table.add_column("#", style="dim", width=2)
        table.add_column("Name")
        table.add_column("PID")
        table.add_column("Status")
        table.add_column("RC")
        table.add_column("Runtime", justify="right")

        for hap in haps:
            table.add_row(
                f"{hap.hid}",
                hap.name,
                f"{hap.pid}",
                hap.status,
                f"{hap.rc}" if hap.rc is not None else "",
                hap.runtime,
            )

        console.print(table)

    @staticmethod
    def show(hap: Hap):
        table = Table(show_header=False, show_footer=False, box=box.SIMPLE)

        status_text = Text()
        table.add_row("Status:", status_text)

        table.add_row("PID:", f"{hap.pid}")

        cmd_text = Text(f"{hap.cmd}", style=f"{config.COLOR_ACCENT} bold")
        table.add_row("Command:", cmd_text)

        table.add_row("Runtime:", f"{hap.runtime}")

        panel = Panel(
            table,
            expand=False,
            title=f"Hap {config.ICON_HAP}{hap.hid}",
            subtitle=hap.name,
        )
        console.print(panel)

    @property
    def dir(self) -> Path:
        return self._hapless_dir

    def _get_hap_dirs(self) -> List[str]:
        hap_dirs = filter(str.isdigit, os.listdir(self._hapless_dir))
        return sorted(hap_dirs)

    def _get_hap_names_map(self) -> Dict[str, str]:
        names = {}
        for dir in self._get_hap_dirs():
            filename = self._hapless_dir / dir / "name"
            if filename.exists():
                with open(filename) as f:
                    name = f.read().strip()
                    names[name] = dir
        return names

    def get_next_hap_id(self):
        dirs = self._get_hap_dirs()
        return 1 if not dirs else int(dirs[-1]) + 1

    def get_hap(self, hap_alias: str) -> Optional[Hap]:
        dirs = self._get_hap_dirs()
        # Check by hap id
        if hap_alias in dirs:
            return Hap(self._hapless_dir / hap_alias)

        # Check by hap name
        names_map = self._get_hap_names_map()
        if hap_alias in names_map:
            return Hap(self._hapless_dir / names_map[hap_alias])

    def get_haps(self) -> List[Hap]:
        haps = []
        if not self._hapless_dir.exists():
            return haps

        for dir in self._get_hap_dirs():
            hap_path = self._hapless_dir / dir
            haps.append(Hap(hap_path))
        return haps

    def create_hap(self):
        pass

    async def run_hap(self):
        pass

    def run(self, cmd: str):
        hid = self.get_next_hap_id()
        hap_dir = self._hapless_dir / f"{hid}"
        hap_dir.mkdir()
        stdout_path = hap_dir / "stdout.log"
        stderr_path = hap_dir / "stderr.log"
        pid_path = hap_dir / "pid"
        rc_path = hap_dir / "rc"
        pid = os.fork()
        if pid == 0:
            coro = subprocess_wrapper(
                cmd,
                stdout_path=stdout_path,
                stderr_path=stderr_path,
                pid_path=pid_path,
                rc_path=rc_path,
            )
            asyncio.run(coro)
        else:
            sys.exit(0)


async def subprocess_wrapper(
    cmd,
    *,
    stdout_path: Path,
    stderr_path: Path,
    pid_path: Path,
    rc_path: Path,
):
    with (
        open(stdout_path, "w") as stdout_pipe,
        open(stderr_path, "w") as stderr_pipe,
    ):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=stdout_pipe,
            stderr=stderr_pipe,
        )
        # todo: update style
        console.print(f"{config.ICON_HAP} Launched hap PID[{proc.pid}]")
        with open(pid_path, "w") as pid_file:
            pid_file.write(f"{proc.pid}")

        _ = await proc.communicate()

        with open(rc_path, "w") as rc_file:
            rc_file.write(f"{proc.returncode}")
