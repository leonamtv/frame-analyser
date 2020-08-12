import os
import cv2
import math
import shutil
import argparse

import numpy as np
import regex as re
import matplotlib.pyplot as plt

from sys import argv
from PIL import Image
from functools import cmp_to_key
from colorthief import ColorThief

img_dump_path = './tmp'
output_path   = './output'

reg = r"(?<=frame)([0-9]+)(?=\.png)"

def sorting_function ( a, b ):
    an, bn = int(re.search(reg, a).group(0)), int(re.search(reg, b).group(0))
    return an - bn

def analyse_video ( video_path, 
                    frame_pace=1, 
                    num_dom_color=8, 
                    clean_tmp=True, 
                    skip_saving=False, 
                    skip_beginning=0, 
                    skip_end=0,
                    generate_html=True,
                    visualize_image=False ):

    name   = os.path.basename(video_path).split('.')[0]

    if not os.path.isfile(video_path):
        raise Exception("Caminho não corresponde a um arquivo")
    
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened(): 
        print("Não foi possível abrir o vídeo.")
    else:
        length = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        fps    = int(cap.get(cv2.CAP_PROP_FPS))

        print ( '> Total de frames.: %d' % length )
        print ( '> Altura do frame.: %d' % height )
        print ( '> Largura do frame: %d' % width )
        print ( '> Framerate.......: %d' % fps )

        if not skip_saving:
            if skip_end < length:
                length -= skip_end

            current_frame = skip_beginning if skip_beginning >= 0 and skip_beginning < length else 0
            success, frame = cap.read()
            
            if not os.path.isdir ( os.path.join ( img_dump_path, name )):
                os.makedirs ( os.path.join ( img_dump_path, name ))

            while current_frame < length and success :
                cap.set ( 1, current_frame )
                if not cv2.imwrite( os.path.join ( img_dump_path, name, 'frame%d.png' % current_frame ), frame ):
                    raise Exception("Não foi possível escrever a imagem")
                success, frame = cap.read()
                current_frame += frame_pace

            print('> Arquivos de frames salvos...')

        cap.release()

    if generate_html:    
        html  = "<html><body><title>Movie Palette</title>"
        html += "<link rel='stylesheet' type='text/css' href='./style.css'><table><tr>"

        for i in range(1, num_dom_color):
            html += "<th>" + str(i) + "ª MCC</th>"

        html += '</tr>'

        for file in sorted(os.listdir(os.path.join ( img_dump_path, name )), key=cmp_to_key(sorting_function)):
            colortf = ColorThief(os.path.join( img_dump_path, name, file))
            dominant = colortf.get_palette(color_count=num_dom_color)
            
            title = re.search(reg, file)
            
            html += "<tr><td class='title'>" + title.group(0) + '</td>'
            for color in dominant:
                style = "'background-color:rgb(%d, %d, %d)'" % color
                html += "<td style=" + style + "></td>"
            html += '</tr>'

        html += '</table></body></html>'

        if not os.path.isdir ( os.path.join ( output_path, name )):
            os.makedirs ( os.path.join ( output_path, name ))

        file = open(os.path.join( output_path, name , 'index.html' ),'w')
        file.write(html)
        file.close()

    if visualize_image:
        d = math.ceil(math.sqrt(( length - skip_beginning - skip_end ) / frame_pace ))
        data = np.zeros(( d, d, 3 ), dtype=np.uint8)
        counter = 0
        for i, file in enumerate(sorted(os.listdir(os.path.join ( img_dump_path, name )), key=cmp_to_key(sorting_function))):
            colortf = ColorThief(os.path.join( img_dump_path, name, file))
            dominant = colortf.get_palette(color_count=num_dom_color)
            r, g, b = 0, 0, 0
            for color in dominant:
                r += color[0]
                g += color[1]
                b += color[2]
            r /= ( num_dom_color - 1 )
            g /= ( num_dom_color - 1 )
            b /= ( num_dom_color - 1 )
            data[( counter - ( counter % d )) // d ][ counter % d ] = [ r, g, b ]
            counter += 1
        img = Image.fromarray(data, 'RGB')
        plt.imshow(img)
        img.save(os.path.join(output_path, name, 'img.png'))
        # img.show()

    if clean_tmp:
        shutil.rmtree(os.path.join ( img_dump_path, name ))

def main () :
    parser = argparse.ArgumentParser(description='Video Color Analyser.', add_help=False)
    parser.add_argument('-p', '--path', nargs=1, action='store', help='Caminho do arquivo do vídeo')
    parser.add_argument('-f', '--frame-pace', nargs=1, action='store', help='Número de frames para pular')
    parser.add_argument('-n', '--num-cor-dom', nargs=1, action='store', help='Número de cores dominantes')
    parser.add_argument('-sb', '--skip-beginning', nargs=1, action='store', help='Número de pixels a ignorar no início')
    parser.add_argument('-se', '--skip-end', nargs=1, action='store', help='Número de pixels a ignorar no final')
    parser.add_argument('-c', '--clean-files', action='store_true', help='Limpar os frames do disco após processar')
    parser.add_argument('-s', '--skip-saving', action='store_true', help='Skip saving images')
    parser.add_argument('-vi', '--visualize-img', action='store_true', help='Visualize image')
    
    args = parser.parse_args()

    frame_pace = 1
    num_dom_color = 8
    clean_tmp = False
    skip_saving = False
    skip_beginning = 0
    skip_end = 0
    visualize_image = False
    generate_html = True

    if not args.path:
        print('Você deve fornecer um caminho para um vídeo')
        return

    if args.clean_files :
        clean_tmp = True

    if args.frame_pace:
        frame_pace = int(args.frame_pace[0])
    
    if args.num_cor_dom:
        num_dom_color = int(args.num_cor_dom[0])

    if args.skip_saving:
        skip_saving = args.skip_saving

    if args.skip_beginning:
        skip_beginning = int(args.skip_beginning)

    if args.skip_end:
        skip_end = int(args.skip_end)

    if args.visualize_img:
        visualize_image = True    

    analyse_video ( args.path[0], 
                    frame_pace, 
                    num_dom_color, 
                    clean_tmp, 
                    skip_saving, 
                    skip_beginning, 
                    skip_end, 
                    generate_html, 
                    visualize_image )

if __name__ == "__main__":
    main()
