#! /usr/bin/env python3

import MySQLdb
import os
import shutil
import html
import re
import os.path
import pprint
import sys
import pdb

def find_project_directory():
    return os.path.split(os.path.abspath(os.path.dirname(sys.argv[0])))[0]

def find_all_files(files_directory):

    all_files = set([])
    for root, dirnames, filenames in os.walk(files_directory):
        for filename in filenames:
            if os.path.basename(root) == "files":
                all_files.add(filename)
            else:
                all_files.add(os.path.basename(root)+"/"+filename)

    return all_files

def main_english(project_directory, all_files):

    print("---English Processing---")

    print("Working from project directory", project_directory)

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

    processed_files = set([])

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
            themes = set(row['mnu1'].split(","))
            themes = sorted(themes)
            themes_fixed = ",".join(["\""+x+"\"" for x in themes])

        with open(filename, "w") as out:
            if row['rpttitle']:
                title = row['rpttitle'].strip().replace("\r\n", " ").replace("\"", "\\\"").title() \
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
                        .replace("M\xc9T", "Mét") \
                        .replace("Methodology\xe2\x84\xa2 -", "Methodology -") \
                        .replace("Health Care Renewal Matters\xe2\x80\xa6", "Health Care Renewal Matters...") \
                        .replace("Commissaire \xc3\xa0 la sant\xc3\xa9 et au bien-\xc3\xaatre du Qu\xc3\xa9bec", "Commissaire à la santé et au bien-être du Québec") \
                        .replace("\xc2", "") \
                        .replace("What Is Th Best Way Forward", "What Is The Best Way Forward") \
                        .replace("'S", "'s") \
                        .replace("'L", "'l") \
                        .replace("De La", "de la") \
                        .replace("Pen:", "PEN:") \
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
                print(title.encode('unicode-escape'))
                title = re.sub(r":([A-Za-z])", ": \g<1>", title)
                title = html.unescape(title)

            out.write("+++\n")
            if row['rpttitle']:
                out.write("title = \"{}\"\n".format(title))
            if row['dte']:
                out.write("date = {}\n".format(row['dte'].isoformat()))
            if themes_fixed:
                out.write("themes = [{}]\n".format(themes_fixed))
            out.write("types = [\"{}\"]\n".format(row['hcc_file_typ']))
            out.write("+++\n")

            processed_files.add(row['file'])

            if row['file'] in all_files:
                out.write("[{file}](/files/{file})\n".format(file=row['file']))
            elif row['id'] == 320:
                out.write("[Published as publication \"Press Release: Canadians Visiting Emergency Departments For Care, Instead Of Seeing Primary Health Care Providers\".](/publications/205/)\n")
            elif row['id'] == 284:
                out.write("[{file}](/files/full/{file})\n".format(file=row['file']))
            elif row['id'] == 780:
                out.write("[{file}](/files/full/{file})\n".format(file="780-TheSaskatchewanSurgicalInitiative.mp4"))
            else:
                processed_files.remove(row['file'])
                print("Missing file", row['file'])
                print(row)

            if row['youtube']:
                m = re.match(r".+//www.youtube.com/embed/(.{11})", row['youtube'])
                if m:
                    out.write("\n[YouTube Link](https://www.youtube.com/watch?v={})\n".format(m.group(1)))
                else:
                    print("PROBLEM HERE")
                    print(row['youtube'])

    return processed_files

