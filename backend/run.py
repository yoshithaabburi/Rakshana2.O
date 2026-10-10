# ============================================
# RAKSHANA 24/7 — Application Entry Point
# ============================================

import os
import logging

from app import create_app, socketio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Create app
app = create_app(os.getenv("FLASK_ENV", "development"))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))

    print("\n" + "=" * 60)
    print("  🛡️  RAKSHANA 24/7 — Backend API Server")
    print(" Digital Safety for Women")
    print("=" * 60)
    print(f"  🌐 Server:    http://localhost:{port}")
    print(f"  📡 API Base:   http://localhost:{port}/api")
    print(f"  🔒 Auth:      http://localhost:{port}/api/auth")
    print(f"  📊 Dashboard: http://localhost:{port}/api/dashboard")
    print(f"  ⚖️  Legal:     http://localhost:{port}/api/legal")
    print(f"  📝 Reports:   http://localhost:{port}/api/reports")
    print(f"  🔍 Scans:     http://localhost:{port}/api/scan")
    print(f"  ❤️  Health:    http://localhost:{port}/api/health")
    print("=" * 60)
    print(f"  Environment: {os.getenv('FLASK_ENV', 'development')}")
    print(f"  Debug:       {app.debug}")
    print("=" * 60 + "\n")

    socketio.run(app, host="0.0.0.0", port=port, debug=app.debug)
