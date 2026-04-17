from __future__ import annotations

import os

from application.bootstrap import build_service_bundle
from presentation.web_controller import create_app


def main() -> None:
    services = build_service_bundle()
    app = create_app(services)
    # Binding to all interfaces is intentional for Docker and deployment scenarios.
    host = os.getenv("WEB_HOST", "0.0.0.0")  # nosec B104
    port = int(os.getenv("WEB_PORT", "8000"))
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
