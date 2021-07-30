"""Utilities for interacting with project data through file-system based Inventory API

Until assets are created entirely in the database, this script
provides a bridge between the file-based project inventory and configuration.

"""

import os
import sys
import copy


from avalon import schema, io, Session, pipeline
from avalon.vendor import toml

self = sys.modules[__name__]
self.collection = None

__all__ = [
    # "init",
    # "save",
    "project_load",
    "project_create",
    # "project_ls",
]


DEFAULT_CONFIG = {
    "schema": "avalon-core:config-1.0",
    "apps": [
        {
            "name": "shell",
            "label": "Shell"
        },
        {
            "name": "maya2016",
            "label": "Autodesk Maya 2016"
        },
    ],
    "tasks": [
        {"name": "model"},
        {"name": "render"},
        {"name": "animate"},
    ],
    "template": {
        "work": "{root}/{project}/{silo}/{asset}/work/{task}",
        "publish": "{root}/{project}/{silo}/{asset}/publish/{subset}/v{version:0>3}/{subset}.{representation}"
    }
}


PIPELINE_FOLDERS = ['logs', 'plugins', 'pythonpath', 'recipes', 'hosts']

def project_create(path, name, label=None):
    """Create project in directory, and establish an example configuration.

    Arguments:
        root (str): Path to project-repo where new project-folder will be made.
        name (str): Unique name of new project. Used for folder-name.
        label (str): Pretty name of new project. Used in interfaces.

    """
    assert os.path.exists(path)
    label = label or name

    # if name in project_ls():
    #     raise Exception("Project already exists in database! Try loading it instead.")

    root = os.path.join(path, name)
    if not os.path.isdir(root):
        _makeDirs(root)
    else:
        print("Project directory already exists!")
        # raise Exception("Project directory already exists! Try loading it instead.")

    projectConfigPath = os.path.join(root, '.project.toml')
    if not os.path.isfile(projectConfigPath):
        project = {
            "schema": "avalon-core:project-2.0",
            "type": "project",
            "name": name,
            "label": label,
            "data": dict(),
            "config": DEFAULT_CONFIG,
            "parent": None,
        }

        # project_id = io.insert_one(project).inserted_id
        # project["_id"] = project_id
        _write(root, "project", project)

    else:
        print("Project already configured! Try loading it instead.")
        # raise Exception("Project already configured! Try loading it instead.")

    pipelineDir = os.path.realpath(os.path.join(root, '.pipeline'))
    if not os.path.exists(pipelineDir):
        _makeDirs(pipelineDir)

    for name in PIPELINE_FOLDERS:
        path = os.path.realpath(os.path.join(pipelineDir, name))
        if os.path.isdir(path):
            continue
        _makeDirs(path)

    print("Successfully made new project: {0} - {1}".format(name, root))
    return root


def project_load(root):
    """Load project from file system.
    Arguments:
        root (str): Path to root of project.
    """
    assert os.path.exists(root)

    print("Loading .project.toml...")
    project = _read(root, "project")
    if not project:
        msg = "Unable to load project - Config file is missing. \t {0}".format(root)
        raise Exception(msg)

    pipeline.register_project(project)
    Session["AVALON_PROJECT"] = project['name']
    print("Successfully loaded project: {0}".format(project['name']))

    return project

def project_close():
    project = pipeline.registered_project()
    Session["AVALON_PROJECT"] = None
    pipeline.deregister_project()
    pass

#
# def project_ls():
#     """Return a list of project names in database."""
#     return [project["name"] for project in io.projects()]



def create_asset(name, silo, data, parent):
    assert isinstance(parent, io.ObjectId)

    # if io.find_one({"type": "asset", "name": name}):
    #     raise RuntimeError("%s already exists" % name)

    asset = {
        "schema": "avalon-core:asset-2.0",
        "name": name,
        "silo": silo,
        "parent": parent,
        "type": "asset",
        "data": data
    }
    # _id = io.insert_one(asset).inserted_id
    # asset["_id"] = _id
    #
    return asset




def _read(root, name):
    fname = os.path.join(root, ".%s.toml" % name)

    try:
        with open(fname) as f:
            data = toml.load(f)
    except IOError:
        raise

    return data


def _write(root, name, data):
    fname = os.path.join(root, ".%s.toml" % name)

    try:
        with open(fname, "w") as f:
            toml.dump(data, f)
            schema.validate(data)
    except IOError:
        raise

    return data

def _makeDirs(path):
    try:
        os.makedirs(path)
        print("Made directory: \t {0}".format(path))
    except OSError:
        print("Error - Could not make directory: \t {0}".format(path))




# def _cli():
#     import argparse
#
#     parser = argparse.ArgumentParser(__doc__)
#
#     parser.add_argument("--silo",
#                         help="Optional container of silos",
#                         action="append",
#                         default=["assets", "film"])
#     parser.add_argument("--silo-parent", help="Optional silo silo_parent")
#     parser.add_argument("--init",
#                         action="store_true",
#                         help="Start a new project")
#     parser.add_argument("--save",
#                         action="store_true",
#                         help="Save inventory from disk to database")
#     parser.add_argument("--load",
#                         nargs="?",
#                         default=False,
#                         help="Load inventory from database to disk")
#     parser.add_argument("--ls",
#                         action="store_true",
#                         help="List all projects in database")
#     parser.add_argument("--extract",
#                         action="store_true",
#                         help="Generate config and inventory "
#                              "from assets already on disk.")
#     parser.add_argument("--overwrite",
#                         action="store_true",
#                         help="Overwrite exitsing assets on upload")
#     parser.add_argument("--upload",
#                         action="store_true",
#                         help="Upload generated project to database.")
#     parser.add_argument("--root", help="Absolute path to project.")
#
#     kwargs = parser.parse_args()
#
#     root = kwargs.root or os.getcwd()
#     name = kwargs.load or os.path.basename(root)
#
#     if any([kwargs.load,
#             kwargs.save,
#             kwargs.upload,
#             kwargs.init,
#             kwargs.ls]) or kwargs.load is None:
#         os.environ["AVALON_PROJECT"] = name
#         io.install()
#
#     if kwargs.init:
#         config, inventory = init(name)
#         _write(root, "config", config)
#         _write(root, "inventory", inventory)
#         print("Success!")
#
#     elif kwargs.load or kwargs.load is None:
#         config, inventory = load(name)
#         _write(root, "config", config)
#         _write(root, "inventory", inventory)
#         print("Success!")
#
#     elif kwargs.save:
#         inventory = _read(root, "inventory")
#         config = _read(root, "config")
#         save(name, config, inventory)
#         print("Successfully saved to %s" % os.getenv("AVALON_MONGO"))
#
#     elif kwargs.ls:
#         msg = "Projects in database:"
#         for name in ls():
#             msg += "\n- {0}".format(name)
#         print(msg)
#
#     else:
#         print(__doc__)
#
#
# if __name__ == '__main__':
#
#     try:
#         _cli()
#     except Exception as e:
#         print(e)
#         sys.exit(1)
