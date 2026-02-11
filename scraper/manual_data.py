"""
manual_data.py - Hand-curated data for the TOP 20 most popular government schemes.

This serves as a fallback if web scraping fails, and also supplements
scraped data with high-quality, verified information for flagship schemes.

Usage:
    from scraper.manual_data import get_manual_schemes
    schemes = get_manual_schemes()
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

TODAY = datetime.now().strftime("%Y-%m-%d")


def _doc(name: str, mandatory: bool = True) -> Dict[str, Any]:
    """Shortcut for document entry."""
    return {
        "document_name": name,
        "mandatory": mandatory,
        "specifications": "",
        "notes": "",
        "validity": "",
    }


# ============================================================
# AGRICULTURE (5 schemes)
# ============================================================

PM_KISAN = {
    "scheme_id": "PM-KISAN-001",
    "scheme_name": "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)",
    "scheme_name_local": "प्रधानमंत्री किसान सम्मान निधि",
    "category": "Agriculture",
    "brief_description": "Direct income support of Rs 6,000/year to small & marginal farmers across India.",
    "detailed_description": (
        "PM-KISAN provides income support of Rs 6,000 per year to all landholding farmer families "
        "across India. The amount is paid in three equal installments of Rs 2,000 each, directly "
        "into the bank accounts of the beneficiaries through Direct Benefit Transfer (DBT). The scheme "
        "was launched on 24 February 2019 to supplement the financial needs of farmers in purchasing "
        "inputs for agriculture and allied activities. All landholding farmers' families are eligible, "
        "subject to certain exclusion criteria related to higher economic status."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "farmer",
        "state": "All India",
        "land_ownership": "Must own cultivable land",
        "other_conditions": [
            "Must be a landholding farmer family",
            "Institutional landholders are excluded",
            "Former/present ministers, MPs, MLAs, mayors are excluded",
            "Government employees drawing monthly pension >= Rs 10,000 are excluded",
            "Income tax payers in last assessment year are excluded",
            "Professionals like doctors, engineers, lawyers, CAs who are registered are excluded",
        ],
        "raw_eligibility_text": (
            "All landholding farmers families with cultivable land are eligible. Excludes institutional "
            "landholders, government employees with pension >= Rs 10,000/month, income tax payers, and "
            "professionals registered with their respective bodies."
        ),
    },
    "benefits": {
        "summary": "Rs 6,000 per year in 3 equal installments of Rs 2,000 each, directly to bank account via DBT.",
        "financial_benefit": "Rs 6,000/year",
        "benefit_type": "Direct Cash Transfer",
        "frequency": "3 installments per year (every 4 months)",
        "additional_benefits": [],
        "raw_benefits_text": "Rs 6,000 per year in 3 installments of Rs 2,000 each.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Bank Account Details (with IFSC)"),
        _doc("Land Ownership Documents / Land Records"),
        _doc("Mobile Number linked to Aadhaar"),
    ],
    "application_process": [
        "Visit the PM-KISAN portal (pmkisan.gov.in) or nearest Common Service Centre (CSC)",
        "Click on 'New Farmer Registration'",
        "Enter Aadhaar number and captcha for verification",
        "Fill the registration form with personal, bank, and land details",
        "Submit land ownership documents",
        "Application is verified by local patwari/revenue officer",
        "After verification, amount is credited directly to bank account",
    ],
    "application_deadline": "Rolling basis",
    "official_website": "https://pmkisan.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pm-kisan",
    "last_updated": TODAY,
    "data_quality_score": 95,
}

FASAL_BIMA = {
    "scheme_id": "PMFBY-001",
    "scheme_name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
    "scheme_name_local": "प्रधानमंत्री फसल बीमा योजना",
    "category": "Agriculture",
    "brief_description": "Crop insurance scheme providing financial support to farmers in case of crop loss due to natural calamities.",
    "detailed_description": (
        "PMFBY provides comprehensive crop insurance coverage against non-preventable natural risks "
        "from pre-sowing to post-harvest stage. Farmers pay a very low premium of 2% for Kharif crops, "
        "1.5% for Rabi crops, and 5% for commercial/horticultural crops. The difference between the "
        "actual premium and the farmer's share is borne equally by the Central and State governments. "
        "The scheme uses satellite imagery, remote sensing, drones, and AI to quickly assess crop damage."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "farmer",
        "state": "All India (states that have opted in)",
        "land_ownership": "Loanee and non-loanee farmers",
        "other_conditions": [
            "Sharecroppers and tenant farmers are also eligible",
            "Both loanee (crop loan) and non-loanee farmers can enroll",
            "Coverage available for notified crops in notified areas only",
        ],
        "raw_eligibility_text": "All farmers growing notified crops in notified areas are eligible, including tenant and sharecropper farmers.",
    },
    "benefits": {
        "summary": "Insurance coverage for crop loss; claim amount depends on assessed damage, up to sum insured. Farmer premium: 2% Kharif, 1.5% Rabi, 5% commercial crops.",
        "financial_benefit": "Sum Insured varies by crop and region",
        "benefit_type": "Insurance",
        "frequency": "Per crop season",
        "additional_benefits": ["Post-harvest loss coverage for up to 14 days", "Localized calamity coverage"],
        "raw_benefits_text": "Crop insurance with farmer premium of 2% for Kharif, 1.5% for Rabi, 5% for commercial. Government bears the rest.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Bank Account Details"),
        _doc("Land Records / Khasra-Khatauni"),
        _doc("Sowing Certificate from Patwari"),
        _doc("Crop Loan Certificate (for loanee farmers)", False),
    ],
    "application_process": [
        "Visit nearest bank branch, CSC, or the PMFBY portal (pmfby.gov.in)",
        "Fill the crop insurance application form",
        "Submit land records and sowing certificate",
        "Pay the farmer's share of premium",
        "Application is processed by the insurance company",
        "In case of crop loss, file a claim within 72 hours via helpline or app",
        "Claim is assessed using technology and field surveys",
        "Compensation credited to bank account",
    ],
    "application_deadline": "Before cutoff dates announced each season (typically within 2 weeks of sowing)",
    "official_website": "https://pmfby.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pmfby",
    "last_updated": TODAY,
    "data_quality_score": 95,
}

KCC = {
    "scheme_id": "KCC-001",
    "scheme_name": "Kisan Credit Card (KCC)",
    "scheme_name_local": "किसान क्रेडिट कार्ड",
    "category": "Agriculture",
    "brief_description": "Provides affordable credit to farmers for crop production, post-harvest expenses, and farm maintenance at low interest rates.",
    "detailed_description": (
        "The Kisan Credit Card scheme provides timely and adequate credit support to farmers for their "
        "agricultural operations. It offers a revolving credit facility with a credit limit based on "
        "the farmer's landholding and cropping pattern. Interest rate is subsidized at 4% per annum "
        "(with prompt repayment), compared to the normal rate of 7%. KCC also includes a personal "
        "accident insurance cover of Rs 50,000 for death and Rs 25,000 for disability. Extended to "
        "fisheries and animal husbandry farmers as well."
    ),
    "eligibility_criteria": {
        "age_range": "18-75",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "farmer",
        "state": "All India",
        "land_ownership": "Own or leased land",
        "other_conditions": [
            "Individual farmers, joint farmers, tenant farmers, sharecroppers are eligible",
            "Self Help Groups or Joint Liability Groups of farmers",
            "Fishermen and animal husbandry farmers also eligible",
        ],
        "raw_eligibility_text": "All farmers (individual/joint), tenant farmers, sharecroppers, SHGs, JLGs. Also extended to fisheries and animal husbandry.",
    },
    "benefits": {
        "summary": "Credit up to Rs 3 lakh at 4% interest (with prompt repayment); personal accident insurance of Rs 50,000.",
        "financial_benefit": "Up to Rs 3,00,000 credit limit",
        "benefit_type": "Subsidized Credit",
        "frequency": "Annual renewal",
        "additional_benefits": [
            "Interest subvention bringing effective rate to 4% p.a.",
            "Personal accident insurance: Rs 50,000 (death) / Rs 25,000 (disability)",
            "Flexible repayment after harvest",
        ],
        "raw_benefits_text": "Crop loans up to Rs 3 lakh at 7% interest rate with 3% interest subvention for prompt repayment (effective 4%).",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("PAN Card", False),
        _doc("Land Ownership / Lease Documents"),
        _doc("Passport-size Photographs"),
        _doc("Bank Account Details"),
        _doc("Crop Details / Sowing Plan"),
    ],
    "application_process": [
        "Visit the nearest bank branch (any scheduled commercial bank, cooperative bank, or RRB)",
        "Fill the KCC application form",
        "Submit land documents and identity proof",
        "Bank assesses the landholding and fixes credit limit",
        "KCC is issued (physical card or account-based)",
        "Withdraw credit as needed during the crop season",
        "Repay after harvest within the stipulated period to get interest subvention",
    ],
    "application_deadline": "Rolling basis",
    "official_website": "https://pmkisan.gov.in/KCC.aspx",
    "source_url": "https://www.myscheme.gov.in/schemes/kcc",
    "last_updated": TODAY,
    "data_quality_score": 92,
}

SOIL_HEALTH = {
    "scheme_id": "SHC-001",
    "scheme_name": "Soil Health Card Scheme",
    "scheme_name_local": "मृदा स्वास्थ्य कार्ड योजना",
    "category": "Agriculture",
    "brief_description": "Provides soil health cards to farmers with crop-wise nutrient recommendations for improved productivity.",
    "detailed_description": (
        "The Soil Health Card scheme provides farmers with a printed card for their soil that tells "
        "them the nutrients available and the nutrients needed. It also recommends the dosage of "
        "fertilizers and organic amendments. Soil samples are collected and tested in labs. Cards "
        "are issued every 2 years. This helps farmers make informed decisions about nutrient usage, "
        "reducing input costs and improving yields."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "farmer",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": ["Any farmer with cultivable land can apply"],
        "raw_eligibility_text": "All farmers across India with cultivable land are eligible.",
    },
    "benefits": {
        "summary": "Free soil testing and personalized Soil Health Card with nutrient status and crop-wise fertilizer recommendations.",
        "financial_benefit": "Free service",
        "benefit_type": "Technical Assistance",
        "frequency": "Every 2 years",
        "additional_benefits": ["Better crop yields through optimized fertilizer use", "Reduced input costs"],
        "raw_benefits_text": "Free soil health card with testing and recommendations every 2 years.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Land Records / Khasra Number"),
    ],
    "application_process": [
        "Contact local agriculture department or Krishi Vigyan Kendra",
        "Soil sample is collected from the farm",
        "Sample is analyzed in soil testing laboratory",
        "Soil Health Card is generated with nutrient analysis",
        "Card is distributed to farmer with personalized recommendations",
        "Farmer can also check card status on soilhealth.dac.gov.in",
    ],
    "application_deadline": "Rolling basis",
    "official_website": "https://soilhealth.dac.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/shc",
    "last_updated": TODAY,
    "data_quality_score": 85,
}

E_NAM = {
    "scheme_id": "ENAM-001",
    "scheme_name": "National Agriculture Market (e-NAM)",
    "scheme_name_local": "राष्ट्रीय कृषि बाजार (ई-नाम)",
    "category": "Agriculture",
    "brief_description": "Online trading portal connecting APMC mandis for transparent price discovery and better prices for farmers.",
    "detailed_description": (
        "e-NAM is a pan-India electronic trading portal linking existing APMC mandis across India. "
        "It promotes transparency in price discovery, enables farmers to get better prices for their "
        "produce, reduces intermediaries, and provides real-time price information. Farmers can sell "
        "their produce at any e-NAM mandi, not just the nearest one, increasing competition and "
        "reducing exploitation by middlemen."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "farmer",
        "state": "All India (participating states)",
        "land_ownership": "any",
        "other_conditions": [
            "Farmer must register on the e-NAM portal",
            "Applicable for commodities listed on e-NAM",
        ],
        "raw_eligibility_text": "Any farmer, FPO, or trader can register on the e-NAM portal.",
    },
    "benefits": {
        "summary": "Better price realization through transparent bidding, reduced intermediaries, online payment, and access to pan-India market.",
        "financial_benefit": "Better market price for produce",
        "benefit_type": "Market Access",
        "frequency": "Ongoing",
        "additional_benefits": ["Real-time price information", "Direct payment to bank account", "Quality testing at mandi"],
        "raw_benefits_text": "Better price realization, transparent bidding, online payment directly to farmer's bank account.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Bank Account Details"),
        _doc("Mobile Number"),
        _doc("Land Records", False),
    ],
    "application_process": [
        "Visit enam.gov.in or download the e-NAM mobile app",
        "Register as a farmer using Aadhaar and bank details",
        "Take produce to the nearest e-NAM linked mandi",
        "Produce is quality tested and listed for bidding",
        "Traders bid online for the produce",
        "Farmer accepts the best bid",
        "Payment is transferred directly to bank account",
    ],
    "application_deadline": "Rolling basis",
    "official_website": "https://enam.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/enam",
    "last_updated": TODAY,
    "data_quality_score": 85,
}


# ============================================================
# EDUCATION (5 schemes)
# ============================================================

SC_SCHOLARSHIP = {
    "scheme_id": "PMSC-001",
    "scheme_name": "Post Matric Scholarship for SC Students",
    "scheme_name_local": "अनुसूचित जाति के छात्रों के लिए पोस्ट मैट्रिक छात्रवृत्ति",
    "category": "Education",
    "brief_description": "Scholarship for SC students studying in post-matriculation classes to cover fees and maintenance costs.",
    "detailed_description": (
        "The Post Matric Scholarship for Scheduled Caste Students is a centrally sponsored scheme "
        "that provides financial assistance to SC students studying at post-matriculation or post-secondary "
        "level (Class 11 onwards, including professional courses). It covers tuition fees, living expenses, "
        "book allowance, and other academic costs. The scheme aims to support education among SC "
        "communities and improve their socio-economic status."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "SC",
        "income_limit": "< Rs 2.5 lakhs per annum (family income)",
        "occupation": "student",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must be a Scheduled Caste student",
            "Must be studying post-matric course (Class 11 and above)",
            "Family annual income should not exceed Rs 2,50,000",
            "Must have passed the previous qualifying examination",
        ],
        "raw_eligibility_text": "SC students studying in Class 11 and above with family income below Rs 2.5 lakh per annum.",
    },
    "benefits": {
        "summary": "Full tuition fees, maintenance allowance (Rs 380-1200/month depending on course and day scholar/hosteller), book allowance, and thesis typing/printing charges.",
        "financial_benefit": "Varies by course (Rs 380-1200/month maintenance + full fees)",
        "benefit_type": "Scholarship",
        "frequency": "Annual (per academic year)",
        "additional_benefits": ["Tuition fee reimbursement", "Study tour charges", "Book allowance"],
        "raw_benefits_text": "Maintenance allowance, full tuition fees, book allowance, study tour charges.",
    },
    "required_documents": [
        _doc("Caste Certificate (SC)"),
        _doc("Income Certificate"),
        _doc("Previous Year Marksheet"),
        _doc("Admission Letter / Fee Receipt"),
        _doc("Aadhaar Card"),
        _doc("Bank Account Details"),
        _doc("Passport-size Photographs"),
    ],
    "application_process": [
        "Visit the National Scholarship Portal (scholarships.gov.in)",
        "Register with mobile number and email",
        "Log in and select 'Post Matric Scholarship for SC Students'",
        "Fill academic, personal, and bank details",
        "Upload required documents (caste cert, income cert, marksheets)",
        "Submit the application before deadline",
        "Application is verified by institute and state nodal officer",
        "Scholarship amount credited to bank account",
    ],
    "application_deadline": "Usually October-November each year (check NSP for exact dates)",
    "official_website": "https://scholarships.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pmssc",
    "last_updated": TODAY,
    "data_quality_score": 93,
}

OBC_SCHOLARSHIP = {
    "scheme_id": "PMOBC-001",
    "scheme_name": "Post Matric Scholarship for OBC Students",
    "scheme_name_local": "अन्य पिछड़ा वर्ग के छात्रों के लिए पोस्ट मैट्रिक छात्रवृत्ति",
    "category": "Education",
    "brief_description": "Financial assistance for OBC students pursuing post-matric education to meet educational expenses.",
    "detailed_description": (
        "This centrally sponsored scheme provides financial assistance to OBC students studying at "
        "post-matriculation level. It covers maintenance allowance and non-refundable fees. The scheme "
        "is implemented by state governments and UTs. Students from Other Backward Classes whose family "
        "income is within the prescribed limit are eligible for this scholarship."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "OBC",
        "income_limit": "< Rs 1.5 lakhs per annum (family income)",
        "occupation": "student",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must belong to OBC (non-creamy layer)",
            "Must be pursuing post-matric course",
            "Family income should not exceed Rs 1,50,000 per annum",
        ],
        "raw_eligibility_text": "OBC students (non-creamy layer) in post-matric courses with family income below Rs 1.5 lakh.",
    },
    "benefits": {
        "summary": "Maintenance allowance (Rs 260-1200/month) and reimbursement of non-refundable compulsory fees.",
        "financial_benefit": "Rs 260-1200/month + fee reimbursement",
        "benefit_type": "Scholarship",
        "frequency": "Annual",
        "additional_benefits": ["Fee reimbursement", "Reader charges for blind students"],
        "raw_benefits_text": "Maintenance allowance and compulsory non-refundable fees reimbursement.",
    },
    "required_documents": [
        _doc("OBC Certificate (non-creamy layer)"),
        _doc("Income Certificate"),
        _doc("Marksheet of qualifying exam"),
        _doc("Admission Letter / Bonafide Certificate"),
        _doc("Aadhaar Card"),
        _doc("Bank Account Details"),
    ],
    "application_process": [
        "Visit the National Scholarship Portal (scholarships.gov.in)",
        "Register as new student or login",
        "Select 'Post Matric Scholarship for OBC Students'",
        "Fill the application form with personal, academic, and financial details",
        "Upload OBC certificate, income certificate, and marksheet",
        "Submit before the deadline",
        "Verified by institute and state department",
        "Scholarship credited to bank account",
    ],
    "application_deadline": "Usually October-November (check NSP each year)",
    "official_website": "https://scholarships.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pmsobc",
    "last_updated": TODAY,
    "data_quality_score": 90,
}

NSP_SCHEMES = {
    "scheme_id": "NSP-001",
    "scheme_name": "National Scholarship Portal (NSP) - Central Sector Scheme of Scholarships",
    "scheme_name_local": "राष्ट्रीय छात्रवृत्ति पोर्टल",
    "category": "Education",
    "brief_description": "One-stop portal for multiple central and state government scholarships for meritorious students.",
    "detailed_description": (
        "The National Scholarship Portal is a one-stop solution for students to apply for various "
        "government scholarships. The Central Sector Scheme of Scholarships provides financial assistance "
        "to meritorious students from economically weaker sections. Students who score above 80th "
        "percentile in their Class 12 exam and pursue regular college courses are eligible. The "
        "portal hosts scholarships from multiple ministries including MoMA, MoSJE, MoTA, MoHRD."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "< Rs 8 lakhs per annum (family income for Central Sector Scheme)",
        "occupation": "student",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must score above 80th percentile in Class 12 board exam",
            "Must be pursuing regular courses (not distance education)",
            "Should not be receiving any other scholarship",
        ],
        "raw_eligibility_text": "Students above 80th percentile in Class 12 with family income below Rs 8 lakh for Central Sector Scheme.",
    },
    "benefits": {
        "summary": "Rs 10,000/year for graduation (first 3 years), Rs 20,000/year for post-graduation. Additional Rs 2,000/year for college/university fees for professional courses.",
        "financial_benefit": "Rs 10,000-20,000 per year",
        "benefit_type": "Scholarship",
        "frequency": "Annual",
        "additional_benefits": ["Merit-based selection", "Available for UG and PG"],
        "raw_benefits_text": "Rs 10,000/year for UG, Rs 20,000/year for PG. Additional amounts for professional courses.",
    },
    "required_documents": [
        _doc("Class 12 Marksheet"),
        _doc("Aadhaar Card"),
        _doc("Income Certificate"),
        _doc("Bank Account Details"),
        _doc("College Admission Proof"),
        _doc("Caste Certificate (if applicable)", False),
    ],
    "application_process": [
        "Visit scholarships.gov.in",
        "Register with academic credentials",
        "Browse and select the appropriate scholarship",
        "Fill the application form",
        "Upload required documents",
        "Submit before deadline",
        "Track application status on the portal",
    ],
    "application_deadline": "September-November each year (varies by scholarship)",
    "official_website": "https://scholarships.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/nsp",
    "last_updated": TODAY,
    "data_quality_score": 88,
}

PM_SCHOLARSHIP = {
    "scheme_id": "PMSS-001",
    "scheme_name": "Prime Minister's Scholarship Scheme (PMSS)",
    "scheme_name_local": "प्रधानमंत्री छात्रवृत्ति योजना",
    "category": "Education",
    "brief_description": "Scholarships for dependents of ex-servicemen/ex-Coast Guard personnel for professional degree courses.",
    "detailed_description": (
        "The PM's Scholarship Scheme (PMSS) under the National Defence Fund provides scholarships to "
        "the wards and widows of ex-servicemen, ex-Coast Guard personnel, and deceased/disabled "
        "servicemen for pursuing professional degree courses like MBBS, BDS, Engineering, MBA, MCA, etc. "
        "Boys get Rs 2,500/month and girls get Rs 3,000/month for the duration of the course."
    ),
    "eligibility_criteria": {
        "age_range": "18-25",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "student",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must be a ward/widow of ex-serviceman/ex-Coast Guard/deceased/disabled soldier",
            "Must be pursuing first professional degree course",
            "Minimum 60% marks in qualifying examination",
            "Should not be employed",
        ],
        "raw_eligibility_text": "Wards and widows of defence personnel pursuing first professional degree with min 60% marks.",
    },
    "benefits": {
        "summary": "Rs 2,500/month for boys and Rs 3,000/month for girls for the full duration of professional course.",
        "financial_benefit": "Rs 2,500-3,000 per month",
        "benefit_type": "Scholarship",
        "frequency": "Monthly (for course duration)",
        "additional_benefits": [],
        "raw_benefits_text": "Rs 2,500/month for boys, Rs 3,000/month for girls for the entire course duration.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Ex-Serviceman / Service Certificate"),
        _doc("PPO (Pension Payment Order) / Discharge Certificate"),
        _doc("Marksheet of qualifying exam"),
        _doc("Bank Account Details"),
        _doc("College Admission Letter"),
    ],
    "application_process": [
        "Visit the Kendriya Sainik Board website (ksb.gov.in)",
        "Register and fill the PMSS application form online",
        "Upload relevant service certificates and academic documents",
        "Submit the application before the deadline",
        "Application verified by Zila Sainik Board",
        "Scholarship disbursed on completion of each semester",
    ],
    "application_deadline": "October-November each year",
    "official_website": "https://ksb.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pmss",
    "last_updated": TODAY,
    "data_quality_score": 88,
}

BEGUM_HAZRAT = {
    "scheme_id": "BHMNS-001",
    "scheme_name": "Begum Hazrat Mahal National Scholarship (for Minority Girls)",
    "scheme_name_local": "बेगम हजरत महल राष्ट्रीय छात्रवृत्ति",
    "category": "Education",
    "brief_description": "Scholarship for meritorious girls belonging to minority communities studying in Classes 9-12.",
    "detailed_description": (
        "The Begum Hazrat Mahal National Scholarship is for meritorious girls from notified minority "
        "communities (Muslim, Christian, Sikh, Buddhist, Jain, Parsi) who are studying in Classes 9-12. "
        "Managed by Maulana Azad Education Foundation (MAEF), it provides Rs 5,000 for Class 9-10 "
        "and Rs 6,000 for Class 11-12 to cover books and school supplies."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "female",
        "caste_category": "Minority (Muslim, Christian, Sikh, Buddhist, Jain, Parsi)",
        "income_limit": "< Rs 2 lakhs per annum",
        "occupation": "student",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Girl student of minority community",
            "Studying in Class 9, 10, 11, or 12",
            "Must have scored at least 50% in previous class",
            "Family income below Rs 2 lakh per annum",
        ],
        "raw_eligibility_text": "Minority community girl students in Class 9-12 with min 50% marks and family income below Rs 2 lakh.",
    },
    "benefits": {
        "summary": "Rs 5,000 for Class 9-10 and Rs 6,000 for Class 11-12 per annum.",
        "financial_benefit": "Rs 5,000-6,000 per year",
        "benefit_type": "Scholarship",
        "frequency": "Annual",
        "additional_benefits": [],
        "raw_benefits_text": "Rs 5,000 for Classes 9-10 and Rs 6,000 for Classes 11-12 annually.",
    },
    "required_documents": [
        _doc("Self-declaration of minority community"),
        _doc("Income Certificate"),
        _doc("Previous Year Marksheet"),
        _doc("School Bonafide / Admission Certificate"),
        _doc("Aadhaar Card"),
        _doc("Bank Account / Passbook (student's own)"),
    ],
    "application_process": [
        "Visit the MAEF Scholarship portal or National Scholarship Portal",
        "Register and select the Begum Hazrat Mahal Scholarship",
        "Fill personal, academic, and bank details",
        "Upload minority declaration, income certificate, marksheet",
        "Submit the application before the deadline",
        "School verifies the application",
        "Amount credited to student's bank account",
    ],
    "application_deadline": "September-October each year",
    "official_website": "https://www.maef.nic.in",
    "source_url": "https://www.myscheme.gov.in/schemes/bhmns",
    "last_updated": TODAY,
    "data_quality_score": 88,
}

# ============================================================
# HEALTHCARE (3 schemes)
# ============================================================

AYUSHMAN = {
    "scheme_id": "PMJAY-001",
    "scheme_name": "Ayushman Bharat - Pradhan Mantri Jan Arogya Yojana (PM-JAY)",
    "scheme_name_local": "आयुष्मान भारत - प्रधानमंत्री जन आरोग्य योजना",
    "category": "Healthcare",
    "brief_description": "Free health insurance cover of Rs 5 lakh per family per year for secondary and tertiary hospitalization.",
    "detailed_description": (
        "PM-JAY is the world's largest government-funded health insurance scheme, providing coverage "
        "of Rs 5 lakh per family per year for secondary and tertiary care hospitalization. It covers "
        "over 12 crore poor and vulnerable families (approximately 55 crore beneficiaries) based on "
        "SECC 2011 deprivation criteria. The scheme covers pre-hospitalization (3 days), hospitalization, "
        "and post-hospitalization (15 days) expenses. Over 1,900 treatment packages are covered including "
        "surgeries, medical treatments, and day care procedures."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "BPL / SECC 2011 listed families",
        "occupation": "any",
        "state": "All India (33 states/UTs have implemented)",
        "land_ownership": "any",
        "other_conditions": [
            "Family must be listed in SECC 2011 database",
            "No cap on family size or age of members",
            "Covers pre-existing conditions from day one",
            "No enrollment fee or premium for beneficiaries",
        ],
        "raw_eligibility_text": "Families identified through SECC 2011 deprivation criteria. No enrollment fee. Covers entire family.",
    },
    "benefits": {
        "summary": "Rs 5 lakh health cover per family per year; cashless treatment at 28,000+ empanelled hospitals; 1,900+ treatment packages covered.",
        "financial_benefit": "Rs 5,00,000 per family per year",
        "benefit_type": "Health Insurance",
        "frequency": "Annual (renewable)",
        "additional_benefits": [
            "Cashless and paperless at point of service",
            "Pre and post hospitalization expenses covered",
            "No restriction on family size",
            "All pre-existing diseases covered",
        ],
        "raw_benefits_text": "Rs 5 lakh per family per year for hospitalization at empanelled hospitals. Cashless treatment.",
    },
    "required_documents": [
        _doc("Aadhaar Card / Ration Card / Any government ID"),
        _doc("SECC Family ID or Ration Card"),
        _doc("Mobile Number"),
    ],
    "application_process": [
        "Check eligibility on mera.pmjay.gov.in using mobile number or ration card",
        "If eligible, visit nearest Ayushman Bharat Arogya Mitra at empanelled hospital or CSC",
        "Verify identity using Aadhaar",
        "E-card is generated instantly",
        "Visit any empanelled hospital for cashless treatment",
        "Show e-card or Aadhaar at the hospital",
        "All treatment costs up to Rs 5 lakh are covered",
    ],
    "application_deadline": "Rolling basis (no enrollment deadline)",
    "official_website": "https://pmjay.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/ab-pmjay",
    "last_updated": TODAY,
    "data_quality_score": 96,
}

PMMVY = {
    "scheme_id": "PMMVY-001",
    "scheme_name": "Pradhan Mantri Matru Vandana Yojana (PMMVY)",
    "scheme_name_local": "प्रधानमंत्री मातृ वंदना योजना",
    "category": "Healthcare",
    "brief_description": "Cash incentive of Rs 5,000 to pregnant and lactating women for first live birth to improve health and nutrition.",
    "detailed_description": (
        "PMMVY provides a cash incentive of Rs 5,000 in three installments to pregnant women and "
        "lactating mothers for the first live birth. An additional Rs 1,000 is provided through "
        "Janani Suraksha Yojana if the delivery is institutional. The scheme aims to provide partial "
        "compensation for wage loss, enable better rest during pregnancy, and improve health-seeking "
        "behavior. From 2024 onwards, extended to second child if the child is a girl."
    ),
    "eligibility_criteria": {
        "age_range": "19+",
        "gender": "female",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "any",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Pregnant and lactating women for first live birth",
            "From 2024: also for second child if it is a girl",
            "Must register pregnancy at Anganwadi Centre or health facility",
            "Not applicable to government/PSU employees",
        ],
        "raw_eligibility_text": "All pregnant women for first live birth (extended to second child if girl). Not for government employees.",
    },
    "benefits": {
        "summary": "Rs 5,000 in 3 installments: Rs 1,000 (on pregnancy registration), Rs 2,000 (after 6 months), Rs 2,000 (after birth registration + first vaccination).",
        "financial_benefit": "Rs 5,000",
        "benefit_type": "Direct Cash Transfer",
        "frequency": "One-time (per eligible birth)",
        "additional_benefits": ["Additional Rs 1,000 under JSY for institutional delivery"],
        "raw_benefits_text": "Rs 5,000 in 3 installments. Plus Rs 1,000 under JSY for institutional delivery.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Bank / Post Office Account Passbook"),
        _doc("MCP Card (Mother and Child Protection Card)"),
        _doc("Pregnancy Registration Proof"),
        _doc("Child Birth Certificate (for last installment)"),
    ],
    "application_process": [
        "Register pregnancy at nearest Anganwadi Centre (AWC) or health facility",
        "Fill Form 1-A for first installment (within 150 days of LMP)",
        "Fill Form 1-B for second installment (after at least 6 months of pregnancy)",
        "Fill Form 1-C for third installment (after child birth registration and first vaccination)",
        "Submit forms along with MCP card and Aadhaar at AWC",
        "Amount is transferred directly to bank/post office account",
    ],
    "application_deadline": "Within the stipulated time after each milestone",
    "official_website": "https://pmmvy.wcd.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pmmvy",
    "last_updated": TODAY,
    "data_quality_score": 92,
}

JSY = {
    "scheme_id": "JSY-001",
    "scheme_name": "Janani Suraksha Yojana (JSY)",
    "scheme_name_local": "जननी सुरक्षा योजना",
    "category": "Healthcare",
    "brief_description": "Cash assistance to pregnant women for institutional delivery to reduce maternal and neo-natal mortality.",
    "detailed_description": (
        "Janani Suraksha Yojana (JSY) is a safe motherhood intervention under the National Health Mission. "
        "It provides cash assistance to BPL pregnant women for institutional delivery at government "
        "or accredited private health facilities. In rural areas of Low Performing States (LPS), "
        "mothers receive Rs 1,400 and ASHAs receive Rs 600. In urban areas of LPS, mothers receive Rs 1,000. "
        "The scheme is linked with Ayushman Bharat and operates across all states with higher benefits "
        "for Low Performing States."
    ),
    "eligibility_criteria": {
        "age_range": "19+",
        "gender": "female",
        "caste_category": "SC/ST/BPL preferred; all in LPS states",
        "income_limit": "BPL (in High Performing States)",
        "occupation": "any",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "All pregnant women in Low Performing States (LPS) are eligible regardless of age/parity",
            "In High Performing States (HPS): BPL women aged 19+ for first 2 live births",
            "Must deliver at government or accredited private institution",
        ],
        "raw_eligibility_text": "All women in LPS states; BPL women (19+, up to 2 births) in HPS states. Must be institutional delivery.",
    },
    "benefits": {
        "summary": "Cash assistance: Rs 1,400 (rural LPS), Rs 1,000 (urban LPS), Rs 700 (rural HPS), Rs 600 (urban HPS). ASHA also gets incentive.",
        "financial_benefit": "Rs 600-1,400",
        "benefit_type": "Direct Cash Transfer",
        "frequency": "Per delivery",
        "additional_benefits": ["ASHA receives Rs 600 per beneficiary in LPS states", "Free ambulance transport in many states"],
        "raw_benefits_text": "Cash assistance of Rs 600 to Rs 1,400 depending on state and rural/urban area.",
    },
    "required_documents": [
        _doc("BPL Card / Income Certificate (for HPS states)"),
        _doc("Aadhaar Card"),
        _doc("JSY Card / MCH Card"),
        _doc("Bank Account Details"),
        _doc("Referral Slip from ASHA", False),
    ],
    "application_process": [
        "Register with ASHA worker or at the nearest government health facility",
        "Receive JSY card / MCH card",
        "Attend at least 3 ante-natal check-ups",
        "Deliver at a government or accredited private health facility",
        "Cash is disbursed at the time of delivery or within a few days",
        "ASHA worker facilitates the process",
    ],
    "application_deadline": "Rolling basis",
    "official_website": "https://nhm.gov.in/index1.php?lang=1&level=3&sublinkid=841&lid=309",
    "source_url": "https://www.myscheme.gov.in/schemes/jsy",
    "last_updated": TODAY,
    "data_quality_score": 90,
}

# ============================================================
# SENIOR CITIZENS (3 schemes)
# ============================================================

IGNOAPS = {
    "scheme_id": "IGNOAPS-001",
    "scheme_name": "Indira Gandhi National Old Age Pension Scheme (IGNOAPS)",
    "scheme_name_local": "इंदिरा गांधी राष्ट्रीय वृद्धावस्था पेंशन योजना",
    "category": "Senior Citizens",
    "brief_description": "Monthly pension of Rs 200-500 for BPL citizens aged 60+ under the National Social Assistance Programme.",
    "detailed_description": (
        "IGNOAPS provides monthly pension to BPL persons aged 60 years and above. The Central "
        "Government contributes Rs 200/month for beneficiaries aged 60-79 and Rs 500/month for those "
        "aged 80+. Most state governments add a top-up, so actual pension ranges from Rs 400-2000 "
        "depending on the state. The scheme is part of the National Social Assistance Programme (NSAP) "
        "and is one of the most widely availed pension schemes in India."
    ),
    "eligibility_criteria": {
        "age_range": "60+",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "BPL (Below Poverty Line)",
        "occupation": "any",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must be aged 60 years or above",
            "Must be a BPL card holder",
            "Must be a citizen of India",
        ],
        "raw_eligibility_text": "Indian citizens aged 60+ who are BPL card holders.",
    },
    "benefits": {
        "summary": "Central share: Rs 200/month (age 60-79), Rs 500/month (age 80+). State governments add additional amounts.",
        "financial_benefit": "Rs 200-500/month (Central) + State top-up",
        "benefit_type": "Pension",
        "frequency": "Monthly",
        "additional_benefits": ["State top-up varies (Rs 200-1500 additional)"],
        "raw_benefits_text": "Rs 200/month for 60-79 age, Rs 500/month for 80+. States add their own contribution.",
    },
    "required_documents": [
        _doc("Age Proof (Aadhaar / Voter ID / Birth Certificate)"),
        _doc("BPL Card / Certificate"),
        _doc("Bank Account / Post Office Account Details"),
        _doc("Passport-size Photographs"),
        _doc("Aadhaar Card"),
    ],
    "application_process": [
        "Visit the nearest Gram Panchayat (rural) or Urban Local Body (urban) office",
        "Collect and fill the IGNOAPS application form",
        "Attach age proof, BPL certificate, and bank details",
        "Submit the form at the Panchayat/ULB office",
        "Application is verified by Block/District authorities",
        "Upon approval, pension is credited monthly to bank/post office account",
    ],
    "application_deadline": "Rolling basis",
    "official_website": "https://nsap.nic.in",
    "source_url": "https://www.myscheme.gov.in/schemes/ignoaps",
    "last_updated": TODAY,
    "data_quality_score": 90,
}

APY = {
    "scheme_id": "APY-001",
    "scheme_name": "Atal Pension Yojana (APY)",
    "scheme_name_local": "अटल पेंशन योजना",
    "category": "Senior Citizens",
    "brief_description": "Guaranteed pension of Rs 1,000-5,000/month after age 60 for unorganized sector workers with government co-contribution.",
    "detailed_description": (
        "Atal Pension Yojana is a government-backed pension scheme for workers in the unorganized "
        "sector. It guarantees a minimum pension of Rs 1,000 to Rs 5,000 per month after the age "
        "of 60, depending on the contribution amount and age of joining. The government co-contributed "
        "50% of the premium or Rs 1,000/year (whichever is lower) for 5 years for those who joined "
        "before 31 March 2016 and were not income tax payers. The pension is guaranteed by the government."
    ),
    "eligibility_criteria": {
        "age_range": "18-40",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "Primarily for unorganized sector workers",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must be aged 18-40 at the time of joining",
            "Must have a savings bank account",
            "Must have Aadhaar and mobile number linked to bank",
            "Not a member of any statutory social security scheme",
            "Not an income tax payer (for government co-contribution)",
        ],
        "raw_eligibility_text": "Indian citizens aged 18-40 with a bank account. Primarily for unorganized sector, but open to all.",
    },
    "benefits": {
        "summary": "Guaranteed monthly pension of Rs 1,000-5,000 after age 60; spouse gets same pension after subscriber's death; nominees get lump sum.",
        "financial_benefit": "Rs 1,000-5,000/month after age 60",
        "benefit_type": "Pension",
        "frequency": "Monthly (after age 60)",
        "additional_benefits": [
            "Spouse continues to receive same pension after death",
            "Nominee receives lump sum accumulated corpus",
            "Government guarantee on pension amount",
        ],
        "raw_benefits_text": "Monthly pension of Rs 1,000 to 5,000 after 60, based on contribution. Spouse pension and nominee lump sum.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Bank Account / Savings Account"),
        _doc("Mobile Number linked to bank"),
    ],
    "application_process": [
        "Visit any bank branch where you have a savings account",
        "Fill the APY registration form",
        "Choose pension amount (Rs 1,000/2,000/3,000/4,000/5,000)",
        "Contribution is auto-debited from bank account monthly/quarterly/half-yearly",
        "Can also register through net banking of supported banks",
        "Pension starts at age 60 automatically",
    ],
    "application_deadline": "Rolling basis (join anytime between age 18-40)",
    "official_website": "https://www.npscra.nsdl.co.in/scheme-details.php",
    "source_url": "https://www.myscheme.gov.in/schemes/apy",
    "last_updated": TODAY,
    "data_quality_score": 93,
}

PMVVY = {
    "scheme_id": "PMVVY-001",
    "scheme_name": "Pradhan Mantri Vaya Vandana Yojana (PMVVY)",
    "scheme_name_local": "प्रधानमंत्री वय वंदना योजना",
    "category": "Senior Citizens",
    "brief_description": "Guaranteed 7.4% annual return pension plan for senior citizens (60+) through LIC, with investment up to Rs 15 lakh.",
    "detailed_description": (
        "PMVVY is a pension scheme for senior citizens aged 60+ that provides an assured return of "
        "7.4% per annum (for FY 2023-24 onwards, subject to revision) for 10 years. It is sold exclusively "
        "through LIC. The maximum investment limit is Rs 15 lakh per senior citizen. Pension can be "
        "received monthly, quarterly, half-yearly, or annually. After 10 years, the purchase price "
        "is returned along with the final pension installment."
    ),
    "eligibility_criteria": {
        "age_range": "60+",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "any",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must be aged 60 years or above",
            "Maximum investment of Rs 15 lakh per senior citizen",
            "Policy term is 10 years",
        ],
        "raw_eligibility_text": "Indian senior citizens aged 60 and above. Maximum investment Rs 15 lakh.",
    },
    "benefits": {
        "summary": "Guaranteed pension at 7.4% p.a. for 10 years on investment up to Rs 15 lakh. Monthly pension of Rs 1,000-9,250.",
        "financial_benefit": "Rs 1,000-9,250/month (based on investment)",
        "benefit_type": "Pension / Investment",
        "frequency": "Monthly/Quarterly/Half-yearly/Annually (choice)",
        "additional_benefits": [
            "Loan facility up to 75% of purchase price after 3 years",
            "Full purchase price returned after 10 years",
            "Premature exit allowed for critical illness with 98% refund",
        ],
        "raw_benefits_text": "Assured return of 7.4% for 10 years. Pension monthly/quarterly/half-yearly/annually. Loan facility after 3 years.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("PAN Card"),
        _doc("Age Proof"),
        _doc("Bank Account Details"),
        _doc("Passport-size Photographs"),
    ],
    "application_process": [
        "Visit the nearest LIC branch or LIC website (licindia.in)",
        "Fill the PMVVY proposal form",
        "Submit age proof and identity documents",
        "Pay the purchase price (lump sum) by cheque/NEFT",
        "Policy is issued by LIC",
        "Pension starts from the chosen frequency",
    ],
    "application_deadline": "Subject to scheme extension by government (check LIC website)",
    "official_website": "https://licindia.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pmvvy",
    "last_updated": TODAY,
    "data_quality_score": 88,
}

# ============================================================
# WOMEN & CHILDREN (2 schemes)
# ============================================================

SSY = {
    "scheme_id": "SSY-001",
    "scheme_name": "Sukanya Samriddhi Yojana (SSY)",
    "scheme_name_local": "सुकन्या समृद्धि योजना",
    "category": "Women & Children",
    "brief_description": "Government savings scheme for girl child with 8%+ interest rate and tax benefits under Section 80C.",
    "detailed_description": (
        "Sukanya Samriddhi Yojana is a small savings scheme for the girl child, launched under the "
        "Beti Bachao Beti Padhao campaign. Parents/guardians can open an account for a girl child "
        "below 10 years. Minimum deposit is Rs 250/year (max Rs 1.5 lakh/year). The current interest "
        "rate is approximately 8.2% p.a. (revised quarterly). The account matures after 21 years from "
        "opening or on marriage of the girl after age 18. Partial withdrawal (50%) is allowed after "
        "the girl turns 18 for higher education."
    ),
    "eligibility_criteria": {
        "age_range": "<10 (girl child)",
        "gender": "female",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "any",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Girl child must be below 10 years of age at the time of opening",
            "Maximum 2 accounts (one for each girl child in the family)",
            "Exception: 3 accounts if twins/triplets in second birth",
        ],
        "raw_eligibility_text": "Girl child below 10 years. Parents/guardians open and operate the account. Max 2 per family.",
    },
    "benefits": {
        "summary": "High interest rate (~8.2% p.a., tax-free); deposits qualify for 80C deduction; maturity after 21 years; partial withdrawal for education at 18.",
        "financial_benefit": "~8.2% p.a. interest (tax-free maturity)",
        "benefit_type": "Savings Scheme",
        "frequency": "Annual deposits for 15 years, maturity at 21 years",
        "additional_benefits": [
            "Tax deduction under Section 80C on deposits",
            "Interest earned is tax-free",
            "Maturity amount is tax-free",
            "Partial withdrawal (50%) at age 18 for education",
        ],
        "raw_benefits_text": "~8.2% interest, EEE tax status (deposit, interest, maturity all tax-free). Partial withdrawal for education.",
    },
    "required_documents": [
        _doc("Birth Certificate of girl child"),
        _doc("Aadhaar Card / ID of parent/guardian"),
        _doc("Address Proof of parent/guardian"),
        _doc("Passport-size Photographs"),
    ],
    "application_process": [
        "Visit any post office or authorized bank (SBI, BOB, PNB, etc.)",
        "Collect and fill the SSY account opening form",
        "Submit birth certificate and parent's ID/address proof",
        "Make the initial deposit (minimum Rs 250)",
        "Account is opened and passbook is issued",
        "Continue annual deposits for 15 years",
        "Account matures after 21 years from opening date",
    ],
    "application_deadline": "Rolling basis (before girl turns 10)",
    "official_website": "https://www.nsiindia.gov.in",
    "source_url": "https://www.myscheme.gov.in/schemes/ssy",
    "last_updated": TODAY,
    "data_quality_score": 93,
}

BBBP = {
    "scheme_id": "BBBP-001",
    "scheme_name": "Beti Bachao Beti Padhao (BBBP)",
    "scheme_name_local": "बेटी बचाओ बेटी पढ़ाओ",
    "category": "Women & Children",
    "brief_description": "National campaign to improve child sex ratio, education of girls, and ensure survival & protection of the girl child.",
    "detailed_description": (
        "Beti Bachao Beti Padhao is a joint initiative of the Ministry of Women and Child Development, "
        "Ministry of Health, and Ministry of Human Resource Development. It focuses on districts with "
        "low Child Sex Ratio (CSR) and aims to prevent gender-biased sex selective elimination, ensure "
        "survival and protection of the girl child, and ensure education and participation of girls. "
        "The scheme involves multi-sectoral action including awareness campaigns, enforcement of PC-PNDT Act, "
        "and girls' enrollment drives."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "female",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "any",
        "state": "All India (all 640+ districts)",
        "land_ownership": "any",
        "other_conditions": [
            "Focus on districts with low Child Sex Ratio",
            "Benefits extend to all families with girl children",
        ],
        "raw_eligibility_text": "National campaign applicable to all. Focus on districts with low CSR.",
    },
    "benefits": {
        "summary": "Awareness campaign; improved institutional delivery; girl child enrollment in schools; strict PC-PNDT enforcement. No direct cash benefit (SSY is linked).",
        "financial_benefit": "No direct financial benefit (linked to SSY for savings)",
        "benefit_type": "Awareness & Institutional Support",
        "frequency": "Ongoing",
        "additional_benefits": [
            "Linked with Sukanya Samriddhi Yojana for savings",
            "Community-level awareness programs",
            "Girls' education enrollment drives",
        ],
        "raw_benefits_text": "Awareness and institutional support. Linked with SSY for financial benefit.",
    },
    "required_documents": [],
    "application_process": [
        "No individual application required for the awareness campaign",
        "For Sukanya Samriddhi Yojana (linked scheme), apply at post office/bank",
        "Contact local Anganwadi or District Women & Child Development office for programs",
    ],
    "application_deadline": "Not applicable (ongoing campaign)",
    "official_website": "https://wcd.nic.in/bbbp-schemes",
    "source_url": "https://www.myscheme.gov.in/schemes/bbbp",
    "last_updated": TODAY,
    "data_quality_score": 80,
}

# ============================================================
# BUSINESS & EMPLOYMENT (2 schemes)
# ============================================================

MUDRA = {
    "scheme_id": "PMMY-001",
    "scheme_name": "Pradhan Mantri Mudra Yojana (PMMY)",
    "scheme_name_local": "प्रधानमंत्री मुद्रा योजना",
    "category": "Business & Employment",
    "brief_description": "Collateral-free loans up to Rs 10 lakh for micro/small enterprises in three categories: Shishu, Kishore, Tarun.",
    "detailed_description": (
        "PMMY provides collateral-free loans up to Rs 10 lakh to non-corporate, non-farm small/micro "
        "enterprises. Loans are given in three categories: Shishu (up to Rs 50,000 for startups), "
        "Kishore (Rs 50,001 to Rs 5 lakh for mid-stage), and Tarun (Rs 5,00,001 to Rs 10 lakh for "
        "expansion). Loans are available from banks, NBFCs, and MFIs. No collateral or guarantor "
        "required. The scheme especially encourages women entrepreneurs, SC/ST borrowers, and those "
        "starting their first business."
    ),
    "eligibility_criteria": {
        "age_range": "any",
        "gender": "any",
        "caste_category": "any",
        "income_limit": "any",
        "occupation": "small/micro entrepreneur",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Non-corporate, non-farm income generating activity",
            "Existing enterprises or new startups",
            "Manufacturing, trading, services, and allied agricultural activities",
            "Should not be defaulter to any bank/financial institution",
        ],
        "raw_eligibility_text": "Any Indian citizen with a business plan for non-farm income activity. No collateral needed. Not a defaulter.",
    },
    "benefits": {
        "summary": "Collateral-free loans: Shishu (up to Rs 50K), Kishore (50K-5L), Tarun (5L-10L). Interest varies by lender (typically 7-12%).",
        "financial_benefit": "Up to Rs 10,00,000 loan",
        "benefit_type": "Subsidized Loan",
        "frequency": "One-time (renewable)",
        "additional_benefits": [
            "No collateral required",
            "No processing fee for Shishu loans",
            "Mudra Card for working capital needs",
        ],
        "raw_benefits_text": "Collateral-free loans up to Rs 10 lakh in three tiers: Shishu, Kishore, Tarun.",
    },
    "required_documents": [
        _doc("Identity Proof (Aadhaar / Voter ID / Passport)"),
        _doc("Address Proof"),
        _doc("Business Plan / Project Report"),
        _doc("Quotations for machinery/equipment (if any)"),
        _doc("Caste Certificate (if SC/ST)", False),
        _doc("Business Registration / License", False),
        _doc("Passport-size Photographs"),
    ],
    "application_process": [
        "Visit any bank branch, NBFC, or MFI that offers Mudra loans",
        "Alternatively, apply online through mudra.org.in or psbloansin59minutes.com",
        "Fill the loan application form and submit business plan",
        "Submit identity, address, and business-related documents",
        "Bank assesses the proposal",
        "Loan sanctioned and disbursed to bank account",
        "Mudra Card issued for working capital withdrawal",
    ],
    "application_deadline": "Rolling basis",
    "official_website": "https://www.mudra.org.in",
    "source_url": "https://www.myscheme.gov.in/schemes/pmmy",
    "last_updated": TODAY,
    "data_quality_score": 94,
}

PMEGP = {
    "scheme_id": "PMEGP-001",
    "scheme_name": "Prime Minister's Employment Generation Programme (PMEGP)",
    "scheme_name_local": "प्रधानमंत्री रोजगार सृजन कार्यक्रम",
    "category": "Business & Employment",
    "brief_description": "Credit-linked subsidy scheme for setting up micro enterprises, with 15-35% subsidy on project cost.",
    "detailed_description": (
        "PMEGP is a credit-linked subsidy programme for generating self-employment opportunities through "
        "establishment of micro-enterprises in the non-farm sector. It provides a subsidy of 15-35% of "
        "project cost (max project cost: Rs 50 lakh for manufacturing, Rs 20 lakh for services). Higher "
        "subsidy rates apply for SC/ST, women, minorities, PH, NER/hill area applicants. The scheme is "
        "administered by the Khadi & Village Industries Commission (KVIC) along with State KVI Boards "
        "and District Industries Centres."
    ),
    "eligibility_criteria": {
        "age_range": "18+",
        "gender": "any",
        "caste_category": "any (higher subsidy for SC/ST/OBC/Women/Minority)",
        "income_limit": "any",
        "occupation": "aspiring entrepreneur",
        "state": "All India",
        "land_ownership": "any",
        "other_conditions": [
            "Must have passed Class 8 (for projects above Rs 10 lakh in manufacturing / Rs 5 lakh in services)",
            "Existing units or units already availing government subsidy are not eligible",
            "Only one person from a family is eligible",
            "Assistance is only for new projects",
        ],
        "raw_eligibility_text": "Indian citizens aged 18+ with Class 8 pass (for larger projects). Only new projects. One per family.",
    },
    "benefits": {
        "summary": "Subsidy of 15-35% on project cost: General (Urban 15%, Rural 25%), Special (Urban 25%, Rural 35%). Max project: Rs 50L manufacturing, Rs 20L services.",
        "financial_benefit": "15-35% subsidy (up to Rs 17.5 lakh for manufacturing)",
        "benefit_type": "Capital Subsidy",
        "frequency": "One-time",
        "additional_benefits": [
            "Higher subsidy for SC/ST/Women/PH/NER/Minorities (25% urban, 35% rural)",
            "No collateral for loans up to Rs 10 lakh under CGTMSE",
            "EDP (Entrepreneurship Development Programme) training provided",
        ],
        "raw_benefits_text": "15-35% margin money subsidy on project cost. Max Rs 50L manufacturing, Rs 20L services.",
    },
    "required_documents": [
        _doc("Aadhaar Card"),
        _doc("Educational Certificate (Class 8 pass)"),
        _doc("Project Report / Detailed Project Proposal"),
        _doc("Caste Certificate (for SC/ST/OBC)", False),
        _doc("EDP/SDP/ESDP Training Certificate", False),
        _doc("Rural Area Certificate (for higher subsidy)", False),
        _doc("Passport-size Photographs"),
    ],
    "application_process": [
        "Apply online at kviconline.gov.in/pmegpeportal/",
        "Fill the application form with personal and project details",
        "Submit project report (DPR) prepared with guidance from KVIC/KVIB/DIC",
        "Application is screened at district level by the DLTFC (Task Force Committee)",
        "If approved, bank sanctions the loan",
        "Margin money (subsidy portion) is released to the bank by KVIC",
        "Set up the unit and start the business",
        "Subsidy is kept in a TDR for 3 years and released on successful running",
    ],
    "application_deadline": "Rolling basis (based on annual allocation)",
    "official_website": "https://www.kviconline.gov.in/pmegpeportal/",
    "source_url": "https://www.myscheme.gov.in/schemes/pmegp",
    "last_updated": TODAY,
    "data_quality_score": 92,
}


# ============================================================
# Public API
# ============================================================


def get_manual_schemes() -> List[Dict[str, Any]]:
    """Return all 20 manually curated schemes."""
    return [
        # Agriculture (5)
        PM_KISAN,
        FASAL_BIMA,
        KCC,
        SOIL_HEALTH,
        E_NAM,
        # Education (5)
        SC_SCHOLARSHIP,
        OBC_SCHOLARSHIP,
        NSP_SCHEMES,
        PM_SCHOLARSHIP,
        BEGUM_HAZRAT,
        # Healthcare (3)
        AYUSHMAN,
        PMMVY,
        JSY,
        # Senior Citizens (3)
        IGNOAPS,
        APY,
        PMVVY,
        # Women & Children (2)
        SSY,
        BBBP,
        # Business & Employment (2)
        MUDRA,
        PMEGP,
    ]


def get_schemes_by_category(category: str) -> List[Dict[str, Any]]:
    """Return manually curated schemes filtered by category."""
    return [s for s in get_manual_schemes() if s["category"].lower() == category.lower()]


def get_scheme_by_id(scheme_id: str) -> Dict[str, Any] | None:
    """Find a manual scheme by its ID."""
    for s in get_manual_schemes():
        if s["scheme_id"] == scheme_id:
            return s
    return None


if __name__ == "__main__":
    schemes = get_manual_schemes()
    print(f"Total manual schemes: {len(schemes)}")
    for s in schemes:
        print(f"  [{s['category']}] {s['scheme_name']} ({s['scheme_id']})")
    print(f"\nCategories: {set(s['category'] for s in schemes)}")
