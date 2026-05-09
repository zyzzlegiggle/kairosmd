"""Patient profiles for FHIR seeding. 15 chronic outpatient scenarios."""

# Vitals tuple: (days_ago, sbp, dbp, hr, rr, spo2, temp_c)
# Labs dict: {loinc: (value, unit)}

PROFILES = [
    {
        "name": ("Ahmad", "Rahman"), "gender": "male", "dob": "1958-03-15",
        "appt_hour": 9, "appt_reason": "Diabetes and hypertension follow-up",
        "conditions": [
            ("I10", "Essential hypertension"),
            ("E11.65", "Type 2 diabetes with hyperglycemia"),
            ("N18.3", "Chronic kidney disease, stage 3"),
        ],
        "allergies": [("Penicillin", "rash"), ("Sulfonamides", "anaphylaxis")],
        "medications": [
            ("Metformin 500mg", 860975, "500 mg", "twice daily", "oral"),
            ("Lisinopril 10mg", 314077, "10 mg", "once daily", "oral"),
            ("Amlodipine 5mg", 329528, "5 mg", "once daily", "oral"),
            ("Atorvastatin 20mg", 259255, "20 mg", "at bedtime", "oral"),
            ("Metoprolol 25mg", 866514, "25 mg", "twice daily", "oral"),
        ],
        "vitals": [
            (60, 148, 92, 78, 16, 97, 36.7),
            (30, 152, 95, 82, 18, 96, 36.8),
            (7, 158, 98, 85, 18, 95, 36.9),
        ],
        "labs": [
            (30, {"6690-2": (7.2, "K/uL"), "718-7": (12.8, "g/dL"), "777-3": (220, "K/uL"),
                  "2951-2": (140, "mEq/L"), "2823-3": (4.8, "mEq/L"), "2160-0": (1.8, "mg/dL"),
                  "3094-0": (28, "mg/dL"), "2345-7": (185, "mg/dL"), "1742-6": (32, "U/L"),
                  "1920-8": (28, "U/L")}),
            (7, {"6690-2": (7.5, "K/uL"), "718-7": (12.5, "g/dL"), "777-3": (215, "K/uL"),
                 "2951-2": (138, "mEq/L"), "2823-3": (5.2, "mEq/L"), "2160-0": (2.1, "mg/dL"),
                 "3094-0": (32, "mg/dL"), "2345-7": (210, "mg/dL"), "1742-6": (35, "U/L"),
                 "1920-8": (30, "U/L")}),
        ],
        "notes": "68yo male with poorly controlled HTN and DM2. BP trending upward "
                 "despite 3-drug regimen. Creatinine rising from 1.8 to 2.1 over past month. "
                 "Glucose remains elevated. Patient reports occasional dizziness and fatigue. "
                 "May need medication adjustment. CKD stage 3 progressing.",
    },
    {
        "name": ("Sarah", "Chen"), "gender": "female", "dob": "1981-07-22",
        "appt_hour": 9, "appt_reason": "Annual wellness visit",
        "conditions": [("I10", "Essential hypertension")],
        "allergies": [("Latex", "contact dermatitis")],
        "medications": [
            ("Lisinopril 5mg", 314076, "5 mg", "once daily", "oral"),
            ("Vitamin D 1000IU", 315966, "1000 IU", "once daily", "oral"),
        ],
        "vitals": [
            (90, 128, 82, 72, 14, 98, 36.6),
            (7, 125, 80, 70, 14, 99, 36.5),
        ],
        "labs": [
            (90, {"6690-2": (6.1, "K/uL"), "718-7": (13.5, "g/dL"), "777-3": (250, "K/uL"),
                  "2951-2": (141, "mEq/L"), "2823-3": (4.2, "mEq/L"), "2160-0": (0.9, "mg/dL"),
                  "3094-0": (14, "mg/dL"), "2345-7": (92, "mg/dL"), "1742-6": (22, "U/L"),
                  "1920-8": (18, "U/L")}),
        ],
        "notes": "45yo female here for annual check. HTN well controlled on lisinopril. "
                 "No complaints. Active lifestyle, exercises 3x/week. Labs all within normal limits.",
    },
    {
        "name": ("James", "Morrison"), "gender": "male", "dob": "1954-11-08",
        "appt_hour": 10, "appt_reason": "Heart failure management",
        "conditions": [
            ("I50.22", "Chronic systolic heart failure"),
            ("I48.91", "Unspecified atrial fibrillation"),
            ("I10", "Essential hypertension"),
            ("E11", "Type 2 diabetes mellitus"),
        ],
        "allergies": [("ACE inhibitors", "angioedema")],
        "medications": [
            ("Warfarin 5mg", 855332, "5 mg", "once daily", "oral"),
            ("Aspirin 81mg", 243670, "81 mg", "once daily", "oral"),
            ("Metoprolol 50mg", 866924, "50 mg", "twice daily", "oral"),
            ("Furosemide 40mg", 310429, "40 mg", "once daily", "oral"),
            ("Spironolactone 25mg", 313096, "25 mg", "once daily", "oral"),
            ("Digoxin 0.125mg", 197604, "0.125 mg", "once daily", "oral"),
            ("Carvedilol 12.5mg", 200033, "12.5 mg", "twice daily", "oral"),
        ],
        "vitals": [
            (30, 135, 82, 88, 20, 94, 36.8),
            (14, 130, 78, 92, 22, 92, 37.0),
            (3, 125, 75, 98, 24, 89, 37.1),
        ],
        "labs": [
            (14, {"6690-2": (8.5, "K/uL"), "718-7": (11.2, "g/dL"), "777-3": (180, "K/uL"),
                  "2951-2": (136, "mEq/L"), "2823-3": (5.0, "mEq/L"), "2160-0": (1.6, "mg/dL"),
                  "3094-0": (30, "mg/dL"), "2345-7": (145, "mg/dL"),
                  "30934-4": (450, "pg/mL"), "2069-3": (0.02, "ng/mL")}),
            (3, {"6690-2": (9.2, "K/uL"), "718-7": (10.8, "g/dL"), "777-3": (170, "K/uL"),
                 "2951-2": (134, "mEq/L"), "2823-3": (5.4, "mEq/L"), "2160-0": (1.9, "mg/dL"),
                 "3094-0": (35, "mg/dL"), "2345-7": (160, "mg/dL"),
                 "30934-4": (680, "pg/mL"), "2069-3": (0.03, "ng/mL")}),
        ],
        "notes": "72yo male with CHF NYHA class III. Increasing dyspnea on exertion over "
                 "past 2 weeks. SpO2 declining, now 89% at rest. BNP significantly elevated "
                 "at 680. Weight gain 3kg in 2 weeks suggesting fluid retention. On warfarin "
                 "AND aspirin - bleeding risk elevated. Potassium trending up on spironolactone. "
                 "Needs urgent medication review.",
    },
    {
        "name": ("Maria", "Santos"), "gender": "female", "dob": "1971-04-12",
        "appt_hour": 10, "appt_reason": "Chest pain evaluation follow-up",
        "conditions": [
            ("R07.9", "Chest pain, unspecified"),
            ("F41.1", "Generalized anxiety disorder"),
            ("I10", "Essential hypertension"),
        ],
        "allergies": [("Codeine", "nausea and vomiting")],
        "medications": [
            ("Amlodipine 5mg", 329528, "5 mg", "once daily", "oral"),
            ("Sertraline 50mg", 312940, "50 mg", "once daily", "oral"),
            ("Omeprazole 20mg", 198053, "20 mg", "once daily", "oral"),
            ("Aspirin 81mg", 243670, "81 mg", "once daily", "oral"),
        ],
        "vitals": [
            (14, 138, 85, 78, 16, 98, 36.6),
            (3, 145, 90, 92, 20, 97, 36.8),
        ],
        "labs": [
            (3, {"6690-2": (7.8, "K/uL"), "718-7": (13.2, "g/dL"), "777-3": (240, "K/uL"),
                 "2951-2": (140, "mEq/L"), "2823-3": (4.1, "mEq/L"), "2160-0": (0.8, "mg/dL"),
                 "3094-0": (15, "mg/dL"), "2345-7": (105, "mg/dL"),
                 "2069-3": (0.06, "ng/mL")}),
        ],
        "notes": "55yo female with recurrent chest pain episodes. Last visit troponin was "
                 "borderline elevated at 0.06. HR elevated at 92. Patient reports chest "
                 "tightness worsening with exertion. Anxiety component likely but cardiac "
                 "cause not yet excluded. Needs stress test results review.",
    },
    {
        "name": ("Robert", "Kim"), "gender": "male", "dob": "1966-09-30",
        "appt_hour": 11, "appt_reason": "COPD management",
        "conditions": [
            ("J44.1", "COPD with acute exacerbation"),
            ("J18.9", "Pneumonia, unspecified"),
            ("I10", "Essential hypertension"),
            ("F17.210", "Nicotine dependence, cigarettes"),
        ],
        "allergies": [("Erythromycin", "GI upset")],
        "medications": [
            ("Tiotropium 18mcg", 1487517, "18 mcg", "once daily", "inhalation"),
            ("Albuterol inhaler", 745679, "90 mcg", "as needed", "inhalation"),
            ("Prednisone 10mg", 312617, "10 mg", "once daily", "oral"),
            ("Azithromycin 250mg", 248656, "250 mg", "once daily", "oral"),
            ("Lisinopril 10mg", 314077, "10 mg", "once daily", "oral"),
        ],
        "vitals": [
            (30, 132, 80, 82, 18, 94, 36.7),
            (14, 135, 82, 88, 22, 91, 37.2),
            (3, 130, 78, 90, 24, 90, 37.5),
        ],
        "labs": [
            (14, {"6690-2": (12.5, "K/uL"), "718-7": (15.2, "g/dL"), "777-3": (310, "K/uL"),
                  "2951-2": (139, "mEq/L"), "2823-3": (4.0, "mEq/L"), "2160-0": (1.1, "mg/dL"),
                  "3094-0": (18, "mg/dL"), "2345-7": (130, "mg/dL")}),
            (3, {"6690-2": (14.8, "K/uL"), "718-7": (15.0, "g/dL"), "777-3": (320, "K/uL"),
                 "2951-2": (137, "mEq/L"), "2823-3": (3.9, "mEq/L"), "2160-0": (1.2, "mg/dL"),
                 "3094-0": (20, "mg/dL"), "2345-7": (145, "mg/dL")}),
        ],
        "notes": "60yo male smoker with COPD. Recent pneumonia treated with azithromycin. "
                 "Respiratory rate increasing, SpO2 declining to 90%. WBC elevated at 14.8 "
                 "suggesting ongoing infection. Temp mildly elevated. May need escalation "
                 "of antibiotics if not improving.",
    },
    {
        "name": ("Fatima", "Al-Hassan"), "gender": "female", "dob": "1988-01-18",
        "appt_hour": 11, "appt_reason": "Post-gestational diabetes follow-up",
        "conditions": [
            ("O24.419", "Gestational diabetes in pregnancy"),
            ("Z87.39", "Personal history of other endocrine disorders"),
        ],
        "allergies": [("Amoxicillin", "hives")],
        "medications": [
            ("Metformin 500mg", 860975, "500 mg", "once daily", "oral"),
            ("Prenatal vitamins", 904420, "1 tablet", "once daily", "oral"),
        ],
        "vitals": [
            (30, 118, 74, 72, 14, 99, 36.5),
            (7, 120, 76, 70, 14, 99, 36.6),
        ],
        "labs": [
            (30, {"6690-2": (6.8, "K/uL"), "718-7": (12.1, "g/dL"), "777-3": (260, "K/uL"),
                  "2951-2": (140, "mEq/L"), "2823-3": (4.0, "mEq/L"), "2160-0": (0.7, "mg/dL"),
                  "3094-0": (12, "mg/dL"), "2345-7": (98, "mg/dL")}),
        ],
        "notes": "38yo female, 6 months postpartum. History of gestational diabetes. "
                 "Glucose normalizing on low-dose metformin. All vitals stable. "
                 "Routine follow-up, no concerns.",
    },
    {
        "name": ("William", "OBrien"), "gender": "male", "dob": "1946-06-25",
        "appt_hour": 13, "appt_reason": "Polypharmacy review and fall risk assessment",
        "conditions": [
            ("I48.91", "Unspecified atrial fibrillation"),
            ("I10", "Essential hypertension"),
            ("E11", "Type 2 diabetes mellitus"),
            ("M81.0", "Age-related osteoporosis"),
            ("G47.33", "Obstructive sleep apnea"),
            ("F32.1", "Major depressive disorder, moderate"),
        ],
        "allergies": [("Metformin", "lactic acidosis risk"), ("Iodine contrast", "anaphylaxis")],
        "medications": [
            ("Warfarin 3mg", 855318, "3 mg", "once daily", "oral"),
            ("Metoprolol 50mg", 866924, "50 mg", "twice daily", "oral"),
            ("Amlodipine 10mg", 329526, "10 mg", "once daily", "oral"),
            ("Glipizide 5mg", 310488, "5 mg", "twice daily", "oral"),
            ("Atorvastatin 40mg", 259255, "40 mg", "at bedtime", "oral"),
            ("Omeprazole 20mg", 198053, "20 mg", "once daily", "oral"),
            ("Sertraline 100mg", 312941, "100 mg", "once daily", "oral"),
            ("Alendronate 70mg", 314084, "70 mg", "once weekly", "oral"),
            ("Gabapentin 300mg", 310431, "300 mg", "three times daily", "oral"),
            ("Tramadol 50mg", 835603, "50 mg", "as needed", "oral"),
            ("Zolpidem 5mg", 312898, "5 mg", "at bedtime", "oral"),
            ("Lisinopril 20mg", 314077, "20 mg", "once daily", "oral"),
        ],
        "vitals": [
            (30, 140, 85, 75, 16, 95, 36.7),
            (7, 135, 80, 78, 16, 94, 36.8),
        ],
        "labs": [
            (30, {"6690-2": (5.8, "K/uL"), "718-7": (11.5, "g/dL"), "777-3": (195, "K/uL"),
                  "2951-2": (138, "mEq/L"), "2823-3": (4.5, "mEq/L"), "2160-0": (1.4, "mg/dL"),
                  "3094-0": (22, "mg/dL"), "2345-7": (155, "mg/dL"), "1742-6": (28, "U/L"),
                  "1920-8": (25, "U/L")}),
            (7, {"6690-2": (5.5, "K/uL"), "718-7": (11.2, "g/dL"), "777-3": (190, "K/uL"),
                 "2951-2": (136, "mEq/L"), "2823-3": (4.6, "mEq/L"), "2160-0": (1.5, "mg/dL"),
                 "3094-0": (24, "mg/dL"), "2345-7": (162, "mg/dL"), "1742-6": (30, "U/L"),
                 "1920-8": (27, "U/L")}),
        ],
        "notes": "80yo male on 12 medications. High fall risk - on gabapentin, tramadol, "
                 "and zolpidem (all sedating). Sertraline + tramadol is a serotonin syndrome "
                 "risk. On warfarin - INR monitoring needed. Mild anemia. Glucose elevated. "
                 "Needs comprehensive medication reconciliation.",
    },
    {
        "name": ("Priya", "Patel"), "gender": "female", "dob": "1974-12-05",
        "appt_hour": 13, "appt_reason": "Depression and pain management follow-up",
        "conditions": [
            ("F32.1", "Major depressive disorder, moderate"),
            ("E03.9", "Hypothyroidism, unspecified"),
            ("M54.5", "Low back pain"),
        ],
        "allergies": [("Ibuprofen", "gastric bleeding")],
        "medications": [
            ("Sertraline 100mg", 312941, "100 mg", "once daily", "oral"),
            ("Tramadol 50mg", 835603, "50 mg", "every 6 hours as needed", "oral"),
            ("Levothyroxine 75mcg", 966247, "75 mcg", "once daily", "oral"),
            ("Gabapentin 300mg", 310431, "300 mg", "three times daily", "oral"),
            ("Acetaminophen 500mg", 198440, "500 mg", "every 6 hours", "oral"),
        ],
        "vitals": [
            (30, 122, 78, 74, 14, 98, 36.6),
            (7, 120, 76, 72, 14, 98, 36.5),
        ],
        "labs": [
            (30, {"6690-2": (6.5, "K/uL"), "718-7": (12.8, "g/dL"), "777-3": (240, "K/uL"),
                  "2951-2": (141, "mEq/L"), "2823-3": (4.1, "mEq/L"), "2160-0": (0.8, "mg/dL"),
                  "3094-0": (13, "mg/dL"), "2345-7": (88, "mg/dL"), "1742-6": (20, "U/L"),
                  "1920-8": (18, "U/L")}),
        ],
        "notes": "52yo female with depression and chronic low back pain. On sertraline + "
                 "tramadol - serotonin syndrome risk. Reports pain is manageable. Mood "
                 "improving. Thyroid levels stable on current levothyroxine dose. "
                 "Allergic to ibuprofen - ensure no NSAIDs prescribed.",
    },
    {
        "name": ("David", "Thompson"), "gender": "male", "dob": "1961-08-14",
        "appt_hour": 14, "appt_reason": "CKD progression monitoring",
        "conditions": [
            ("N18.4", "Chronic kidney disease, stage 4"),
            ("I10", "Essential hypertension"),
            ("E11.22", "Type 2 diabetes with diabetic CKD"),
        ],
        "allergies": [("Contrast dye", "nephrotoxicity risk")],
        "medications": [
            ("Lisinopril 20mg", 314077, "20 mg", "once daily", "oral"),
            ("Spironolactone 25mg", 313096, "25 mg", "once daily", "oral"),
            ("Furosemide 80mg", 310429, "80 mg", "once daily", "oral"),
            ("Insulin glargine", 261551, "20 units", "at bedtime", "subcutaneous"),
            ("Sodium bicarbonate 650mg", 198144, "650 mg", "three times daily", "oral"),
            ("Atorvastatin 40mg", 259255, "40 mg", "at bedtime", "oral"),
        ],
        "vitals": [
            (30, 145, 88, 80, 16, 96, 36.7),
            (14, 150, 92, 82, 18, 95, 36.8),
            (3, 155, 95, 85, 20, 94, 36.9),
        ],
        "labs": [
            (30, {"6690-2": (6.8, "K/uL"), "718-7": (10.5, "g/dL"), "777-3": (200, "K/uL"),
                  "2951-2": (137, "mEq/L"), "2823-3": (5.3, "mEq/L"), "2160-0": (3.8, "mg/dL"),
                  "3094-0": (45, "mg/dL"), "2345-7": (160, "mg/dL")}),
            (3, {"6690-2": (7.0, "K/uL"), "718-7": (10.0, "g/dL"), "777-3": (190, "K/uL"),
                 "2951-2": (135, "mEq/L"), "2823-3": (5.8, "mEq/L"), "2160-0": (4.5, "mg/dL"),
                 "3094-0": (52, "mg/dL"), "2345-7": (175, "mg/dL")}),
        ],
        "notes": "65yo male with CKD stage 4 progressing. Creatinine jumped from 3.8 to 4.5. "
                 "Potassium 5.8 on ACE inhibitor + spironolactone - dangerous combination "
                 "in advanced CKD. BP worsening. Anemia of CKD. May need nephrology "
                 "referral for dialysis planning. Urgent potassium management needed.",
    },
    {
        "name": ("Lisa", "Wang"), "gender": "female", "dob": "1984-02-28",
        "appt_hour": 14, "appt_reason": "Rheumatoid arthritis medication review",
        "conditions": [
            ("M05.79", "RA with rheumatoid factor, unspecified"),
            ("K76.0", "Fatty liver disease"),
        ],
        "allergies": [("Sulfasalazine", "hepatotoxicity")],
        "medications": [
            ("Methotrexate 15mg", 105585, "15 mg", "once weekly", "oral"),
            ("Folic acid 1mg", 315966, "1 mg", "once daily", "oral"),
            ("Ibuprofen 400mg", 197806, "400 mg", "three times daily", "oral"),
            ("Prednisone 5mg", 312615, "5 mg", "once daily", "oral"),
            ("Omeprazole 20mg", 198053, "20 mg", "once daily", "oral"),
        ],
        "vitals": [
            (30, 118, 72, 74, 14, 99, 36.6),
            (7, 120, 74, 76, 14, 98, 36.7),
        ],
        "labs": [
            (30, {"6690-2": (5.5, "K/uL"), "718-7": (12.5, "g/dL"), "777-3": (230, "K/uL"),
                  "2951-2": (140, "mEq/L"), "2823-3": (4.0, "mEq/L"), "2160-0": (0.7, "mg/dL"),
                  "3094-0": (12, "mg/dL"), "2345-7": (90, "mg/dL"),
                  "1742-6": (55, "U/L"), "1920-8": (48, "U/L")}),
            (7, {"6690-2": (5.2, "K/uL"), "718-7": (12.2, "g/dL"), "777-3": (225, "K/uL"),
                 "2951-2": (139, "mEq/L"), "2823-3": (4.1, "mEq/L"), "2160-0": (0.8, "mg/dL"),
                 "3094-0": (13, "mg/dL"), "2345-7": (88, "mg/dL"),
                 "1742-6": (85, "U/L"), "1920-8": (72, "U/L")}),
        ],
        "notes": "42yo female with RA on methotrexate + ibuprofen - methotrexate toxicity "
                 "risk with concurrent NSAID use. Liver enzymes rising: ALT 55->85, AST "
                 "48->72. Fatty liver disease as baseline. Need to discontinue ibuprofen "
                 "and switch to non-NSAID pain management. Methotrexate dose may need hold.",
    },
    {
        "name": ("Michael", "Johnson"), "gender": "male", "dob": "1968-05-20",
        "appt_hour": 15, "appt_reason": "Diabetes quarterly check",
        "conditions": [
            ("E11", "Type 2 diabetes mellitus"),
            ("E78.5", "Hyperlipidemia, unspecified"),
        ],
        "allergies": [("Shellfish", "anaphylaxis")],
        "medications": [
            ("Metformin 1000mg", 861004, "1000 mg", "twice daily", "oral"),
            ("Glipizide 5mg", 310488, "5 mg", "once daily", "oral"),
            ("Atorvastatin 20mg", 259255, "20 mg", "at bedtime", "oral"),
        ],
        "vitals": [
            (90, 130, 82, 76, 14, 98, 36.6),
            (7, 128, 80, 74, 14, 99, 36.5),
        ],
        "labs": [
            (90, {"6690-2": (6.2, "K/uL"), "718-7": (14.5, "g/dL"), "777-3": (250, "K/uL"),
                  "2951-2": (141, "mEq/L"), "2823-3": (4.2, "mEq/L"), "2160-0": (0.9, "mg/dL"),
                  "3094-0": (15, "mg/dL"), "2345-7": (115, "mg/dL")}),
            (7, {"6690-2": (6.0, "K/uL"), "718-7": (14.3, "g/dL"), "777-3": (248, "K/uL"),
                 "2951-2": (140, "mEq/L"), "2823-3": (4.3, "mEq/L"), "2160-0": (0.9, "mg/dL"),
                 "3094-0": (14, "mg/dL"), "2345-7": (108, "mg/dL")}),
        ],
        "notes": "58yo male with well-controlled DM2. Glucose improving. Lipids stable "
                 "on statin. No new complaints. Continue current regimen.",
    },
    {
        "name": ("Elena", "Rodriguez"), "gender": "female", "dob": "1956-10-03",
        "appt_hour": 15, "appt_reason": "Chronic pain management",
        "conditions": [
            ("G89.29", "Other chronic pain"),
            ("N18.3", "Chronic kidney disease, stage 3"),
            ("K59.00", "Constipation, unspecified"),
        ],
        "allergies": [("Morphine", "respiratory depression")],
        "medications": [
            ("Oxycodone 5mg", 1049621, "5 mg", "every 6 hours", "oral"),
            ("Gabapentin 600mg", 310433, "600 mg", "three times daily", "oral"),
            ("Docusate 100mg", 315090, "100 mg", "twice daily", "oral"),
            ("Senna 8.6mg", 317638, "8.6 mg", "at bedtime", "oral"),
            ("Amlodipine 5mg", 329528, "5 mg", "once daily", "oral"),
        ],
        "vitals": [
            (30, 135, 80, 70, 14, 97, 36.6),
            (7, 132, 78, 68, 14, 96, 36.5),
        ],
        "labs": [
            (30, {"6690-2": (6.0, "K/uL"), "718-7": (11.8, "g/dL"), "777-3": (210, "K/uL"),
                  "2951-2": (139, "mEq/L"), "2823-3": (4.3, "mEq/L"), "2160-0": (1.6, "mg/dL"),
                  "3094-0": (25, "mg/dL"), "2345-7": (95, "mg/dL")}),
        ],
        "notes": "70yo female with chronic pain managed on oxycodone. Mild CKD. "
                 "Pain stable, no dose escalation needed. Constipation managed with "
                 "stool softeners. Mild anemia. Routine follow-up.",
    },
    {
        "name": ("Thomas", "Brown"), "gender": "male", "dob": "1951-03-17",
        "appt_hour": 16, "appt_reason": "Post-MI cardiac follow-up",
        "conditions": [
            ("I25.2", "Old myocardial infarction"),
            ("I10", "Essential hypertension"),
            ("E78.5", "Hyperlipidemia"),
        ],
        "allergies": [("Clopidogrel", "bruising")],
        "medications": [
            ("Aspirin 81mg", 243670, "81 mg", "once daily", "oral"),
            ("Metoprolol 50mg", 866924, "50 mg", "twice daily", "oral"),
            ("Atorvastatin 80mg", 259255, "80 mg", "at bedtime", "oral"),
            ("Lisinopril 10mg", 314077, "10 mg", "once daily", "oral"),
            ("Nitroglycerin 0.4mg", 311702, "0.4 mg", "as needed", "sublingual"),
        ],
        "vitals": [
            (30, 128, 78, 65, 14, 98, 36.6),
            (7, 125, 76, 62, 14, 98, 36.5),
        ],
        "labs": [
            (30, {"6690-2": (6.5, "K/uL"), "718-7": (14.0, "g/dL"), "777-3": (240, "K/uL"),
                  "2951-2": (140, "mEq/L"), "2823-3": (4.2, "mEq/L"), "2160-0": (1.0, "mg/dL"),
                  "3094-0": (16, "mg/dL"), "2345-7": (100, "mg/dL"),
                  "2069-3": (0.01, "ng/mL")}),
        ],
        "notes": "75yo male, 2 years post-MI. Stable angina well controlled. No chest "
                 "pain at rest. Troponin normal. BP and HR well controlled on current "
                 "regimen. Routine cardiac follow-up.",
    },
    {
        "name": ("Aisha", "Mohammed"), "gender": "female", "dob": "1978-07-09",
        "appt_hour": 16, "appt_reason": "Uncontrolled diabetes management",
        "conditions": [
            ("E11.65", "Type 2 diabetes with hyperglycemia"),
            ("E11.40", "Type 2 diabetes with diabetic neuropathy"),
            ("I10", "Essential hypertension"),
            ("E66.01", "Morbid obesity due to excess calories"),
        ],
        "allergies": [("Metformin", "severe GI intolerance")],
        "medications": [
            ("Insulin glargine", 261551, "30 units", "at bedtime", "subcutaneous"),
            ("Insulin lispro", 261542, "sliding scale", "with meals", "subcutaneous"),
            ("Lisinopril 20mg", 314077, "20 mg", "once daily", "oral"),
            ("Gabapentin 300mg", 310431, "300 mg", "three times daily", "oral"),
            ("Amlodipine 10mg", 329526, "10 mg", "once daily", "oral"),
            ("Atorvastatin 40mg", 259255, "40 mg", "at bedtime", "oral"),
        ],
        "vitals": [
            (30, 148, 90, 82, 16, 97, 36.8),
            (7, 152, 92, 84, 16, 97, 36.9),
        ],
        "labs": [
            (30, {"6690-2": (7.0, "K/uL"), "718-7": (13.0, "g/dL"), "777-3": (250, "K/uL"),
                  "2951-2": (140, "mEq/L"), "2823-3": (4.5, "mEq/L"), "2160-0": (1.0, "mg/dL"),
                  "3094-0": (16, "mg/dL"), "2345-7": (280, "mg/dL")}),
            (7, {"6690-2": (7.2, "K/uL"), "718-7": (12.8, "g/dL"), "777-3": (245, "K/uL"),
                 "2951-2": (139, "mEq/L"), "2823-3": (4.6, "mEq/L"), "2160-0": (1.1, "mg/dL"),
                 "3094-0": (18, "mg/dL"), "2345-7": (310, "mg/dL")}),
        ],
        "notes": "48yo female with uncontrolled DM2. Cannot tolerate metformin. Glucose "
                 "280->310, worsening despite insulin. Neuropathy symptoms progressing - "
                 "burning and tingling in feet. BP not at goal. Obese BMI 42. Needs "
                 "insulin dose adjustment and possible GLP-1 agonist addition.",
    },
    {
        "name": ("George", "Wilson"), "gender": "male", "dob": "1944-11-22",
        "appt_hour": 9, "appt_reason": "Urgent follow-up - recent UTI with confusion",
        "conditions": [
            ("N39.0", "Urinary tract infection"),
            ("A41.9", "Sepsis, unspecified organism"),
            ("I10", "Essential hypertension"),
            ("F03.90", "Unspecified dementia"),
            ("N18.3", "Chronic kidney disease, stage 3"),
        ],
        "allergies": [("Fluoroquinolones", "tendon rupture risk"), ("Sulfa drugs", "rash")],
        "medications": [
            ("Ceftriaxone 1g", 309090, "1 g", "once daily", "intravenous"),
            ("Amlodipine 5mg", 329528, "5 mg", "once daily", "oral"),
            ("Donepezil 10mg", 312835, "10 mg", "at bedtime", "oral"),
            ("Acetaminophen 500mg", 198440, "500 mg", "every 6 hours as needed", "oral"),
            ("Furosemide 20mg", 310429, "20 mg", "once daily", "oral"),
        ],
        "vitals": [
            (7, 130, 75, 78, 16, 96, 36.8),
            (3, 105, 60, 105, 24, 93, 38.5),
            (1, 98, 55, 112, 26, 91, 38.8),
        ],
        "labs": [
            (7, {"6690-2": (8.0, "K/uL"), "718-7": (12.0, "g/dL"), "777-3": (200, "K/uL"),
                  "2951-2": (140, "mEq/L"), "2823-3": (4.2, "mEq/L"), "2160-0": (1.8, "mg/dL"),
                  "3094-0": (28, "mg/dL"), "2345-7": (110, "mg/dL")}),
            (1, {"6690-2": (18.5, "K/uL"), "718-7": (11.0, "g/dL"), "777-3": (160, "K/uL"),
                 "2951-2": (132, "mEq/L"), "2823-3": (5.0, "mEq/L"), "2160-0": (2.8, "mg/dL"),
                 "3094-0": (42, "mg/dL"), "2345-7": (165, "mg/dL"),
                 "1742-6": (45, "U/L"), "1920-8": (52, "U/L")}),
        ],
        "notes": "82yo male with UTI progressing to possible sepsis. Found confused and "
                 "febrile at 38.8C by family yesterday. HR 112, BP dropping to 98/55, "
                 "SpO2 91%. WBC markedly elevated at 18.5. Creatinine jumped from 1.8 to "
                 "2.8 - acute kidney injury on chronic CKD. Started IV ceftriaxone. "
                 "Allergic to fluoroquinolones and sulfa. Altered mental status - baseline "
                 "dementia makes assessment difficult. Needs urgent review today.",
    },
]
