from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import app.db as db
from app.config import Config
from app.extensions import csrf, limiter
from app.models import Base
from app.routes import bp


def create_app() -> Flask:
    config = Config()
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config["SECRET_KEY"] = config.secret_key
    app.config["WTF_CSRF_TIME_LIMIT"] = None
    app.config["MIN_SUBMIT_SECONDS"] = config.min_submit_seconds
    app.config["MAX_NAME_LENGTH"] = config.max_name_length
    app.config["BASE_PATH"] = config.base_path
    app.config["RATELIMIT_STORAGE_URI"] = config.limiter_storage_uri
    app.config["FPJS_PUBLIC_KEY"] = config.fpjs_public_key
    app.config["FPJS_SERVER_API_KEY"] = config.fpjs_server_api_key
    app.config["FPJS_CONFIDENCE_THRESHOLD"] = config.fpjs_confidence_threshold
    app.config["FPJS_SERVER_API_BASE_URL"] = config.fpjs_server_api_base_url
    app.config["FPJS_VERIFY_TIMEOUT_SECONDS"] = config.fpjs_verify_timeout_seconds
    app.config["FPJS_FAIL_OPEN"] = config.fpjs_fail_open

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    db.init_db(config.database_url)
    Base.metadata.create_all(bind=db.engine)
    db.ensure_submission_fp_columns()

    csrf.init_app(app)
    limiter.init_app(app)

    app.register_blueprint(bp)

    return app
