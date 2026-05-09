"""Inpatient ward seed data - 15 patients for general medicine ward round."""

from datetime import datetime, timedelta, timezone

NOW = datetime.now(timezone.utc)
TODAY = NOW.date()

# Helper: days ago from now
def _ago(days=0, hours=0):
    return (NOW - timedelta(days=days, hours=hours)).isoformat()


# =====================================================================
# PATIENT 1: James Carter - Sepsis (UTI source), deteriorating
# =====================================================================
P1 = {
    "name": ("James", "Carter"), "gender": "male", "dob": "1948-03-12",
    "ward": "General Medicine", "bed": "Bay A, Bed 1",
    "admission_days_ago": 3,
    "admitting_dx": "Urosepsis",
    "encounter_reason": "Found confused and febrile at home by carer",
    "conditions": [
        ("A41.9", "Sepsis, unspecified organism"),
        ("N39.0", "Urinary tract infection"),
        ("N18.3", "Chronic kidney disease, stage 3"),
        ("I10", "Essential hypertension"),
        ("F03.90", "Unspecified dementia"),
    ],
    "allergies": [
        ("Penicillin", "anaphylaxis"),
        ("Sulfonamides", "rash"),
    ],
    "medications": [
        ("Meropenem 1g", 311364, "1 g", "every 8 hours", "intravenous", "active"),
        ("Paracetamol 1g", 198440, "1 g", "every 6 hours", "oral", "active"),
        ("Metoclopramide 10mg", 311700, "10 mg", "three times daily", "oral", "active"),
        ("Enoxaparin 40mg", 854228, "40 mg", "once daily", "subcutaneous", "active"),
        ("Amlodipine 5mg", 329528, "5 mg", "once daily", "oral", "active"),
        ("Donepezil 10mg", 312835, "10 mg", "at bedtime", "oral", "active"),
        ("IV Normal Saline", 313002, "1000 mL", "over 8 hours", "intravenous", "active"),
    ],
    # (hours_ago, given/missed/held)
    "med_admin": [
        ("Meropenem 1g", 2, "given"), ("Meropenem 1g", 10, "given"),
        ("Meropenem 1g", 18, "given"),
        ("Paracetamol 1g", 3, "given"), ("Paracetamol 1g", 9, "missed"),
        ("Paracetamol 1g", 15, "given"), ("Paracetamol 1g", 21, "given"),
        ("Enoxaparin 40mg", 6, "given"),
        ("Amlodipine 5mg", 8, "held"),  # held due to low BP
        ("Donepezil 10mg", 10, "given"),
    ],
    # (hours_ago, sbp, dbp, hr, rr, spo2, temp, gcs)
    "vitals": [
        (24, 125, 72, 88, 18, 96, 37.2, 14),
        (20, 118, 68, 92, 20, 95, 37.8, 14),
        (16, 112, 65, 98, 22, 94, 38.2, 13),
        (12, 105, 58, 105, 24, 93, 38.6, 13),
        (8,  98, 52, 112, 26, 91, 38.9, 12),
        (4,  92, 48, 118, 28, 89, 39.2, 11),
        (1,  88, 45, 122, 30, 87, 39.4, 10),
    ],
    "labs": [
        (48, {
            "6690-2": (12.5, "K/uL"), "718-7": (11.2, "g/dL"), "777-3": (180, "K/uL"),
            "2951-2": (138, "mEq/L"), "2823-3": (4.5, "mEq/L"), "2160-0": (1.9, "mg/dL"),
            "3094-0": (28, "mg/dL"), "2345-7": (145, "mg/dL"),
            "1988-5": (85, "mg/L"), "33959-8": (1.2, "ng/mL"),
        }),
        (6, {
            "6690-2": (22.0, "K/uL"), "718-7": (10.0, "g/dL"), "777-3": (120, "K/uL"),
            "2951-2": (132, "mEq/L"), "2823-3": (5.2, "mEq/L"), "2160-0": (3.1, "mg/dL"),
            "3094-0": (48, "mg/dL"), "2345-7": (180, "mg/dL"),
            "1988-5": (280, "mg/L"), "33959-8": (8.5, "ng/mL"),
            "1742-6": (55, "U/L"), "1920-8": (62, "U/L"),
        }),
    ],
    "notes": {
        "admission": (
            "76yo male brought in by ambulance after carer found him confused and "
            "febrile at home. PMH: CKD3, HTN, dementia. On examination: temp 38.5, "
            "HR 95, BP 110/65, RR 22, SpO2 94% RA. Abdomen soft, suprapubic tenderness. "
            "Urine dipstick positive nitrites and leucocytes. Working diagnosis: urosepsis. "
            "Plan: blood cultures x2, urine MCS, IV meropenem (penicillin allergic), "
            "IV fluids, sepsis bundle, catheterise for urine output monitoring."
        ),
        "nursing": [
            (18, "Night shift: Patient restless overnight, temp spiked to 38.9. "
                 "Given paracetamol with good effect. Urine output 15ml/hr via catheter. "
                 "IV fluids running. Called doctor regarding low urine output."),
            (10, "Morning shift: Patient increasingly confused, not oriented to time or place. "
                 "Refusing oral intake. Temp 39.2. BP trending down, HR up. "
                 "SpO2 dropped to 89% - started 2L O2 via nasal prongs. "
                 "Escalated to registrar."),
            (2,  "Afternoon shift: Patient appears comfortable and settled. "
                 "Observations stable. No acute concerns this shift."),
        ],
        "progress": (
            "S: Patient confused, unable to give history. Carer reports worsening over 3 days. "
            "O: Febrile 38.6, tachycardic 105, hypotensive 98/52, RR 26, SpO2 91% on 2L. "
            "WBC 22.0, CRP 280, Procalcitonin 8.5, Cr 3.1 (baseline 1.9). "
            "A: Deteriorating sepsis with AKI. Source likely urinary. "
            "P: Continue IV meropenem. Increase fluids to 250ml/hr bolus. "
            "Hold amlodipine. Repeat bloods in 6 hours. Consider ICU referral if no improvement."
        ),
    },
    "procedures": [
        ("Urinary catheter insertion", _ago(days=3)),
        ("Peripheral IV cannulation", _ago(days=3)),
        ("Blood culture collection x2", _ago(days=3)),
    ],
    "diagnostics": [
        ("Chest X-ray", _ago(days=3),
         "PA erect chest radiograph. Heart size normal. No focal consolidation. "
         "No pleural effusion. No pneumothorax. Clear lung fields bilaterally."),
        ("Urine MCS", _ago(days=2),
         "Gram-negative bacilli seen on microscopy. Culture: E. coli >10^5 CFU/mL. "
         "Sensitive to meropenem, gentamicin, nitrofurantoin. Resistant to amoxicillin, "
         "trimethoprim, ciprofloxacin."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
        ("Dr Amir Khan", "Registrar", "General Medicine"),
        ("Dr Lucy Patel", "Junior Doctor", "General Medicine"),
        ("Nurse Karen Williams", "Primary Nurse", "Ward"),
    ],
    "flags": [
        ("fall-risk", "high", "Confusion + elderly"),
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 2: Margaret Liu - Decompensated heart failure
# =====================================================================
P2 = {
    "name": ("Margaret", "Liu"), "gender": "female", "dob": "1955-11-28",
    "ward": "General Medicine", "bed": "Bay A, Bed 3",
    "admission_days_ago": 5,
    "admitting_dx": "Decompensated heart failure",
    "encounter_reason": "Progressive dyspnoea and bilateral leg swelling over 1 week",
    "conditions": [
        ("I50.9", "Heart failure, unspecified"),
        ("I10", "Essential hypertension"),
        ("E11.9", "Type 2 diabetes mellitus without complications"),
        ("I48.91", "Atrial fibrillation"),
        ("N18.3", "Chronic kidney disease, stage 3"),
    ],
    "allergies": [
        ("ACE inhibitors", "angioedema"),
    ],
    "medications": [
        ("Furosemide 80mg", 310429, "80 mg", "twice daily", "intravenous", "active"),
        ("Spironolactone 25mg", 313096, "25 mg", "once daily", "oral", "active"),
        ("Bisoprolol 5mg", 854916, "5 mg", "once daily", "oral", "active"),
        ("Digoxin 125mcg", 197604, "125 mcg", "once daily", "oral", "active"),
        ("Warfarin 5mg", 855332, "5 mg", "once daily", "oral", "active"),
        ("Metformin 500mg", 861004, "500 mg", "twice daily", "oral", "active"),
        ("Aspirin 75mg", 243670, "75 mg", "once daily", "oral", "active"),
        ("Omeprazole 20mg", 198053, "20 mg", "once daily", "oral", "active"),
    ],
    "med_admin": [
        ("Furosemide 80mg", 2, "given"), ("Furosemide 80mg", 14, "given"),
        ("Spironolactone 25mg", 8, "given"),
        ("Bisoprolol 5mg", 8, "given"),
        ("Digoxin 125mcg", 8, "given"),
        ("Warfarin 5mg", 20, "given"),
        ("Metformin 500mg", 2, "given"), ("Metformin 500mg", 14, "given"),
        ("Aspirin 75mg", 8, "given"),
    ],
    "vitals": [
        (24, 145, 85, 95, 22, 93, 36.8, 15),
        (20, 140, 82, 92, 20, 94, 36.7, 15),
        (16, 138, 80, 88, 20, 94, 36.8, 15),
        (12, 135, 78, 85, 18, 95, 36.7, 15),
        (8,  132, 76, 82, 18, 95, 36.8, 15),
        (4,  130, 75, 80, 16, 96, 36.7, 15),
    ],
    "labs": [
        (72, {
            "6690-2": (8.0, "K/uL"), "718-7": (11.5, "g/dL"), "777-3": (200, "K/uL"),
            "2951-2": (135, "mEq/L"), "2823-3": (5.0, "mEq/L"), "2160-0": (1.6, "mg/dL"),
            "3094-0": (30, "mg/dL"), "2345-7": (110, "mg/dL"),
            "30934-4": (1200, "pg/mL"), "2069-3": (0.02, "ng/mL"),
        }),
        (8, {
            "6690-2": (7.5, "K/uL"), "718-7": (11.0, "g/dL"), "777-3": (195, "K/uL"),
            "2951-2": (133, "mEq/L"), "2823-3": (5.4, "mEq/L"), "2160-0": (1.8, "mg/dL"),
            "3094-0": (35, "mg/dL"), "2345-7": (105, "mg/dL"),
            "30934-4": (850, "pg/mL"),
        }),
    ],
    "notes": {
        "admission": (
            "71yo female presents with 1 week worsening dyspnoea on exertion, "
            "now dyspnoeic at rest. Bilateral pitting oedema to knees. PMH: HF, "
            "AF, DM2, CKD3. On examination: elevated JVP, bilateral basal crackles "
            "to mid-zones, peripheral oedema. BNP 1200. CXR: bilateral pleural effusions. "
            "Diagnosis: decompensated HF. Plan: IV furosemide, daily weights, fluid restrict "
            "1.5L/day, monitor renal function."
        ),
        "nursing": [
            (18, "Night shift: Patient slept with 4 pillows. Woke twice with breathlessness. "
                 "O2 sats 93% on room air. Urine output 180ml overnight with IV frusemide. "
                 "Weight this morning 82.3kg (yesterday 83.1kg). Fluid intake 800ml."),
            (10, "Morning shift: Patient reports feeling slightly better. Able to walk to "
                 "bathroom with assistance. Appetite poor. No chest pain. "
                 "Oedema slightly improved bilaterally."),
            (2,  "Afternoon shift: Patient resting comfortably. O2 sats 96% on room air. "
                 "Good urine output this shift. Weight trending down. No concerns."),
        ],
        "progress": (
            "S: Patient reports improved breathing compared to admission. Still SOB on exertion. "
            "O: BP 132/76, HR 82 irregular, RR 18, SpO2 95%. JVP 4cm. Crackles at bases only. "
            "Oedema improved. Weight down 3.8kg from admission. BNP trending down 1200->850. "
            "K+ 5.4 on spironolactone + furosemide. Cr 1.8 (baseline 1.6). "
            "A: Improving HF. Monitor potassium closely - borderline high on dual diuretics. "
            "P: Continue IV frusemide. Recheck K+ and Cr tomorrow. If stable, switch to oral "
            "frusemide and plan discharge in 2 days."
        ),
    },
    "procedures": [
        ("Peripheral IV cannulation", _ago(days=5)),
        ("ECG 12-lead", _ago(days=5)),
    ],
    "diagnostics": [
        ("Chest X-ray", _ago(days=5),
         "PA erect. Cardiomegaly. Bilateral pleural effusions, moderate. "
         "Upper lobe pulmonary venous congestion. No focal consolidation."),
        ("ECG", _ago(days=5),
         "Atrial fibrillation, ventricular rate 95. No acute ST changes. "
         "Left axis deviation. T-wave inversion in V5-V6, old."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
        ("Dr Amir Khan", "Registrar", "General Medicine"),
        ("Dr Lucy Patel", "Junior Doctor", "General Medicine"),
        ("Nurse James Obi", "Primary Nurse", "Ward"),
    ],
    "flags": [
        ("fall-risk", "moderate", "Oedema + diuretics"),
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 3: Robert Okafor - Community-acquired pneumonia, improving
# =====================================================================
P3 = {
    "name": ("Robert", "Okafor"), "gender": "male", "dob": "1962-07-15",
    "ward": "General Medicine", "bed": "Bay B, Bed 5",
    "admission_days_ago": 4,
    "admitting_dx": "Community-acquired pneumonia",
    "encounter_reason": "Productive cough, fever, and pleuritic chest pain for 5 days",
    "conditions": [
        ("J18.9", "Pneumonia, unspecified organism"),
        ("J44.1", "COPD with acute exacerbation"),
        ("E78.5", "Hyperlipidaemia"),
    ],
    "allergies": [
        ("Clarithromycin", "QT prolongation"),
    ],
    "medications": [
        ("Amoxicillin 1g", 308182, "1 g", "three times daily", "oral", "active"),
        ("Doxycycline 100mg", 310027, "100 mg", "twice daily", "oral", "active"),
        ("Salbutamol nebuliser 5mg", 630208, "5 mg", "every 4 hours", "inhaled", "active"),
        ("Prednisolone 40mg", 312615, "40 mg", "once daily", "oral", "active"),
        ("Enoxaparin 40mg", 854228, "40 mg", "once daily", "subcutaneous", "active"),
        ("Atorvastatin 20mg", 259255, "20 mg", "at bedtime", "oral", "active"),
    ],
    "med_admin": [
        ("Amoxicillin 1g", 2, "given"), ("Amoxicillin 1g", 10, "given"),
        ("Amoxicillin 1g", 18, "given"),
        ("Doxycycline 100mg", 2, "given"), ("Doxycycline 100mg", 14, "given"),
        ("Salbutamol nebuliser 5mg", 4, "given"), ("Salbutamol nebuliser 5mg", 8, "given"),
        ("Prednisolone 40mg", 8, "given"),
        ("Enoxaparin 40mg", 22, "given"),
        ("Atorvastatin 20mg", 10, "given"),
    ],
    "vitals": [
        (24, 128, 78, 90, 22, 93, 38.0, 15),
        (20, 125, 76, 86, 20, 94, 37.6, 15),
        (16, 122, 74, 82, 18, 95, 37.2, 15),
        (12, 120, 72, 80, 18, 96, 37.0, 15),
        (8,  118, 72, 78, 16, 96, 36.8, 15),
        (4,  118, 70, 76, 16, 97, 36.7, 15),
    ],
    "labs": [
        (72, {
            "6690-2": (15.0, "K/uL"), "718-7": (13.5, "g/dL"), "777-3": (250, "K/uL"),
            "2951-2": (139, "mEq/L"), "2823-3": (4.0, "mEq/L"), "2160-0": (0.9, "mg/dL"),
            "3094-0": (14, "mg/dL"), "2345-7": (125, "mg/dL"),
            "1988-5": (180, "mg/L"),
        }),
        (8, {
            "6690-2": (10.5, "K/uL"), "718-7": (13.2, "g/dL"), "777-3": (245, "K/uL"),
            "2951-2": (140, "mEq/L"), "2823-3": (4.1, "mEq/L"), "2160-0": (0.9, "mg/dL"),
            "3094-0": (13, "mg/dL"), "2345-7": (115, "mg/dL"),
            "1988-5": (65, "mg/L"),
        }),
    ],
    "notes": {
        "admission": (
            "64yo male presents with 5-day history of productive cough (green sputum), "
            "fever, and right-sided pleuritic chest pain. PMH: COPD, hyperlipidaemia. "
            "On examination: temp 38.5, RR 24, SpO2 92% RA. Right lower lobe crackles. "
            "CXR: right lower lobe consolidation. CURB-65 score 2. "
            "Plan: IV amoxicillin + doxycycline (clarithromycin allergic), nebulisers, "
            "prednisolone for COPD component. Reassess in 48 hours for step-down."
        ),
        "nursing": [
            (18, "Night shift: Patient slept well. Temp 36.8. Cough productive but less "
                 "frequent. O2 sats 96% on room air - O2 weaned off yesterday evening. "
                 "Good oral intake. No concerns overnight."),
            (10, "Morning shift: Patient mobilising to bathroom independently. "
                 "Appetite improving. Sputum clearing. Reports feeling much better. "
                 "Keen to go home."),
            (2,  "Afternoon shift: Patient stable. Mobilising well. No O2 requirement. "
                 "Observations all within normal limits. Discussed discharge planning."),
        ],
        "progress": (
            "S: Patient reports significant improvement. Cough less frequent, sputum clearing. "
            "No fever for 48 hours. Able to mobilise independently. "
            "O: Temp 36.7, HR 76, BP 118/70, RR 16, SpO2 97% RA. Chest: reduced crackles "
            "right base, much improved. WBC down 15->10.5, CRP 180->65. "
            "A: Improving CAP. Ready for step-down to oral antibiotics. "
            "P: Continue oral amoxicillin and doxycycline. Wean prednisolone. "
            "Plan discharge tomorrow if continues to improve."
        ),
    },
    "procedures": [
        ("Sputum sample collection", _ago(days=4)),
        ("Peripheral IV cannulation", _ago(days=4)),
    ],
    "diagnostics": [
        ("Chest X-ray", _ago(days=4),
         "PA erect. Right lower lobe consolidation with air bronchograms. "
         "No pleural effusion. Heart size normal."),
        ("Chest X-ray", _ago(days=1),
         "Interval improvement. Residual right lower lobe opacity, clearing. "
         "No new changes."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
        ("Dr Amir Khan", "Registrar", "General Medicine"),
        ("Dr Lucy Patel", "Junior Doctor", "General Medicine"),
        ("Nurse Fiona Chen", "Primary Nurse", "Ward"),
    ],
    "flags": [
        ("fall-risk", "low", "Mobilising independently"),
        ("resuscitation", "full", "Full resuscitation"),
    ],
}


# =====================================================================
# PATIENT 4: Sarah Mitchell - AKI on CKD, rising creatinine
# =====================================================================
P4 = {
    "name": ("Sarah", "Mitchell"), "gender": "female", "dob": "1968-05-22",
    "ward": "General Medicine", "bed": "Bay B, Bed 6",
    "admission_days_ago": 2,
    "admitting_dx": "Acute kidney injury on CKD",
    "encounter_reason": "Nausea, vomiting, and reduced urine output",
    "conditions": [
        ("N17.9", "Acute kidney failure, unspecified"),
        ("N18.3", "Chronic kidney disease, stage 3"),
        ("E11.9", "Type 2 diabetes mellitus"),
        ("M10.9", "Gout, unspecified"),
    ],
    "allergies": [
        ("Iodinated contrast", "anaphylaxis"),
    ],
    "medications": [
        ("IV Normal Saline", 313002, "1000 mL", "over 12 hours", "intravenous", "active"),
        ("Metformin 500mg", 861004, "500 mg", "twice daily", "oral", "active"),
        ("Naproxen 500mg", 197992, "500 mg", "twice daily", "oral", "active"), # DDI/Risk
        ("Lisinopril 10mg", 311354, "10 mg", "once daily", "oral", "active"),
        ("Allopurinol 100mg", 197318, "100 mg", "once daily", "oral", "active"),
    ],
    "med_admin": [
        ("IV Normal Saline", 12, "given"),
        ("Metformin 500mg", 8, "given"),
        ("Naproxen 500mg", 8, "given"), # Patient took this for gout flare
        ("Lisinopril 10mg", 8, "given"),
    ],
    "vitals": [
        (24, 150, 90, 80, 16, 98, 36.6, 15),
        (20, 145, 88, 78, 16, 98, 36.5, 15),
        (16, 140, 85, 75, 14, 99, 36.6, 15),
        (12, 138, 82, 72, 14, 99, 36.5, 15),
        (8,  135, 80, 70, 12, 99, 36.6, 15),
        (4,  130, 78, 68, 12, 99, 36.5, 15),
    ],
    "labs": [
        (48, {
            "2160-0": (1.8, "mg/dL"), "3094-0": (25, "mg/dL"), "2823-3": (4.2, "mEq/L"),
        }),
        (6, {
            "2160-0": (2.9, "mg/dL"), "3094-0": (45, "mg/dL"), "2823-3": (5.5, "mEq/L"),
        }),
    ],
    "notes": {
        "admission": (
            "56yo female with CKD3 and DM2 admitted with nausea and vomiting. "
            "Reported taking naproxen for a gout flare over the last 3 days. "
            "Urine output has been sparse. BP 150/90. Working diagnosis: AKI secondary "
            "to NSAID use and dehydration. Plan: IV hydration, hold nephrotoxic "
            "medications (metformin, lisinopril, naproxen), daily U&Es."
        ),
        "nursing": [
            (18, "Night shift: Patient nauseous, vomited once. IV fluids running at 80ml/hr. "
                 "Urine output minimal, approx 20ml in 4 hours."),
            (10, "Morning shift: Patient complaining of pain in right big toe. "
                 "Requested pain relief. Administered naproxen as per chart."), # Conflict: nurse gave held med
            (2,  "Afternoon shift: Doctor reviewed patient. Noted rising creatinine. "
                 "Strict fluid balance chart initiated."),
        ],
        "progress": (
            "S: Patient feels tired, persistent toe pain. Nausea slightly improved. "
            "O: BP 130/78, urine output <0.5ml/kg/hr. Cr rose from 1.8 to 2.9. "
            "Potassium 5.5. A: AKI stage 2, likely NSAID induced. "
            "P: REITERATE: Hold all nephrotoxics. Increase IV fluids. Check K+ in 4h. "
            "Review medication administration - naproxen should not have been given.")
    },
    "procedures": [
        ("Strict fluid balance", _ago(hours=12)),
    ],
    "diagnostics": [
        ("Renal Ultrasound", _ago(days=1), "Normal sized kidneys. No hydronephrosis. "
         "Increased echogenicity consistent with medical renal disease."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
        ("Nurse Karen Williams", "Primary Nurse", "Ward"),
    ],
    "flags": [
        ("fall-risk", "low", "Independent"),
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 5: William Park - COPD exacerbation
# =====================================================================
P5 = {
    "name": ("William", "Park"), "gender": "male", "dob": "1952-11-05",
    "ward": "General Medicine", "bed": "Bay B, Bed 7",
    "admission_days_ago": 1,
    "admitting_dx": "COPD exacerbation",
    "encounter_reason": "Increased shortness of breath and wheezing",
    "conditions": [
        ("J44.1", "COPD with acute exacerbation"),
        ("I10", "Essential hypertension"),
    ],
    "allergies": [],
    "medications": [
        ("Prednisolone 40mg", 312615, "40 mg", "once daily", "oral", "active"),
        ("Salbutamol 2.5mg", 630208, "2.5 mg", "every 4 hours", "inhaled", "active"),
        ("Ipratropium 500mcg", 197825, "500 mcg", "every 6 hours", "inhaled", "active"),
        ("Oxygen", 312152, "2 L/min", "continuous", "inhalation", "active"),
    ],
    "med_admin": [
        ("Prednisolone 40mg", 8, "given"),
        ("Salbutamol 2.5mg", 4, "given"), ("Salbutamol 2.5mg", 8, "given"),
        ("Ipratropium 500mcg", 6, "given"),
    ],
    "vitals": [
        (24, 140, 85, 100, 24, 88, 37.0, 15),
        (20, 138, 82, 98, 22, 90, 36.9, 15),
        (16, 135, 80, 95, 22, 91, 37.0, 15),
        (12, 132, 78, 92, 20, 92, 36.9, 15),
        (8,  130, 76, 90, 20, 92, 37.0, 15),
        (4,  128, 75, 88, 18, 93, 36.9, 15),
    ],
    "labs": [
        (24, {
            "2019-8": (45, "mmHg"), "2703-7": (65, "mmHg"), "2744-1": (7.36, "pH"),
        }),
    ],
    "notes": {
        "admission": (
            "72yo male with long-standing COPD presents with worsening SOB "
            "for 2 days. On examination: barrel chest, diffuse wheeze, "
            "SpO2 88% on RA. ABG shows pH 7.36, pCO2 45. "
            "Plan: steroids, nebulisers, controlled oxygen (target 88-92%)."
        ),
        "nursing": [
            (18, "Night shift: Patient required 2 extra nebulisers for SOB. "
                 "Maintains SpO2 90% on 2L O2."),
            (10, "Morning shift: Breathing more comfortable. Using accessory muscles less."),
            (2,  "Afternoon shift: Stable. Peak flow 250."),
        ],
        "progress": (
            "S: Better. O: Wheeze reduced. SpO2 92% on 1L. A: Improving COPD exacerbation. "
            "P: Continue current management. Wean O2 as tolerated.")
    },
    "procedures": [],
    "diagnostics": [
        ("Chest X-ray", _ago(days=1), "Hyperexpanded lungs. Flattened diaphragms. "
         "No acute consolidation."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
        ("Nurse Fiona Chen", "Primary Nurse", "Ward"),
    ],
    "flags": [
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 6: Dorothy Chen - Hypertensive crisis
# =====================================================================
P6 = {
    "name": ("Dorothy", "Chen"), "gender": "female", "dob": "1945-09-30",
    "ward": "General Medicine", "bed": "Bay C, Bed 10",
    "admission_days_ago": 1,
    "admitting_dx": "Hypertensive crisis",
    "encounter_reason": "Severe headache and blurred vision",
    "conditions": [
        ("I16.9", "Hypertensive crisis, unspecified"),
        ("I10", "Essential hypertension"),
    ],
    "allergies": [],
    "medications": [
        ("Labetalol 200mg", 311303, "200 mg", "twice daily", "oral", "active"),
        ("Amlodipine 10mg", 329528, "10 mg", "once daily", "oral", "active"),
    ],
    "med_admin": [
        ("Labetalol 200mg", 8, "given"),
        ("Amlodipine 10mg", 8, "given"),
    ],
    "vitals": [
        (24, 210, 115, 70, 18, 98, 36.5, 15),
        (20, 200, 110, 68, 16, 98, 36.4, 15),
        (16, 190, 105, 68, 16, 98, 36.5, 15),
        (12, 185, 100, 66, 14, 99, 36.4, 15),
        (8,  180, 95,  66, 14, 99, 36.5, 15),
        (4,  175, 90,  64, 14, 99, 36.4, 15),
    ],
    "labs": [
        (24, {
            "2160-0": (1.1, "mg/dL"), "2345-7": (120, "mg/dL"),
        }),
    ],
    "notes": {
        "admission": (
            "78yo female with known HTN presents with severe headache. "
            "BP 210/115. No neuro deficits on exam. Plan: gradual BP reduction "
            "with oral agents. Monitor for end-organ damage."
        ),
        "nursing": [
            (12, "Patient reports headache is improving. BP trending down."),
        ],
        "progress": (
            "S: Headache better. O: BP 175/90. A: Controlled HTN. "
            "P: Continue labetalol and amlodipine. Aim for <140/90.")
    },
    "procedures": [],
    "diagnostics": [
        ("CT Head", _ago(days=1), "No acute intracranial haemorrhage or infarct."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("resuscitation", "full", "Full resuscitation"),
    ],
}


# =====================================================================
# PATIENT 7: Ahmed Hassan - Ischaemic stroke
# =====================================================================
P7 = {
    "name": ("Ahmed", "Hassan"), "gender": "male", "dob": "1960-02-15",
    "ward": "General Medicine", "bed": "Bay C, Bed 11",
    "admission_days_ago": 4,
    "admitting_dx": "Ischaemic stroke",
    "encounter_reason": "Right-sided weakness and slurred speech",
    "conditions": [
        ("I63.9", "Cerebral infarction, unspecified"),
        ("I10", "Essential hypertension"),
        ("I48.0", "Paroxysmal atrial fibrillation"),
    ],
    "allergies": [],
    "medications": [
        ("Aspirin 300mg", 243670, "300 mg", "once daily", "oral", "active"),
        ("Atorvastatin 80mg", 259255, "80 mg", "once daily", "oral", "active"),
        ("Amlodipine 5mg", 329528, "5 mg", "once daily", "oral", "active"),
    ],
    "med_admin": [
        ("Aspirin 300mg", 8, "given"),
        ("Atorvastatin 80mg", 20, "given"),
        ("Amlodipine 5mg", 8, "given"),
    ],
    "vitals": [
        (24, 160, 95, 75, 16, 98, 36.6, 15),
        (20, 155, 92, 72, 16, 98, 36.5, 15),
        (16, 150, 90, 72, 14, 99, 36.6, 15),
        (12, 148, 88, 70, 14, 99, 36.5, 15),
        (8,  145, 85, 70, 14, 99, 36.6, 15),
        (4,  140, 80, 68, 14, 99, 36.5, 15),
    ],
    "labs": [
        (24, {
            "2345-7": (110, "mg/dL"), "2160-0": (1.0, "mg/dL"),
        }),
    ],
    "notes": {
        "admission": (
            "64yo male presented with sudden onset R-sided weakness. "
            "CT Head showed no bleed. Loading dose of aspirin given. "
            "Plan: stroke unit admission, swallow assessment, MRI brain."
        ),
        "nursing": [
            (12, "Neuro-obs stable. Power 4/5 in R arm. Speech improving."),
        ],
        "progress": (
            "S: Better. O: Neuro exam stable. A: Resolving stroke. "
            "P: Continue aspirin 300mg for 2 weeks, then switch to clopidogrel.")
    },
    "procedures": [],
    "diagnostics": [
        ("CT Head", _ago(days=4), "No acute haemorrhage."),
        ("MRI Brain", _ago(days=3), "Acute infarct in the left MCA territory."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("fall-risk", "high", "Unilateral weakness"),
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 8: Patricia Brown - DVT with Pulmonary embolism
# =====================================================================
P8 = {
    "name": ("Patricia", "Brown"), "gender": "female", "dob": "1970-11-12",
    "ward": "General Medicine", "bed": "Bay C, Bed 12",
    "admission_days_ago": 3,
    "admitting_dx": "Pulmonary embolism",
    "encounter_reason": "Shortness of breath and pleuritic chest pain",
    "conditions": [
        ("I26.99", "Pulmonary embolism without acute cor pulmonale"),
        ("I82.40", "Acute embolism and thrombosis of unspecified deep veins of lower extremity"),
    ],
    "allergies": [],
    "medications": [
        ("Rivaroxaban 15mg", 1114448, "15 mg", "twice daily", "oral", "active"),
        ("Enoxaparin 80mg", 854228, "80 mg", "twice daily", "subcutaneous", "active"), # Overlap conflict
    ],
    "med_admin": [
        ("Rivaroxaban 15mg", 8, "given"),
        ("Enoxaparin 80mg", 8, "given"), # Conflict: dual anticoagulation
    ],
    "vitals": [
        (24, 120, 80, 110, 22, 92, 37.2, 15),
        (20, 118, 78, 105, 20, 93, 37.0, 15),
        (16, 115, 75, 95,  20, 95, 36.9, 15),
        (12, 112, 72, 90,  18, 96, 36.8, 15),
        (8,  110, 70, 85,  18, 97, 36.7, 15),
        (4,  110, 70, 80,  16, 98, 36.6, 15),
    ],
    "labs": [
        (24, {
            "48065-7": (4500, "ng/mL"), # D-dimer high
        }),
    ],
    "notes": {
        "admission": (
            "53yo female with calf swelling and sudden SOB. CTPA confirmed PE. "
            "Plan: anticoagulation, monitor for bleeding."
        ),
        "nursing": [
            (12, "Patient comfortable. SOB resolving. Calf pain improved."),
        ],
        "progress": (
            "S: Better. O: HR 80, SpO2 98%. A: Improving PE. "
            "P: Start rivaroxaban. Stop enoxaparin.")
    },
    "procedures": [],
    "diagnostics": [
        ("CTPA", _ago(days=3), "Acute PE in the right lower lobe pulmonary artery."),
        ("Venous Doppler", _ago(days=3), "DVT in the right popliteal vein."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 9: David Nguyen - Diabetic ketoacidosis
# =====================================================================
P9 = {
    "name": ("David", "Nguyen"), "gender": "male", "dob": "1995-03-25",
    "ward": "General Medicine", "bed": "Bay D, Bed 15",
    "admission_days_ago": 1,
    "admitting_dx": "Diabetic ketoacidosis",
    "encounter_reason": "Vomiting, abdominal pain, and rapid breathing",
    "conditions": [
        ("E10.10", "Type 1 diabetes mellitus with ketoacidosis without coma"),
    ],
    "allergies": [],
    "medications": [
        ("IV Insulin Infusion", 311053, "0.1 units/kg/hr", "continuous", "intravenous", "active"),
        ("IV Normal Saline + 20mmol KCl", 313002, "1000 mL", "over 4 hours", "intravenous", "active"),
    ],
    "med_admin": [
        ("IV Insulin Infusion", 1, "given"),
    ],
    "vitals": [
        (24, 110, 70, 120, 30, 99, 37.0, 14),
        (20, 112, 72, 115, 28, 99, 36.9, 14),
        (16, 115, 75, 105, 24, 99, 37.0, 15),
        (12, 118, 78, 95,  22, 99, 36.9, 15),
        (8,  120, 80, 85,  20, 99, 37.0, 15),
        (4,  122, 82, 80,  18, 99, 36.9, 15),
    ],
    "labs": [
        (24, {
            "2345-7": (450, "mg/dL"), "2744-1": (7.15, "pH"), "20591-1": (5.5, "mmol/L"), # Ketones high
        }),
        (4, {
            "2345-7": (210, "mg/dL"), "2744-1": (7.32, "pH"), "20591-1": (1.2, "mmol/L"),
        }),
    ],
    "notes": {
        "admission": (
            "29yo male with T1DM. Nausea/vomiting. Glucose 450, pH 7.15. "
            "Plan: DKA protocol, IV insulin, aggressive fluids."
        ),
        "nursing": [
            (12, "Glucose checks hourly. Ketones clearing. Fluid balance strict."),
        ],
        "progress": (
            "S: Feels better. O: pH 7.32. A: Resolving DKA. "
            "P: Continue insulin until ketones <0.6 and eating. Then switch to SC.")
    },
    "procedures": [
        ("Hourly glucose monitoring", _ago(hours=24)),
    ],
    "diagnostics": [],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("resuscitation", "full", "Full resuscitation"),
    ],
}


# =====================================================================
# PATIENT 10: Helen Taylor - Upper GI bleed
# =====================================================================
P10 = {
    "name": ("Helen", "Taylor"), "gender": "female", "dob": "1940-08-14",
    "ward": "General Medicine", "bed": "Bay D, Bed 16",
    "admission_days_ago": 2,
    "admitting_dx": "Upper GI bleed",
    "encounter_reason": "Melaena and dizziness",
    "conditions": [
        ("K92.1", "Melaena"),
        ("I10", "Essential hypertension"),
        ("M17.9", "Osteoarthritis of knee"),
    ],
    "allergies": [
        ("Aspirin", "gastric bleed"),
    ],
    "medications": [
        ("Omeprazole 40mg", 198053, "40 mg", "twice daily", "intravenous", "active"),
        ("IV Normal Saline", 313002, "1000 mL", "over 8 hours", "intravenous", "active"),
    ],
    "med_admin": [
        ("Omeprazole 40mg", 8, "given"),
    ],
    "vitals": [
        (24, 100, 60, 110, 20, 99, 36.8, 15),
        (20, 105, 62, 105, 18, 99, 36.7, 15),
        (16, 110, 65, 95,  18, 99, 36.8, 15),
        (12, 115, 70, 90,  16, 99, 36.7, 15),
        (8,  118, 72, 85,  16, 99, 36.8, 15),
        (4,  120, 75, 80,  16, 99, 36.7, 15),
    ],
    "labs": [
        (48, {
            "718-7": (7.5, "g/dL"), "777-3": (250, "K/uL"),
        }),
        (8, {
            "718-7": (8.2, "g/dL"), "777-3": (245, "K/uL"),
        }),
    ],
    "notes": {
        "admission": (
            "83yo female. Melaena stool x2. Hb 7.5. Plan: IV PPI, "
            "Group and Save, OGD (gastroscopy)."
        ),
        "nursing": [
            (12, "Patient stable. No further melaena reported today. "
                 "Nil by mouth for OGD."),
        ],
        "progress": (
            "S: Feels better. O: Hb 8.2 after 1 unit blood. A: Resolving GI bleed. "
            "P: Proceed with OGD today. If clear, start oral PPI and discharge.")
    },
    "procedures": [
        ("Group and Save", _ago(days=2)),
        ("Blood transfusion x1 unit", _ago(days=1)),
    ],
    "diagnostics": [
        ("OGD", _ago(hours=4), "Small gastric ulcer with clean base. No active bleeding."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("nil-by-mouth", "active", "For OGD"),
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 11: Frank Morrison - Fall with hip fracture
# =====================================================================
P11 = {
    "name": ("Frank", "Morrison"), "gender": "male", "dob": "1942-05-18",
    "ward": "General Medicine", "bed": "Bay E, Bed 18",
    "admission_days_ago": 1,
    "admitting_dx": "Hip fracture",
    "encounter_reason": "Fall at home, unable to weight bear",
    "conditions": [
        ("S72.00", "Fracture of neck of femur, unspecified"),
        ("F03.90", "Dementia"),
    ],
    "allergies": [],
    "medications": [
        ("Morphine 2.5mg", 311740, "2.5 mg", "every 4 hours prn", "intravenous", "active"),
        ("Enoxaparin 40mg", 854228, "40 mg", "once daily", "subcutaneous", "active"),
    ],
    "med_admin": [
        ("Enoxaparin 40mg", 8, "given"),
    ],
    "vitals": [
        (24, 130, 80, 85, 18, 97, 36.6, 13),
        (20, 128, 78, 82, 16, 98, 36.5, 13),
        (16, 125, 75, 80, 16, 98, 36.6, 14),
        (12, 122, 72, 78, 16, 98, 36.5, 14),
        (8,  120, 70, 75, 16, 98, 36.6, 14),
        (4,  120, 70, 72, 16, 98, 36.5, 15),
    ],
    "labs": [
        (24, {
            "718-7": (12.0, "g/dL"), "2160-0": (0.9, "mg/dL"),
        }),
    ],
    "notes": {
        "admission": (
            "81yo male. Fall at home. X-ray: fractured neck of femur. "
            "Plan: Orthopaedic consult, pre-op optimization, analgesia."
        ),
        "nursing": [
            (12, "Patient confused but comfortable with analgesia. "
                 "Awaiting theatre slot."),
        ],
        "progress": (
            "S: Confused. O: Stable. A: Pre-op hip fracture. "
            "P: Keep NPO for surgery today. Ensure consent obtained.")
    },
    "procedures": [
        ("Fascia Iliaca Block", _ago(hours=18)),
    ],
    "diagnostics": [
        ("X-ray Hip", _ago(days=1), "Displaced intracapsular fracture of the left neck of femur."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("nil-by-mouth", "active", "For surgery"),
        ("fall-risk", "high", "Hip fracture + confusion"),
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 12: Maria Santos - Chest pain / NSTEMI
# =====================================================================
P12 = {
    "name": ("Maria", "Santos"), "gender": "female", "dob": "1965-06-12",
    "ward": "General Medicine", "bed": "Bay E, Bed 19",
    "admission_days_ago": 1,
    "admitting_dx": "NSTEMI",
    "encounter_reason": "Central chest pain and sweating",
    "conditions": [
        ("I21.4", "Non-ST elevation myocardial infarction"),
        ("E11.9", "Type 2 diabetes mellitus"),
    ],
    "allergies": [],
    "medications": [
        ("Fondaparinux 2.5mg", 310410, "2.5 mg", "once daily", "subcutaneous", "active"),
        ("Ticagrelor 90mg", 1008436, "90 mg", "twice daily", "oral", "active"),
        ("Bisoprolol 2.5mg", 854916, "2.5 mg", "once daily", "oral", "active"),
    ],
    "med_admin": [
        ("Fondaparinux 2.5mg", 8, "given"),
        ("Ticagrelor 90mg", 8, "given"),
    ],
    "vitals": [
        (24, 140, 90, 95, 20, 96, 36.8, 15),
        (20, 135, 85, 90, 18, 97, 36.7, 15),
        (16, 130, 82, 85, 18, 98, 36.8, 15),
        (12, 125, 80, 80, 16, 99, 36.7, 15),
        (8,  122, 78, 75, 16, 99, 36.8, 15),
        (4,  120, 75, 70, 16, 99, 36.7, 15),
    ],
    "labs": [
        (24, {
            "30934-4": (150, "pg/mL"), "2069-3": (0.5, "ng/mL"), # Troponin high
        }),
        (8, {
            "2069-3": (1.2, "ng/mL"), # Troponin rising
        }),
    ],
    "notes": {
        "admission": (
            "58yo female. Chest pain. ECG: T-wave inversion. Troponin high. "
            "Plan: ACS protocol, cardiologist review, angio."
        ),
        "nursing": [
            (12, "Patient pain-free at rest. Cardiac monitor stable."),
        ],
        "progress": (
            "S: Pain-free. O: Troponin rising. A: NSTEMI. "
            "P: Arrange coronary angiography tomorrow. Continue dual antiplatelets.")
    },
    "procedures": [],
    "diagnostics": [
        ("ECG", _ago(days=1), "Sinus rhythm. T-wave inversion in V4-V6."),
    ],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("resuscitation", "full", "Full resuscitation"),
    ],
}


# =====================================================================
# PATIENT 13: Thomas Wright - Cellulitis, improving
# =====================================================================
P13 = {
    "name": ("Thomas", "Wright"), "gender": "male", "dob": "1975-01-20",
    "ward": "General Medicine", "bed": "Bay F, Bed 21",
    "admission_days_ago": 6,
    "admitting_dx": "Cellulitis",
    "encounter_reason": "Red, swollen, and painful left lower leg",
    "conditions": [
        ("L03.116", "Cellulitis of left lower limb"),
    ],
    "allergies": [],
    "medications": [
        ("Flucloxacillin 500mg", 310383, "500 mg", "four times daily", "oral", "active"),
    ],
    "med_admin": [
        ("Flucloxacillin 500mg", 6, "given"),
    ],
    "vitals": [
        (24, 120, 80, 70, 16, 99, 36.6, 15),
        (4,  118, 78, 68, 16, 99, 36.5, 15),
    ],
    "labs": [
        (24, {
            "6690-2": (8.5, "K/uL"), "1988-5": (15, "mg/L"), # CRP low
        }),
    ],
    "notes": {
        "admission": (
            "49yo male. Cellulitis. Plan: IV flucloxacillin, leg elevation."
        ),
        "nursing": [
            (12, "Redness receding. Patient mobilising well. Ready for home."),
        ],
        "progress": (
            "S: Feels great. O: Apyrexial. A: Resolved cellulitis. "
            "P: Discharge today on oral antibiotics.")
    },
    "procedures": [],
    "diagnostics": [],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 14: Susan Kim - Post-op Cholecystectomy
# =====================================================================
P14 = {
    "name": ("Susan", "Kim"), "gender": "female", "dob": "1980-11-30",
    "ward": "General Medicine", "bed": "Bay F, Bed 22",
    "admission_days_ago": 2,
    "admitting_dx": "Gallstone cholecystitis",
    "encounter_reason": "Right upper quadrant pain and nausea",
    "conditions": [
        ("K81.0", "Acute cholecystitis"),
    ],
    "allergies": [],
    "medications": [
        ("Co-codamol 30/500", 311053, "2 tabs", "every 6 hours", "oral", "active"),
    ],
    "med_admin": [
        ("Co-codamol 30/500", 6, "given"),
    ],
    "vitals": [
        (24, 115, 75, 75, 18, 98, 36.7, 15),
        (4,  112, 72, 72, 16, 99, 36.6, 15),
    ],
    "labs": [
        (24, {
            "1988-5": (45, "mg/L"),
        }),
    ],
    "notes": {
        "admission": (
            "43yo female. Cholecystitis. Plan: Laparoscopic cholecystectomy."
        ),
        "nursing": [
            (12, "Post-op day 1. Pain controlled. Mobilising."),
        ],
        "progress": (
            "S: Bit sore. O: Stable. A: Post-op recovery. "
            "P: Continue analgesia. Discharge tomorrow if eating well.")
    },
    "procedures": [
        ("Laparoscopic cholecystectomy", _ago(days=1)),
    ],
    "diagnostics": [],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("resuscitation", "full", "Full resuscitation"),
    ],
}

# =====================================================================
# PATIENT 15: Edward Jones - UTI + Delirium
# =====================================================================
P15 = {
    "name": ("Edward", "Jones"), "gender": "male", "dob": "1935-05-10",
    "ward": "General Medicine", "bed": "Bay F, Bed 25",
    "admission_days_ago": 3,
    "admitting_dx": "Delirium secondary to UTI",
    "encounter_reason": "Confusion and agitation reported by family",
    "conditions": [
        ("F05", "Delirium due to known physiological condition"),
        ("N39.0", "Urinary tract infection"),
    ],
    "allergies": [],
    "medications": [
        ("Gentamicin 240mg", 310461, "240 mg", "once daily", "intravenous", "active"),
        ("Digoxin 62.5mcg", 197604, "62.5 mcg", "once daily", "oral", "active"),
        ("Amiodarone 200mg", 197361, "200 mg", "once daily", "oral", "active"), # Interaction
    ],
    "med_admin": [
        ("Gentamicin 240mg", 8, "given"),
        ("Digoxin 62.5mcg", 8, "given"),
        ("Amiodarone 200mg", 8, "given"),
    ],
    "vitals": [
        (24, 120, 80, 85, 20, 96, 37.5, 13),
        (4,  115, 75, 80, 18, 97, 37.2, 13),
    ],
    "labs": [
        (24, {
            "6690-2": (13.5, "K/uL"), "2160-0": (1.1, "mg/dL"),
        }),
    ],
    "notes": {
        "admission": (
            "89yo male. Confused. UTI diagnosed. Plan: IV antibiotics, "
            "delirium screen."
        ),
        "nursing": [
            (12, "Patient pulling at lines. Reoriented frequently."),
        ],
        "progress": (
            "S: Agitated. O: Confusion continues. A: UTI/Delirium. "
            "P: Continue gentamicin. Check levels.")
    },
    "procedures": [],
    "diagnostics": [],
    "care_team": [
        ("Dr Sarah Reynolds", "Consultant", "General Medicine"),
    ],
    "flags": [
        ("fall-risk", "high", "Confusion + elderly"),
        ("resuscitation", "dnr", "Do Not Resuscitate"),
    ],
}


# Master list - will grow as more patients are added
PROFILES = [P1, P2, P3, P4, P5, P6, P7, P8, P9, P10, P11, P12, P13, P14, P15]
