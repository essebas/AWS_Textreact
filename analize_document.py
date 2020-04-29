import boto3
import json
import sys
import re
from pprint import pprint

# Amazon Textract

textract = boto3.client(
    service_name = 'textract',
    region_name = 'us-east-1'
)

def get_kv_map(s3BucketName, objectName):

    # Process using image bytes
    response = textract.analyze_document(
        Document={
            'S3Object': {
                'Bucket': s3BucketName,
                'Name': objectName,
            }
        },
        FeatureTypes=['FORMS']
    )

    # Get the text blocks
    blocks = response['Blocks']


    # get key and value maps
    key_map = {}
    value_map = {}
    block_map = {}

    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    return key_map, value_map, block_map


def get_kv_relationship(key_map, value_map, block_map):
    kvs = {}
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key] = val
    return kvs


def find_value_block(key_block, value_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map[value_id]
    return value_block


def get_text(result, blocks_map):
    text = ''
    if 'Relationships' in result:
        for relationship in result['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = blocks_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ''
    return text


def print_kvs(kvs):
    for key, value in kvs.items():
        print(key, ":", value)


def search_value(kvs, search_key):
    for key, value in kvs.items():
        if re.search(search_key, re.IGNORECASE):
            return value


# Informacion del Documento
s3BucketName = "textract-console-us-east-1-50ce762e-d6fc-434a-881a-c109b45836c8"
documentName = "1587349378/img/out_2.jpg"

# MAIN PROGRAM
key_map, value_map, block_map = get_kv_map(s3BucketName, documentName)

kvs = get_kv_relationship(key_map, value_map, block_map)
print("\n\n== FOUND KEY : VALUE pairs ===\n")
print_kvs(kvs)


while input('\n Desea buscar un valor por una clave? (enter "n" for exit)') != 'n':
    search_key = input('\n Enter a search key:')
    print('The value is:', search_value(kvs, search_key))
