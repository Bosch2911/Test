#!/usr/bin/python

# -*- coding: utf-8 -*-

##
# Sample script for uploading to Sketchfab
# using the V3 API and the requests library
##
import json
import os

from time import sleep

# import the requests library
# http://docs.python-requests.org/en/latest
# pip install requests
import requests

##
# Uploading a model to Sketchfab is a two step process
#
# 1. Upload a model. If the upload is successful, the API will return
#    the model's uid in the `Location` header, and the model will be placed in the processing queue
#
# 2. Poll for the processing status
#    You can use your model id (see 1.) to poll the model processing status
#    The processing status can be one of the following:
#    - PENDING: the model is in the processing queue
#    - PROCESSING: the model is being processed
#    - SUCCESSED: the model has being sucessfully processed and can be view on sketchfab.com
#    - FAILED: the processing has failed. An error message detailing the reason for the failure
#              will be returned with the response
#
# HINTS
# - limit the rate at which you poll for the status (once every few seconds is more than enough)
##

SKETCHFAB_DOMAIN = 'sketchfab.com'
SKETCHFAB_API_URL = 'https://docs.{}/data-api/v3'.format(SKETCHFAB_DOMAIN)
#https://docs.sketchfab.com/data-api/v3

YOUR_API_TOKEN = '2923a6a46e794800a9f232a4df064c72'


def _get_request_payload(data={}, files={}, json_payload=False):
    """Helper method that returns the authentication token and proper content
    type depending on whether or not we use JSON payload."""
    headers = {'Authorization': 'Token {}'.format(YOUR_API_TOKEN)}

    if json_payload:
        headers.update({'Content-Type': 'application/json'})
        data = json.dumps(data)

    return {'data': data, 'files': files, 'headers': headers}


def upload():
    """POST a model to sketchfab.

    This endpoint only accepts formData as we upload a file.
    """
    model_endpoint = os.path.join(SKETCHFAB_API_URL, 'models')

    # Mandatory parameters
    #model_file = './data/pikachu.zip'  # path to your model
    model_file = '/Users/brian/Downloads/Para3D/Test/Test_dense_mesh_refine_texture.ply'  # path to your model

    # Optional parameters
    name = 'A Bob model'
    description = 'This is a bob model I made with love and passion'
    #password = 'my-password'  # requires a pro account
    #private = 1  # requires a pro account
    tags = ['bob', 'character', 'video-games']  # Array of tags
    categories = ['people','test']  # Array of categories slugs
    license = 'CC Attribution-ShareAlike'  # License label
    isPublished = False, # Model will be on draft instead of published
    isInspectable = True, # Allow 2D view in model inspector

    data = {
        'name': name,
        'description': description,
        'tags': tags,
        'categories': categories,
        'license': license,
        #'private': private,
        #'password': password,
        'isPublished': isPublished,
        'isInspectable': isInspectable
    }

    print(model_file)
    f = open(model_file, 'rb')

    files = {'modelFile': f}

    print("--------")
    print(files)

    print('Uploading ...')

    try:
        r = requests.post(
            model_endpoint, **_get_request_payload(
                data, files=files))
        print("hizo el reque")
        print(r)
        print("fin de re")
    except requests.exceptions.RequestException as e:
        print('An error occured: {}'.format(e))
        return
    finally:
        f.close()

    if r.status_code != 201:
        print('Upload failed with error: {}'.format(r.json()))
        return

    # Should be https://api.sketchfab.com/v3/models/XXXX
    model_url = r.headers['Location']
    print('Upload successful. Your model is being processed.')
    print('Once the processing is done, the model will be available at: {}'.format(
        model_url))

    return model_url


def poll_processing_status(model_url):
    """GET the model endpoint to check the processing status."""
    max_errors = 10
    errors = 0
    retry = 0
    max_retries = 50
    retry_timeout = 5  # seconds

    print('Start polling processing status for model')

    while (retry < max_retries) and (errors < max_errors):
        print('Try polling processing status (attempt #{}) ...'.format(retry))

        try:
            r = requests.get(model_url, **_get_request_payload())
        except requests.exceptions.RequestException as e:
            print('Try failed with error {}'.format(e))
            errors += 1
            retry += 1
            continue

        result = r.json()

        if r.status_code != 200:#requests.codes[ok]:
            print('Upload failed with error: {}'.format(result['error']))
            errors += 1
            retry += 1
            continue

        processing_status = result['status']['processing']

        if processing_status == 'PENDING':
            print('Your model is in the processing queue. Will retry in {} seconds'.format(
                retry_timeout))
            print('Want to skip the line? Get a pro account! https://sketchfab.com/plans')
            retry += 1
            sleep(retry_timeout)
            continue
        elif processing_status == 'PROCESSING':
            print('Your model is still being processed. Will retry in {} seconds'.format(
                retry_timeout))
            retry += 1
            sleep(retry_timeout)
            continue
        elif processing_status == 'FAILED':
            print('Processing failed: {}'.format(result['error']))
            return False
        elif processing_status == 'SUCCEEDED':
            print('Processing successful. Check your model here: {}'.format(
                model_url))
            return True

        retry += 1

    print('Stopped polling after too many retries or too many errors')
    return False


def patch_model(model_url):
    """PATCH the model endpoint to update its name, description ...

    Important: The call uses a JSON payload.
    """

    data = {'name': 'A super Bob model'}

    try:
        r = requests.patch(
            model_url, **_get_request_payload(
                data, json_payload=True))
    except requests.exceptions.RequestException as e:
        print('An error occured: {}'.format(e))
    else:
        if r.status_code != 204:
            print('PATCH model failed with error: {}'.format(r.content))
        else:
            print('PATCH model successful.')


def patch_model_options(model_url):
    """PATCH the model options endpoint to update the model background, shading,
    orienration."""
    options_url = os.path.join(model_url, 'options')

    data = {
        'shading': 'shadeless',
        'background': '{"color": "#FFFFFF"}',
        # For axis/angle rotation:
        'orientation': '{"axis": [1, 1, 0], "angle": 34}',
        # Or for 4x4 matrix rotation:
        # 'orientation': '{"matrix": [1, 0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]}'
    }

    try:
        r = requests.patch(
            options_url, **_get_request_payload(
                data, json_payload=True))
    except requests.exceptions.RequestException as e:
        print('An error occured: {}'.format(e))
    else:
        if r.status_code != 204:
            print('PATCH options failed with error: {}'.format(r.content))
        else:
            print('PATCH options successful.')


###################################
# Uploads, polls and patch a model
###################################

model_url = upload()

if model_url:
    if poll_processing_status(model_url):
        patch_model(model_url)
        patch_model_options(model_url) 