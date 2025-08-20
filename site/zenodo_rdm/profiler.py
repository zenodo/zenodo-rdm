# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 CERN.
#
# ZenodoRDM is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
"""Profiler module."""

import re
from datetime import datetime, timedelta
from pathlib import Path

import pyinstrument
import sqlalchemy as sa
import sqltap
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy.pool import SingletonThreadPool
from werkzeug.local import LocalProxy
from werkzeug.utils import secure_filename

#
# SQLite DB model
#
Base = declarative_base()


class SessionRequest(Base):
    """Profiling session requests model."""

    __tablename__ = "session_requests"

    id = sa.Column(sa.Integer, primary_key=True)
    ts = sa.Column(sa.DateTime)
    context = sa.Column(sa.JSON)
    base_report = sa.Column(sa.Text)
    sql_report = sa.Column(sa.Text)


#
# Proxies
#
current_profiler = LocalProxy(lambda: current_app.extensions["profiler"])
"""Proxy for the profiler extension."""


#
# Views
#
blueprint = Blueprint(
    "profiler",
    __name__,
    url_prefix="/profiler",
    template_folder="templates",
)


@blueprint.get("/")
def index():
    """Index view."""
    return render_template(
        "profiler/index.html",
        active_session=current_profiler.active_session,
        profiler_sessions=current_profiler.profiler_sessions,
    )


@blueprint.post("/start")
def start_session():
    """Start a profiling session."""
    active_session = current_profiler.active_session
    if active_session:
        flash(
            f"You already have a profiling session running with {active_session['id']}",
            "error",
        )
        return redirect(url_for("profiler.index"), 302)

    current_profiler.active_session = {
        "id": secure_filename(request.form["id"]),
        "base": request.form.get("base", type=bool),
        "sql": request.form.get("sql", type=bool),
    }
    return redirect(url_for("profiler.index"), 303)


@blueprint.post("/stop")
def stop_session():
    """Stop a profiling session."""
    active_session = current_profiler.active_session
    if not active_session:
        flash("You don't have an active profiling session running", "error")
        return redirect(url_for("profiler.index"), 302)
    current_profiler.active_session = None
    return redirect(url_for("profiler.index"), 303)


@blueprint.post("/delete")
def clear_sessions():
    """Clear profiling sessions from storage."""
    current_profiler.clear_sessions()
    return redirect(url_for("profiler.index"), 302)


@blueprint.get("/reports/<session_id>/<request_id>/<report_type>")
def report_view(session_id, request_id, report_type):
    """Serve an profiling HTML report."""
    content = current_profiler.get_request_report(session_id, request_id, report_type)
    if not content:
        abort(404)
    resp = make_response(content, 200)
    resp.content_type = "text/html"
    resp.charset = "utf-8"
    return resp


@blueprint.before_request
def check_permission():
    """Hook for permission check over all the profiler views."""
    if not current_profiler.permission_func():
        abort(403)


