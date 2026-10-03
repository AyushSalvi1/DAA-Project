"""NexaSearch - Intelligent Algorithmic Information Retrieval Engine
Design and Analysis of Algorithms project.

Run with::

    python app.py

or with the Flask CLI::

    flask --app app run

The application factory creates the SQLite database, seeds the sample
corpus, builds the Trie / hash table / inverted index, computes PageRank on
the document graph and registers every route.
"""

from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

from flask import Flask, jsonify, render_template, request

# make the project importable no matter where the process was started
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.service import NexaService            # noqa: E402
from routes.admin_routes import bp as admin_bp  # noqa: E402
from routes.algorithm_routes import bp as algorithms_bp  # noqa: E402
from routes.api_routes import bp as api_bp      # noqa: E402
from routes.search_routes import bp as search_bp  # noqa: E402

APP_NAME = "NexaSearch"
TAGLINE = "Search Smarter. Analyze Faster."


def create_app(db_path: str | None = None, seed: bool = True) -> Flask:
    """Application factory."""
    app = Flask(__name__, instance_relative_config=False)
    app.config.update(
        SECRET_KEY=os.environ.get("NEXASEARCH_SECRET", "nexasearch-dev-secret-key"),
        DATABASE=db_path or os.environ.get("NEXASEARCH_DB"),
        JSON_SORT_KEYS=False,
        TEMPLATES_AUTO_RELOAD=True,
        MAX_CONTENT_LENGTH=8 * 1024 * 1024,
    )
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s %(name)s: %(message)s",
    )

    # ---------------------------------------------------------------- data
    service = NexaService(app.config["DATABASE"])
    info = service.bootstrap(seed=seed)
    app.extensions["nexasearch"] = service
    app.extensions["bootstrap_info"] = info
    app.logger.info(
        "Indexed %d documents / %d terms in %.1f ms (boot %.1f ms)",
        info["documents"], info["vocabulary"], info["index_time_ms"], info["boot_time_ms"],
    )

    # -------------------------------------------------------------- routes
    app.register_blueprint(search_bp)
    app.register_blueprint(algorithms_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # ------------------------------------------------------ template glue
    @app.context_processor
    def inject_globals():
        stats = service.index.stats()
        return {
            "app_name": APP_NAME,
            "tagline": TAGLINE,
            "categories": service.db.categories(),
            "recent_searches": service.db.recent_searches(6),
            "index_stats": stats,
            "current_year": datetime.now().year,
            "now": datetime.now(),
        }

    @app.template_filter("ms")
    def format_ms(value):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return "0.000"
        if number >= 100:
            return f"{number:.0f}"
        if number >= 1:
            return f"{number:.2f}"
        return f"{number:.4f}"

    @app.template_filter("compact")
    def format_compact(value):
        try:
            number = int(value)
        except (TypeError, ValueError):
            return "0"
        return f"{number:,}"

    @app.template_filter("percent")
    def format_percent(value):
        try:
            return f"{float(value):.1f}%"
        except (TypeError, ValueError):
            return "0%"

    # ------------------------------------------------------ error handlers
    def wants_json() -> bool:
        return request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json"

    @app.errorhandler(400)
    def bad_request(error):
        if wants_json():
            return jsonify({"error": "bad request", "detail": str(error)}), 400
        return render_template("error.html", title="Bad Request",
                               message="That request was malformed. Please try again.",
                               code=400), 400

    @app.errorhandler(404)
    def not_found(error):
        if wants_json():
            return jsonify({"error": "not found"}), 404
        return render_template("error.html", title="Page Not Found",
                               message="We could not find that page. The corpus index is still "
                                       "running - try searching from the home page.",
                               code=404), 404

    @app.errorhandler(413)
    def too_large(error):
        return render_template("error.html", title="Payload Too Large",
                               message="That upload exceeds the 2 MB per-file limit.",
                               code=413), 413

    @app.errorhandler(500)
    def server_error(error):  # pragma: no cover - defensive
        app.logger.exception("unhandled error: %s", error)
        if wants_json():
            return jsonify({"error": "internal server error"}), 500
        return render_template("error.html", title="Server Error",
                               message="Something went wrong while handling that request. "
                                       "The error has been logged.",
                               code=500), 500

    @app.errorhandler(Exception)
    def catch_all(error):  # pragma: no cover - defensive
        from werkzeug.exceptions import HTTPException
        if isinstance(error, HTTPException):
            return error
        app.logger.exception("unhandled exception: %s", error)
        if wants_json():
            return jsonify({"error": "internal server error",
                            "detail": type(error).__name__}), 500
        return render_template("error.html", title="Unexpected Error",
                               message="An unexpected error occurred and has been logged.",
                               code=500), 500

    # ------------------------------------------------------------ commands
    @app.cli.command("reindex")
    def cli_reindex():  # pragma: no cover - CLI helper
        """Rebuild the index, graph and TF-IDF model."""
        print(service.rebuild(reason="cli"))

    @app.cli.command("seed")
    def cli_seed():  # pragma: no cover - CLI helper
        """Reload the sample corpus into the database."""
        from core.seed_data import seed_database
        print(seed_database(service.db, force=True))

    return app


if __name__ == "__main__":
    # Built here rather than at import time: importing this module (from the
    # tests, or from a WSGI server using the factory) must not boot a second
    # copy of the index. `flask --app app run` still finds create_app().
    app = create_app()
    host = os.environ.get("NEXASEARCH_HOST", "127.0.0.1")
    port = int(os.environ.get("NEXASEARCH_PORT", "5000"))
    debug = os.environ.get("NEXASEARCH_DEBUG", "0") == "1"
    stats = app.extensions["nexasearch"].index.stats()
    print("=" * 68)
    print(f"  {APP_NAME} - {TAGLINE}")
    print(f"  Serving on http://{host}:{port}")
    print(f"  Documents: {stats['documents']}   Terms: {stats['unique_terms']}")
    print("=" * 68)
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)
