import boto3
import time
import re
from pprint import pprint

# Cliente Amazon
client = boto3.client(
    service_name = 'textract',
    region_name = 'us-east-1'
)

def startJob(s3BucketName, objectName):
    response = None
    response = client.start_document_text_detection(
        DocumentLocation={
            'S3Object' : {
                'Bucket' : s3BucketName,
                'Name' : objectName
            }
    })
    return response ['JobId']

def isJobComplete(jobId):
    time.sleep(5)
    # client = boto3.client('textract')
    response = client.get_document_text_detection(JobId = jobId)
    status = response["JobStatus"]
    print("Job status: {}".format(status))

    while(status == "IN_PROGRESS"):
        time.sleep(5)
        response = client.get_document_text_detection(JobId = jobId)
        status = response["JobStatus"]
        print("Job status: {}".format(status))

    return status

def getJobResults(jobId):
    pages = []
    time.sleep(5)

    #client = boto3.client('textract')
    response = client.get_document_text_detection(JobId = jobId)

    pages.append(response)
    print("Resultset page recived: {}".format(len(pages)))
    nextToken = None
    if('NextToken' in response):
        nextToken = response['NextToken']

    while(nextToken):
        time.sleep(5)

        response = client.get_document_text_detection(JobId = jobId, NextToken = nextToken)

        pages.append(response)
        print("Resultset page recived: {}".format(len(pages)))
        nextToken = None
        if('NextToken' in response):
            nextToken = response['NextToken']

    return pages

def get_kv_map(response):

    for resultPage in response:
        blocks = resultPage['Blocks']

    print("El valor del blowue es: {}".format(len(blocks)))
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

# Funcion para optener los datos wue fueron clasificados como clave-valor
def get_kv_relationship(key_map, value_map, block_map):
    kvs = {}
    for block_id, key_block, in key_map.items():
        value_block = find_value_block(key_block, value_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        kvs[key] = val
    return kvs

# Funcion para obtener los blowues de texto de la respuesta de la API de Amazon
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

# Funcion para imprimir todo la respuesta de la API de Amazon (Por Paginas)
def print_results(response):
    for resultPage in response:
        for item in resultPage["Blocks"]:
            if item["BlockType"] == "LINE":
                print ("\033[92m {}\033[00m".format(item['Text']))
            elif item["BlockType"] == "KEY_VALUE_SET":
                print ("ES CLAVE VALOR HPTA")
        print('')

def print_kvs(kvs):
    for key, value in kvs.items():
        print(key, ":", value)

# Funcion para buscar una determinada palabra o frase en toda la respuesta de la API de Amazon
def search_value(response, line):
    search_results = []
    for resultPage in response:
        for item in resultPage["Blocks"]:
            if item["BlockType"] == "LINE":
                if item['Text'] == line:
                    search_results.append(item['Text'])
    return search_results

# Identificar Cedulas
def document_identification(response):
    search_results = []
    start_line_document = "REPUBLICA DE COLOMBIA"
    end_line_document_1 = "INDICE"
    end_line_document_2 = "DERECHO"
    listofCedulas = []
    cedula = []
    isDocument = False
    for resultPage in response:
        for item in resultPage["Blocks"]:
            if item["BlockType"] == "LINE":
                if item['Text'] == start_line_document and not isDocument:
                    isDocument = True
                    cedula.append(item['Text'])
                if isDocument:
                    if item['Text'].isupper():
                        cedula.append(item['Text'])
                        # print(item['Text'])
                    else:
                        try:
                            val = float(item['Text'])
                            # print("Input is an float number. Number = ", val)
                            cedula.append(val)
                        except ValueError:
                            try:
                                val = int(item['Text'].replace('.', ''))
                                cedula.append(val)
                                # print("str is replace= ", val)
                                # print(type(val))
                            except ValueError:
                                # print("No.. input is not a number. It's a string")
                                 print("NO ESTA EN MAYUSCULA: " + item['Text'])
                    if item['Text'] == end_line_document_1 or item['Text'] == end_line_document_2:
                        isDocument = False
                        print("---------------------")
                        # print(cedula)
                        print("---------------------")
                        listofCedulas.append(cedula)
                        cedula.clear()

    return listofCedulas

# Informacion del Documento
def analize_document(s3BucketName, documentName):

    jobId = startJob(s3BucketName, documentName)
    print("Started job with id: {}".format(jobId))
    if(isJobComplete(jobId)):
        response = getJobResults(jobId)
        print("TOTAL DE PAGINAS: {}".format(len(response)))
        doucumentos = document_identification(response)
        print(doucumentos)
        #for cedula in doucumentos:
            #print(*cedula)
            #print("-------------------------")

    #Respuesta
    #search_results = search_value(response, "IDENTIFICACION PERSONAL")
    #print(search_results)
    #print("El total de documentos de identidad encontrados es: {}".format(len(search_results)))