#
# Flask extension
#
class Profiler:
    """Profiler Flask extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["profiler"] = self
        app.register_blueprint(blueprint)

        @app.before_request
        def _setup_profilers():
            active_session = self.active_session
            if active_session:
                endpoint_ignored = any(
                    re.match(e, request.endpoint)
                    for e in current_app.config["PROFILER_IGNORED_ENDPOINTS"]
                )
                if endpoint_ignored:
                    return
                g.profiler_session_id = active_session["id"]
                if active_session.get("base"):
                    g.base_profiler = pyinstrument.Profiler()
                    g.base_profiler.start()
                if active_session.get("sql"):
                    g.sql_profiler = sqltap.ProfilingSession()
                    g.sql_profiler.start()

        @app.after_request
        def _store_profiler_reports(response):
            reports = {}
            if hasattr(g, "base_profiler"):
                g.base_profiler.stop()
                report_html = g.base_profiler.output_html()
                reports["base"] = report_html
            if hasattr(g, "sql_profiler"):
                g.sql_profiler.stop()
                report_html = sqltap.report(
                    g.sql_profiler.collect(),
                    report_format="html",
                )
                reports["sql"] = report_html
            if reports:
                self.store_session_request(reports)
            self.refresh_active_session()
            return response

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault("PROFILER_STORAGE", Path(app.instance_path) / "profiler")
        app.config.setdefault("PROFILER_ACTIVE_SESSION_LIFETIME", timedelta(minutes=60))
        app.config.setdefault("PROFILER_ACTIVE_SESSION_REFRESH", timedelta(minutes=30))
        app.config.setdefault("PROFILER_IGNORED_ENDPOINTS", ["static", r"profiler\..+"])
        app.config.setdefault("PROFILER_PERMISSION", lambda: True)

    @property
    def active_session(self):
        """Get currently active profiling session, stored in ``Flask.session``."""
        value = session.get("profiler_session")
        expires_at = (value or {}).get("expires_at")
        if value and expires_at < datetime.utcnow():
            # delete from session and return
            session.pop("profiler_session")
            return
        return value

    @active_session.setter
    def active_session(self, value):
        """Set currently active profiling session, stored in ``Flask.session``."""
        if value:
            value["expires_at"] = (
                datetime.utcnow()
                + current_app.config["PROFILER_ACTIVE_SESSION_LIFETIME"]
            )
        session["profiler_session"] = value

    def refresh_active_session(self):
        """Refresh the expiration of the active session."""
        target_ts = (
            datetime.utcnow() + current_app.config["PROFILER_ACTIVE_SESSION_REFRESH"]
        )
        if self.active_session and target_ts > self.active_session["expires_at"]:
            session["profiler_session"]["expires_at"] = (
                datetime.utcnow() + self.active_session_lifetime
            )

    @property
    def permission_func(self):
        """Get permission check function from config."""
        return current_app.config["PROFILER_PERMISSION"]

    @property
    def storage_dir(self):
        """Profiling sessions storage directory path from config."""
        return Path(current_app.config["PROFILER_STORAGE"])

    def get_session_entries(self, session_id):
        """Get profiling session request entries for a session."""
        session = self._db_session(session_id)
        return session.query(
            SessionRequest.id,
            SessionRequest.ts,
            SessionRequest.context,
            SessionRequest.base_report.is_not(None).label("has_base_report"),
            SessionRequest.sql_report.is_not(None).label("has_sql_report"),
        ).order_by(SessionRequest.ts.asc())

    @property
    def profiler_sessions(self):
        """List profiler sessions information."""
        if self.storage_dir.exists():
            return {
                sess_db.stem: self.get_session_entries(sess_db.stem).all()
                for sess_db in self.storage_dir.iterdir()
                if sess_db.is_file() and sess_db.suffix == ".db"
            }
        return {}

    def clear_sessions(self):
        """Delete all profiling sesions files from storage."""
        for sess_db in self.storage_dir.iterdir():
            if sess_db.is_file() and sess_db.suffix == ".db":
                sess_db.unlink(missing_ok=True)

    def get_request_report(self, session_id, request_id, report_type):
        """Retrieve raw HTML report type for a specific profiling session request."""
        session = self._db_session(session_id)
        if report_type == "sql":
            query = session.query(SessionRequest.sql_report)
        elif report_type == "base":
            query = session.query(SessionRequest.base_report)
        return query.filter(SessionRequest.id == request_id).scalar()

    def _db_session(self, session_id=None):
        """SQLAlchemy session for the SQLite file of a profiling session."""
        db_path = self.storage_dir / f"{session_id or g.profiler_session_id}.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        engine = sa.create_engine(f"sqlite:///{db_path}", poolclass=SingletonThreadPool)
        Base.metadata.create_all(engine)
        return Session(bind=engine)

    def store_session_request(self, reports):
        """Store profiling reports and context for a request in a session."""
        session = self._db_session()
        session.add(
            SessionRequest(
                ts=datetime.utcnow(),
                context={
                    "endpoint": request.endpoint,
                    "url": request.url,
                    "path": request.path,
                    "method": request.method,
                    "referrer": request.referrer,
                    "headers": dict(request.headers),
                },
                base_report=reports.get("base"),
                sql_report=reports.get("sql"),
            )
        )
        session.commit()
