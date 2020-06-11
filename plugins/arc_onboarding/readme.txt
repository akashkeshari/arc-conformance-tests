###
This plugin verifies if the azure arc-agents can be successfully deployed on a kubernetes cluster.
The test passes on successful installation of the arc-agents and fails otherwise
###


###
Description about various files:

1. dockerfile
This file is used to build the test image that performs the installation of arc-agents on the kubernetes cluster

2. install_arc_agents.py
This is the main python script that runs as a part of this test plugin. It also uses utility.py present in common directory

3. onboardingplugin.yaml
This file describes the metadata for the test plugin. It includes details like the container image to run, name of the plugin etc.

4. results directory
This directory contains the results of a sample run of the test plugin.
The tar of this directory is directly provided by sonobuoy.
To see the container logs of the test run: results\podlogs\sonobuoy\sonobuoy-arc-onboarding-job-f876099ca0284c9f\logs\plugin.txt
To see the custom logs collected during the test run: results\plugins\arc-onboarding\results\global\out
It depends on the test developer to collect custom logs. 
As a part of this test, we are collecting output of helm commands as custom logs
###


###
Trying out the test on your kubernetes cluster:
1. Install sonobuoy. Instructions here: https://sonobuoy.io/docs/master/index.html
2. docker build -t <sampletag> -f <path_to_dockerfile> <build_context>
   build_context should be set to plugins directory.
   Sample: navigate to /plugins/arc_onboarding directory and run docker build -t <sampletag> -f .\dockerfile ..
3. navigate to /plugins/arc_onboarding directory and run:
   sonobuoy run --plugin onboardingplugin.yaml --plugin-env arc-onboarding.TENANT_ID=72f988bf-86f1-41af-91ab-2d7cd011db47 --plugin-env arc-onboarding.SUBSCRIPTION_ID=1bfbb5d0-917e-4346-9026-1d3b344417f5 --plugin-env arc-onboarding.RESOURCE_GROUP=akkeshar-test2 --plugin-env arc-onboarding.CLUSTER_NAME=testcl1 --plugin-env arc-onboarding.LOCATION=eastus --plugin-env arc-onboarding.CLIENT_ID=d2508c14-ddcd-41ed-a8e4-1492f37a6daa --plugin-env arc-onboarding.CLIENT_SECRET=014986b3-50d6-44dd-b231-c1e8d4a808ed
4. you can run 'sonobuoy status' to see the status of the test run.
   Run 'sonobuoy retrieve' to get results tarball after test run is complete
###
