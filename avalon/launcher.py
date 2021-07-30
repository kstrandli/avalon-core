

import sys
import json
import errno
import shutil
import os

import logging
log = logging.getLogger(__name__)

from avalon import pipeline, io, lib
from avalon.pipeline import Action

from .vendor import six

class Application(Action):
    """Default application launcher

    This is a convenience application Action that when "config" refers to a
    parsed application `.toml` this can launch the application.

    """

    config = None

    def is_compatible(self, session):
        required = ["AVALON_PROJECTS",
                    "AVALON_PROJECT",
                    "AVALON_ASSET",
                    "AVALON_TASK"]
        missing = [x for x in required if x not in session]
        if missing:
            self.log.debug("Missing keys: %s" % (missing,))
            return False
        return True

    def environ(self, session):
        """Build application environment"""

        session = session.copy()
        session["AVALON_APP"] = self.config["application_dir"]
        session["AVALON_APP_NAME"] = self.name

        # Compute work directory
        project = io.find_one({"type": "project"})
        template = project["config"]["template"]["work"]
        workdir = pipeline._format_work_template(template, session)
        session["AVALON_WORKDIR"] = os.path.normpath(workdir)

        # Construct application environment from .toml config
        app_environment = self.config.get("environment", {})
        for key, value in app_environment.copy().items():
            if isinstance(value, list):
                # Treat list values as paths, e.g. PYTHONPATH=[]
                app_environment[key] = os.pathsep.join(value)

            elif isinstance(value, six.string_types):
                if lib.PY2:
                    # Protect against unicode in the environment
                    encoding = sys.getfilesystemencoding()
                    app_environment[key] = value.encode(encoding)
                else:
                    app_environment[key] = value
            else:
                log.error(
                    "%s: Unsupported environment reference in %s for %s"
                    % (value, self.name, key)
                )

        # Build environment
        env = os.environ.copy()
        env.update(session)
        app_environment = self._format(app_environment, **env)
        env.update(app_environment)

        return env

    def initialize(self, environment):
        """Initialize work directory"""
        # Create working directory
        workdir = environment["AVALON_WORKDIR"]
        workdir_existed = os.path.exists(workdir)
        if not workdir_existed:
            os.makedirs(workdir)
            self.log.info("Creating working directory '%s'" % workdir)

            # Create default directories from app configuration
            default_dirs = self.config.get("default_dirs", [])
            default_dirs = self._format(default_dirs, **environment)
            if default_dirs:
                self.log.debug("Creating default directories..")
                for dirname in default_dirs:
                    try:
                        os.makedirs(os.path.join(workdir, dirname))
                        self.log.debug(" - %s" % dirname)
                    except OSError as e:
                        # An already existing default directory is fine.
                        if e.errno == errno.EEXIST:
                            pass
                        else:
                            raise

        # Perform application copy
        for src, dst in self.config.get("copy", {}).items():
            dst = os.path.join(workdir, dst)
            # Expand env vars
            src, dst = self._format([src, dst], **environment)

            try:
                self.log.info("Copying %s -> %s" % (src, dst))
                shutil.copy(src, dst)
            except OSError as e:
                self.log.error("Could not copy application file: %s" % e)
                self.log.error(" - %s -> %s" % (src, dst))

    def launch(self, environment):

        executable = lib.which(self.config["executable"])
        if executable is None:
            raise ValueError(
                "'%s' not found on your PATH\n%s"
                % (self.config["executable"], os.getenv("PATH"))
            )

        args = self.config.get("args", [])
        return lib.launch(
            executable=executable,
            args=args,
            environment=environment,
            cwd=environment["AVALON_WORKDIR"]
        )

    def process(self, session, **kwargs):
        """Process the full Application action"""

        environment = self.environ(session)

        if kwargs.get("initialize", True):
            self.initialize(environment)

        if kwargs.get("launch", True):
            return self.launch(environment)

    def _format(self, original, **kwargs):
        """Utility recursive dict formatting that logs the error clearly."""

        try:
            return lib.dict_format(original, **kwargs)
        except KeyError as e:
            log.error(
                "One of the {variables} defined in the application "
                "definition wasn't found in this session.\n"
                "The variable was %s " % e
            )
            log.error(json.dumps(kwargs, indent=4, sort_keys=True))

            raise ValueError(
                "This is typically a bug in the pipeline, "
                "ask your developer.")