def main_french(project_directory, all_files):

    print("---French Processing---")

    print("Working from project directory", project_directory)

    hugo_content_directory = os.path.join(project_directory, "conseilcanadiendelasante", "content")

    print("Deleting content from content directory ", hugo_content_directory ," ...")
    shutil.rmtree(hugo_content_directory)
    os.mkdir(hugo_content_directory)
    print("Done!")

    print("Create _index.html file for homepage frontmatter...")
    with open(os.path.join(hugo_content_directory, "_index.html"), "w") as index_file:
        content = ["+++",
                   "title = \"Page d'accueil\"",
                   "+++"]
        index_file.writelines([x+"\n" for x in content])
    print("Done!")

    print("Connecting to Database...")
    hcc_db = MySQLdb.connect(user='hcc', db='hcc_fr', passwd='Lq6jg9XyrcCUrN1ZFpUKSmM3YmW0vR4rrHfMo9Pg')
    print("Done!")

    processed_files = set([])

    hcc_c = hcc_db.cursor(MySQLdb.cursors.DictCursor)
    hcc_c.execute("""   SELECT GROUP_CONCAT(mnu_main_1.mnu1) as mnu1, hcc_files.id, COALESCE(hcc_file_typ,"Non classé") as hcc_file_typ, dte, rpttitle, keywords, file, youtube, hcc_files.filettle
                        FROM hcc_files LEFT JOIN hcc_files_types ON hcc_files_types.id = hcc_files.typid
                        LEFT JOIN hcc_files_rel ON hcc_files_rel.fileid = hcc_files.id 
                        LEFT JOIN mnu_main_1 ON hcc_files_rel.mnu1id =  mnu_main_1.id
                        GROUP BY hcc_files.id""")

    print("Output content markdown...")
    for row in hcc_c:
        filename = os.path.join(hugo_content_directory, "{}.md".format(row['id']))
        themes_fixed = None
        if row['mnu1']:
            themes = set(row['mnu1'].split(","))
            themes = sorted(themes)
            themes_fixed = ",".join(["\""+x+"\"" for x in themes])
            themes_fixed = html.unescape(themes_fixed)
            themes_fixed = themes_fixed.replace("santÃ©", "santé") \
                           .replace("SantÃ©", "Santé") \
                           .replace("AccÃ¨s", "Accès") \
                           .replace("Ã\x89tat de santé et rÃ©sultats de santé", "État de santé et résultats de santé") \
                           .replace("Ã©lectroniques", "électroniques") \
                           .replace("Soins Ã\xa0", "Soins à")

        type_fixed = html.unescape(row['hcc_file_typ'])
        with open(filename, "w") as out:
            if row['rpttitle']:
                title = row['rpttitle'].strip().replace("\r\n", " ").replace("\"", "\\\"") \
                        .replace("<br />", " ") \
                        .replace("<Br />", " ") \
                        .replace("<Br>", " ") \
                        .replace("<br>", " ") \
                        .replace("Canadaâ\x80\x99", "Canada'") \
                        .replace("St. Johnâ\x80\x99", "St. John'") \
                        .replace(" \xe2\x80\x93 ", " - ") \
                        .replace("s\xe2\x80\x99", "s'") \
                        .replace("M\xc3\xa9tis", "Métis") \
                        .replace("Commissaire \xc3\xa0 la sant\xc3\xa9 et au bien-\xc3\xaatre du Qu\xc3\xa9bec", "Commissaire à la santé et au bien-être du Québec") \
                        .replace("\xc2", "") \
                        .replace("d\\'information", "d'information") \
                        .replace("l\\'opinion", "l'opinion") \
                        .replace("qualit&eacute;&eacute;", "qualit&eacute;") \
                        .replace("dÃ©part", "départ") \
                        .replace("santÃ©","santé") \
                        .replace("SantÃ©","Santé") \
                        .replace("Ã\xa0", "à") \
                        .replace("rÃ©forme", "réforme") \
                        .replace("systÃ¨me", "système") \
                        .replace("axÃ©s", "axés") \
                        .replace("rÃ©gions", "région") \
                        .replace("Ã©loignÃ©es", "éloignée") \
                        .replace("prÃ©vention", "prévention") \
                        .replace("lâ\x80\x99innovation", "l'innovation") \
                        .replace("lâ\x80\x99action", "l'action") \
                        .replace("matiÃ¨re", "matiére") \
                        .replace("AmÃ©lioration", "Amélioration") \
                        .replace("qualitÃ©", "qualité") \
                        .replace("sÃ©curitÃ©", "sécurité") \
                        .replace("AccÃ¨s", "Accès") \
                        .replace("accÃ¨s", "accès") \
                        .replace("dâ\x80\x99attente", "d'attente") \
                        .replace("Ã¢gÃ©es", "âgées") \
                        .replace("vuln\xc3\xa9rables", "vulnérables") \
                        .replace("lâ\x80\x99amÃ©lioration", "l'amélioration") \
                        .replace("lâ\x80\x99approche", "l'approche") \
                        .replace("lâ\x80\x99Economic", "l'Economic") \
                        .replace("nâ\x80\x99avancent", "n'avancent") \
                        .replace("stratÃ©giques", "stratégiques") \
                        .replace("Ã\x89valuation", "Évaluation") \
                        .replace("dÃ©cennie", "décennie") \
                        .replace("Ã©chec", "échec") \
                        .replace("vidÃ©os", "vidéos") \
                        .replace("sÃ©rie", "série") \
                        .replace("CommuniquÃ©", "Communiqués") \
                        .replace("mÃªme", "même") 

                title = re.sub(r":([A-Za-z])", ": \g<1>", title)
                title = html.unescape(title)

            out.write("+++\n")
            if row['rpttitle']:
                out.write("title = \"{}\"\n".format(title))
            if row['dte']:
                out.write("date = {}\n".format(row['dte'].isoformat()))
            if themes_fixed:
                out.write("themes = [{}]\n".format(themes_fixed))
            out.write("types = [\"{}\"]\n".format(type_fixed))
            out.write("+++\n")

            processed_files.add(row['file'])

            if row['file'] in all_files:
                out.write("[{file}](/files/{file})\n".format(file=row['file']))
            else:
                processed_files.remove(row['file'])
                print("Missing file", row['file'])
                print(row)

            if row['youtube']:
                m = re.match(r".+//www.youtube.com/embed/(.{11})", row['youtube'])
                if m:
                    out.write("\n[YouTube](https://www.youtube.com/watch?v={})\n".format(m.group(1)))
                else:
                    print("PROBLEM HERE")
                    print(row['youtube'])

    return processed_files

if __name__ == "__main__":
    project_directory =  find_project_directory()
    files_directory = os.path.join(project_directory, "files")
    print("Working from files directory", files_directory)
    all_files = find_all_files(files_directory)
    english_files = main_english(project_directory, all_files)
    french_files = main_french(project_directory, all_files)

    remaining_files = (all_files - english_files) - french_files

    print("Unlinked files:")
    for file in remaining_files:
        print(file)
