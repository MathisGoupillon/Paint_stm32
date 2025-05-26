import serial
import time
import struct

def read_pixel_line(ser, line_length):
    """
    Lit une ligne de 'line_length' pixels sur le port série déjà ouvert 'ser'.
    Retourne une liste d’entiers 0xRRGGBB, ou None si la ligne est incomplète.
    """
    raw = ser.readline().decode('ascii', errors='ignore').strip()
    parts = raw.split()
    if len(parts) != line_length:
        print(f"⚠️ Ligne reçue : {len(parts)}/{line_length} valeurs")
        return None
    return [int(p, 16) for p in parts]

def write_bmp_line(f, pixel_offset, row_index, pixels, width):
    """
    Écrit une seule ligne de pixels dans le BMP déjà ouvert 'f'.
    'pixel_offset' est l’offset de début des données pixel.
    'row_index' est l’indice de la ligne dans le fichier (0 = première ligne stockée = bas de l’image).
    'pixels' est la liste des valeurs 0xRRGGBB.
    """
    # chaque ligne BMP stocke width pixels ×3 octets + padding pour aligner sur 4‑octets
    row_size = width * 3
    pad = (4 - (row_size % 4)) % 4

    # calculer où écrire cette ligne
    offset = pixel_offset + row_index * (row_size + pad)
    f.seek(offset)

    # écrire les pixels en BGR
    for val in pixels:
        r = (val >> 16) & 0xFF
        g = (val >> 8)  & 0xFF
        b = val & 0xFF
        f.write(bytes((b, g, r)))
    # remplir le padding
    if pad:
        f.write(b'\x00' * pad)

if __name__ == "__main__":
    port   = "COM7"     # adapter si besoin
    baud   = 115200
    width  = 480
    height = 272
    bmp_path = "c:/Users/33779/Desktop/fichier_base_paintMathis.bmp"

    # 1) Ouvrir port série et fichier BMP
    ser = serial.Serial(port, baud, timeout=1.0)
    f   = open(bmp_path, 'r+b')

    # 2) lire l’offset des données pixel depuis l’en‑tête BMP
    f.seek(10)
    pixel_offset = struct.unpack('<I', f.read(4))[0]
    print(f"Pixel data offset = {pixel_offset}")

    # 3) Pour chaque ligne envoyée par le STM32 (envoi bottom→top)
    for row in range(height):
        # lire jusqu’à obtenir une ligne complète
        while True:
            line = read_pixel_line(ser, width)
            if line is not None:
                break
        # row=0 correspond à la première ligne reçue = bottom of BMP
        write_bmp_line(f, pixel_offset, row, line, width)
        print(f"Ligne {row+1}/{height} écrite dans BMP")

    # 4) fermer tout
    f.close()
    ser.close()
    print("Terminé — image complète mise à jour dans le BMP.")
