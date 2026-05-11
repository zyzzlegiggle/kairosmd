"""
Multidisciplinary Ward Round Decision Support (MDS) - Scenario Bank.
Contains 20 high-fidelity clinical scenarios for General Medicine Ward 4.
Mix: ~8 with conflicts, ~5 stable/routine, ~4 improving/discharge-ready, ~3 deteriorating.
"""

from datetime import datetime, timedelta, timezone

NOW = datetime.now(timezone.utc)

def days_ago(d: int, h: int = 0) -> str:
    return (NOW - timedelta(days=d, hours=h)).isoformat()

CONSULTANTS = [
    {"id": "dr-whitfield", "name": "Dr. James Whitfield", "role": "General Medicine Consultant"},
    {"id": "dr-nair", "name": "Dr. Priya Nair", "role": "General Medicine Consultant"},
    {"id": "dr-mendez", "name": "Dr. Carlos Mendez", "role": "General Medicine Consultant"},
]

NURSES = ["Nurse Faridah", "Nurse Sarah", "Nurse Wong", "Nurse Kumar", "Nurse Thompson"]

SCENARIOS = [
    # ── 1. CAP, Day 3, DETERIORATING — Note vs Vitals conflict ──
    {
        "bed": "1",
        "patient": {"name": "Ahmad Razali", "dob": "1957-04-12", "gender": "male",
                    "condition": "Community Acquired Pneumonia", "consultant": CONSULTANTS[0], "day": 3},
        "vitals_trend": "deteriorating",
        "labs": [
            {"code": "6299-1", "name": "WBC", "value": 18.5, "unit": "10*9/L", "flag": "H"},
            {"code": "1988-5", "name": "CRP", "value": 245, "unit": "mg/L", "flag": "H"},
            {"code": "2019-8", "name": "Lactate", "value": 3.1, "unit": "mmol/L", "flag": "H"},
        ],
        "notes": {
            "clerking": "67yo male, smoker. PC: 4 days SOB, rusty sputum, fever. PMH: HTN, Mild COPD. Exam: RR 24, SpO2 92% RA. Crackles right base. Plan: IV Co-Amoxiclav + Clarithromycin.",
            "consultant": "Day 2: CRP rising 180→245. Spiking temps. Review cultures, escalate if no improvement.",
            "nursing_night": "02:30: Patient sleeping comfortably. No complaints. IV site intact. [CONFLICT: Vitals at 03:00 showed RR 30, SpO2 88%].",
        },
        "meds": [
            {"name": "Co-Amoxiclav", "code": "308461", "dosage": "1.2g IV TDS", "status": "active"},
            {"name": "Clarithromycin", "code": "21701", "dosage": "500mg IV BD", "status": "active"},
        ],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "FALLS", "detail": "Medium Risk"}, {"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # ── 2. AKI on T2DM, Day 2, STABLE — Contraindicated med conflict ──
    {
        "bed": "2",
        "patient": {"name": "Siti Norzahrah", "dob": "1968-08-22", "gender": "female",
                    "condition": "AKI on T2DM", "consultant": CONSULTANTS[1], "day": 2},
        "vitals_trend": "stable",
        "labs": [
            {"code": "2160-0", "name": "Creatinine", "value": 210, "unit": "umol/L", "flag": "H"},
            {"code": "33914-3", "name": "eGFR", "value": 24, "unit": "mL/min/1.73m2", "flag": "L"},
        ],
        "notes": {
            "clerking": "55yo female, T2DM. PC: Vomiting, dehydration. Plan: IV Fluids, hold nephrotoxics.",
            "junior": "S: Feeling better. O: BP 115/70. A: Renal function stable. [CONFLICT: Creatinine rose 165→210 overnight].",
        },
        "meds": [
            {"name": "Metformin", "code": "228471", "dosage": "1g BD PO", "status": "active"},
            {"name": "Dapagliflozin", "code": "1488564", "dosage": "10mg OD PO", "status": "on-hold"},
        ],
        "allergies": [{"code": "70618", "name": "Penicillin G", "criticality": "high"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # ── 3. Heart Failure, Day 4, IMPROVING — Lab conflict (low K+) ──
    {
        "bed": "3",
        "patient": {"name": "Rajendran Pillai", "dob": "1945-11-30", "gender": "male",
                    "condition": "Heart Failure", "consultant": CONSULTANTS[2], "day": 4},
        "vitals_trend": "improving",
        "labs": [
            {"code": "30522-7", "name": "BNP", "value": 1850, "unit": "pg/mL", "flag": "H"},
            {"code": "2823-3", "name": "Potassium", "value": 3.2, "unit": "mmol/L", "flag": "L"},
        ],
        "notes": {
            "consultant": "Day 3: Good response to IV Furosemide. 3kg weight loss. Switch to oral. Discharge tomorrow if stable.",
            "junior": "S: Breathing better. A: Stable. P: Home tomorrow. [CONFLICT: K+ 3.2, BNP still high].",
            "specialist": "Cardiology: Known HFrEF (EF 30%). Optimise GDMT once stable.",
        },
        "meds": [
            {"name": "Furosemide", "code": "4603", "dosage": "40mg OD PO", "status": "active"},
            {"name": "Spironolactone", "code": "9997", "dosage": "25mg OD PO", "status": "active"},
        ],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "high"}],
        "flags": [{"code": "FALLS", "detail": "High Risk"}],
    },

    # ── 4. COPD Exacerbation, Day 2, STABLE — No conflict ──
    {
        "bed": "4",
        "patient": {"name": "William Bennett", "dob": "1952-02-14", "gender": "male",
                    "condition": "AECOPD", "consultant": CONSULTANTS[0], "day": 2},
        "vitals_trend": "stable",
        "notes": {
            "clerking": "72yo male, severe COPD. Ex-smoker. PC: Wheeze and sputum. Plan: Controlled O2 (24% Venturi), Nebs, Steroids.",
            "nursing_night": "03:30: Patient restless. Removing O2 mask. SpO2 88% off mask.",
        },
        "meds": [
            {"name": "Salbutamol", "code": "9504", "dosage": "5mg Neb QDS", "status": "active"},
            {"name": "Hydrocortisone", "code": "5492", "dosage": "100mg IV QDS", "status": "active"},
        ],
        "allergies": [{"code": "1351", "name": "Latex", "criticality": "high"}],
        "flags": [{"code": "RESUS", "detail": "DNAR"}],
    },

    # ── 5. Sepsis (UTI), Day 1, DETERIORATING ──
    {
        "bed": "5",
        "patient": {"name": "Mei Ling", "dob": "1982-05-15", "gender": "female",
                    "condition": "Sepsis", "consultant": CONSULTANTS[1], "day": 1},
        "vitals_trend": "deteriorating",
        "labs": [
            {"code": "2019-8", "name": "Lactate", "value": 4.5, "unit": "mmol/L", "flag": "H"},
            {"code": "6299-1", "name": "WBC", "value": 22.0, "unit": "10*9/L", "flag": "H"},
        ],
        "notes": {
            "clerking": "41yo female. Rigors and flank pain. NEWS2=7 on arrival. Sepsis 6 initiated.",
            "nursing_afternoon": "16:00: Remains febrile. BP 90/50. Minimal urine output (20ml/hr).",
        },
        "meds": [
            {"name": "Gentamicin", "code": "4733", "dosage": "320mg IV OD", "status": "active"},
            {"name": "Amoxicillin", "code": "723", "dosage": "1g IV TDS", "status": "active"},
        ],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "ISOLATION", "detail": "Contact Precautions"}],
    },

    # ── 6. AF with RVR, Day 2, STABLE — Drug interaction conflict ──
    {
        "bed": "6",
        "patient": {"name": "David O'Connor", "dob": "1960-09-05", "gender": "male",
                    "condition": "AF with RVR", "consultant": CONSULTANTS[2], "day": 2},
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

    # ── 7. DKA, Day 1, STABLE — Missed symptom conflict ──
    {
        "bed": "7",
        "patient": {"name": "Norhaslinda Hassan", "dob": "2001-11-12", "gender": "female",
                    "condition": "DKA", "consultant": CONSULTANTS[0], "day": 1},
        "vitals_trend": "stable",
        "labs": [
            {"code": "2345-7", "name": "Glucose", "value": 28.5, "unit": "mmol/L", "flag": "H"},
            {"code": "1960-4", "name": "Bicarbonate", "value": 14, "unit": "mmol/L", "flag": "L"},
        ],
        "notes": {
            "clerking": "22yo, T1DM. PC: Nausea, thirst. FRII started. IV Fluids with K+.",
            "nursing_night": "05:00: Worsening abdominal pain. [CONFLICT: Not addressed in doctor note].",
        },
        "meds": [{"name": "Insulin Soluble", "code": "311028", "dosage": "0.1u/kg/hr IV", "status": "active"}],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "high"}],
        "flags": [{"code": "FALLS", "detail": "Low Risk"}],
    },

    # ── 8. GI Bleed, Day 3, DETERIORATING — Unactioned result ──
    {
        "bed": "8",
        "patient": {"name": "Rajesh Gupta", "dob": "1955-03-25", "gender": "male",
                    "condition": "Upper GI Bleed", "consultant": CONSULTANTS[1], "day": 3},
        "vitals_trend": "deteriorating",
        "labs": [
            {"code": "718-7", "name": "Hb", "value": 7.2, "unit": "g/dL", "flag": "L"},
            {"code": "6301-5", "name": "INR", "value": 4.8, "unit": "", "flag": "H"},
        ],
        "notes": {
            "consultant": "Day 2: UGIE showed gastric ulcer. Hb 8.5. Keep NBM. Hold Warfarin.",
            "nursing_morning": "08:30: Melena stools. Hb 7.2. INR 4.8. No Vitamin K given yet.",
        },
        "meds": [{"name": "Warfarin", "code": "11289", "dosage": "5mg OD PO", "status": "on-hold"}],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "high"}],
        "flags": [{"code": "NBM", "detail": "Strict NBM"}],
    },

    # ── 9. PE, Day 2, STABLE — NSAID + Anticoagulant conflict ──
    {
        "bed": "9",
        "patient": {"name": "Sarah Thompson", "dob": "1975-07-14", "gender": "female",
                    "condition": "PE", "consultant": CONSULTANTS[2], "day": 2},
        "vitals_trend": "stable",
        "notes": {
            "clerking": "CTPA confirmed bilateral PE. Started Heparin infusion.",
            "junior": "S: Sharp chest pain. P: Prescribed Ibuprofen. [CONFLICT: NSAID + Heparin = bleeding risk].",
        },
        "meds": [
            {"name": "Heparin", "code": "5224", "dosage": "Infusion", "status": "active"},
            {"name": "Ibuprofen", "code": "5640", "dosage": "400mg TDS PO", "status": "active"},
        ],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "FALLS", "detail": "Low Risk"}],
    },

    # ── 10. Hypertensive Crisis, Day 1, IMPROVING — No conflict ──
    {
        "bed": "10",
        "patient": {"name": "John Miller", "dob": "1965-12-01", "gender": "male",
                    "condition": "Hypertensive Crisis", "consultant": CONSULTANTS[0], "day": 1},
        "vitals_trend": "improving",
        "notes": {
            "clerking": "BP 220/120. Headache. Renal artery stenosis. Plan: IV Labetalol. Target SBP 160.",
            "junior": "BP 170/95. Fundoscopy: Clear. Continue slow reduction.",
        },
        "meds": [{"name": "Labetalol", "code": "6185", "dosage": "20mg IV", "status": "active"}],
        "allergies": [{"code": "70618", "name": "Penicillin", "criticality": "low"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # ── 11. Stroke, Day 4, STABLE — NBM violation conflict ──
    {
        "bed": "11",
        "patient": {"name": "Eleanor Rigby", "dob": "1940-06-18", "gender": "female",
                    "condition": "Ischaemic Stroke", "consultant": CONSULTANTS[1], "day": 4},
        "vitals_trend": "stable",
        "notes": {
            "consultant": "Day 3: Left weakness. Speech Therapy: Dysphagia. NBM, NG meds only.",
            "nursing_morning": "08:00: Given Aspirin/Clopidogrel orally with water. [CONFLICT: Violates NBM plan].",
        },
        "meds": [
            {"name": "Aspirin", "code": "1191", "dosage": "75mg OD PO", "status": "active"},
            {"name": "Clopidogrel", "code": "32968", "dosage": "75mg OD PO", "status": "active"},
        ],
        "allergies": [{"code": "6185", "name": "Labetalol", "criticality": "low"}],
        "flags": [{"code": "DIET", "detail": "Thickened Fluids Only"}],
    },

    # ── 12. Cellulitis, Day 5, IMPROVING — Allergy conflict ──
    {
        "bed": "12",
        "patient": {"name": "Chee Keong Lim", "dob": "1972-04-30", "gender": "male",
                    "condition": "Cellulitis", "consultant": CONSULTANTS[2], "day": 5},
        "vitals_trend": "improving",
        "notes": {
            "consultant": "Day 4: Redness receding. Afebrile. Step down to oral Flucloxacillin.",
            "junior": "Switched to oral. Awaiting discharge. [CONFLICT: Patient has Penicillin allergy].",
        },
        "meds": [{"name": "Flucloxacillin", "code": "4492", "dosage": "500mg QDS PO", "status": "active"}],
        "allergies": [{"code": "70618", "name": "Penicillin", "criticality": "high"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # ── 13. Pancreatitis, Day 3, STABLE — No conflict ──
    {
        "bed": "13",
        "patient": {"name": "Maria Hernandez", "dob": "1988-01-20", "gender": "female",
                    "condition": "Pancreatitis", "consultant": CONSULTANTS[0], "day": 3},
        "vitals_trend": "stable",
        "labs": [{"code": "1798-2", "name": "Amylase", "value": 450, "unit": "U/L", "flag": "H"}],
        "notes": {
            "clerking": "Severe epigastric pain. Amylase 1200. Plan: NBM, IV Fluids, Morphine.",
            "nursing_afternoon": "14:00: Pain well controlled. Tolerating sips of water.",
        },
        "meds": [{"name": "Morphine", "code": "7052", "dosage": "10mg PRN", "status": "active"}],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "NBM", "detail": "Strict NBM"}],
    },

    # ── 14. CAP (Improving), Day 6, DISCHARGE READY — No conflict ──
    {
        "bed": "14",
        "patient": {"name": "Kevin Peterson", "dob": "1995-10-10", "gender": "male",
                    "condition": "CAP (Improving)", "consultant": CONSULTANTS[1], "day": 6},
        "vitals_trend": "improving",
        "notes": {
            "consultant": "Day 5: Clinically well. SpO2 98% RA. Home today. Medically fit for discharge.",
            "junior": "Discharge script written. Mobility stable. Waiting for pharmacy.",
        },
        "meds": [{"name": "Amoxicillin", "code": "723", "dosage": "500mg TDS PO", "status": "active"}],
        "allergies": [{"code": "29633", "name": "Codeine", "criticality": "low"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # ── 15. CKD Stage 4, Day 3, STABLE — Unactioned med conflict ──
    {
        "bed": "15",
        "patient": {"name": "Samuel Jackson", "dob": "1948-02-28", "gender": "male",
                    "condition": "CKD Exacerbation", "consultant": CONSULTANTS[2], "day": 3},
        "vitals_trend": "stable",
        "labs": [
            {"code": "2823-3", "name": "Potassium", "value": 6.2, "unit": "mmol/L", "flag": "H"},
            {"code": "33914-3", "name": "eGFR", "value": 14, "unit": "mL/min/1.73m2", "flag": "L"},
        ],
        "notes": {
            "specialist": "Nephrology: Severe hyperkalaemia (6.2). Hold ACEi. Calcium Resonium started.",
            "junior": "Stable on diuretics. [CONFLICT: Still on Ramipril despite hyperkalaemia/MDT plan].",
        },
        "meds": [
            {"name": "Ramipril", "code": "35296", "dosage": "10mg OD PO", "status": "active"},
            {"name": "Calcium Resonium", "code": "203253", "dosage": "15g TDS PO", "status": "active"},
        ],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "low"}],
        "flags": [{"code": "DIET", "detail": "Low Potassium Diet"}],
    },

    # ── 16. DVT, Day 3, IMPROVING, DISCHARGE READY — No conflict ──
    {
        "bed": "16",
        "patient": {"name": "Fatimah Zahra", "dob": "1990-03-18", "gender": "female",
                    "condition": "DVT Left Leg", "consultant": CONSULTANTS[0], "day": 3},
        "vitals_trend": "improving",
        "notes": {
            "consultant": "Day 2: USS confirmed DVT. Therapeutic LMWH. Bridging to Rivaroxaban. Package of care confirmed for home.",
            "junior": "Switched to Rivaroxaban 15mg BD. Mobility stable. OPD follow-up booked.",
        },
        "meds": [{"name": "Rivaroxaban", "code": "1114195", "dosage": "15mg BD PO", "status": "active"}],
        "allergies": [],
        "flags": [],
    },

    # ── 17. Acute Asthma, Day 1, STABLE — No conflict ──
    {
        "bed": "17",
        "patient": {"name": "Liam O'Brien", "dob": "2003-07-22", "gender": "male",
                    "condition": "Acute Severe Asthma", "consultant": CONSULTANTS[1], "day": 1},
        "vitals_trend": "stable",
        "notes": {
            "clerking": "20yo male. Known asthmatic, poor compliance with inhalers. PC: Wheeze, unable to complete sentences. Peak flow 35% predicted. Plan: Back-to-back nebs, IV Hydrocortisone, Salbutamol.",
            "nursing_morning": "07:00: Peak flow improved to 60%. Speaking full sentences. O2 sats 96% on room air.",
        },
        "meds": [
            {"name": "Salbutamol", "code": "9504", "dosage": "5mg Neb QDS", "status": "active"},
            {"name": "Hydrocortisone", "code": "5492", "dosage": "100mg IV QDS", "status": "active"},
        ],
        "allergies": [{"code": "1191", "name": "Aspirin", "criticality": "high"}],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}],
    },

    # ── 18. Liver Cirrhosis + Variceal Bleed, Day 2, DETERIORATING ──
    {
        "bed": "18",
        "patient": {"name": "George Tan", "dob": "1958-11-05", "gender": "male",
                    "condition": "Variceal Bleed", "consultant": CONSULTANTS[2], "day": 2},
        "vitals_trend": "deteriorating",
        "labs": [
            {"code": "718-7", "name": "Hb", "value": 6.8, "unit": "g/dL", "flag": "L"},
            {"code": "6301-5", "name": "INR", "value": 2.1, "unit": "", "flag": "H"},
            {"code": "1742-6", "name": "ALT", "value": 120, "unit": "U/L", "flag": "H"},
        ],
        "notes": {
            "clerking": "66yo male. Known alcohol-related cirrhosis. Haematemesis x2. Resuscitated with 2u PRBC. Urgent endoscopy booked.",
            "nursing_night": "04:00: Further episode of haematemesis. Tachycardic HR 120. BP 85/50. MET call initiated.",
        },
        "meds": [
            {"name": "Terlipressin", "code": "64528", "dosage": "2mg IV Q4H", "status": "active"},
            {"name": "Omeprazole", "code": "7646", "dosage": "40mg IV BD", "status": "active"},
        ],
        "allergies": [],
        "flags": [{"code": "RESUS", "detail": "Full Resuscitation"}, {"code": "FALLS", "detail": "High Risk"}],
    },

    # ── 19. Hip Fracture (Post-Op), Day 5, IMPROVING, DISCHARGE CANDIDATE ──
    {
        "bed": "19",
        "patient": {"name": "Dorothy Chen", "dob": "1938-09-12", "gender": "female",
                    "condition": "Hip Fracture (Post-Op)", "consultant": CONSULTANTS[0], "day": 5},
        "vitals_trend": "improving",
        "notes": {
            "consultant": "Day 4: Mobilising with frame. Physio happy. Awaiting OT home assessment. Pain well controlled on regular Paracetamol.",
            "junior": "Discharge planning meeting held. Social work referral for home support.",
            "nursing_morning": "09:00: Independently toileting. Eating well. Ready for step-down or discharge.",
        },
        "meds": [
            {"name": "Paracetamol", "code": "161", "dosage": "1g QDS PO", "status": "active"},
            {"name": "Enoxaparin", "code": "67108", "dosage": "40mg SC OD", "status": "active"},
        ],
        "allergies": [{"code": "7052", "name": "Morphine", "criticality": "high"}],
        "flags": [{"code": "FALLS", "detail": "High Risk"}],
    },

    # ── 20. Alcohol Withdrawal, Day 2, STABLE — No conflict ──
    {
        "bed": "20",
        "patient": {"name": "Ryan Mitchell", "dob": "1985-04-03", "gender": "male",
                    "condition": "Alcohol Withdrawal", "consultant": CONSULTANTS[1], "day": 2},
        "vitals_trend": "stable",
        "labs": [
            {"code": "1742-6", "name": "ALT", "value": 85, "unit": "U/L", "flag": "H"},
            {"code": "2345-7", "name": "Glucose", "value": 4.2, "unit": "mmol/L", "flag": ""},
        ],
        "notes": {
            "clerking": "38yo male. Heavy alcohol use. CIWA score 18 on admission. Tremor, sweating, agitation. Plan: Chlordiazepoxide reducing regime, IV Pabrinex, monitor CIWA.",
            "nursing_morning": "08:00: CIWA score 8. Sleeping well. No seizures. Eating breakfast.",
        },
        "meds": [
            {"name": "Chlordiazepoxide", "code": "2356", "dosage": "20mg QDS PO", "status": "active"},
            {"name": "Pabrinex", "code": "43596", "dosage": "IV BD", "status": "active"},
        ],
        "allergies": [],
        "flags": [{"code": "FALLS", "detail": "Medium Risk"}],
    },
]
