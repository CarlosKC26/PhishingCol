from __future__ import annotations

import sys

from application.bootstrap import build_service_bundle
from presentation.cli_controller import CLIController


def build_cli_controller() -> CLIController:
    services = build_service_bundle()
    return CLIController(
        services.input_handler,
        services.analysis_service,
        services.batch_monitor_service,
    )


def main(argv: list[str] | None = None) -> int:
    controller = build_cli_controller()
    return controller.run(argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
