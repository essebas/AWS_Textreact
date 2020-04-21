import boto3
import time
import calendar
import sys
from pprint import pprint
from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)
from pdf2image import convert_from_path
from get_document_text_detection import analize_document

file_name = sys.argv[1]

# Obtener Amazon s3
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')

time = calendar.timegm(time.gmtime())

def upload_file(file_name, bucket, object_name = None):

    if object_name is None:
        object_name = file_name

    try:
        response = s3_client.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    return True

def upload_file2(f_name, b_name, o_name = None):
    if o_name is None:
        o_name = f_name
    else:
        obj_name = o_name + f_name

    with open(f_name, 'rb') as f:
        s3_client.upload_fileobj(f, b_name, obj_name)
        convert_pdf_to_images(f_name, 500, b_name, o_name)
    return obj_name


# Las paginas del pdf son convertidas en imagenes pues aws
# incorpora una herramienta para detectar formularios, dando como Respuesta
# objetos con clave-valor. Sin embargo solo se puede utilizar con formatos
# de imagen (.png, .jpg, .jpeg)
def convert_pdf_to_images(f_name, dpi, b_name, o_name):
    pages = convert_from_path(f_name, dpi)
    for index, page in enumerate(pages):
        obj_name = o_name + 'img/'
        name = 'out_' + str(index) + '.jpg'
        obj_name = obj_name + name
        page.save(name, 'JPEG')
        with open(name, 'rb')as f:
            s3_client.upload_fileobj(f, b_name, obj_name)


#Imprimir nombres de buckets
for bucket in s3.buckets.all():
    print("For this bucket {}, we have this elements :".format(bucket.name))
    name = upload_file2(file_name, bucket.name, str(time)+'/')
    analize_document(bucket.name,name)
