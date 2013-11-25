#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Montador de imágenes clonezilla en directorio libre y válido.
Requiere partclone
jpueyob 6/6/2012
'''

from pwd import getpwnam
from commands import getoutput
import os
import sys

EXEC_NAME = 'clonezilla_img_mounter.py'
MOUNTABLE_IMG_FILE = './temporal.img'

OK = 0
UNPRIVILEGED_USER = 2
INVALID_PARAMETER_NUMBER=3
BAD_IMAGE_FILE = 4
BAD_MOUNT_DIR = 5
ERROR_CREATING_MOUNTABLE_IMG = 6
ERROR_MOUNTING_IMAGE = 7
BAD_PARTITION_FORMAT = 8
BROKEN_DEPENDENCIES = 9

VALID_PARTITION_FORMAT = { 'ext2':'ext2', 'ext3':'ext3', 'ext4':'ext4', 'vfat':'vfat', 'fat':'vfat', 'fat32':'vfat',  'ntfs':'ntfs-3g', 'ntfs-3g':'ntfs-3g'}
PACKAGE_DEPENDENCIES = ['ntfs-3g', 'partclone' ]

def get_user_info(user):
    '''
    int/list get_user_info(string user)
    Extraemos con pwd.getpwnam los datos de un usuario, nos devuelve la función una estructura.
    0 : nombre de usuario o login.
    1 : contraseña, si está cifrada nos devolverá 'x'.
    2 : UID del usuario.
    3 : será el GID.
    4 : nombre completo del usuario.
    5 : home del usuario.
    6 : shell que utiliza.

    Nos interesa en este caso el 3.
    '''
    try:
        info = getpwnam(user)

        return {
            'gid'    : info[3],
        }
    except:
        return False

def user_is_root(user):
    '''
    bool user_is_root(string user)
    Un usuario será considerado root si su GID es 0
    '''
    user_info = get_user_info(user)
    if not user_info or user_info['gid'] != 0:
        return False

    return True

def print_help():
    print '''Maravilloso montador de imágenes de clonezilla.

Uso: %s <archivo_imagen.aa> </directorio/montaje> <formato_particion>
Formatos de particion válidos: vfat, ntfs-3g, ext2, ext3, ext4.

Asegúrate de que el formato de partición es el correcto.
Si existe un archivo de imagen %s se sobreescribirá con el que se vaya a generar.

''' % (EXEC_NAME, MOUNTABLE_IMG_FILE)

def check_needed_packages(needed_packages):
    for package in needed_packages:
        if os.system('dpkg -s %s > /dev/null 2>&1' % package) != 0:
            print 'Error de dependencias: Falta por instalar el paquete %s.' % package
            return False
    return True

def create_img_file(imgfile=None):
    print 'Generando imagen válida...'

    try:
        os.system('cat %s* | gzip -d -c | partclone.restore -C -s - -O %s' % (imgfile[:-2], MOUNTABLE_IMG_FILE))
    except:
        return ERROR_CREATING_MOUNTABLE_IMG

    #mensaje informativo si todo fue bien.
    print '====='
    print 'Proceso de unión de archivos de imagen CloneZilla a archivo .img montable hecho correctamente.'
    print '====='

    #buscar alternativa llamada al sistema which, devolver ruta entera.
    return MOUNTABLE_IMG_FILE

def mount_file_in_dir(partition_format=None, mountable_img=None, mount_dir=None):
    try:
        os.system('mount -o loop -t %s %s %s' % (partition_format, mountable_img, mount_dir))
    except:
        return ERROR_MOUNTING_IMAGE

def clonezilla_img_mounter(imgfile=None, mount_dir=None, partition_format=None):
    '''
    to-do
    Esta parte se puede mejorar
    '''
    mountable_img = create_img_file(imgfile)
    mount_file_in_dir(partition_format, mountable_img, mount_dir)

    print ''
    print 'Resumen de la acción realizada:'
    print 'Imagen de clonezilla a montar: %s' % imgfile
    print 'Imagen generada: %s' % mountable_img
    print 'Directorio dónde se ha montado la imagen: %s' % mount_dir
    print 'Formato de la partición montada: %s'  % partition_format
    print ''
    print 'Recuerda que tendrás que desmontar manualmente el directorio %s.' % mount_dir
    print 'Tampoco olvides eliminar la imagen %s cuando termines de trabajar con ella.' % mountable_img
    print ''

    return OK

def run():
    #solo root o alguien con privilegios puede ejecutarme
    if not user_is_root(os.environ.get('USER')):
        print 'Debe tener privilegios de administrador para ejecutar el script.'
        return UNPRIVILEGED_USER
    #chequeo de dependencias, le pasamos el vector PACKAGE_DEPENDENCIES
    if not check_needed_packages(PACKAGE_DEPENDENCIES):
        return BROKEN_DEPENDENCIES
    #control de argumentos pasados al programa
    if (len(sys.argv) == 4):
        #Argumentos con los que trabajaremos
        image_file = sys.argv[1]
        work_dir = sys.argv[2]
        partition_format = sys.argv[3]
        #comprobación directorio de montaje, existe y está vacio.
        if not ((os.path.exists(work_dir) == True) and ((len(os.listdir(work_dir)) == 0))):
            print 'El directorio donde montaremos la imagen es inválido, asegúrate que existe y que está vacio'
            return BAD_MOUNT_DIR
        #comprobar que no hay imagenes anteriores.
        if os.path.isfile(MOUNTABLE_IMG_FILE):
            print 'El archivo de imagen %s existe, probablemente sea una imagen anterior.' % MOUNTABLE_IMG_FILE
            print 'Deberás borrarla manualmente para poder continuar.'
            return ERROR_CREATING_MOUNTABLE_IMG
        #Comprobación de que el archivo de imagen tiene .aa como extensión y que el tipo de compresión es gzip
        if image_file[-3:] != '.aa' and (getoutput("file -ib %s | awk '{print $1}'" % (image_file)) == 'application/x-gzip;'):
            print 'Archivo de imagen inválido. La imagen deberá ser gzip y su extensión .aa.'
            return BAD_IMAGE_FILE
        #control de formato de partición, deberá ser uno contenido en el diccionario VALID_PARTITION_FORMAT
        if not partition_format in VALID_PARTITION_FORMAT:
            print 'Formato de partición no válido. Particiones soportadas: vfat, ntfs-3g, ext2, ext3, ext4.'
            print 'Asegurate que le das al script el formato de partición correcto.'
            return BAD_PARTITION_FORMAT

        #comprobaciones realizadas, ejecutamos operaciones de conversion y montaje
        return clonezilla_img_mounter(image_file, work_dir, partition_format)
    else:
        print_help()
        return INVALID_PARAMETER_NUMBER

if __name__ == "__main__":
    sys.exit(run())
