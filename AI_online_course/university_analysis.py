import sqlite3
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

DB = '/home/claude/university.db'

RED   = '#D90012'
BLUE  = '#0033A0'
GOLD  = '#F2A900'
DARK_BG        = '#0F1117'
CARD_BG        = '#1A1D27'
TEXT_MAIN      = '#EAEAEA'
TEXT_SUB       = '#9099B0'
GRID_LINE      = '#2A2D3A'
GREEN          = '#2ECC71'
PURPLE         = '#9B59B6'

PALETTE = [RED, BLUE, GOLD, GREEN, PURPLE,
           '#E67E22', '#1ABC9C', '#E74C3C', '#3498DB', '#F39C12']

plt.rcParams.update({
    'figure.facecolor':  DARK_BG,
    'axes.facecolor':    CARD_BG,
    'axes.edgecolor':    GRID_LINE,
    'axes.labelcolor':   TEXT_MAIN,
    'axes.titlecolor':   TEXT_MAIN,
    'xtick.color':       TEXT_SUB,
    'ytick.color':       TEXT_SUB,
    'text.color':        TEXT_MAIN,
    'grid.color':        GRID_LINE,
    'grid.alpha':        0.5,
    'font.family':       'DejaVu Sans',
    'axes.spines.top':   False,
    'axes.spines.right': False,
    'legend.facecolor':  CARD_BG,
    'legend.edgecolor':  GRID_LINE,
    'legend.labelcolor': TEXT_MAIN,
})


def get_conn():
    return sqlite3.connect(DB)


