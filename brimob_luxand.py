#!/usr/bin/env python
from __future__ import print_function # for compatability with Python 2.x
import sys, math, os.path, base64, pathlib
from luxand.fsdk import FSDK
from os import environ, path
from dotenv import load_dotenv
import mysql.connector as mysql
from os.path import exists
import PIL
from PIL import ImageDraw, ImageFont
import time




internal_resize_width = 384
internal_resize_width_array = [50,200,384,512,2000]
max_internal_resize_width = max(internal_resize_width_array)
face_detection_threshold = 5

class Brimob_Luxand:

    def __init__(self):
        print("Initializing FSDK... ", end='')
        basedir = path.abspath(path.dirname(__file__))
        load_dotenv(path.join(basedir, '.env'))
        license_key = environ.get('license_key')
        FSDK.ActivateLibrary(license_key);
        FSDK.Initialize()

    def test(self):
        print("tesT")
        return "test dari brimob luxand"


    def find_match_portrait(self,db_filename, haystacks, portraits, confidence, rotation, rotation_angle, resize, face):
        print("Find match portrait .........")
        output = dict()
        rotation_angle_bool = False
        rotation_bool = False
        try:  # read all photo from database
            with open(db_filename) as db:
                base = dict(l.rsplit(' ', 1) for l in db if l)
        except FileNotFoundError:
            print('\nCannot open', db_filename, 'database file.\nUse "-a" option to create database.');
            exit(1)
        #
        def draw_features(f,draw,n,percent, color):
            def dot_center(dots):  # calc geometric center of dots
                return sum(p.x for p in dots) / len(dots), sum(p.y for p in dots) / len(dots)

            xl, yl = dot_center([f[k] for k in FSDK.FSDKP_LEFT_EYE_SET])
            xr, yr = dot_center([f[k] for k in FSDK.FSDKP_RIGHT_EYE_SET])
            w = (xr - xl) * 2.8
            h = w * 1.4
            center = (xr + xl) / 2, (yr + yl) / 2 + w * 0.05
            angle = math.atan2(yr - yl, xr - xl) * 180 / math.pi
            frame = -w / 2, -h / 2, w / 2, h / 2
            # container = graph.beginContainer()
            # graph.translateTransform(*center).rotateTransform(angle).ellipse(facePen, *frame)  # draw frame
            # graph.endContainer(container)
            draw.rectangle((xl-w/2, yl-h/2, xl+w, yr+h*0.8), fill=None, outline=color, width=4)
            # specified font size
            font = ImageFont.truetype(r'C:\Users\System-Pc\Desktop\arial.ttf', 12)
            texttodisplay = os.path.splitext(os.path.basename(n))[0] + "("+percent+"%)"
            # draw.text((xl-w/2 + 10, yl-h/2 + 10), texttodisplay, font=font,fill=(255,0,0,255))
            # print(xl, yl, xr, yr)
            # for p in f: graph.circle(featurePen, p.x, p.y, 3)  # draw features
        #
        matches = []
        portraitcolor = dict()
        output['matches'] = []
        outpath = ''
        for portrait in portraits:
            portraitcolor[portrait['img']] = portrait['color']

        if str(rotation).lower() == "true":
            rotation_bool = True
        if str(rotation_angle).lower() == "true":
            rotation_angle_bool = True
        print("portrait color")
        print(portraitcolor)
        for haystack in haystacks:
            haystack_path = os.path.normcase(os.path.abspath(environ.get('UPLOAD_HAYSTACK') + haystack['img']))
            ts = time.time()

            timestamp = os.path.splitext(str(ts))[0]
            if os.path.exists(haystack_path):
                print("inside if")
                # FSDK.get_all_fsdk_exceptions()
                img = FSDK.Image(haystack_path)
                im = PIL.Image.open(haystack_path)
                print("-")
                print(haystack_path)
                print("--")
                draw = ImageDraw.Draw(im)
                FSDK.SetFaceDetectionParameters(rotation_bool, rotation_angle_bool, resize)

                faces = img.DetectMultipleFaces()

                print("FACES : .......")
                print(len(faces))
                temp_array = []
                temp_dict = dict()
                temp_portrait = dict()
                temp_match = []
                for p in faces:
                    template = img.GetFaceTemplate(p)
                    src = ((n, FSDK.FaceTemplate(*base64.b64decode(ft))) for n, ft in base.items())
                    for n, ft in src:
                        color = portraitcolor[os.path.basename(n)]
                        percent = template.Match(ft) * 100
                        print(n + " >> " + str(percent))
                        if percent > confidence:
                            temp2_dict = dict()
                            print(os.path.basename(n) + " -----> " + str(percent))
                            draw_features(img.DetectFacialFeatures(p), draw, n, str(math.floor(percent)), color)
                            # temp_dict[os.path.basename(n)] = str(percent)
                            string_to_split = os.path.basename(n)
                            temp2_dict["portrait"] = os.path.basename(n)
                            temp2_dict["color"] = color
                            temp2_dict["original"] = "original-" + string_to_split.split("-")[1]
                            temp2_dict["match_percentage"] = str(percent)
                            print(temp2_dict)
                            temp_match.append(temp2_dict)

                temp_dict["haystack"] = haystack['img']
                temp_dict["match_found"] = temp_match
                print("+++++++++++++++")
                print(temp_match)
                output_path = os.path.join(environ.get('OUTPUT_FOLDER') + 'output-' + os.path.splitext(haystack['img'])[0] + '-' + timestamp + ".jpg")
                outpath = os.path.basename(output_path)
                temp_dict['output_file'] = outpath
                matches.append(temp_dict)
                # matches[] = temp_dict


                # draw_features(img.DetectFacialFeatures(p), draw)
                im.save(output_path, quality=95)
                print(output_path)
            else:
                print("not exist")
        output['result'] = matches
        # output['output_file'] = outpath
        db.close()

        return output


    def populate_portrait_db(self,db_filename, needles):
        print("Populating DB .........")
        ### DIBAWAH INI KALAU DIBKIN 2000 jadi hanya bisa jalan seklai
        FSDK.SetFaceDetectionParameters(True, False, 384)  # HandleArbitraryRotations, DetermineFaceRotationAngle, InternalResizeWidthTrue 384 or 512 value
        FSDK.SetFaceDetectionThreshold(face_detection_threshold)
        with open(db_filename, 'a+') as db:
            for needle in needles:
                portrait_path = os.path.normcase(os.path.abspath(environ.get('UPLOAD_PORTRAIT') + needle['img']))
                print(portrait_path)
                if os.path.exists(portrait_path):
                    face_template = FSDK.Image(portrait_path).GetFaceTemplate()  # get template of detected face
                    print("Populating DB - portrait path.........")
                    ft = base64.b64encode(face_template).decode('utf-8')
                    print(portrait_path, ft, file=db)
                    print(os.path.basename(portrait_path), 'is added to the database.')
                else :
                    print("not exist")

        # exit(1)
        db.close()
        return "image mtch result"




    def create_portrait(filepath, outpath):
        basedir = path.abspath(path.dirname(__file__))
        load_dotenv(path.join(basedir, '.env'))
        license_key = environ.get('license_key')

        print("Initializing FSDK... ", end='')
        FSDK.ActivateLibrary(license_key);
        FSDK.Initialize()
        print("OK\nLicense info:", FSDK.GetLicenseInfo())

        print("\nLoading file", filepath , "...")
        file_exists = exists(filepath)
        if file_exists:
            print("EXISTS")
        else:
            print("NO FILE")

        img = FSDK.Image(filepath)  # create image from file

        FSDK.SetFaceDetectionThreshold(face_detection_threshold) #1 - 5. low get more false psotives

        print("Detecting face...")
        FSDK.SetFaceDetectionParameters(True, False,2000)  # HandleArbitraryRotations, DetermineFaceRotationAngle, InternalResizeWidth
        try:
            face = img.DetectFace()  # detect face in the image
        except:
            return 0
        # for w in internal_resize_width_array:
        #     print(w)
        #     FSDK.SetFaceDetectionParameters(True, False,w)  # HandleArbitraryRotations, DetermineFaceRotationAngle, InternalResizeWidth
        #     try:
        #         face = img.DetectFace()  # detect face in the image
        #         break
        #     except:
        #         if w >= max_internal_resize_width:
        #             return 0



        maxWidth, maxHeight = 337, 450
        img = img.Crop(*face.rect).Resize(max((maxWidth + 0.4) / (face.w + 1),
                                              (maxHeight + 0.4) / (face.w + 1)))  # crop and resize face image inplace
        img.SaveToFile(outpath, quality=100)  # save face image to file with given compression quality

        print("File '%s' with detected face is created." % outpath)
        return 1


    def create_portrait_test(file):
        print("inside create portrait")
        basedir = path.abspath(path.dirname(__file__))
        load_dotenv(path.join(basedir, '.env'))
        license_key = environ.get('license_key')

        if len(sys.argv) < 2:
            print("Usage: portrait.py <in_file> [out_file]")  # default out_file name is 'face.in_file'
            exit(-1)

        inputFileName, outFileName = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'face.' + sys.argv[1]

        print("Initializing FSDK... ", end='')
        FSDK.ActivateLibrary(license_key);
        FSDK.Initialize()
        print("OK\nLicense info:", FSDK.GetLicenseInfo())

        print("\nLoading file", inputFileName, "...")
        img = FSDK.Image(inputFileName)  # create image from file

        FSDK.SetFaceDetectionThreshold(face_detection_threshold)
        FSDK.SetFaceDetectionParameters(True, False,2000)  # HandleArbitraryRotations, DetermineFaceRotationAngle, InternalResizeWidth
        try:
            face = img.DetectFace()  # detect face in the image
        except:
            return 0

        # for w in internal_resize_width_array:
        #     print(w)
        #     FSDK.SetFaceDetectionParameters(True, False,w)  # HandleArbitraryRotations, DetermineFaceRotationAngle, InternalResizeWidth
        #     try:
        #         face = img.DetectFace()  # detect face in the image
        #         break
        #     except:
        #         if w >= max_internal_resize_width:
        #             return 0

        maxWidth, maxHeight = 337, 450
        img = img.Crop(*face.rect).Resize(max((maxWidth + 0.4) / (face.w + 1),
                                              (maxHeight + 0.4) / (face.w + 1)))  # crop and resize face image inplace
        img.SaveToFile(outFileName, quality=85)  # save face image to file with given compression quality

        print("File '%s' with detected face is created." % outFileName)
        return "success"