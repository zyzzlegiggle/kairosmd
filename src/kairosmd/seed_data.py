"""
Multidisciplinary Ward Round Decision Support (MDS) - Scenario Bank.
Contains 15 high-fidelity clinical scenarios for General Medicine Ward 4.
"""

from datetime import datetime, timedelta, timezone

# Reference Date (Now)
NOW = datetime.now(timezone.utc)

def days_ago(d: int, h: int = 0) -> str:
    return (NOW - timedelta(days=d, hours=h)).isoformat()

# --- MDT Staff ---
CONSULTANTS = [
    {"id": "dr-whitfield", "name": "Dr. James Whitfield", "role": "General Medicine Consultant"},
    {"id": "dr-nair", "name": "Dr. Priya Nair", "role": "General Medicine Consultant"},
    {"id": "dr-mendez", "name": "Dr. Carlos Mendez", "role": "General Medicine Consultant"},
]

NURSES = ["Nurse Faridah", "Nurse Sarah", "Nurse Wong", "Nurse Kumar", "Nurse Thompson"]

# --- The 15 Clinical Scenarios ---
SCENARIOS = [
    # 1. Community Acquired Pneumonia, Day 3, Deteriorating
    {
        "bed": "1",
        "patient": {
            "name": "Ahmad Razali",
            "dob": "1957-04-12",
            "gender": "male",
            "condition": "Community Acquired Pneumonia",
            "consultant": CONSULTANTS[0],
            "day": 3,
        },
        "vitals_trend": "deteriorating", 
        "labs": [
            {"code": "6299-1", "name": "WBC", "value": 18.5, "unit": "10*9/L", "flag": "H"},
            {"code": "1988-5", "name": "CRP", "value": 245, "unit": "mg/L", "flag": "H"},
            {"code": "2019-8", "name": "Lactate", "value": 3.1, "unit": "mmol/L", "flag": "H"},
        ],
        "notes": {
            "clerking": "67yo male, smoker. PC: 4 days of SOB, rusty sputum, and fever. PMH: HTN, Mild COPD. Exam: RR 24, SpO2 92% RA. Crackles at right base. Dullness to percussion. Plan: IV Co-Amoxiclav + Clarithromycin. Oxygen target 94-98%.",
            "consultant": "Day 2 Review: CRP rising from 180 to 245. Patient spiking temperatures. Oxygen requirements stable. Review blood cultures and consider escalation if no improvement by evening.",
            "junior": "S: Feels okay. O: RR 22, SpO2 94% on 2L. A: Stable CAP. P: Continue current plan.",
            "nursing_night": "02:30: Patient appears comfortable and sleeping well. No complaints. IV site intact. [CONFLICT: Vitals at 03:00 showed RR 30 and SpO2 88% while patient was 'sleeping'].",
        },
        "meds": [
            {"name": "Co-Amoxiclav", "code": "308461", "dosage": "1.2g IV TDS", "status": "active"},
            {"name": "Clarithromycin", "code": "21701", "dosage": "500mg IV BD", "status": "active"},
        ],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "FALLS", "detail": "Medium Risk"}, {"code": "RESUS", "detail": "Full Resuscitation"}],
    },
    
    # 2. AKI on Type 2 Diabetes, Day 2
    {
        "bed": "2",
        "patient": {
            "name": "Siti Norzahrah",
            "dob": "1968-08-22",
            "gender": "female",
            "condition": "AKI on T2DM",
            "consultant": CONSULTANTS[1],
            "day": 2,
        },
        "vitals_trend": "stable",
        "labs": [
            {"code": "2160-0", "name": "Creatinine", "value": 210, "unit": "umol/L", "flag": "H"},
            {"code": "33914-3", "name": "eGFR", "value": 24, "unit": "mL/min/1.73m2", "flag": "L"},
        ],
        "notes": {
            "clerking": "55yo female, T2DM. PC: Vomiting, dehydration. Plan: IV Fluids. Hold nephrotoxics. Monitor U&Es.",
            "junior": "S: Feeling better. O: BP 115/70. A: Renal function stable. [CONFLICT: Creatinine rose from 165 to 210 overnight].",
            "nursing_morning": "09:00: Tolerating oral fluids. Urine output 300ml over shift.",
        },
        "meds": [
            {"name": "Metformin", "code": "228471", "dosage": "1g BD PO", "status": "active"}, # CONFLICT: Contraindicated in AKI
            {"name": "Dapagliflozin", "code": "1488564", "dosage": "10mg OD PO", "status": "on-hold"},
        ],
        "allergies": [{"code": "70618", "name": "Penicillin G", "criticality": "high"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # 3. Decompensated Heart Failure, Day 4
    {
        "bed": "3",
        "patient": {
            "name": "Rajendran Pillai",
            "dob": "1945-11-30",
            "gender": "male",
            "condition": "Heart Failure",
            "consultant": CONSULTANTS[2],
            "day": 4,
        },
        "vitals_trend": "improving",
        "labs": [
            {"code": "30522-7", "name": "BNP", "value": 1850, "unit": "pg/mL", "flag": "H"},
            {"code": "2823-3", "name": "Potassium", "value": 3.2, "unit": "mmol/L", "flag": "L"},
        ],
        "notes": {
            "consultant": "Day 3 Review: Good response to IV Furosemide. 3kg weight loss. Plan: Switch to oral diuretics. Discharge tomorrow if stable.",
            "junior": "S: Breathing better. O: Lungs clear. A: Stable. P: Home tomorrow. [CONFLICT: Potassium is 3.2 and BNP is still high].",
            "specialist": "Cardiology: Known HFrEF (EF 30%). Optimise GDMT once stable on oral diuretics. Discharge with early heart failure clinic follow-up.",
        },
        "meds": [
            {"name": "Furosemide", "code": "4603", "dosage": "40mg OD PO", "status": "active"},
            {"name": "Spironolactone", "code": "9997", "dosage": "25mg OD PO", "status": "active"},
        ],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "high"}],
        "flags": [{"code": "FALLS", "detail": "High Risk"}],
    },

    # 4. COPD Exacerbation, Day 2
    {
        "bed": "4",
        "patient": {
            "name": "William Bennett",
            "dob": "1952-02-14",
            "gender": "male",
            "condition": "AECOPD",
            "consultant": CONSULTANTS[0],
            "day": 2,
        },
        "vitals_trend": "stable",
        "notes": {
            "clerking": "72yo male, severe COPD. Ex-smoker. PC: Wheeze and sputum. Plan: Controlled O2 (24% Venturi), Nebs, Steroids.",
            "nursing_night": "03:30: Patient restless. Repeatedly removing O2 mask. Refusing to keep it on. SpO2 88% off mask.",
        },
        "meds": [
            {"name": "Salbutamol", "code": "9504", "dosage": "5mg Neb QDS", "status": "active"},
            {"name": "Hydrocortisone", "code": "5492", "dosage": "100mg IV QDS", "status": "active"},
        ],
        "allergies": [{"code": "1351", "name": "Latex", "criticality": "high"}],
        "flags": [{"code": "RESUS", "detail": "DNAR"}],
    },

    # 5. Sepsis (UTI), Day 1
    {
        "bed": "5",
        "patient": {
            "name": "Mei Ling",
            "dob": "1982-05-15",
            "gender": "female",
            "condition": "Sepsis",
            "consultant": CONSULTANTS[1],
            "day": 1,
        },
        "vitals_trend": "deteriorating",
        "labs": [
            {"code": "2019-8", "name": "Lactate", "value": 4.5, "unit": "mmol/L", "flag": "H"},
            {"code": "6299-1", "name": "WBC", "value": 22.0, "unit": "10*9/L", "flag": "H"},
        ],
        "notes": {
            "clerking": "41yo female. Rigors and flank pain. NEWS2=7 on arrival. Sepsis 6 initiated. 2L IV fluids given. Plan: IV Antibiotics.",
            "nursing_afternoon": "16:00: Patient remains febrile. BP 90/50. Minimal urine output (20ml/hr). HO informed.",
        },
        "meds": [
            {"name": "Gentamicin", "code": "4733", "dosage": "320mg IV OD", "status": "active"},
            {"name": "Amoxicillin", "code": "723", "dosage": "1g IV TDS", "status": "active"},
        ],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "medium"}],
        "flags": [{"code": "ISOLATION", "detail": "Contact Precautions"}],
    },

    # 6. Atrial Fibrillation with RVR, Day 2
    {
        "bed": "6",
        "patient": {
            "name": "David O'Connor",
            "dob": "1960-09-05",
            "gender": "male",
            "condition": "AF with RVR",
            "consultant": CONSULTANTS[2],
            "day": 2,
        },
        "vitals_trend": "stable",
        "notes": {
            "clerking": "63yo male. Palpitations. HR 150. Plan: Digoxin for rate control.",
            "junior": "01:00: Tachycardia persists. Started Amiodarone 200mg TDS. [CONFLICT: Amiodarone doubles Digoxin levels].",
        },
        "meds": [
            {"name": "Digoxin", "code": "3407", "dosage": "125mcg OD PO", "status": "active"},
            {"name": "Amiodarone", "code": "703", "dosage": "200mg TDS PO", "status": "active"},
        ],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "low"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # 7. Diabetic Ketoacidosis, Day 1
    {
        "bed": "7",
        "patient": {
            "name": "Norhaslinda Hassan",
            "dob": "2001-11-12",
            "gender": "female",
            "condition": "DKA",
            "consultant": CONSULTANTS[0],
            "day": 1,
        },
        "vitals_trend": "stable",
        "labs": [
            {"code": "2345-7", "name": "Glucose", "value": 28.5, "unit": "mmol/L", "flag": "H"},
            {"code": "1960-4", "name": "Bicarbonate", "value": 14, "unit": "mmol/L", "flag": "L"},
        ],
        "notes": {
            "clerking": "22yo, T1DM. PC: Nausea, thirst. FRII started. IV Fluids with K+.",
            "nursing_night": "05:00: Patient complaining of worsening abdominal pain. [CONFLICT: Abdominal pain in DKA not addressed in doctor note].",
        },
        "meds": [{"name": "Insulin Soluble", "code": "311028", "dosage": "0.1u/kg/hr IV", "status": "active"}],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "high"}],
        "flags": [{"code": "FALLS", "detail": "Low Risk"}],
    },

    # 8. GI Bleed, Day 3
    {
        "bed": "8",
        "patient": {
            "name": "Rajesh Gupta",
            "dob": "1955-03-25",
            "gender": "male",
            "condition": "Upper GI Bleed",
            "consultant": CONSULTANTS[1],
            "day": 3,
        },
        "vitals_trend": "deteriorating",
        "labs": [
            {"code": "718-7", "name": "Hb", "value": 7.2, "unit": "g/dL", "flag": "L"},
            {"code": "6301-5", "name": "INR", "value": 4.8, "unit": "", "flag": "H"},
        ],
        "notes": {
            "consultant": "Day 2 Review: UGIE showed gastric ulcer. Hb 8.5. Keep NBM. Hold Warfarin.",
            "nursing_morning": "08:30: Melena stools noted. Hb 7.2. INR 4.8. No Vitamin K or reversal given yet.",
        },
        "meds": [{"name": "Warfarin", "code": "11289", "dosage": "5mg OD PO", "status": "on-hold"}],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "high"}],
        "flags": [{"code": "NBM", "detail": "Strict NBM"}],
    },

    # 9. Pulmonary Embolism, Day 2
    {
        "bed": "9",
        "patient": {
            "name": "Sarah Thompson",
            "dob": "1975-07-14",
            "gender": "female",
            "condition": "PE",
            "consultant": CONSULTANTS[2],
            "day": 2,
        },
        "vitals_trend": "stable",
        "notes": {
            "clerking": "CTPA confirmed bilateral PE. Started Heparin infusion. Monitor aPTT.",
            "junior": "S: Sharp chest pain. P: Prescribed Ibuprofen. [CONFLICT: NSAID + Heparin bleeding risk].",
        },
        "meds": [
            {"name": "Heparin", "code": "5224", "dosage": "Infusion", "status": "active"},
            {"name": "Ibuprofen", "code": "5640", "dosage": "400mg TDS PO", "status": "active"},
        ],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "FALLS", "detail": "Low Risk"}],
    },

    # 10. Hypertensive Crisis, Day 1
    {
        "bed": "10",
        "patient": {
            "name": "John Miller",
            "dob": "1965-12-01",
            "gender": "male",
            "condition": "Hypertensive Crisis",
            "consultant": CONSULTANTS[0],
            "day": 1,
        },
        "vitals_trend": "improving",
        "notes": {
            "clerking": "BP 220/120. Headache. Renal artery stenosis. Plan: IV Labetalol. Target SBP 160.",
            "junior": "BP 170/95. Fundoscopy: Clear. Continue slow reduction.",
        },
        "meds": [{"name": "Labetalol", "code": "6185", "dosage": "20mg IV", "status": "active"}],
        "allergies": [{"code": "70618", "name": "Penicillin", "criticality": "medium"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # 11. Stroke, Day 4
    {
        "bed": "11",
        "patient": {
            "name": "Eleanor Rigby",
            "dob": "1940-06-18",
            "gender": "female",
            "condition": "Ischaemic Stroke",
            "consultant": CONSULTANTS[1],
            "day": 4,
        },
        "vitals_trend": "stable",
        "notes": {
            "consultant": "Day 3 Review: Left weakness. Speech Therapy: Dysphagia. NBM, NG meds only.",
            "nursing_morning": "08:00: Given Aspirin/Clopidogrel orally with water. [CONFLICT: Violates dysphagia/NBM plan].",
        },
        "meds": [
            {"name": "Aspirin", "code": "1191", "dosage": "75mg OD PO", "status": "active"},
            {"name": "Clopidogrel", "code": "32968", "dosage": "75mg OD PO", "status": "active"},
        ],
        "allergies": [{"code": "6185", "name": "Labetalol", "criticality": "medium"}],
        "flags": [{"code": "DIET", "detail": "Thickened Fluids Only"}],
    },

    # 12. Cellulitis, Day 5, Improving
    {
        "bed": "12",
        "patient": {
            "name": "Chee Keong Lim",
            "dob": "1972-04-30",
            "gender": "male",
            "condition": "Cellulitis",
            "consultant": CONSULTANTS[2],
            "day": 5,
        },
        "vitals_trend": "improving",
        "notes": {
            "consultant": "Day 4 Review: Redness receding. Afebrile. Step down to oral Flucloxacillin.",
            "junior": "Switched to oral. Awaiting discharge. [CONFLICT: Patient has Penicillin allergy, Flucloxacillin is a penicillin].",
        },
        "meds": [{"name": "Flucloxacillin", "code": "4492", "dosage": "500mg QDS PO", "status": "active"}],
        "allergies": [{"code": "70618", "name": "Penicillin", "criticality": "high"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # 13. Acute Pancreatitis, Day 3
    {
        "bed": "13",
        "patient": {
            "name": "Maria Hernandez",
            "dob": "1988-01-20",
            "gender": "female",
            "condition": "Pancreatitis",
            "consultant": CONSULTANTS[0],
            "day": 3,
        },
        "vitals_trend": "stable",
        "labs": [{"code": "1798-2", "name": "Amylase", "value": 450, "unit": "U/L", "flag": "H"}],
        "notes": {
            "clerking": "Severe epigastric pain. Amylase 1200. Plan: NBM, IV Fluids, Morphine.",
            "nursing_afternoon": "14:00: Found eating chocolate bar brought by family. Educated on NBM.",
        },
        "meds": [{"name": "Morphine", "code": "7052", "dosage": "10mg PRN", "status": "active"}],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "medium"}],
        "flags": [{"code": "NBM", "detail": "Strict NBM"}],
    },

    # 14. CAP, Day 6, Ready for Discharge
    {
        "bed": "14",
        "patient": {
            "name": "Kevin Peterson",
            "dob": "1995-10-10",
            "gender": "male",
            "condition": "CAP (Improving)",
            "consultant": CONSULTANTS[1],
            "day": 6,
        },
        "vitals_trend": "improving",
        "notes": {
            "consultant": "Day 5 Review: Clinically well. SpO2 98% RA. Home today. Discharge meds requested.",
            "junior": "Discharge script written. Waiting for pharmacy.",
        },
        "meds": [{"name": "Amoxicillin", "code": "723", "dosage": "500mg TDS PO", "status": "active"}],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # 15. CKD Stage 4 Exacerbation, Day 3
    {
        "bed": "15",
        "patient": {
            "name": "Samuel Jackson",
            "dob": "1948-02-28",
            "gender": "male",
            "condition": "CKD Exacerbation",
            "consultant": CONSULTANTS[2],
            "day": 3,
        },
        "vitals_trend": "stable",
        "labs": [
            {"code": "2823-3", "name": "Potassium", "value": 6.2, "unit": "mmol/L", "flag": "H"},
            {"code": "33914-3", "name": "eGFR", "value": 14, "unit": "mL/min/1.73m2", "flag": "L"},
        ],
        "notes": {
            "specialist": "Nephrology: Severe hyperkalaemia (6.2). Hold ACEi. Calcium Resonium started.",
            "junior": "Stable on diuretics. [CONFLICT: Still on Ramipril (ACEi) despite hyperkalaemia/MDT plan].",
        },
        "meds": [
            {"name": "Ramipril", "code": "35296", "dosage": "10mg OD PO", "status": "active"}, # CONFLICT
            {"name": "Calcium Resonium", "code": "203253", "dosage": "15g TDS PO", "status": "active"},
        ],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "medium"}],
        "flags": [{"code": "DIET", "detail": "Low Potassium Diet"}],
    },
]