def build_database():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS departments (
        department_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        department_name TEXT NOT NULL,
        department_code TEXT UNIQUE NOT NULL,
        head_of_department TEXT,
        established_year INTEGER,
        building TEXT,
        budget REAL
    );
    CREATE TABLE IF NOT EXISTS programs (
        program_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        program_name TEXT NOT NULL,
        program_code TEXT UNIQUE NOT NULL,
        department_id INTEGER REFERENCES departments(department_id),
        degree_level TEXT,
        duration_years INTEGER,
        total_credits_required INTEGER,
        is_active INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS instructors (
        instructor_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name  TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        department_id INTEGER REFERENCES departments(department_id),
        title TEXT,
        hire_date TEXT,
        office_location TEXT,
        phone TEXT,
        specialization TEXT
    );
    CREATE TABLE IF NOT EXISTS students (
        student_id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name  TEXT NOT NULL,
        date_of_birth TEXT,
        gender TEXT,
        email TEXT UNIQUE NOT NULL,
        phone TEXT,
        address TEXT,
        city TEXT,
        enrollment_date TEXT NOT NULL,
        expected_graduation TEXT,
        program_id INTEGER REFERENCES programs(program_id),
        advisor_id INTEGER REFERENCES instructors(instructor_id),
        status TEXT DEFAULT 'Active',
        gpa REAL,
        total_credits_earned INTEGER DEFAULT 0,
        scholarship_amount REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS courses (
        course_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        course_code TEXT UNIQUE NOT NULL,
        course_name TEXT NOT NULL,
        department_id INTEGER REFERENCES departments(department_id),
        credits INTEGER NOT NULL,
        course_level INTEGER,
        description TEXT,
        max_enrollment INTEGER DEFAULT 30,
        is_active INTEGER DEFAULT 1,
        prerequisite_course_id INTEGER REFERENCES courses(course_id)
    );
    CREATE TABLE IF NOT EXISTS semesters (
        semester_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        semester_name TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date   TEXT NOT NULL,
        registration_deadline TEXT,
        withdrawal_deadline   TEXT,
        is_current INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS course_sections (
        section_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id     INTEGER REFERENCES courses(course_id),
        semester_id   INTEGER REFERENCES semesters(semester_id),
        instructor_id INTEGER REFERENCES instructors(instructor_id),
        section_number TEXT,
        classroom TEXT,
        schedule_days TEXT,
        schedule_time TEXT,
        max_students  INTEGER DEFAULT 30,
        enrolled_count INTEGER DEFAULT 0,
        delivery_mode  TEXT DEFAULT 'In-Person'
    );
    CREATE TABLE IF NOT EXISTS enrollments (
        enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id    INTEGER REFERENCES students(student_id),
        section_id    INTEGER REFERENCES course_sections(section_id),
        enrollment_date TEXT NOT NULL,
        status TEXT DEFAULT 'Enrolled',
        midterm_grade REAL,
        final_grade   REAL,
        overall_grade REAL,
        attendance_percentage REAL,
        notes TEXT,
        UNIQUE(student_id, section_id)
    );
    CREATE TABLE IF NOT EXISTS assignments (
        assignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        section_id    INTEGER REFERENCES course_sections(section_id),
        assignment_name TEXT NOT NULL,
        assignment_type TEXT,
        max_score REAL NOT NULL,
        weight_percentage REAL,
        due_date TEXT,
        description TEXT
    );
    CREATE TABLE IF NOT EXISTS assignment_submissions (
        submission_id INTEGER PRIMARY KEY AUTOINCREMENT,
        assignment_id INTEGER REFERENCES assignments(assignment_id),
        student_id    INTEGER REFERENCES students(student_id),
        submission_date TEXT,
        score REAL,
        normalized_score REAL,
        feedback TEXT,
        is_late INTEGER DEFAULT 0,
        UNIQUE(assignment_id, student_id)
    );
    CREATE TABLE IF NOT EXISTS academic_holds (
        hold_id    INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER REFERENCES students(student_id),
        hold_type  TEXT,
        reason     TEXT,
        placed_date TEXT,
        released_date TEXT,
        placed_by  TEXT,
        is_active  INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS scholarships (
        scholarship_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        scholarship_name TEXT NOT NULL,
        amount REAL NOT NULL,
        criteria TEXT,
        department_id INTEGER REFERENCES departments(department_id),
        available_slots INTEGER,
        academic_year TEXT
    );
    CREATE TABLE IF NOT EXISTS student_scholarships (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id     INTEGER REFERENCES students(student_id),
        scholarship_id INTEGER REFERENCES scholarships(scholarship_id),
        awarded_date TEXT,
        academic_year TEXT,
        UNIQUE(student_id, scholarship_id, academic_year)
    );
    CREATE TABLE IF NOT EXISTS extracurricular_activities (
        activity_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        activity_name TEXT NOT NULL,
        activity_type TEXT,
        faculty_advisor_id INTEGER REFERENCES instructors(instructor_id),
        meeting_schedule TEXT,
        max_members INTEGER
    );
    CREATE TABLE IF NOT EXISTS student_activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id  INTEGER REFERENCES students(student_id),
        activity_id INTEGER REFERENCES extracurricular_activities(activity_id),
        role TEXT,
        join_date TEXT,
        UNIQUE(student_id, activity_id)
    );
    """)

    c.executemany("INSERT OR IGNORE INTO departments VALUES (?,?,?,?,?,?,?)", [
        (1,'Computer Science','CS','Armen Petrosyan',1985,'Engineering Hall',2500000),
        (2,'Mathematics','MATH','Nvard Sargsyan',1960,'Science Building',1800000),
        (3,'Physics','PHYS','Gegham Harutyunyan',1962,'Science Building',2100000),
        (4,'Business Administration','BUS','Sona Mkrtchyan',1975,'Business Tower',3200000),
        (5,'Language & Literature','ARM','Anahit Grigoryan',1958,'Humanities Hall',1200000),
        (6,'History','HIST','Vartan Hovhannisyan',1958,'Humanities Hall',1100000),
        (7,'Biology','BIO','Lusine Simonyan',1970,'Life Sciences Building',1950000),
        (8,'Economics','ECON','Hayk Karapetyan',1972,'Business Tower',1700000),
        (9,'Engineering','ENG','Tigran Abrahamyan',1980,'Engineering Hall',2800000),
        (10,'Psychology','PSY','Marine Galstyan',1990,'Social Sciences Building',1400000),
    ])

    c.executemany("INSERT OR IGNORE INTO programs VALUES (?,?,?,?,?,?,?,?)", [
        (1,'Bachelor of Science in Computer Science','BSCS',1,'Bachelor',4,128,1),
        (2,'Master of Science in Computer Science','MSCS',1,'Master',2,60,1),
        (3,'Bachelor of Science in Mathematics','BSMATH',2,'Bachelor',4,120,1),
        (4,'Master of Science in Applied Mathematics','MSMATH',2,'Master',2,56,1),
        (5,'Bachelor of Science in Physics','BSPHYS',3,'Bachelor',4,124,1),
        (6,'Bachelor of Business Administration','BBA',4,'Bachelor',4,132,1),
        (7,'Master of Business Administration','MBA',4,'Master',2,60,1),
        (8,'Bachelor of Arts in Literature','BAAL',5,'Bachelor',4,116,1),
        (9,'Bachelor of Arts in History','BAHIST',6,'Bachelor',4,116,1),
        (10,'Bachelor of Science in Biology','BSBIO',7,'Bachelor',4,126,1),
        (11,'Bachelor of Science in Economics','BSECON',8,'Bachelor',4,120,1),
        (12,'Bachelor of Science in Engineering','BSENG',9,'Bachelor',4,136,1),
        (13,'Master of Science in Engineering','MSENG',9,'Master',2,62,1),
        (14,'Bachelor of Science in Psychology','BSPSY',10,'Bachelor',4,118,1),
        (15,'PhD in Computer Science','PHDCS',1,'PhD',4,90,1),
    ])

    c.executemany("INSERT OR IGNORE INTO instructors VALUES (?,?,?,?,?,?,?,?,?,?)", [
        (1,'Armen','Petrosyan','a.petrosyan@university.am',1,'Professor','1995-09-01','EH-201','+374-10-001001','Artificial Intelligence'),
        (2,'Ashot','Vardanyan','a.vardanyan@university.am',1,'Associate Professor','2005-02-15','EH-205','+374-10-001002','Database Systems'),
        (3,'Kristine','Nalbandyan','k.nalbandyan@university.am',1,'Assistant Professor','2015-08-20','EH-210','+374-10-001003','Machine Learning'),
        (4,'Nvard','Sargsyan','n.sargsyan@university.am',2,'Professor','1988-09-01','SB-101','+374-10-002001','Real Analysis'),
        (5,'Davit','Mkhitaryan','d.mkhitaryan@university.am',2,'Associate Professor','2003-01-10','SB-105','+374-10-002002','Number Theory'),
        (6,'Gegham','Harutyunyan','g.harutyunyan@university.am',3,'Professor','1992-09-01','SB-201','+374-10-003001','Quantum Mechanics'),
        (7,'Anush','Khachaturyan','a.khachaturyan@university.am',3,'Associate Professor','2008-08-15','SB-210','+374-10-003002','Astrophysics'),
        (8,'Sona','Mkrtchyan','s.mkrtchyan@university.am',4,'Professor','1997-09-01','BT-301','+374-10-004001','Strategic Management'),
        (9,'Aram','Hakobyan','a.hakobyan@university.am',4,'Associate Professor','2010-03-01','BT-305','+374-10-004002','Finance'),
        (10,'Anahit','Grigoryan','an.grigoryan@university.am',5,'Professor','1985-09-01','HH-101','+374-10-005001','Classical Literature'),
        (11,'Vartan','Hovhannisyan','v.hovhannisyan@university.am',6,'Professor','1990-09-01','HH-201','+374-10-006001','Medieval History'),
        (12,'Lusine','Simonyan','l.simonyan@university.am',7,'Professor','2000-09-01','LSB-101','+374-10-007001','Molecular Biology'),
        (13,'Narek','Babayan','n.babayan@university.am',7,'Assistant Professor','2018-08-01','LSB-110','+374-10-007002','Genetics'),
        (14,'Hayk','Karapetyan','h.karapetyan@university.am',8,'Professor','1999-09-01','BT-401','+374-10-008001','Macroeconomics'),
        (15,'Mariam','Poghosyan','m.poghosyan@university.am',8,'Associate Professor','2012-01-15','BT-410','+374-10-008002','International Economics'),
        (16,'Tigran','Abrahamyan','t.abrahamyan@university.am',9,'Professor','1993-09-01','EH-301','+374-10-009001','Civil Engineering'),
        (17,'Lilit','Gasparyan','l.gasparyan@university.am',9,'Associate Professor','2007-08-20','EH-310','+374-10-009002','Electrical Engineering'),
        (18,'Marine','Galstyan','m.galstyan@university.am',10,'Professor','2001-09-01','SSB-101','+374-10-010001','Clinical Psychology'),
        (19,'Vahagn','Danielyan','v.danielyan@university.am',10,'Assistant Professor','2019-08-01','SSB-110','+374-10-010002','Cognitive Psychology'),
        (20,'Gohar','Asatryan','g.asatryan@university.am',1,'Assistant Professor','2020-08-15','EH-215','+374-10-001004','Cybersecurity'),
    ])

    c.executemany("INSERT OR IGNORE INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        (1,'Aram','Petrosyan','2002-03-15','Male','aram.petrosyan@student.am','+374-91-100001','12 Abovyan St','Yerevan','2020-09-01','2024-06-30',1,1,'Active',88.5,96,500000),
        (2,'Ani','Sargsyan','2001-07-22','Female','ani.sargsyan@student.am','+374-91-100002','5 Tigranyan St','Yerevan','2020-09-01','2024-06-30',1,2,'Active',92.3,96,700000),
        (3,'Narek','Hovhannisyan','2002-11-08','Male','narek.hovh@student.am','+374-91-100003','33 Komitas Ave','Yerevan','2020-09-01','2024-06-30',1,1,'Active',75.4,90,0),
        (4,'Lusine','Vardanyan','2003-01-30','Female','lusine.vardanyan@student.am','+374-91-100004','7 Baghramyan Ave','Yerevan','2021-09-01','2025-06-30',1,3,'Active',85.7,64,300000),
        (5,'Tigran','Mkrtchyan','2002-05-17','Male','tigran.mkr@student.am','+374-91-100005','18 Moskovyan St','Yerevan','2020-09-01','2024-06-30',1,2,'Active',79.2,92,0),
        (6,'Mariam','Abrahamyan','2003-09-03','Female','mariam.abr@student.am','+374-91-100006','45 Charents St','Yerevan','2021-09-01','2025-06-30',2,1,'Active',91.0,28,600000),
        (7,'Davit','Karapetyan','2001-12-20','Male','davit.kara@student.am','+374-91-100007','3 Sayat-Nova Ave','Yerevan','2020-09-01','2024-06-30',3,4,'Active',88.0,94,400000),
        (8,'Narine','Harutyunyan','2002-04-11','Female','narine.har@student.am','+374-91-100008','22 Nalbandyan St','Yerevan','2020-09-01','2024-06-30',3,5,'Active',94.5,96,800000),
        (9,'Artur','Grigoryan','2002-08-25','Male','artur.grig@student.am','+374-91-100009','9 Tumanyan St','Yerevan','2020-09-01','2024-06-30',4,6,'Active',71.3,88,0),
        (10,'Anahit','Nalbandyan','2003-02-14','Female','anahit.nalb@student.am','+374-91-100010','15 Pushkin St','Yerevan','2021-09-01','2025-06-30',6,8,'Active',83.6,66,200000),
        (11,'Sargis','Hakobyan','2001-06-07','Male','sargis.hak@student.am','+374-91-100011','28 Isahakyan St','Gyumri','2020-09-01','2024-06-30',6,9,'Active',77.8,90,0),
        (12,'Kristine','Poghosyan','2002-10-19','Female','kristine.pogh@student.am','+374-91-100012','6 Hanrapetutyan St','Vanadzor','2020-09-01','2024-06-30',7,8,'Active',89.4,32,500000),
        (13,'Vahan','Danielyan','2003-03-28','Male','vahan.dan@student.am','+374-91-100013','41 Azatutyan Ave','Yerevan','2021-09-01','2025-06-30',8,10,'Active',81.5,62,0),
        (14,'Gohar','Simonyan','2002-07-05','Female','gohar.sim@student.am','+374-91-100014','11 Gevorgyan St','Yerevan','2020-09-01','2024-06-30',8,10,'Active',86.2,94,300000),
        (15,'Hayk','Mkhitaryan','2001-11-23','Male','hayk.mkh@student.am','+374-91-100015','19 Arami St','Yerevan','2020-09-01','2024-06-30',9,11,'Active',90.1,96,600000),
        (16,'Lilit','Babayan','2002-01-16','Female','lilit.bab@student.am','+374-91-100016','7 Koryun St','Yerevan','2020-09-01','2024-06-30',10,12,'Active',84.7,92,200000),
        (17,'Armen','Asatryan','2003-05-09','Male','armen.asa@student.am','+374-91-100017','33 Teryan St','Yerevan','2021-09-01','2025-06-30',10,13,'Active',78.3,60,0),
        (18,'Nvard','Khachaturyan','2002-09-14','Female','nvard.khach@student.am','+374-91-100018','5 Tpagrichner St','Yerevan','2020-09-01','2024-06-30',11,14,'Active',87.9,94,400000),
        (19,'Gegham','Galstyan','2001-04-02','Male','gegham.gal@student.am','+374-91-100019','14 Vardanants St','Abovyan','2020-09-01','2024-06-30',12,16,'Active',82.4,96,0),
        (20,'Anahit','Gevorgyan','2002-12-27','Female','anahit.gev@student.am','+374-91-100020','22 Arshakunyats Ave','Yerevan','2020-09-01','2024-06-30',12,17,'Active',76.6,90,0),
        (21,'Vahagn','Avagyan','2003-06-18','Male','vahagn.av@student.am','+374-91-100021','8 Garegin Nzhdeh Sq','Yerevan','2021-09-01','2025-06-30',14,18,'Active',93.1,64,700000),
        (22,'Sofya','Petrosyan','2002-02-11','Female','sofya.petr@student.am','+374-91-100022','17 Tigranyan St','Yerevan','2020-09-01','2024-06-30',14,19,'Active',88.8,92,300000),
        (23,'Arshak','Vardanyan','2001-08-30','Male','arshak.var@student.am','+374-91-100023','3 Anipemza St','Artashat','2020-09-01','2024-06-30',1,2,'Active',68.5,86,0),
        (24,'Tamara','Mkrtchyan','2002-04-22','Female','tamara.mkr@student.am','+374-91-100024','9 Spandaryan St','Yerevan','2020-09-01','2024-06-30',4,7,'Active',80.0,88,100000),
        (25,'Mher','Harutyunyan','2003-10-07','Male','mher.har@student.am','+374-91-100025','25 Frikyan St','Yerevan','2021-09-01','2025-06-30',5,6,'Active',85.5,60,200000),
        (26,'Tamar','Grigoryan','2002-06-15','Female','tamar.grig@student.am','+374-91-100026','11 Sebastia St','Yerevan','2020-09-01','2024-06-30',5,7,'Active',91.7,92,600000),
        (27,'Karapet','Nalbandyan','2001-03-24','Male','karapet.nalb@student.am','+374-91-100027','7 Adoyan St','Yerevan','2020-09-01','2024-06-30',6,8,'Graduated',86.3,132,300000),
        (28,'Zara','Hakobyan','2002-11-01','Female','zara.hak@student.am','+374-91-100028','31 Haghtanaki Ave','Gyumri','2020-09-01','2024-06-30',1,3,'Active',72.9,88,0),
        (29,'Levon','Poghosyan','2003-07-19','Male','levon.pogh@student.am','+374-91-100029','6 Hrachya Acharian St','Yerevan','2021-09-01','2025-06-30',11,15,'Active',79.8,58,0),
        (30,'Hermine','Danielyan','2002-01-08','Female','hermine.dan@student.am','+374-91-100030','42 Tigranyan St','Yerevan','2020-09-01','2024-06-30',13,16,'Active',87.2,28,400000),
        (31,'Ruben','Simonyan','2001-09-13','Male','ruben.sim@student.am','+374-91-100031','18 Charents St','Yerevan','2020-09-01','2024-06-30',3,4,'Active',83.4,94,200000),
        (32,'Astghik','Mkhitaryan','2002-05-28','Female','astghik.mkh@student.am','+374-91-100032','4 Sepuh St','Yerevan','2020-09-01','2024-06-30',10,12,'Active',90.6,92,600000),
        (33,'Hovhannes','Babayan','2003-02-17','Male','hovhannes.bab@student.am','+374-91-100033','29 Azatutyan Ave','Vanadzor','2021-09-01','2025-06-30',9,11,'Active',74.1,56,0),
        (34,'Arev','Asatryan','2002-08-06','Female','arev.asa@student.am','+374-91-100034','13 Nalbandyan St','Yerevan','2020-09-01','2024-06-30',7,10,'Active',88.9,92,400000),
        (35,'Arman','Khachaturyan','2001-12-31','Male','arman.khach@student.am','+374-91-100035','20 Melik-Adamyan St','Yerevan','2020-09-01','2024-06-30',12,16,'Active',81.5,90,100000),
        (36,'Lianna','Galstyan','2003-04-10','Female','lianna.gal@student.am','+374-91-100036','8 Abovyan St','Yerevan','2021-09-01','2025-06-30',6,8,'Active',84.4,62,200000),
        (37,'Rafik','Gevorgyan','2002-10-25','Male','rafik.gev@student.am','+374-91-100037','15 Baghramyan Ave','Yerevan','2020-09-01','2024-06-30',2,1,'Active',86.0,28,300000),
        (38,'Mariam','Avagyan','2001-06-14','Female','mariam.ava@student.am','+374-91-100038','3 Mashtots Ave','Yerevan','2020-09-01','2024-06-30',8,10,'Active',92.7,94,700000),
        (39,'Ararat','Petrosyan','2002-02-03','Male','ararat.petr@student.am','+374-91-100039','16 Komitas Ave','Yerevan','2020-09-01','2024-06-30',5,6,'Active',69.8,86,0),
        (40,'Nune','Vardanyan','2003-08-21','Female','nune.var@student.am','+374-91-100040','7 Tigranyan St','Yerevan','2021-09-01','2025-06-30',14,18,'Active',87.0,60,300000),
        (41,'Hamlet','Mkrtchyan','2002-03-12','Male','hamlet.mkr@student.am','+374-91-100041','24 Azatutyan Ave','Yerevan','2020-09-01','2024-06-30',11,14,'Active',76.5,90,0),
        (42,'Salome','Harutyunyan','2001-07-29','Female','salome.har@student.am','+374-91-100042','12 Hanrapetutyan St','Abovyan','2020-09-01','2024-06-30',1,20,'Active',89.3,94,500000),
        (43,'Andranik','Grigoryan','2003-11-18','Male','andranik.grig@student.am','+374-91-100043','5 Isahakyan St','Yerevan','2021-09-01','2025-06-30',12,17,'Active',82.1,58,100000),
        (44,'Tatev','Nalbandyan','2002-09-07','Female','tatev.nalb@student.am','+374-91-100044','33 Arshakunyats Ave','Yerevan','2020-09-01','2024-06-30',3,5,'Active',91.2,92,600000),
        (45,'Vardan','Hakobyan','2001-01-26','Male','vardan.hak@student.am','+374-91-100045','18 Anipemza St','Artashat','2020-09-01','2024-06-30',9,16,'Active',78.6,90,0),
        (46,'Lara','Poghosyan','2002-05-15','Female','lara.pogh@student.am','+374-91-100046','9 Sayat-Nova Ave','Yerevan','2020-09-01','2024-06-30',10,12,'Active',85.3,92,200000),
        (47,'Edvard','Danielyan','2003-09-04','Male','edvard.dan@student.am','+374-91-100047','27 Vardanants St','Yerevan','2021-09-01','2025-06-30',11,15,'Active',80.7,60,100000),
        (48,'Ani','Simonyan','2002-12-23','Female','ani.sim@student.am','+374-91-100048','6 Koryun St','Yerevan','2020-09-01','2024-06-30',7,12,'Active',86.8,92,300000),
        (49,'Arsen','Mkhitaryan','2001-04-08','Male','arsen.mkh@student.am','+374-91-100049','14 Pushkin St','Yerevan','2020-09-01','2024-06-30',4,6,'Active',73.2,88,0),
        (50,'Satenik','Babayan','2002-07-16','Female','satenik.bab@student.am','+374-91-100050','21 Tigranyan St','Yerevan','2020-09-01','2024-06-30',8,10,'Graduated',88.1,116,400000),
    ])

    c.executemany("INSERT OR IGNORE INTO semesters VALUES (?,?,?,?,?,?,?,?)", [
        (1,'Fall 2021','2021-2022','2021-09-01','2022-01-15','2021-08-20','2021-10-15',0),
        (2,'Spring 2022','2021-2022','2022-02-01','2022-06-15','2022-01-20','2022-03-15',0),
        (3,'Fall 2022','2022-2023','2022-09-01','2023-01-15','2022-08-20','2022-10-15',0),
        (4,'Spring 2023','2022-2023','2023-02-01','2023-06-15','2023-01-20','2023-03-15',0),
        (5,'Fall 2023','2023-2024','2023-09-01','2024-01-15','2023-08-20','2023-10-15',0),
        (6,'Spring 2024','2023-2024','2024-02-01','2024-06-15','2024-01-20','2024-03-15',1),
    ])

    c.executemany("INSERT OR IGNORE INTO courses VALUES (?,?,?,?,?,?,?,?,?,?)", [
        (1,'CS101','Introduction to Programming',1,4,100,None,35,1,None),
        (2,'CS201','Data Structures and Algorithms',1,4,200,None,30,1,None),
        (3,'CS301','Database Systems',1,4,300,None,30,1,None),
        (4,'CS302','Operating Systems',1,4,300,None,28,1,None),
        (5,'CS401','Machine Learning',1,4,400,None,25,1,None),
        (6,'CS402','Computer Networks',1,4,400,None,28,1,None),
        (7,'CS501','Advanced Algorithms',1,4,500,None,20,1,None),
        (8,'MATH101','Calculus I',2,4,100,None,40,1,None),
        (9,'MATH102','Calculus II',2,4,100,None,38,1,None),
        (10,'MATH201','Linear Algebra',2,4,200,None,35,1,None),
        (11,'MATH202','Discrete Mathematics',2,4,200,None,35,1,None),
        (12,'MATH301','Real Analysis',2,4,300,None,25,1,None),
        (13,'MATH401','Numerical Methods',2,3,400,None,25,1,None),
        (14,'PHYS101','General Physics I',3,4,100,None,40,1,None),
        (15,'PHYS102','General Physics II',3,4,100,None,38,1,None),
        (16,'PHYS301','Quantum Mechanics',3,4,300,None,20,1,None),
        (17,'BUS101','Principles of Management',4,3,100,None,45,1,None),
        (18,'BUS201','Accounting I',4,3,200,None,40,1,None),
        (19,'BUS202','Marketing Principles',4,3,200,None,42,1,None),
        (20,'BUS301','Corporate Finance',4,4,300,None,35,1,None),
        (21,'BUS401','Strategic Management',4,4,400,None,30,1,None),
        (22,'ARM101','Classical Literature',5,3,100,None,30,1,None),
        (23,'ARM201','Modern Poetry',5,3,200,None,25,1,None),
        (24,'HIST101','Ancient History',6,3,100,None,35,1,None),
        (25,'HIST201','Medieval History',6,3,200,None,30,1,None),
        (26,'BIO101','General Biology I',7,4,100,None,38,1,None),
        (27,'BIO201','Cell Biology',7,4,200,None,30,1,None),
        (28,'BIO301','Genetics',7,4,300,None,25,1,None),
        (29,'ECON101','Microeconomics',8,3,100,None,45,1,None),
        (30,'ECON102','Macroeconomics',8,3,100,None,45,1,None),
        (31,'ECON301','International Economics',8,3,300,None,30,1,None),
        (32,'ENG101','Engineering Mechanics',9,4,100,None,40,1,None),
        (33,'ENG201','Circuit Analysis',9,4,200,None,35,1,None),
        (34,'ENG301','Thermodynamics',9,4,300,None,30,1,None),
        (35,'PSY101','Introduction to Psychology',10,3,100,None,45,1,None),
        (36,'PSY201','Developmental Psychology',10,3,200,None,35,1,None),
        (37,'PSY301','Abnormal Psychology',10,3,300,None,30,1,None),
    ])

    sections = [
        (1,1,5,2,'A','EH-101','Mon/Wed/Fri','09:00-10:00',35,32,'In-Person'),
        (2,1,6,3,'A','EH-101','Mon/Wed/Fri','09:00-10:00',35,28,'In-Person'),
        (3,2,5,2,'A','EH-102','Tue/Thu','10:00-11:30',30,27,'In-Person'),
        (4,2,6,2,'A','EH-102','Tue/Thu','10:00-11:30',30,25,'In-Person'),
        (5,3,5,2,'A','EH-103','Mon/Wed','11:00-12:30',30,26,'In-Person'),
        (6,3,6,2,'A','EH-103','Mon/Wed','11:00-12:30',30,22,'In-Person'),
        (7,4,5,1,'A','EH-104','Tue/Thu','13:00-14:30',28,24,'In-Person'),
        (8,5,5,3,'A','EH-105','Mon/Wed/Fri','14:00-15:00',25,22,'In-Person'),
        (9,5,6,3,'A','EH-105','Mon/Wed/Fri','14:00-15:00',25,18,'Hybrid'),
        (10,6,5,1,'A','EH-106','Tue/Thu','15:00-16:30',28,20,'In-Person'),
        (11,8,5,4,'A','SB-101','Mon/Wed/Fri','08:00-09:00',40,38,'In-Person'),
        (12,8,6,4,'A','SB-101','Mon/Wed/Fri','08:00-09:00',40,35,'In-Person'),
        (13,9,5,4,'A','SB-102','Tue/Thu','09:00-10:30',38,34,'In-Person'),
        (14,10,5,5,'A','SB-103','Mon/Wed/Fri','10:00-11:00',35,30,'In-Person'),
        (15,11,5,5,'A','SB-104','Tue/Thu','11:00-12:30',35,28,'In-Person'),
        (16,12,5,4,'A','SB-105','Mon/Wed','13:00-14:30',25,18,'In-Person'),
        (17,14,5,6,'A','SB-201','Mon/Wed/Fri','09:00-10:00',40,36,'In-Person'),
        (18,15,5,7,'A','SB-202','Tue/Thu','10:00-11:30',38,30,'In-Person'),
        (19,16,5,6,'A','SB-203','Mon/Wed','13:00-14:30',20,14,'In-Person'),
        (20,17,5,8,'A','BT-101','Mon/Wed/Fri','09:00-10:00',45,40,'In-Person'),
        (21,18,5,9,'A','BT-102','Tue/Thu','10:00-11:30',40,35,'In-Person'),
        (22,19,5,8,'A','BT-103','Mon/Wed/Fri','11:00-12:00',42,38,'In-Person'),
        (23,20,5,9,'A','BT-104','Tue/Thu','13:00-14:30',35,28,'In-Person'),
        (24,21,5,8,'A','BT-105','Mon/Wed','14:00-15:30',30,22,'In-Person'),
        (25,22,5,10,'A','HH-101','Tue/Thu','09:00-10:30',30,22,'In-Person'),
        (26,23,5,10,'A','HH-102','Mon/Wed','11:00-12:30',25,18,'In-Person'),
        (27,24,5,11,'A','HH-201','Tue/Thu','11:00-12:30',35,30,'In-Person'),
        (28,25,5,11,'A','HH-202','Mon/Wed/Fri','13:00-14:00',30,24,'In-Person'),
        (29,26,5,12,'A','LSB-101','Mon/Wed/Fri','09:00-10:00',38,34,'In-Person'),
        (30,27,5,12,'A','LSB-102','Tue/Thu','10:00-11:30',30,26,'In-Person'),
        (31,28,5,13,'A','LSB-103','Mon/Wed','13:00-14:30',25,20,'In-Person'),
        (32,29,5,14,'A','BT-401','Mon/Wed/Fri','10:00-11:00',45,40,'In-Person'),
        (33,30,5,14,'A','BT-402','Tue/Thu','11:00-12:30',45,38,'In-Person'),
        (34,31,5,15,'A','BT-403','Mon/Wed','14:00-15:30',30,22,'In-Person'),
        (35,32,5,16,'A','EH-301','Mon/Wed/Fri','09:00-10:00',40,36,'In-Person'),
        (36,33,5,17,'A','EH-302','Tue/Thu','10:00-11:30',35,30,'In-Person'),
        (37,34,5,16,'A','EH-303','Mon/Wed','13:00-14:30',30,24,'In-Person'),
        (38,35,5,18,'A','SSB-101','Mon/Wed/Fri','11:00-12:00',45,42,'In-Person'),
        (39,36,5,18,'A','SSB-102','Tue/Thu','13:00-14:30',35,30,'In-Person'),
        (40,37,5,19,'A','SSB-103','Mon/Wed','15:00-16:30',30,24,'In-Person'),
    ]
    c.executemany("INSERT OR IGNORE INTO course_sections VALUES (?,?,?,?,?,?,?,?,?,?,?)", sections)

    enrollments = [
        (1,1,1,'2023-09-01','Completed',85.0,90.0,88.0,95.0,None),
        (2,2,1,'2023-09-01','Completed',94.0,97.0,96.0,98.0,None),
        (3,3,1,'2023-09-01','Completed',72.0,76.0,74.5,88.0,None),
        (4,5,1,'2023-09-01','Completed',78.0,81.0,79.5,91.0,None),
        (5,23,1,'2023-09-01','Completed',65.0,70.0,67.5,82.0,None),
        (6,28,1,'2023-09-01','Completed',70.0,73.0,71.5,85.0,None),
        (7,42,1,'2023-09-01','Completed',88.0,91.0,89.5,96.0,None),
        (8,1,3,'2023-09-01','Completed',88.0,91.0,89.5,93.0,None),
        (9,2,3,'2023-09-01','Completed',95.0,98.0,96.5,99.0,None),
        (10,3,3,'2023-09-01','Completed',74.0,77.0,75.5,87.0,None),
        (11,5,3,'2023-09-01','Completed',80.0,79.0,79.5,90.0,None),
        (12,23,3,'2023-09-01','Completed',62.0,66.0,64.0,80.0,None),
        (13,7,14,'2023-09-01','Completed',87.0,90.0,88.5,94.0,None),
        (14,8,14,'2023-09-01','Completed',95.0,97.0,96.0,100.0,None),
        (15,31,14,'2023-09-01','Completed',82.0,85.0,83.5,92.0,None),
        (16,44,14,'2023-09-01','Completed',90.0,93.0,91.5,97.0,None),
        (17,10,20,'2023-09-01','Completed',82.0,85.0,83.5,91.0,None),
        (18,11,20,'2023-09-01','Completed',76.0,79.0,77.5,88.0,None),
        (19,27,20,'2023-09-01','Completed',85.0,88.0,86.5,93.0,None),
        (20,36,20,'2023-09-01','Completed',83.0,85.0,84.0,90.0,None),
        (21,14,25,'2023-09-01','Completed',85.0,88.0,86.5,92.0,None),
        (22,38,25,'2023-09-01','Completed',91.0,94.0,92.5,97.0,None),
        (23,50,25,'2023-09-01','Completed',87.0,89.0,88.0,94.0,None),
        (24,13,25,'2023-09-01','Completed',79.0,82.0,80.5,89.0,None),
        (25,15,27,'2023-09-01','Completed',88.0,91.0,89.5,95.0,None),
        (26,34,27,'2023-09-01','Completed',87.0,89.0,88.0,93.0,None),
        (27,48,27,'2023-09-01','Completed',85.0,87.0,86.0,91.0,None),
        (28,18,31,'2023-09-01','Completed',86.0,89.0,87.5,92.0,None),
        (29,29,31,'2023-09-01','Completed',78.0,81.0,79.5,88.0,None),
        (30,41,31,'2023-09-01','Completed',74.0,77.0,75.5,86.0,None),
        (31,47,31,'2023-09-01','Completed',79.0,82.0,80.5,89.0,None),
        (32,19,35,'2023-09-01','Completed',81.0,84.0,82.5,90.0,None),
        (33,20,35,'2023-09-01','Completed',74.0,77.0,75.5,85.0,None),
        (34,35,35,'2023-09-01','Completed',80.0,83.0,81.5,89.0,None),
        (35,43,35,'2023-09-01','Completed',80.0,83.0,81.5,87.0,None),
        (36,45,35,'2023-09-01','Completed',77.0,80.0,78.5,88.0,None),
        (37,16,29,'2023-09-01','Completed',83.0,86.0,84.5,91.0,None),
        (38,46,29,'2023-09-01','Completed',84.0,87.0,85.5,92.0,None),
        (39,21,40,'2023-09-01','Completed',92.0,94.0,93.0,97.0,None),
        (40,22,40,'2023-09-01','Completed',87.0,90.0,88.5,94.0,None),
        (41,40,40,'2023-09-01','Completed',85.0,88.0,86.5,92.0,None),
        (42,1,5,'2023-09-01','Completed',86.0,90.0,88.0,94.0,None),
        (43,2,5,'2023-09-01','Completed',93.0,96.0,94.5,98.0,None),
        (44,5,5,'2023-09-01','Completed',77.0,80.0,78.5,90.0,None),
        (45,23,5,'2023-09-01','Completed',64.0,68.0,66.0,81.0,None),
        (46,28,5,'2023-09-01','Completed',69.0,73.0,71.0,84.0,None),
        (47,42,5,'2023-09-01','Completed',87.0,90.0,88.5,95.0,None),
        (48,1,7,'2023-09-01','Completed',84.0,88.0,86.0,93.0,None),
        (49,2,7,'2023-09-01','Completed',92.0,95.0,93.5,97.0,None),
        (50,5,7,'2023-09-01','Completed',75.0,79.0,77.0,89.0,None),
        (51,37,7,'2023-09-01','Completed',84.0,87.0,85.5,91.0,None),
        (52,6,8,'2023-09-01','Completed',89.0,92.0,90.5,96.0,None),
        (53,2,8,'2023-09-01','Completed',94.0,97.0,95.5,99.0,None),
        (54,37,8,'2023-09-01','Completed',85.0,87.0,86.0,92.0,None),
        (55,4,2,'2024-02-01','Enrolled',82.0,None,None,90.0,None),
        (56,6,9,'2024-02-01','Enrolled',90.0,None,None,95.0,None),
        (57,25,17,'2024-02-01','Enrolled',84.0,None,None,91.0,None),
        (58,26,18,'2024-02-01','Enrolled',90.0,None,None,96.0,None),
        (59,30,12,'2024-02-01','Enrolled',85.0,None,None,92.0,None),
        (60,33,24,'2024-02-01','Enrolled',72.0,None,None,85.0,None),
        (61,17,28,'2024-02-01','Enrolled',77.0,None,None,88.0,None),
        (62,24,21,'2024-02-01','Enrolled',79.0,None,None,87.0,None),
        (63,49,22,'2024-02-01','Enrolled',71.0,None,None,84.0,None),
        (64,12,6,'2024-02-01','Enrolled',88.0,None,None,93.0,None),
        (65,32,30,'2024-02-01','Enrolled',89.0,None,None,94.0,None),
        (66,39,16,'2024-02-01','Enrolled',68.0,None,None,82.0,None),
    ]
    c.executemany("INSERT OR IGNORE INTO enrollments VALUES (?,?,?,?,?,?,?,?,?,?)", enrollments)

    c.executemany("INSERT OR IGNORE INTO scholarships VALUES (?,?,?,?,?,?,?)", [
        (1,'Excellence in Computer Science Award',700000,'GPA above 90, CS major',1,5,'2023-2024'),
        (2,'Mathematics Merit Scholarship',600000,'GPA above 92, Math major',2,3,'2023-2024'),
        (3,'University Presidential Scholarship',800000,'Top 1% GPA, any major',None,10,'2023-2024'),
        (4,'STEM Achievement Award',500000,'GPA above 88, STEM major',None,15,'2023-2024'),
        (5,'Humanities Excellence Grant',400000,'GPA above 85, Humanities major',None,8,'2023-2024'),
        (6,'Gyumri Regional Scholarship',450000,'Students from Gyumri, GPA above 80',None,6,'2023-2024'),
    ])

    c.executemany("INSERT OR IGNORE INTO student_scholarships VALUES (?,?,?,?,?)", [
        (1,2,1,'2023-09-01','2023-2024'),
        (2,8,2,'2023-09-01','2023-2024'),
        (3,2,3,'2023-09-01','2023-2024'),
        (4,21,3,'2023-09-01','2023-2024'),
        (5,38,3,'2023-09-01','2023-2024'),
        (6,1,4,'2023-09-01','2023-2024'),
        (7,26,4,'2023-09-01','2023-2024'),
        (8,14,5,'2023-09-01','2023-2024'),
        (9,38,5,'2023-09-01','2023-2024'),
        (10,11,6,'2023-09-01','2023-2024'),
        (11,28,6,'2023-09-01','2023-2024'),
    ])

    c.executemany("INSERT OR IGNORE INTO extracurricular_activities VALUES (?,?,?,?,?,?)", [
        (1,'Computer Science Club','Academic',1,'Every Wednesday 17:00',50),
        (2,'Mathematics Society','Academic',4,'Every Thursday 16:00',40),
        (3,'Student Government Association','Leadership',8,'Every Tuesday 18:00',30),
        (4,'Chess Club','Recreation',5,'Every Friday 15:00',25),
        (5,'Debate Club','Academic',11,'Every Monday 17:00',35),
        (6,'Basketball Team','Sports',16,'Mon/Wed/Fri 18:00',15),
        (7,'Cultural Heritage Club','Cultural',10,'Every Saturday 11:00',60),
        (8,'Programming Competition Team','Academic',3,'Every Tuesday 17:00',20),
        (9,'Science Olympiad Team','Academic',6,'Every Thursday 17:00',25),
        (10,'Student Newspaper','Media',18,'Every Wednesday 16:00',20),
    ])

    c.executemany("INSERT OR IGNORE INTO student_activities VALUES (?,?,?,?,?)", [
        (1,1,1,'Member','2020-10-01'),(2,2,1,'Vice President','2020-10-01'),
        (3,3,1,'Member','2021-10-01'),(4,5,1,'Member','2020-10-01'),
        (5,42,1,'President','2020-10-01'),(6,1,8,'Member','2021-09-15'),
        (7,2,8,'Team Captain','2020-09-15'),(8,6,8,'Member','2021-09-15'),
        (9,8,2,'President','2020-10-15'),(10,7,2,'Member','2020-10-15'),
        (11,44,2,'Secretary','2020-10-15'),(12,21,3,'President','2021-09-01'),
        (13,22,3,'Member','2021-09-01'),(14,10,3,'Treasurer','2021-09-01'),
        (15,38,3,'Vice President','2021-09-01'),(16,15,5,'Member','2020-11-01'),
        (17,14,7,'Member','2020-11-01'),(18,38,7,'Member','2020-11-01'),
        (19,50,7,'Secretary','2020-11-01'),(20,19,6,'Member','2020-10-01'),
        (21,35,6,'Captain','2020-10-01'),(22,45,6,'Member','2020-10-01'),
    ])

    conn.commit()
    conn.close()


def load_frames():
    conn = get_conn()
    students     = pd.read_sql("SELECT * FROM students", conn)
    departments  = pd.read_sql("SELECT * FROM departments", conn)
    programs     = pd.read_sql("SELECT * FROM programs", conn)
    instructors  = pd.read_sql("SELECT * FROM instructors", conn)
    courses      = pd.read_sql("SELECT * FROM courses", conn)
    enrollments  = pd.read_sql("SELECT * FROM enrollments", conn)
    sections     = pd.read_sql("SELECT * FROM course_sections", conn)
    semesters    = pd.read_sql("SELECT * FROM semesters", conn)
    scholarships = pd.read_sql("SELECT * FROM scholarships", conn)
    stu_sch      = pd.read_sql("SELECT * FROM student_scholarships", conn)
    activities   = pd.read_sql("SELECT * FROM extracurricular_activities", conn)
    stu_act      = pd.read_sql("SELECT * FROM student_activities", conn)
    conn.close()
    return (students, departments, programs, instructors, courses,
            enrollments, sections, semesters, scholarships, stu_sch,
            activities, stu_act)


def add_label(ax, val, fmt='{:.1f}', color=TEXT_MAIN, fontsize=9, offset=1.5):
    ax.text(val + offset, ax.get_yticks()[0], fmt.format(val),
            color=color, fontsize=fontsize, va='center')


def page1_overview(students, departments, programs, enrollments):
    fig = plt.figure(figsize=(22, 14))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle('UNIVERSITY: ACADEMIC PERFORMANCE DASHBOARD',
                 fontsize=22, fontweight='bold', color=TEXT_MAIN, y=0.98,
                 fontfamily='DejaVu Sans')

    gs = gridspec.GridSpec(3, 4, figure=fig, hspace=0.55, wspace=0.4)

    stu_prog = students.merge(programs[['program_id','program_code','department_id','degree_level']], on='program_id')
    stu_dept = stu_prog.merge(departments[['department_id','department_name']], on='department_id')

    total     = len(students)
    active    = (students['status'] == 'Active').sum()
    graduated = (students['status'] == 'Graduated').sum()
    avg_gpa   = students['gpa'].mean()
    on_schol  = (students['scholarship_amount'] > 0).sum()

    kpis = [
        ('Total Students', total, BLUE),
        ('Active', active, GREEN),
        ('Graduated', graduated, GOLD),
        ('Avg GPA', f'{avg_gpa:.1f}', RED),
        ('On Scholarship', on_schol, PURPLE),
    ]
    ax_kpi = fig.add_subplot(gs[0, :])
    ax_kpi.set_facecolor(DARK_BG)
    ax_kpi.axis('off')
    for i, (label, val, col) in enumerate(kpis):
        x = 0.08 + i * 0.21
        rect = mpatches.FancyBboxPatch((x-0.07, 0.05), 0.17, 0.88,
            boxstyle='round,pad=0.02', facecolor=CARD_BG,
            edgecolor=col, linewidth=2, transform=ax_kpi.transAxes)
        ax_kpi.add_patch(rect)
        ax_kpi.text(x, 0.65, str(val), ha='center', va='center',
                    fontsize=30, fontweight='bold', color=col, transform=ax_kpi.transAxes)
        ax_kpi.text(x, 0.22, label, ha='center', va='center',
                    fontsize=11, color=TEXT_SUB, transform=ax_kpi.transAxes)

    ax1 = fig.add_subplot(gs[1, :2])
    dept_gpa = stu_dept.groupby('department_name')['gpa'].mean().sort_values()
    colors_bar = [RED if v >= dept_gpa.mean() else BLUE for v in dept_gpa.values]
    bars = ax1.barh(dept_gpa.index, dept_gpa.values, color=colors_bar, height=0.6)
    ax1.axvline(dept_gpa.mean(), color=GOLD, linestyle='--', linewidth=1.5, alpha=0.8, label=f'Avg: {dept_gpa.mean():.1f}')
    for bar, val in zip(bars, dept_gpa.values):
        ax1.text(val + 0.3, bar.get_y() + bar.get_height()/2,
                 f'{val:.1f}', va='center', fontsize=8.5, color=TEXT_MAIN)
    ax1.set_xlabel('Average GPA', fontsize=10)
    ax1.set_title('Average GPA by Department', fontsize=13, fontweight='bold', pad=10)
    ax1.legend(fontsize=9)
    ax1.set_xlim(0, 100)
    ax1.grid(axis='x', alpha=0.3)

    ax2 = fig.add_subplot(gs[1, 2:])
    students['standing'] = pd.cut(students['gpa'],
        bins=[0, 60, 70, 80, 90, 100],
        labels=['At Risk\n(<60)', 'Passing\n(60-70)', 'Satisfactory\n(70-80)',
                'Good\n(80-90)', 'Excellent\n(90+)'])
    standing_counts = students['standing'].value_counts().sort_index()
    stand_colors = [RED, '#E67E22', GOLD, BLUE, GREEN]
    wedges, texts, autotexts = ax2.pie(
        standing_counts.values, labels=standing_counts.index,
        colors=stand_colors, autopct='%1.1f%%',
        pctdistance=0.78, startangle=140,
        wedgeprops={'edgecolor': DARK_BG, 'linewidth': 2})
    for t in texts:
        t.set_color(TEXT_SUB); t.set_fontsize(8.5)
    for at in autotexts:
        at.set_color(TEXT_MAIN); at.set_fontsize(9); at.set_fontweight('bold')
    ax2.set_title('Academic Standing Distribution', fontsize=13, fontweight='bold', pad=10)

    ax3 = fig.add_subplot(gs[2, :2])
    gpa_data = [stu_dept[stu_dept['department_name'] == dept]['gpa'].dropna().values
                for dept in dept_gpa.index]
    short_names = [n.replace('Language & Literature','Lang. & Lit.')
                    .replace('Business Administration','Business Admin.')
                    .replace('Computer Science','Comp. Sci.') for n in dept_gpa.index]
    bp = ax3.boxplot(gpa_data, vert=False, patch_artist=True,
                     medianprops={'color': GOLD, 'linewidth': 2})
    for patch, col in zip(bp['boxes'], PALETTE):
        patch.set_facecolor(col); patch.set_alpha(0.7)
    ax3.set_yticklabels(short_names, fontsize=8)
    ax3.set_xlabel('GPA Score', fontsize=10)
    ax3.set_title('GPA Distribution by Department', fontsize=13, fontweight='bold', pad=10)
    ax3.grid(axis='x', alpha=0.3)

    ax4 = fig.add_subplot(gs[2, 2:])
    deg_gpa = stu_prog.groupby('degree_level')['gpa'].mean().sort_values(ascending=False)
    deg_count = stu_prog.groupby('degree_level')['student_id'].count()
    x_pos = range(len(deg_gpa))
    bar_colors = [RED, BLUE, GOLD][:len(deg_gpa)]
    bars4 = ax4.bar(x_pos, deg_gpa.values, color=bar_colors, width=0.5, alpha=0.9)
    ax4b = ax4.twinx()
    ax4b.plot(x_pos, [deg_count.get(d, 0) for d in deg_gpa.index],
              'o--', color=GREEN, linewidth=2, markersize=8, label='# Students')
    ax4b.set_ylabel('# Students', color=GREEN, fontsize=10)
    ax4b.tick_params(axis='y', labelcolor=GREEN)
    for bar, val in zip(bars4, deg_gpa.values):
        ax4.text(bar.get_x() + bar.get_width()/2, val + 0.5,
                 f'{val:.1f}', ha='center', fontsize=11, color=TEXT_MAIN, fontweight='bold')
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(deg_gpa.index, fontsize=11)
    ax4.set_ylabel('Average GPA', fontsize=10)
    ax4.set_title('GPA & Enrollment by Degree Level', fontsize=13, fontweight='bold', pad=10)
    ax4.set_ylim(0, 105)
    ax4.grid(axis='y', alpha=0.3)
    ax4b.legend(loc='upper right', fontsize=9)

    plt.savefig('/home/claude/page1_overview.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
    plt.close()
    print("  ✓ Page 1: Overview Dashboard")


def page2_gpa_deep(students, programs, departments):
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle('GPA DEEP DIVE: DISTRIBUTION, GENDER & PROGRAM ANALYSIS',
                 fontsize=18, fontweight='bold', color=TEXT_MAIN, y=0.98)

    stu_prog = students.merge(programs[['program_id','program_code','department_id']], on='program_id')
    stu_dept = stu_prog.merge(departments[['department_id','department_name']], on='department_id')

    ax = axes[0, 0]
    gpas = students['gpa'].dropna()
    ax.hist(gpas, bins=18, color=BLUE, alpha=0.85, edgecolor=DARK_BG, linewidth=0.8)
    ax.axvline(gpas.mean(), color=RED, linestyle='--', linewidth=2, label=f'Mean: {gpas.mean():.2f}')
    ax.axvline(gpas.median(), color=GOLD, linestyle=':', linewidth=2, label=f'Median: {gpas.median():.2f}')
    mu, std = gpas.mean(), gpas.std()
    x = np.linspace(gpas.min()-2, gpas.max()+2, 200)
    ax2_twin = ax.twinx()
    ax2_twin.plot(x, stats.norm.pdf(x, mu, std), color=GREEN, linewidth=2, alpha=0.8, label='Normal fit')
    ax2_twin.set_ylabel('Density', color=GREEN, fontsize=9)
    ax2_twin.tick_params(axis='y', labelcolor=GREEN)
    ax.set_xlabel('GPA', fontsize=10); ax.set_ylabel('Count', fontsize=10)
    ax.set_title('Overall GPA Distribution', fontsize=13, fontweight='bold', pad=8)
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax.legend(lines1+lines2, labels1+labels2, fontsize=8)
    ax.grid(alpha=0.3)

    ax = axes[0, 1]
    for gender, col in [('Male', BLUE), ('Female', RED)]:
        g = students[students['gender'] == gender]['gpa'].dropna()
        ax.hist(g, bins=12, alpha=0.6, color=col, label=f'{gender} (n={len(g)}, μ={g.mean():.1f})',
                edgecolor=DARK_BG)
    ax.set_xlabel('GPA', fontsize=10); ax.set_ylabel('Count', fontsize=10)
    ax.set_title('GPA Distribution by Gender', fontsize=13, fontweight='bold', pad=8)
    ax.legend(fontsize=9); ax.grid(alpha=0.3)

    t_stat, p_val = stats.ttest_ind(
        students[students['gender']=='Male']['gpa'].dropna(),
        students[students['gender']=='Female']['gpa'].dropna())
    ax.text(0.05, 0.92, f't={t_stat:.2f}, p={p_val:.3f}',
            transform=ax.transAxes, fontsize=8.5, color=TEXT_SUB,
            bbox={'facecolor': CARD_BG, 'alpha': 0.8, 'edgecolor': GRID_LINE, 'pad': 4})

    ax = axes[0, 2]
    gender_stats = students.groupby('gender')['gpa'].agg(['mean','std','count']).reset_index()
    colors_g = [BLUE, RED]
    bars = ax.bar(gender_stats['gender'], gender_stats['mean'],
                  yerr=gender_stats['std'], color=colors_g, alpha=0.85,
                  capsize=6, error_kw={'ecolor': TEXT_SUB, 'linewidth': 1.5}, width=0.4)
    for bar, (_, row) in zip(bars, gender_stats.iterrows()):
        ax.text(bar.get_x() + bar.get_width()/2, row['mean'] + row['std'] + 1,
                f"{row['mean']:.1f}\n(n={int(row['count'])})",
                ha='center', fontsize=10, color=TEXT_MAIN, fontweight='bold')
    ax.set_ylabel('Average GPA', fontsize=10)
    ax.set_title('Mean GPA ± Std Dev by Gender', fontsize=13, fontweight='bold', pad=8)
    ax.set_ylim(0, 105); ax.grid(axis='y', alpha=0.3)

    ax = axes[1, 0]
    city_gpa = students.groupby('city')['gpa'].agg(['mean','count']).reset_index()
    city_gpa = city_gpa[city_gpa['count'] >= 2].sort_values('mean', ascending=False)
    bar_cols = [RED if i == 0 else BLUE for i in range(len(city_gpa))]
    bars = ax.bar(city_gpa['city'], city_gpa['mean'], color=bar_cols, alpha=0.9)
    for bar, (_, row) in zip(bars, city_gpa.iterrows()):
        ax.text(bar.get_x() + bar.get_width()/2, row['mean'] + 0.5,
                f"{row['mean']:.1f}\n(n={int(row['count'])})",
                ha='center', fontsize=9, color=TEXT_MAIN)
    ax.set_ylabel('Average GPA', fontsize=10)
    ax.set_title('GPA by City of Origin', fontsize=13, fontweight='bold', pad=8)
    ax.set_ylim(0, 105); ax.grid(axis='y', alpha=0.3)

    ax = axes[1, 1]
    students['enrollment_year'] = pd.to_datetime(students['enrollment_date']).dt.year
    cohort_gpa = students.groupby('enrollment_year')['gpa'].agg(['mean','std']).reset_index()
    ax.fill_between(cohort_gpa['enrollment_year'],
                    cohort_gpa['mean'] - cohort_gpa['std'],
                    cohort_gpa['mean'] + cohort_gpa['std'],
                    alpha=0.25, color=BLUE)
    ax.plot(cohort_gpa['enrollment_year'], cohort_gpa['mean'],
            'o-', color=RED, linewidth=2.5, markersize=9, markerfacecolor=GOLD)
    for _, row in cohort_gpa.iterrows():
        ax.text(row['enrollment_year'], row['mean'] + row['std'] + 1,
                f"{row['mean']:.1f}", ha='center', fontsize=10, color=TEXT_MAIN)
    ax.set_xlabel('Enrollment Year', fontsize=10)
    ax.set_ylabel('Average GPA', fontsize=10)
    ax.set_title('GPA Trend by Enrollment Cohort', fontsize=13, fontweight='bold', pad=8)
    ax.set_ylim(70, 100); ax.grid(alpha=0.3)

    ax = axes[1, 2]
    prog_gpa = stu_dept.groupby('department_name')['gpa'].agg(['mean','std']).reset_index().sort_values('mean')
    short = [n[:12] + '…' if len(n) > 12 else n for n in prog_gpa['department_name']]
    ax.barh(short, prog_gpa['mean'], xerr=prog_gpa['std'],
            color=PALETTE[:len(prog_gpa)], alpha=0.85, height=0.6,
            error_kw={'ecolor': TEXT_SUB, 'linewidth': 1.5, 'capsize': 4})
    ax.axvline(students['gpa'].mean(), color=GOLD, linestyle='--',
               linewidth=1.5, label=f'Overall avg: {students["gpa"].mean():.1f}')
    ax.set_xlabel('Average GPA', fontsize=10)
    ax.set_title('Department GPA with Std Deviation', fontsize=13, fontweight='bold', pad=8)
    ax.legend(fontsize=9); ax.grid(axis='x', alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('/home/claude/page2_gpa.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
    plt.close()
    print("  ✓ Page 2: GPA Deep Dive")


def page3_enrollment_courses(enrollments, sections, courses, semesters, departments):
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle('ENROLLMENT & COURSE PERFORMANCE ANALYSIS',
                 fontsize=18, fontweight='bold', color=TEXT_MAIN, y=0.98)

    enr_sec = enrollments.merge(sections[['section_id','course_id','semester_id']], on='section_id')
    enr_full = enr_sec.merge(courses[['course_id','course_name','course_code','department_id','course_level']], on='course_id')
    enr_full = enr_full.merge(semesters[['semester_id','semester_name']], on='semester_id')
    enr_full = enr_full.merge(departments[['department_id','department_name']], on='department_id')

    ax = axes[0, 0]
    status_counts = enrollments['status'].value_counts()
    wedge_cols = [GREEN, BLUE, GOLD, RED, PURPLE][:len(status_counts)]
    wedges, texts, autos = ax.pie(status_counts.values, labels=status_counts.index,
                                   colors=wedge_cols, autopct='%1.1f%%', startangle=90,
                                   pctdistance=0.78,
                                   wedgeprops={'edgecolor': DARK_BG, 'linewidth': 2})
    for t in texts: t.set_color(TEXT_SUB); t.set_fontsize(9)
    for at in autos: at.set_color(TEXT_MAIN); at.set_fontsize(9); at.set_fontweight('bold')
    ax.set_title('Enrollment Status Breakdown', fontsize=13, fontweight='bold', pad=8)

    ax = axes[0, 1]
    completed = enr_full[enr_full['status'] == 'Completed']
    dept_perf = completed.groupby('department_name')['overall_grade'].mean().sort_values()
    short = [n[:10]+'…' if len(n)>10 else n for n in dept_perf.index]
    bar_cols = [GREEN if v >= 85 else BLUE if v >= 78 else RED for v in dept_perf.values]
    bars = ax.barh(short, dept_perf.values, color=bar_cols, height=0.6, alpha=0.9)
    ax.axvline(dept_perf.mean(), color=GOLD, linestyle='--', linewidth=1.5)
    for bar, val in zip(bars, dept_perf.values):
        ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}', va='center', fontsize=8.5, color=TEXT_MAIN)
    ax.set_xlabel('Avg Overall Grade', fontsize=10)
    ax.set_title('Avg Course Grade by Department', fontsize=13, fontweight='bold', pad=8)
    ax.set_xlim(0, 102); ax.grid(axis='x', alpha=0.3)

    ax = axes[0, 2]
    level_perf = completed.groupby('course_level')['overall_grade'].agg(['mean','std','count']).reset_index()
    level_perf['course_level'] = level_perf['course_level'].astype(str)
    bars = ax.bar(level_perf['course_level'], level_perf['mean'],
                  yerr=level_perf['std'], color=PALETTE[:len(level_perf)],
                  alpha=0.85, capsize=6, error_kw={'ecolor': TEXT_SUB, 'linewidth': 1.5})
    for bar, (_, row) in zip(bars, level_perf.iterrows()):
        ax.text(bar.get_x() + bar.get_width()/2, 2,
                f"n={int(row['count'])}", ha='center', fontsize=8, color=TEXT_MAIN)
    ax.set_xlabel('Course Level', fontsize=10); ax.set_ylabel('Avg Grade', fontsize=10)
    ax.set_title('Performance by Course Level', fontsize=13, fontweight='bold', pad=8)
    ax.set_ylim(0, 105); ax.grid(axis='y', alpha=0.3)

    ax = axes[1, 0]
    ax.scatter(completed['attendance_percentage'], completed['overall_grade'],
               alpha=0.6, color=BLUE, edgecolors=RED, linewidths=0.5, s=60)
    att = completed['attendance_percentage'].dropna()
    ovr = completed.loc[att.index, 'overall_grade'].dropna()
    common = att.index.intersection(ovr.index)
    if len(common) > 2:
        m, b, r, p, _ = stats.linregress(att[common], ovr[common])
        x_line = np.linspace(att.min(), att.max(), 100)
        ax.plot(x_line, m*x_line + b, color=GOLD, linewidth=2,
                label=f'r={r:.3f}, p={p:.3f}')
        ax.legend(fontsize=9)
    ax.set_xlabel('Attendance %', fontsize=10)
    ax.set_ylabel('Overall Grade', fontsize=10)
    ax.set_title('Attendance vs Grade Correlation', fontsize=13, fontweight='bold', pad=8)
    ax.grid(alpha=0.3)

    ax = axes[1, 1]
    completed2 = completed.dropna(subset=['midterm_grade','final_grade'])
    ax.scatter(completed2['midterm_grade'], completed2['final_grade'],
               alpha=0.65, color=RED, edgecolors=GOLD, linewidths=0.5, s=65)
    lims = [min(completed2['midterm_grade'].min(), completed2['final_grade'].min()) - 2,
            max(completed2['midterm_grade'].max(), completed2['final_grade'].max()) + 2]
    ax.plot(lims, lims, '--', color=TEXT_SUB, linewidth=1.5, alpha=0.7, label='Equal line')
    m, b, r, p, _ = stats.linregress(completed2['midterm_grade'], completed2['final_grade'])
    x_l = np.linspace(lims[0], lims[1], 100)
    ax.plot(x_l, m*x_l + b, color=GREEN, linewidth=2, label=f'r={r:.3f}')
    ax.set_xlabel('Midterm Grade', fontsize=10); ax.set_ylabel('Final Grade', fontsize=10)
    ax.set_title('Midterm vs Final Grade', fontsize=13, fontweight='bold', pad=8)
    ax.legend(fontsize=9); ax.grid(alpha=0.3)

    ax = axes[1, 2]
    improvement = completed2.copy()
    improvement['delta'] = improvement['final_grade'] - improvement['midterm_grade']
    delta_bins = pd.cut(improvement['delta'], bins=[-15,-5,-2,0,2,5,15],
                        labels=['≤-5','(-5,-2]','(-2,0]','(0,2]','(2,5]','>5'])
    delta_counts = delta_bins.value_counts().sort_index()
    cols_delta = [RED, '#E67E22', GOLD, '#AED6F1', BLUE, GREEN]
    ax.bar(delta_counts.index, delta_counts.values, color=cols_delta, alpha=0.9, edgecolor=DARK_BG)
    ax.set_xlabel('Final − Midterm Grade (Δ)', fontsize=10)
    ax.set_ylabel('# Students', fontsize=10)
    ax.set_title('Grade Improvement Distribution', fontsize=13, fontweight='bold', pad=8)
    avg_delta = improvement['delta'].mean()
    ax.axvline(delta_bins.cat.categories.get_loc(
        delta_bins[improvement['delta'].sub(avg_delta).abs().idxmin()]),
               color=GOLD, linestyle='--', linewidth=1.5, alpha=0.7)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('/home/claude/page3_courses.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
    plt.close()
    print("  ✓ Page 3: Enrollment & Course Performance")


def page4_instructors_scholarships(students, instructors, departments, enrollments,
                                   sections, scholarships, stu_sch):
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle('INSTRUCTOR EFFECTIVENESS & SCHOLARSHIP ANALYSIS',
                 fontsize=18, fontweight='bold', color=TEXT_MAIN, y=0.98)

    enr_sec = enrollments[enrollments['status']=='Completed'].merge(
        sections[['section_id','instructor_id']], on='section_id')
    instr_perf = enr_sec.groupby('instructor_id').agg(
        avg_grade=('overall_grade','mean'),
        students_taught=('student_id','nunique'),
        sections_count=('section_id','nunique')
    ).reset_index()
    instr_full = instr_perf.merge(
        instructors[['instructor_id','first_name','last_name','title','department_id']], on='instructor_id')
    instr_full = instr_full.merge(departments[['department_id','department_name']], on='department_id')
    instr_full['name'] = instr_full['first_name'] + ' ' + instr_full['last_name']

    ax = axes[0, 0]
    instr_sorted = instr_full.sort_values('avg_grade', ascending=True)
    title_colors = {'Professor': RED, 'Associate Professor': BLUE,
                    'Assistant Professor': GOLD}
    bar_cols_i = [title_colors.get(t, GREEN) for t in instr_sorted['title']]
    bars = ax.barh(instr_sorted['name'], instr_sorted['avg_grade'],
                   color=bar_cols_i, height=0.6, alpha=0.9)
    for bar, val in zip(bars, instr_sorted['avg_grade']):
        ax.text(val + 0.2, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}', va='center', fontsize=8, color=TEXT_MAIN)
    legend_patches = [mpatches.Patch(color=c, label=t) for t, c in title_colors.items()]
    ax.legend(handles=legend_patches, fontsize=8, loc='lower right')
    ax.set_xlabel('Avg Student Grade', fontsize=10)
    ax.set_title('Instructor Performance Ranking', fontsize=13, fontweight='bold', pad=8)
    ax.grid(axis='x', alpha=0.3)

    ax = axes[0, 1]
    scatter_colors = [PALETTE[i % len(PALETTE)] for i in range(len(instr_full))]
    ax.scatter(instr_full['students_taught'], instr_full['avg_grade'],
               s=instr_full['sections_count']*120, alpha=0.75,
               c=scatter_colors, edgecolors=TEXT_SUB, linewidths=0.8)
    for _, row in instr_full.iterrows():
        ax.annotate(row['last_name'], (row['students_taught'], row['avg_grade']),
                    textcoords='offset points', xytext=(5, 3), fontsize=7.5, color=TEXT_SUB)
    ax.set_xlabel('Total Students Taught', fontsize=10)
    ax.set_ylabel('Avg Student Grade', fontsize=10)
    ax.set_title('Instructor Load vs Performance\n(bubble size = sections taught)',
                 fontsize=12, fontweight='bold', pad=8)
    ax.grid(alpha=0.3)

    ax = axes[0, 2]
    title_perf = instr_full.groupby('title')['avg_grade'].agg(['mean','std','count']).reset_index()
    t_cols = [title_colors.get(t, GREEN) for t in title_perf['title']]
    bars = ax.bar(title_perf['title'], title_perf['mean'],
                  yerr=title_perf['std'], color=t_cols, alpha=0.85, width=0.5,
                  capsize=6, error_kw={'ecolor': TEXT_SUB, 'linewidth': 1.5})
    for bar, (_, row) in zip(bars, title_perf.iterrows()):
        ax.text(bar.get_x() + bar.get_width()/2, row['mean'] + row['std'] + 0.8,
                f"{row['mean']:.1f}\n(n={int(row['count'])})",
                ha='center', fontsize=9, color=TEXT_MAIN)
    ax.set_ylabel('Avg Student Grade', fontsize=10)
    ax.set_title('Student Performance by Instructor Title', fontsize=13, fontweight='bold', pad=8)
    ax.set_ylim(0, 105); ax.grid(axis='y', alpha=0.3)

    ax = axes[1, 0]
    stu_sch_full = stu_sch.merge(scholarships[['scholarship_id','scholarship_name','amount']], on='scholarship_id')
    stu_sch_full = stu_sch_full.merge(students[['student_id','gpa']], on='student_id')
    sch_stats = stu_sch_full.groupby('scholarship_name').agg(
        recipients=('student_id','count'),
        avg_gpa=('gpa','mean'),
        total_awarded=('amount','sum')
    ).reset_index()
    short_names = [n[:22]+'…' if len(n)>22 else n for n in sch_stats['scholarship_name']]
    bars = ax.barh(short_names, sch_stats['total_awarded']/1000,
                   color=PALETTE[:len(sch_stats)], height=0.6, alpha=0.9)
    for bar, (_, row) in zip(bars, sch_stats.iterrows()):
        ax.text(bar.get_width() + 30, bar.get_y() + bar.get_height()/2,
                f"n={int(row['recipients'])}, GPA={row['avg_gpa']:.1f}",
                va='center', fontsize=8, color=TEXT_SUB)
    ax.set_xlabel('Total Awarded (× 1,000 AMD)', fontsize=10)
    ax.set_title('Scholarship Distribution', fontsize=13, fontweight='bold', pad=8)
    ax.grid(axis='x', alpha=0.3)

    ax = axes[1, 1]
    ax.scatter(students['gpa'], students['scholarship_amount']/1000,
               alpha=0.65, color=GOLD, edgecolors=RED, linewidths=0.5, s=70)
    m, b, r, p, _ = stats.linregress(students['gpa'].dropna(),
                                     students['scholarship_amount'].dropna())
    x_l = np.linspace(students['gpa'].min(), students['gpa'].max(), 100)
    ax.plot(x_l, (m*x_l + b)/1000, color=BLUE, linewidth=2.5,
            label=f'r={r:.3f}, p={p:.3f}')
    ax.set_xlabel('GPA', fontsize=10)
    ax.set_ylabel('Scholarship Amount (× 1,000 AMD)', fontsize=10)
    ax.set_title('GPA vs Scholarship Correlation', fontsize=13, fontweight='bold', pad=8)
    ax.legend(fontsize=9); ax.grid(alpha=0.3)

    ax = axes[1, 2]
    students['has_scholarship'] = students['scholarship_amount'] > 0
    grps = [students[students['has_scholarship']]['gpa'].dropna(),
            students[~students['has_scholarship']]['gpa'].dropna()]
    bp = ax.boxplot(grps, patch_artist=True,
                    medianprops={'color': GOLD, 'linewidth': 2.5},
                    labels=['With\nScholarship', 'Without\nScholarship'])
    bp['boxes'][0].set_facecolor(BLUE); bp['boxes'][0].set_alpha(0.7)
    bp['boxes'][1].set_facecolor(RED); bp['boxes'][1].set_alpha(0.7)
    t, p = stats.ttest_ind(grps[0], grps[1])
    sig = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'n.s.'
    ax.text(0.5, 0.95, f't={t:.2f}, p={p:.3f} {sig}',
            transform=ax.transAxes, ha='center', fontsize=9, color=TEXT_SUB,
            bbox={'facecolor': CARD_BG, 'alpha': 0.8, 'edgecolor': GRID_LINE, 'pad': 4})
    ax.set_ylabel('GPA', fontsize=10)
    ax.set_title('GPA: Scholarship vs No Scholarship', fontsize=13, fontweight='bold', pad=8)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('/home/claude/page4_instructors.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
    plt.close()
    print("  ✓ Page 4: Instructors & Scholarships")


def page5_extracurricular_credits(students, programs, departments, stu_act, activities, enrollments):
    fig, axes = plt.subplots(2, 3, figsize=(22, 12))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle('EXTRACURRICULAR ACTIVITIES, CREDITS & STUDENT PROFILES',
                 fontsize=18, fontweight='bold', color=TEXT_MAIN, y=0.98)

    act_count = stu_act.groupby('student_id').size().reset_index(name='activity_count')
    stu_act_merged = students.merge(act_count, on='student_id', how='left').fillna({'activity_count': 0})
    stu_act_merged['activity_count'] = stu_act_merged['activity_count'].astype(int)

    ax = axes[0, 0]
    for n_act in sorted(stu_act_merged['activity_count'].unique()):
        subset = stu_act_merged[stu_act_merged['activity_count'] == n_act]['gpa'].dropna()
        if len(subset) > 0:
            ax.scatter([n_act]*len(subset), subset, alpha=0.55,
                       color=PALETTE[int(n_act)], s=60, edgecolors=TEXT_SUB, linewidths=0.4)
    act_means = stu_act_merged.groupby('activity_count')['gpa'].mean()
    ax.plot(act_means.index, act_means.values, 'o-', color=GOLD,
            linewidth=2.5, markersize=9, zorder=5, label='Group mean')
    m, b, r, p, _ = stats.linregress(stu_act_merged['activity_count'], stu_act_merged['gpa'].fillna(stu_act_merged['gpa'].mean()))
    x_l = np.linspace(0, stu_act_merged['activity_count'].max(), 100)
    ax.plot(x_l, m*x_l + b, '--', color=RED, linewidth=2,
            label=f'Trend r={r:.3f}')
    ax.set_xlabel('# Extracurricular Activities', fontsize=10)
    ax.set_ylabel('GPA', fontsize=10)
    ax.set_title('Activities vs GPA Relationship', fontsize=13, fontweight='bold', pad=8)
    ax.legend(fontsize=9); ax.grid(alpha=0.3)

    ax = axes[0, 1]
    act_type = activities[['activity_id','activity_type']].merge(
        stu_act[['student_id','activity_id']], on='activity_id')
    act_type = act_type.merge(students[['student_id','gpa']], on='student_id')
    type_gpa = act_type.groupby('activity_type')['gpa'].agg(['mean','std','count']).reset_index().sort_values('mean')
    ax.barh(type_gpa['activity_type'], type_gpa['mean'],
            xerr=type_gpa['std'], color=PALETTE[:len(type_gpa)],
            height=0.5, alpha=0.85, error_kw={'ecolor': TEXT_SUB, 'linewidth': 1.5, 'capsize': 4})
    for i, (_, row) in enumerate(type_gpa.iterrows()):
        ax.text(row['mean'] + row['std'] + 0.4, i,
                f"n={int(row['count'])}, μ={row['mean']:.1f}",
                va='center', fontsize=8, color=TEXT_SUB)
    ax.set_xlabel('Average GPA', fontsize=10)
    ax.set_title('GPA by Activity Type', fontsize=13, fontweight='bold', pad=8)
    ax.grid(axis='x', alpha=0.3)

    ax = axes[0, 2]
    activity_pop = stu_act.groupby('activity_id').size().reset_index(name='members')
    activity_pop = activity_pop.merge(activities[['activity_id','activity_name','activity_type']], on='activity_id').sort_values('members', ascending=False)
    short_act = [n[:18]+'…' if len(n)>18 else n for n in activity_pop['activity_name']]
    ax.bar(range(len(activity_pop)), activity_pop['members'],
           color=PALETTE[:len(activity_pop)], alpha=0.9)
    ax.set_xticks(range(len(activity_pop)))
    ax.set_xticklabels(short_act, rotation=35, ha='right', fontsize=8)
    ax.set_ylabel('# Members', fontsize=10)
    ax.set_title('Activity Membership Count', fontsize=13, fontweight='bold', pad=8)
    ax.grid(axis='y', alpha=0.3)

    ax = axes[1, 0]
    stu_prog = students.merge(programs[['program_id','program_code','department_id']], on='program_id')
    stu_dept2 = stu_prog.merge(departments[['department_id','department_name']], on='department_id')
    dept_credits = stu_dept2.groupby('department_name')['total_credits_earned'].mean().sort_values(ascending=False)
    short_d = [n[:12]+'…' if len(n)>12 else n for n in dept_credits.index]
    bars = ax.bar(range(len(dept_credits)), dept_credits.values,
                  color=PALETTE[:len(dept_credits)], alpha=0.9)
    ax.set_xticks(range(len(dept_credits)))
    ax.set_xticklabels(short_d, rotation=35, ha='right', fontsize=8)
    for bar, val in zip(bars, dept_credits.values):
        ax.text(bar.get_x() + bar.get_width()/2, val + 0.5,
                f'{val:.0f}', ha='center', fontsize=8.5, color=TEXT_MAIN)
    ax.set_ylabel('Avg Credits Earned', fontsize=10)
    ax.set_title('Avg Credits Earned by Department', fontsize=13, fontweight='bold', pad=8)
    ax.grid(axis='y', alpha=0.3)

    ax = axes[1, 1]
    ax.scatter(students['total_credits_earned'], students['gpa'],
               alpha=0.65, c=PALETTE[0], edgecolors=GOLD, linewidths=0.5, s=65)
    m, b, r, p, _ = stats.linregress(students['total_credits_earned'].dropna(),
                                     students['gpa'].dropna())
    x_l = np.linspace(students['total_credits_earned'].min(),
                      students['total_credits_earned'].max(), 100)
    ax.plot(x_l, m*x_l + b, color=RED, linewidth=2.5,
            label=f'r={r:.3f}, p={p:.3f}')
    ax.set_xlabel('Total Credits Earned', fontsize=10)
    ax.set_ylabel('GPA', fontsize=10)
    ax.set_title('Credits Earned vs GPA', fontsize=13, fontweight='bold', pad=8)
    ax.legend(fontsize=9); ax.grid(alpha=0.3)

    ax = axes[1, 2]
    top10 = students.nlargest(10, 'gpa')[['first_name','last_name','gpa','total_credits_earned','scholarship_amount']].copy()
    top10['name'] = top10['first_name'] + '\n' + top10['last_name']
    top10 = top10.sort_values('gpa')
    bar_colors_t = [GREEN if v >= 92 else BLUE for v in top10['gpa']]
    bars = ax.barh(top10['name'], top10['gpa'], color=bar_colors_t, height=0.6, alpha=0.9)
    for bar, (_, row) in zip(bars, top10.iterrows()):
        schol_str = f"  AMD {int(row['scholarship_amount']):,}" if row['scholarship_amount'] > 0 else ''
        ax.text(row['gpa'] + 0.15, bar.get_y() + bar.get_height()/2,
                f"{row['gpa']:.1f}{schol_str}", va='center', fontsize=7.5, color=TEXT_MAIN)
    ax.set_xlabel('GPA', fontsize=10)
    ax.set_title('Top 10 Students by GPA', fontsize=13, fontweight='bold', pad=8)
    ax.set_xlim(84, 100); ax.grid(axis='x', alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('/home/claude/page5_activities.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
    plt.close()
    print("  ✓ Page 5: Extracurricular & Credits")


def page6_heatmaps_correlations(students, departments, programs, enrollments, sections, courses, stu_act, activities):
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle('CORRELATION MATRICES & HEATMAP ANALYSIS',
                 fontsize=18, fontweight='bold', color=TEXT_MAIN, y=0.98)

    cmap_custom = LinearSegmentedColormap.from_list(
        'custom', [BLUE, CARD_BG, RED])

    ax = axes[0, 0]
    act_count = stu_act.groupby('student_id').size().reset_index(name='activity_count')
    enr_count = enrollments.groupby('student_id').size().reset_index(name='enrollment_count')
    stu_enr = students.merge(act_count, on='student_id', how='left').fillna({'activity_count': 0})
    stu_enr = stu_enr.merge(enr_count, on='student_id', how='left').fillna({'enrollment_count': 0})
    corr_df = stu_enr[['gpa','total_credits_earned','scholarship_amount',
                        'activity_count','enrollment_count']].rename(columns={
        'total_credits_earned':'credits', 'scholarship_amount':'scholarship',
        'activity_count':'activities', 'enrollment_count':'enrollments'})
    corr_matrix = corr_df.corr()
    sns.heatmap(corr_matrix, ax=ax, cmap=cmap_custom, annot=True, fmt='.3f',
                linewidths=1, linecolor=DARK_BG,
                annot_kws={'size': 11, 'color': TEXT_MAIN},
                cbar_kws={'shrink': 0.8})
    ax.set_title('Student Metrics Correlation Matrix', fontsize=13, fontweight='bold', pad=10)
    ax.tick_params(axis='x', rotation=30, labelsize=9)
    ax.tick_params(axis='y', rotation=0, labelsize=9)

    ax = axes[0, 1]
    stu_prog = students.merge(programs[['program_id','department_id']], on='program_id')
    stu_dept = stu_prog.merge(departments[['department_id','department_name']], on='department_id')
    enr_sec = enrollments[enrollments['status']=='Completed'].merge(
        sections[['section_id','course_id']], on='section_id')
    enr_course = enr_sec.merge(courses[['course_id','course_name','department_id']], on='course_id')
    enr_course = enr_course.merge(departments[['department_id','department_name']], on='department_id')

    piv = enr_course.groupby(['department_name','course_name'])['overall_grade'].mean().unstack(fill_value=0)
    piv_short = piv.copy()
    piv_short.columns = [c[:15]+'…' if len(c)>15 else c for c in piv.columns]
    piv_short.index  = [i[:12]+'…' if len(i)>12 else i for i in piv.index]
    piv_plot = piv_short.replace(0, np.nan)
    sns.heatmap(piv_plot, ax=ax, cmap='YlOrRd', annot=True, fmt='.0f',
                linewidths=0.5, linecolor=DARK_BG,
                annot_kws={'size': 7},
                cbar_kws={'shrink': 0.8},
                mask=piv_plot.isna())
    ax.set_title('Dept × Course Average Grade Heatmap', fontsize=13, fontweight='bold', pad=10)
    ax.tick_params(axis='x', rotation=45, labelsize=6.5)
    ax.tick_params(axis='y', rotation=0, labelsize=7.5)

    ax = axes[1, 0]
    enr_att = enrollments[enrollments['status']=='Completed'].dropna(subset=['attendance_percentage','overall_grade'])
    att_bins = pd.cut(enr_att['attendance_percentage'], bins=[0,70,80,90,95,100],
                      labels=['<70','70-80','80-90','90-95','95-100'])
    grade_bins = pd.cut(enr_att['overall_grade'], bins=[0,60,70,80,90,100],
                        labels=['<60','60-70','70-80','80-90','90-100'])
    heatmap_data = pd.crosstab(att_bins, grade_bins)
    sns.heatmap(heatmap_data, ax=ax, cmap='Blues', annot=True, fmt='d',
                linewidths=1, linecolor=DARK_BG,
                annot_kws={'size': 12, 'color': TEXT_MAIN},
                cbar_kws={'shrink': 0.8})
    ax.set_xlabel('Grade Range', fontsize=10)
    ax.set_ylabel('Attendance Range (%)', fontsize=10)
    ax.set_title('Attendance vs Grade Frequency Heatmap', fontsize=13, fontweight='bold', pad=10)

    ax = axes[1, 1]
    stu_prog2 = students.merge(programs[['program_id','program_name','degree_level']], on='program_id')
    stu_prog2['standing'] = pd.cut(stu_prog2['gpa'],
        bins=[0,60,70,80,90,100],
        labels=['At Risk\n<60','Passing\n60-70','Satisfactory\n70-80','Good\n80-90','Excellent\n90+'])
    pivot_stand = pd.crosstab(stu_prog2['degree_level'], stu_prog2['standing'])
    pivot_norm  = pivot_stand.div(pivot_stand.sum(axis=1), axis=0) * 100
    pivot_norm.plot(kind='bar', ax=ax, stacked=True,
                    color=['#E74C3C','#E67E22','#F1C40F','#3498DB','#2ECC71'],
                    alpha=0.9, width=0.5)
    ax.set_xlabel('Degree Level', fontsize=10)
    ax.set_ylabel('% of Students', fontsize=10)
    ax.set_title('Academic Standing by Degree Level', fontsize=13, fontweight='bold', pad=10)
    ax.legend(title='Standing', fontsize=8, title_fontsize=9, loc='lower right')
    ax.tick_params(axis='x', rotation=0)
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig('/home/claude/page6_heatmaps.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
    plt.close()
    print("  ✓ Page 6: Heatmaps & Correlations")


def page7_statistical_summary(students, departments, programs, enrollments, sections, instructors):
    fig = plt.figure(figsize=(22, 16))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle('STATISTICAL SUMMARY & ADVANCED ANALYSIS',
                 fontsize=18, fontweight='bold', color=TEXT_MAIN, y=0.98)
    gs = gridspec.GridSpec(3, 3, figure=fig, hspace=0.55, wspace=0.38)

    stu_prog = students.merge(programs[['program_id','department_id','degree_level']], on='program_id')
    stu_dept = stu_prog.merge(departments[['department_id','department_name']], on='department_id')

    ax1 = fig.add_subplot(gs[0, :2])
    dept_data = [stu_dept[stu_dept['department_name'] == d]['gpa'].dropna().values
                 for d in departments['department_name']]
    short_dept = [n[:14]+'…' if len(n)>14 else n for n in departments['department_name']]
    vp = ax1.violinplot(dept_data, positions=range(len(dept_data)), showmedians=True,
                        showextrema=True)
    for i, body in enumerate(vp['bodies']):
        body.set_facecolor(PALETTE[i % len(PALETTE)])
        body.set_alpha(0.7)
    vp['cmedians'].set_color(GOLD)
    vp['cmedians'].set_linewidth(2)
    vp['cbars'].set_color(TEXT_SUB)
    vp['cmaxes'].set_color(GREEN)
    vp['cmins'].set_color(RED)
    ax1.set_xticks(range(len(short_dept)))
    ax1.set_xticklabels(short_dept, rotation=30, ha='right', fontsize=8.5)
    ax1.set_ylabel('GPA', fontsize=10)
    ax1.set_title('GPA Violin Plot by Department', fontsize=13, fontweight='bold', pad=8)
    ax1.grid(axis='y', alpha=0.3)

    ax2 = fig.add_subplot(gs[0, 2])
    f_stat, p_val = stats.f_oneway(*[g for g in dept_data if len(g) > 0])
    stats_text = (
        f"ONE-WAY ANOVA\n"
        f"─────────────────────\n"
        f"F-statistic : {f_stat:.4f}\n"
        f"p-value     : {p_val:.4f}\n"
        f"Significant : {'YES ✓' if p_val < 0.05 else 'NO ✗'}\n\n"
        f"OVERALL GPA STATS\n"
        f"─────────────────────\n"
        f"Mean        : {students['gpa'].mean():.3f}\n"
        f"Median      : {students['gpa'].median():.3f}\n"
        f"Std Dev     : {students['gpa'].std():.3f}\n"
        f"Skewness    : {stats.skew(students['gpa'].dropna()):.3f}\n"
        f"Kurtosis    : {stats.kurtosis(students['gpa'].dropna()):.3f}\n"
        f"Min         : {students['gpa'].min():.1f}\n"
        f"Max         : {students['gpa'].max():.1f}\n"
        f"IQR         : {students['gpa'].quantile(0.75)-students['gpa'].quantile(0.25):.2f}"
    )
    ax2.text(0.05, 0.95, stats_text, transform=ax2.transAxes,
             fontsize=9.5, va='top', ha='left', color=TEXT_MAIN,
             fontfamily='monospace',
             bbox={'facecolor': CARD_BG, 'edgecolor': GOLD,
                   'boxstyle': 'round,pad=0.6', 'linewidth': 1.5})
    ax2.axis('off')
    ax2.set_title('Statistical Tests', fontsize=13, fontweight='bold', pad=8)

    ax3 = fig.add_subplot(gs[1, :2])
    enr_sec = enrollments[enrollments['status']=='Completed'].merge(
        sections[['section_id','course_id','instructor_id']], on='section_id')
    enr_sec = enr_sec.merge(
        instructors[['instructor_id','first_name','last_name']], on='instructor_id')
    enr_sec['instructor'] = enr_sec['first_name'] + ' ' + enr_sec['last_name']
    instr_grades = enr_sec.groupby('instructor')['overall_grade'].apply(list)
    instr_means  = enr_sec.groupby('instructor')['overall_grade'].mean().sort_values()
    positions = range(len(instr_means))
    for i, (name, mean_val) in enumerate(instr_means.items()):
        grades = instr_grades[name]
        ax3.scatter([i]*len(grades), grades, alpha=0.5, s=40,
                    color=PALETTE[i % len(PALETTE)], zorder=3)
        ax3.scatter(i, mean_val, s=150, color='white',
                    edgecolors=PALETTE[i % len(PALETTE)], linewidths=2, zorder=4)
    ax3.set_xticks(positions)
    ax3.set_xticklabels([n.split()[1] for n in instr_means.index], rotation=30, ha='right', fontsize=8.5)
    ax3.set_ylabel('Student Grade', fontsize=10)
    ax3.set_title('Grade Distribution per Instructor (white dot = mean)', fontsize=13, fontweight='bold', pad=8)
    ax3.grid(axis='y', alpha=0.3)

    ax4 = fig.add_subplot(gs[1, 2])
    gpas = students['gpa'].dropna()
    qq_data = np.sort(gpas.values)
    n = len(qq_data)
    theoretical_q = stats.norm.ppf(np.arange(1, n+1) / (n+1))
    ax4.scatter(theoretical_q, qq_data, alpha=0.7, color=BLUE,
                edgecolors=RED, linewidths=0.5, s=55)
    min_q, max_q = min(theoretical_q), max(theoretical_q)
    line_y = stats.norm.ppf([0.25, 0.75])
    line_x = np.quantile(qq_data, [0.25, 0.75])
    m_qq = (line_x[1] - line_x[0]) / (line_y[1] - line_y[0])
    b_qq = line_x[0] - m_qq * line_y[0]
    ax4.plot([min_q, max_q], [m_qq*min_q + b_qq, m_qq*max_q + b_qq],
             color=GOLD, linewidth=2, label='Q-Q line')
    stat_sw, p_sw = stats.shapiro(gpas)
    ax4.text(0.05, 0.95, f'Shapiro-Wilk\nW={stat_sw:.4f}\np={p_sw:.4f}',
             transform=ax4.transAxes, fontsize=8.5, va='top', color=TEXT_SUB,
             bbox={'facecolor': CARD_BG, 'edgecolor': GRID_LINE, 'pad': 4})
    ax4.set_xlabel('Theoretical Quantiles', fontsize=9)
    ax4.set_ylabel('Sample Quantiles (GPA)', fontsize=9)
    ax4.set_title('Q-Q Plot (GPA Normality)', fontsize=12, fontweight='bold', pad=8)
    ax4.legend(fontsize=8); ax4.grid(alpha=0.3)

    ax5 = fig.add_subplot(gs[2, :])
    dept_order = stu_dept.groupby('department_name')['gpa'].mean().sort_values(ascending=False).index
    plot_data = []
    labels_x = []
    colors_x = []
    for i, dept in enumerate(dept_order):
        for gender, col in [('Male', BLUE), ('Female', RED)]:
            vals = stu_dept[(stu_dept['department_name']==dept) &
                            (stu_dept['gender']==gender)]['gpa'].dropna()
            if len(vals) > 0:
                plot_data.append(vals.values)
                labels_x.append(f"{dept[:8]}\n{gender[0]}")
                colors_x.append(col)
    positions_x = range(len(plot_data))
    bp2 = ax5.boxplot(plot_data, positions=positions_x, patch_artist=True,
                      widths=0.5,
                      medianprops={'color': GOLD, 'linewidth': 1.8})
    for patch, col in zip(bp2['boxes'], colors_x):
        patch.set_facecolor(col); patch.set_alpha(0.65)
    ax5.set_xticks(positions_x)
    ax5.set_xticklabels(labels_x, fontsize=7)
    ax5.set_ylabel('GPA', fontsize=10)
    ax5.set_title('GPA Distribution by Department × Gender', fontsize=13, fontweight='bold', pad=8)
    male_patch  = mpatches.Patch(color=BLUE,  label='Male',   alpha=0.65)
    female_patch = mpatches.Patch(color=RED,  label='Female', alpha=0.65)
    ax5.legend(handles=[male_patch, female_patch], fontsize=10)
    ax5.grid(axis='y', alpha=0.3)

    plt.savefig('/home/claude/page7_stats.png', dpi=150, bbox_inches='tight', facecolor=DARK_BG)
    plt.close()
    print("  ✓ Page 7: Statistical Summary & Advanced Analysis")


def assemble_pdf():
    from PIL import Image
    pages = [
        '/home/claude/page1_overview.png',
        '/home/claude/page2_gpa.png',
        '/home/claude/page3_courses.png',
        '/home/claude/page4_instructors.png',
        '/home/claude/page5_activities.png',
        '/home/claude/page6_heatmaps.png',
        '/home/claude/page7_stats.png',
    ]
    images = [Image.open(p).convert('RGB') for p in pages]
    images[0].save(
        '/mnt/user-data/outputs/university_analysis.pdf',
        save_all=True,
        append_images=images[1:],
        resolution=150
    )
    print("  ✓ PDF assembled → university_analysis.pdf")


if __name__ == '__main__':
    print("\n═══════════════════════════════════════════════════════")
    print("  UNIVERSITY: FULL PYTHON ANALYSIS")
    print("═══════════════════════════════════════════════════════\n")

    print("► Building SQLite database...")
    build_database()

    print("► Loading data frames...")
    (students, departments, programs, instructors, courses,
     enrollments, sections, semesters, scholarships, stu_sch,
     activities, stu_act) = load_frames()

    print(f"  Loaded: {len(students)} students | {len(enrollments)} enrollments | "
          f"{len(courses)} courses | {len(instructors)} instructors\n")

    print("► Generating analysis pages...")
    page1_overview(students, departments, programs, enrollments)
    page2_gpa_deep(students, programs, departments)
    page3_enrollment_courses(enrollments, sections, courses, semesters, departments)
    page4_instructors_scholarships(students, instructors, departments, enrollments,
                                   sections, scholarships, stu_sch)
    page5_extracurricular_credits(students, programs, departments, stu_act, activities, enrollments)
    page6_heatmaps_correlations(students, departments, programs, enrollments,
                                sections, courses, stu_act, activities)
    page7_statistical_summary(students, departments, programs, enrollments, sections, instructors)

    print("\n► Assembling PDF report...")
    assemble_pdf()

    print("\n═══════════════════════════════════════════════════════")
    print("  ANALYSIS COMPLETE: 7 pages | 42 charts")
    print("═══════════════════════════════════════════════════════\n")
