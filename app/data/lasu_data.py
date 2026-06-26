"""
app/data/lasu_data.py

Hardcoded LASU faculties and departments.
Faculty codes and department codes follow the matric number format:
    Matric: YYFFDDNNN
    YY = admission year, FF = faculty code, DD = dept code, NNN = serial

Codes are 2-digit strings (zero-padded).
"""

LASU_DATA = [
    {
        "name": "Faculty of Science",
        "code": "01",
        "departments": [
            {"name": "Biochemistry",                    "code": "01"},
            {"name": "Botany",                          "code": "02"},
            {"name": "Chemistry",                       "code": "03"},
            {"name": "Computer Science",                "code": "04"},
            {"name": "Mathematics",                     "code": "05"},
            {"name": "Microbiology",                    "code": "06"},
            {"name": "Physics",                         "code": "07"},
            {"name": "Statistics",                      "code": "08"},
            {"name": "Zoology",                         "code": "09"},
        ],
    },
    {
        "name": "Faculty of Arts",
        "code": "02",
        "departments": [
            {"name": "English",                         "code": "01"},
            {"name": "French",                          "code": "02"},
            {"name": "History and International Studies","code": "03"},
            {"name": "Linguistics and African Languages","code": "04"},
            {"name": "Philosophy",                      "code": "05"},
            {"name": "Theatre and Performing Arts",     "code": "06"},
            {"name": "Yoruba",                          "code": "07"},
        ],
    },
    {
        "name": "Faculty of Communication and Media Studies",
        "code": "03",
        "departments": [
            {"name": "Mass Communication",              "code": "01"},
            {"name": "Information Resources Management","code": "02"},
        ],
    },
    {
        "name": "Faculty of Transport",
        "code": "04",
        "departments": [
            {"name": "Transport Management",            "code": "01"},
            {"name": "Maritime Management",             "code": "02"},
            {"name": "Aviation Studies",                "code": "03"},
        ],
    },
    {
        "name": "Faculty of Law",
        "code": "05",
        "departments": [
            {"name": "Private and Business Law",        "code": "01"},
            {"name": "Public and International Law",    "code": "02"},
            {"name": "Jurisprudence and Human Rights Law","code": "03"},
        ],
    },
    {
        "name": "Faculty of Engineering",
        "code": "06",
        "departments": [
            {"name": "Chemical and Polymer Engineering","code": "01"},
            {"name": "Civil Engineering",               "code": "02"},
            {"name": "Electrical and Electronics Engineering","code": "03"},
            {"name": "Mechanical Engineering",          "code": "04"},
            {"name": "Agricultural and Biosystems Engineering","code": "05"},
        ],
    },
    {
        "name": "Faculty of Management Sciences",
        "code": "07",
        "departments": [
            {"name": "Accounting",                      "code": "01"},
            {"name": "Actuarial Science and Insurance", "code": "02"},
            {"name": "Banking and Finance",             "code": "03"},
            {"name": "Business Administration",         "code": "04"},
            {"name": "Marketing",                       "code": "05"},
            {"name": "Public Administration",           "code": "06"},
            {"name": "Industrial Relations and Personnel Management","code": "07"},
        ],
    },
    {
        "name": "Faculty of Agriculture",
        "code": "08",
        "departments": [
            {"name": "Agriculture and Resource Economics","code": "01"},
            {"name": "Animal Science",                  "code": "02"},
            {"name": "Crop Production",                 "code": "03"},
            {"name": "Fisheries",                       "code": "04"},
            {"name": "Forestry and Wildlife Management","code": "05"},
            {"name": "Soil Science and Land Resources Management","code": "06"},
        ],
    },
    {
        "name": "Faculty of Social Sciences",
        "code": "09",
        "departments": [
            {"name": "Economics",                       "code": "01"},
            {"name": "Geography",                       "code": "02"},
            {"name": "Industrial Relations and Labour Studies","code": "03"},
            {"name": "Mass Communication",              "code": "04"},
            {"name": "Political Science",               "code": "05"},
            {"name": "Psychology",                      "code": "06"},
            {"name": "Sociology",                       "code": "07"},
        ],
    },
    {
        "name": "Faculty of Education",
        "code": "10",
        "departments": [
            {"name": "Arts Education",                  "code": "01"},
            {"name": "Counsellor Education",            "code": "02"},
            {"name": "Educational Management",          "code": "03"},
            {"name": "Health Education",                "code": "04"},
            {"name": "Human Kinetics and Sports Science","code": "05"},
            {"name": "Science Education",               "code": "06"},
            {"name": "Social Science Education",        "code": "07"},
            {"name": "Special Education",               "code": "08"},
        ],
    },
    {
        "name": "Faculty of Library, Archival and Information Science",
        "code": "11",
        "departments": [
            {"name": "Archival Studies",                "code": "01"},
            {"name": "Library and Information Science", "code": "02"},
        ],
    },
    {
        "name": "Faculty of Basic Medical Sciences",
        "code": "12",
        "departments": [
            {"name": "Anatomy",                         "code": "01"},
            {"name": "Physiology",                      "code": "02"},
            {"name": "Pharmacology",                    "code": "03"},
        ],
    },
    {
        "name": "Faculty of Clinical Sciences",
        "code": "13",
        "departments": [
            {"name": "Medicine and Surgery",            "code": "01"},
            {"name": "Nursing Science",                 "code": "02"},
            {"name": "Pharmacy",                        "code": "03"},
        ],
    },
    {
        "name": "Faculty of Dentistry",
        "code": "14",
        "departments": [
            {"name": "Dental Surgery",                  "code": "01"},
            {"name": "Oral and Maxillofacial Surgery",  "code": "02"},
        ],
    },
    {
        "name": "Faculty of Allied Health Sciences",
        "code": "15",
        "departments": [
            {"name": "Medical Laboratory Science",      "code": "01"},
            {"name": "Physiotherapy",                   "code": "02"},
            {"name": "Radiography",                     "code": "03"},
        ],
    },
    {
        "name": "Faculty of Environmental Sciences",
        "code": "16",
        "departments": [
            {"name": "Architecture",                    "code": "01"},
            {"name": "Building",                        "code": "02"},
            {"name": "Estate Management",               "code": "03"},
            {"name": "Quantity Surveying",              "code": "04"},
            {"name": "Urban and Regional Planning",     "code": "05"},
        ],
    },
    {
        "name": "Faculty of Computing and Information Technology",
        "code": "17",
        "departments": [
            {"name": "Computer Science",                "code": "01"},
            {"name": "Information Technology",          "code": "02"},
            {"name": "Cyber Security",                  "code": "03"},
            {"name": "Software Engineering",            "code": "04"},
            {"name": "Data Science",                    "code": "05"},
        ],
    },
]
