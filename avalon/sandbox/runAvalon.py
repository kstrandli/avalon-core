

from avalon import api, pipeline, inventory
from avalon.tools import projectmanager, workfiles
import os
import logging
log = logging.getLogger(__name__)

def runTest():
    host = pipeline.debug_host()
    api.install(host)
    projectPath = "D:/Dropbox/PipelineProjectExamples/PipelineDummyProjects/002_projectB"
    projectPath = "D:/Dropbox/PipelineProjectExamples/PipelineDummyProjects/001_projectA"
    projectPath = "D:/Dropbox/PipelineProjectExamples/PipelineDummyProjects/003_projectC"

    # projectRepo = "D:/Dropbox/PipelineProjectExamples/PipelineDummyProjects"
    # projectRoot = inventory.project_create(projectRepo, "003_ProjectC", "ProjectC")
    # print(projectRoot)
    # projectName = "20210130_MyTestProject"
    # inventory.create_project(projectName)
    # inventory.init(projectName)
    inventory.project_load(projectPath)


    # projectmanager.show()
    # workfiles.show()

if __name__ == '__main__':
    # os.environ["AVALON_CONFIG"] = "robotparty"
    # os.environ["AVALON_PROJECT"] = "002_projectB"
    # os.environ["AVALON_SILO"] = "ASSETS"
    # os.environ["AVALON_TASK"] = "mdl"
    # os.environ["AVALON_APP"] = "maya"
    runTest()