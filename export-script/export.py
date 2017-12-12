#! /usr/bin/env python3

import MySQLdb
import os
import shutil
import html
import re
import os.path
import pprint
import sys

def find_project_directory():
    return os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]

def main_english(project_directory):

    print("Working from project directory", project_directory)

    files_directory = os.path.join(project_directory, "files")
    print("Working from files directory", files_directory)

    hugo_content_directory = os.path.join(project_directory, "healthcouncil", "content")

    print("Deleting content from content directory ", hugo_content_directory ," ...")
    shutil.rmtree(hugo_content_directory)
    os.mkdir(hugo_content_directory)
    print("Done!")

    print("Create _index.html file for homepage frontmatter...")
    with open(os.path.join(hugo_content_directory, "_index.html"), "w") as index_file:
        content = ["+++",
                   "title = \"Home\"",
                   "+++"]
        index_file.writelines([x+"\n" for x in content])
    print("Done!")

    print("Connecting to Database...")
    hcc_db = MySQLdb.connect(user='hcc', db='hcc', passwd='Lq6jg9XyrcCUrN1ZFpUKSmM3YmW0vR4rrHfMo9Pg')
    print("Done!")

    all_files = []
    processed_files = []
    fixed = []
    for root, dirnames, filenames in os.walk(files_directory):
        for filename in filenames:
            if os.path.basename(root) == "files":
                all_files.append(filename)
            else:
                all_files.append(os.path.basename(root)+"/"+filename)

    hcc_c = hcc_db.cursor(MySQLdb.cursors.DictCursor)
    hcc_c.execute("""   SELECT GROUP_CONCAT(mnu_main_1.mnu1) as mnu1, hcc_files.id, COALESCE(hcc_file_typ,"Uncategorized") as hcc_file_typ, dte, rpttitle, keywords, file, youtube, hcc_files.filettle
                        FROM hcc_files LEFT JOIN hcc_files_types ON hcc_files_types.id = hcc_files.typid
                        LEFT JOIN hcc_files_rel ON hcc_files_rel.fileid = hcc_files.id 
                        LEFT JOIN mnu_main_1 ON hcc_files_rel.mnu1id =  mnu_main_1.id
                        GROUP BY hcc_files.id""")

    print("Output content markdown...")
    for row in hcc_c:
        filename = os.path.join(hugo_content_directory, "{}.md".format(row['id']))
        themes_fixed = None
        if row['mnu1']:
            themes_fixed = ",".join((set(["\""+x+"\"" for x in row['mnu1'].split(",")])))

        with open(filename, "w") as out:
            if row['rpttitle']:
                title = row['rpttitle'].strip().strip().replace("\r\n", " ").replace("\"", "\\\"") \
                        .replace("<br />", " ") \
                        .replace("<Br />", " ") \
                        .replace("<Br>", " ") \
                        .replace("<br>", " ") \
                        .replace("Canadaâ\x80\x99", "Canada'") \
                        .replace("St. Johnâ\x80\x99", "St. John'") \
                        .replace(" \xe2\x80\x93 ", " - ") \
                        .replace("s\xe2\x80\x99", "s'") \
                        .replace("People\xe2\x80\x99", "People'") \
                        .replace("M\xc3\xa9tis", "Métis") \
                        .replace("Methodology\xe2\x84\xa2 -", "Methodology -") \
                        .replace("Health Care Renewal Matters\xe2\x80\xa6", "Health Care Renewal Matters...") \
                        .replace("Commissaire \xc3\xa0 la sant\xc3\xa9 et au bien-\xc3\xaatre du Qu\xc3\xa9bec", "Commissaire à la santé et au bien-être du Québec") \
                        .replace("\xc2", "") \
                        .replace("What is th best way forward", "What is the best way forward")
                title = re.sub(r":([A-Za-z])", ": \g<1>", title)
                title = html.unescape(title)
                title = title.title() \
                        .replace("'S", "'s") \
                        .replace("'L", "'l") \
                        .replace("De La", "de la") \
                        .replace("Pen: ", "PEN: ") \
                        .replace("I'M", "I'm") \
                        .replace("We'Re", " We're") \
                        .replace("Hcc", "HCC") \
                        .replace("Cma", "CMA") \
                        .replace("Prisma", "PRISMA") \
                        .replace("Ceo", "CEO") \
                        .replace("Opha", "OPHA") \
                        .replace("Cpgs", "CPGs") \
                        .replace("Mcmaster", "McMaster") \
                        .replace("Unama'Ki", "Unama'ki") \
                        .replace("Saint John, Nb", "Saint John, NB") \
                        .replace(", Bc", ", BC") \
                        .replace("Pei", "PEI") \
                        .replace("Commissaire À La Santé Et Au Bien-Être Du Québec", "Commissaire à la santé et au bien-être du Québec") \
                        .replace("Econsultation", "eConsultation") \
                        .replace("EConsultation", "eConsultation")
            out.write("+++\n")
            if row['rpttitle']:
                out.write("title = \"{}\"\n".format(title))
            if row['dte']:
                out.write("date = {}\n".format(row['dte'].isoformat()))
            if themes_fixed:
                out.write("themes = [{}]\n".format(themes_fixed))
            out.write("types = [\"{}\"]\n".format(row['hcc_file_typ']))
            out.write("+++\n")

            if row['file'] in all_files:
                out.write("[{file}](/files/{file})\n".format(file=row['file']))

            if row['id'] == 320:
                out.write("[Published as publication \"Press Release: Canadians Visiting Emergency Departments For Care, Instead Of Seeing Primary Health Care Providers\".](/publications/205/)\n")
                fixed.append(row['id'])

            if row['id'] == 284:
                out.write("[{file}](/files/full/{file})\n".format(file=row['file']))
                fixed.append(row['id'])

            if row['id'] == 780:
                out.write("[{file}](/files/full/{file})\n".format(file="780-TheSaskatchewanSurgicalInitiative.mp4"))
                fixed.append(row['id'])

            if row['youtube']:
                m = re.match(r".+//www.youtube.com/embed/(.{11})", row['youtube'])
                if m:
                    out.write("\n[YouTube Link](https://www.youtube.com/watch?v={})\n".format(m.group(1)))
                else:
                    print("PROBLEM HERE")
                    print(row['youtube'])

            if row['file'] in all_files:
                all_files.remove(row['file'])
                processed_files.append(row['file'])
            elif row['file'] not in processed_files and row['id'] not in fixed:
                print(row)

    print("Unlinked Files:")
    pprint.pprint(all_files)

if __name__ == "__main__":
    project_directory =  find_project_directory()
    main_english(project_directory)
