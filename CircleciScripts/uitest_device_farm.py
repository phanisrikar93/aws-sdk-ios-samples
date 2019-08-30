from functions import runcommand
from uitests_exceptions import *
from parse_config_uitests import config_uitests
from setup_mobile_sdk_dependencies import get_app_config_for
from shutil import rmtree, copyfile
import re
import os

def uitest_device_farm(circleci_root_directory, appname, app_repo_root_directory):

    app_config = get_app_config_for(appname = appname)
    if app_config == None:
        raise FetchAppConfigException(appname = appname)

    logs_folder_name = config_uitests.logs_folder_name
    simulator_specification = "generic/platform=iOS"

    ## cd into app root directory
    app_root_directory = '{0}/{1}'.format(app_repo_root_directory, app_config.path)

    ## install pods
    try:
        os.chdir(app_root_directory)
        if os.path.exists('Podfile.lock'):
            os.remove('Podfile.lock')
    except OSError as err:
        raise RemovePodfileLockException(appname, [str(err)])

    try:
        logs_folder_path = circleci_root_directory + '/' + logs_folder_name
        if os.path.isdir(logs_folder_path):
            rmtree(logs_folder_path)
        os.mkdir(logs_folder_path)
    except OSError as err:
        raise SetUpLogFilesDirectoryException(appname, [str(err)])

    print("step: 1/2... Install Pods \n ")
    runcommand(command="pod --version; pod install",
               exception_to_raise = PodInstallException(appname))

    ## build app; run uitests and store logs
    try:
        derived_data_path = app_root_directory + '/derived_data_folder'
        if os.path.isdir(derived_data_path):
            rmtree(derived_data_path)
        os.mkdir(derived_data_path)
    except OSError as err:
        raise SetUpLogFilesDirectoryException(appname, [str(err)])

    print("step: 2/2... Build and Upload artifacts to device farm \n ")

    app_path = app_config.path.replace('-', '').replace('/', '')
    runcommand(command="xcodebuild build-for-testing -workspace {0}.xcworkspace -scheme \"{0}UITests\" -destination \"{1}\" -derivedDataPath \"{2}\" ".format(
               app_path,
               simulator_specification,
               derived_data_path),
               exception_to_raise=BuildAndUItestFailException(appname, derived_data_path))

    artifacts = {'app': '{0}.app'.format(app_path),
                 'tests':'{0}UITests-Runner.app'.format(app_path)
                }
    for artifact in artifacts:
        try:
            payload_path = derived_data_path + '/Payload/'
            if os.path.isdir(payload_path):
                rmtree(payload_path)
            os.mkdir(payload_path)
        except OSError as err:
            raise SetUpLogFilesDirectoryException(appname, [str(err)])
        copyfile(derived_data_path + '/Build/Products/Debug-iphoneos/' + artifact, derived_data_path + '/Payload/' + artifact)




