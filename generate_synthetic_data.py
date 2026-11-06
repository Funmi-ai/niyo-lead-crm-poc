#!/usr/bin/env python3
"""Generate the 50-lead synthetic dataset (CSV + JSON) plus an expected-
results file describing known characteristics of each lead, for automated
testing of the qualification engine and dedupe logic.

All names, companies, emails are fictional. Emails use the reserved
example.com/example.org/example.net domains per RFC 2606.

Deterministic — no randomness — so re-running this script always produces
the same dataset, which the test suite can rely on.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from src.core.models import LEAD_FIELDS

DATA_DIR = Path(__file__).parent / "data"


def L(lead_id, organisation_name, organisation_type, sector, organisation_size,
      website, contact_name, contact_job_title, contact_email, lead_source,
      location, partnership_interest, relevant_programme, potential_funding_route,
      budget_status, decision_maker_status, existing_relationship_status,
      previous_contact_date, last_interaction, pipeline, crm_stage, notes,
      consent_status):
    return dict(
        lead_id=lead_id, organisation_name=organisation_name, organisation_type=organisation_type,
        sector=sector, organisation_size=organisation_size, website=website,
        contact_name=contact_name, contact_job_title=contact_job_title, contact_email=contact_email,
        lead_source=lead_source, location=location, partnership_interest=partnership_interest,
        relevant_programme=relevant_programme, potential_funding_route=potential_funding_route,
        budget_status=budget_status, decision_maker_status=decision_maker_status,
        existing_relationship_status=existing_relationship_status,
        previous_contact_date=previous_contact_date, last_interaction=last_interaction,
        pipeline=pipeline, crm_stage=crm_stage, notes=notes, consent_status=consent_status,
    )


LEADS: list[dict] = [
    # --- Private sector: strong ICP matches (decision-maker, good sector/size, budget known) ---
    L("LEAD-001", "Castlemere Logistics Ltd", "Private company", "Logistics", "250-999",
      "https://www.castlemerelogistics.example.com", "Priya Chandra", "Head of Learning & Development",
      "priya.chandra@castlemerelogistics.example.com", "Networking event", "Birmingham, UK",
      "Upskilling the ops team on AI tools", "Workforce upskilling academy (Niyo Learn)", "Unknown",
      "Confirmed", "Decision-maker", "New", "", "", "Private-sector", "New", "Met at Midlands Growth Summit.",
      "OK to contact"),
    L("LEAD-002", "Silverline Financial Services", "Private company", "Financial Services", "250-999",
      "https://www.silverlinefs.example.com", "Daniel Okafor", "Head of Talent",
      "daniel.okafor@silverlinefs.example.com", "LinkedIn outreach", "London, UK",
      "Graduate hiring pipeline", "Hiring from cohorts / Demo & Hire", "Unknown",
      "Likely", "Decision-maker", "New", "", "", "Private-sector", "New", "Downloaded Niyo Hack case study.",
      "OK to contact"),
    L("LEAD-003", "Harrow Tech Solutions", "Private company", "Technology / Software", "50-249",
      "https://www.harrowtech.example.com", "Meera Patel", "VP Engineering",
      "meera.patel@harrowtech.example.com", "Referral", "Manchester, UK",
      "Niyo Hack for a real product challenge", "Niyo Hack", "Unknown",
      "Confirmed", "Decision-maker", "New", "", "", "Private-sector", "New", "Referred by Castlemere Logistics contact.",
      "OK to contact"),
    L("LEAD-004", "Granville Partners LLP", "Private company", "Professional Services / Consulting", "50-249",
      "https://www.granvillepartners.example.com", "Owen Marsh", "Partner, People & Culture",
      "owen.marsh@granvillepartners.example.com", "Conference", "Leeds, UK",
      "CSR / social value reporting for bids", "Social value reporting (PPN 002)", "Unknown",
      "Likely", "Decision-maker", "New", "", "", "Private-sector", "New", "Needs social value evidence for public-sector bids.",
      "OK to contact"),
    L("LEAD-005", "Brightwell Financial Group", "Private company", "Financial Services", "250-999",
      "https://www.brightwellfg.example.com", "Isabelle Cho", "Chief People Officer",
      "isabelle.cho@brightwellfg.example.com", "Inbound web enquiry", "London, UK",
      "Sponsoring accelerator seats", "Accelerator seat sponsorship", "Unknown",
      "Confirmed", "Decision-maker", "Warm", "2026-07-02", "Intro call held 2026-07-10", "Private-sector", "Qualifying",
      "Already had an intro call; wants a formal proposal.", "OK to contact"),

    # --- Private sector: weak ICP matches (off-fit sector or size, or no budget signal) ---
    L("LEAD-006", "Oakfield Retail Group", "Private company", "Retail", "1-9",
      "https://www.oakfieldretail.example.com", "Callum Reid", "Store Operations Manager",
      "callum.reid@oakfieldretail.example.com", "Networking event", "Bristol, UK",
      "General interest, no specific need yet", "Unknown", "Unknown",
      "None identified", "Influencer", "New", "", "", "Private-sector", "New",
      "Small retailer, unclear if there's a real use case.", "OK to contact"),
    L("LEAD-007", "Thornbury Manufacturing", "Private company", "Engineering / Manufacturing", "1-9",
      "https://www.thornburymfg.example.com", "Grace Fenwick", "Office Manager",
      "grace.fenwick@thornburymfg.example.com", "Cold outreach list", "Sheffield, UK",
      "Unclear — picked up from a generic list", "Unknown", "Unknown",
      "Unknown", "Not a decision-maker", "New", "", "", "Private-sector", "New",
      "Contact is not in a hiring or L&D role.", "Unknown"),
    L("LEAD-008", "Marchbank Engineering", "Private company", "Engineering / Manufacturing", "250-999",
      "https://www.marchbankeng.example.com", "", "", "info@marchbankeng.example.com",
      "Conference", "Newcastle, UK", "Picked up a brochure at a trade show", "Unknown", "Unknown",
      "Unknown", "Unknown", "New", "", "", "Private-sector", "New",
      "Only a general enquiries inbox captured — no named contact yet.", "Needs review"),
    L("LEAD-009", "Corvid Technology Ltd", "Private company", "Technology / Software", "10-49",
      "https://www.corvidtech.example.com", "Sam Whitfield", "Engineering Lead",
      "sam.whitfield@corvidtech.example.com", "LinkedIn outreach", "Edinburgh, UK",
      "Interested but says engineering lead doesn't hold budget", "Workforce upskilling academy (Niyo Learn)",
      "Unknown", "Unclear", "Influencer", "New", "", "", "Private-sector", "New",
      "Contact flagged they'd need to loop in their Head of People for any spend.", "OK to contact"),
    L("LEAD-010", "Westfold Retail Holdings", "Private company", "Retail", "250-999",
      "https://www.westfoldretail.example.com", "Natasha Byrne", "Group HR Director",
      "natasha.byrne@westfoldretail.example.com", "Referral", "Cardiff, UK",
      "Possible upskilling academy, budget cycle uncertain", "Workforce upskilling academy (Niyo Learn)",
      "Unknown", "Unclear", "Decision-maker", "New", "", "", "Private-sector", "New",
      "Says budget depends on next quarter's review.", "OK to contact"),

    # --- Private sector: previously contacted / existing relationship ---
    L("LEAD-011", "Pennington Engineering Ltd", "Private company", "Engineering / Manufacturing", "50-249",
      "https://www.penningtoneng.example.com", "Jonathan Vale", "Head of People",
      "jonathan.vale@penningtoneng.example.com", "Partner referral", "Coventry, UK",
      "Niyo Hack challenge for apprentices", "Niyo Hack", "Unknown",
      "Likely", "Decision-maker", "Previously contacted", "2026-05-14",
      "Sent a follow-up email 2026-06-01, no reply yet", "Private-sector", "Contacted",
      "Went quiet after first follow-up.", "OK to contact"),
    L("LEAD-012", "Keel & Vane Software", "Private company", "Technology / Software", "10-49",
      "https://www.keelvane.example.com", "Olu Bankole", "COO",
      "olu.bankole@keelvane.example.com", "Inbound web enquiry", "London, UK",
      "Existing partner — renewing cohort sponsorship", "Accelerator seat sponsorship",
      "Confirmed", "Confirmed", "Decision-maker", "Existing partner", "2025-11-03",
      "Renewed last cohort, in conversation about next one", "Private-sector", "Negotiation",
      "Existing sponsor — renewal conversation in progress.", "OK to contact"),
    L("LEAD-013", "Linden Grove Consulting", "Private company", "Professional Services / Consulting", "10-49",
      "https://www.lindengrove.example.com", "Freya Thomson", "Managing Director",
      "freya.thomson@lindengrove.example.com", "Networking event", "Glasgow, UK",
      "Wants to discuss CSR angle", "Social value reporting (PPN 002)", "Unknown",
      "Unclear", "Decision-maker", "Previously contacted", "2026-04-20",
      "Last spoke at an event in April, no formal follow-up sent", "Private-sector", "New",
      "", "OK to contact"),

    # --- Private sector: do-not-contact / opted out ---
    L("LEAD-014", "Ashcombe Logistics", "Private company", "Logistics", "50-249",
      "https://www.ashcombelogistics.example.com", "Ruth Okonjo", "HR Manager",
      "ruth.okonjo@ashcombelogistics.example.com", "Cold outreach list", "Liverpool, UK",
      "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "New", "2026-02-11",
      "Replied asking to be removed from the mailing list", "Private-sector", "New",
      "Contact explicitly opted out — do not re-contact.", "Do not contact"),
    L("LEAD-015", "Fenbridge Consulting Group", "Private company", "Professional Services / Consulting", "10-49",
      "https://www.fenbridgeconsulting.example.com", "Tariq Hussain", "Director",
      "tariq.hussain@fenbridgeconsulting.example.com", "Cold outreach list", "Leicester, UK",
      "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "New", "2026-01-30",
      "Bounced complaint via email provider; marked as do-not-contact for compliance", "Private-sector", "New",
      "Spam complaint on file — exclude from all future sends.", "Do not contact"),

    # --- Private sector: corporate size, strong roles, mixed signals (round out to 18) ---
    L("LEAD-016", "Heathgate Capital Partners", "Private company", "Financial Services", "250-999",
      "https://www.heathgatecapital.example.com", "Alicia Fontaine", "Head of Early Careers",
      "alicia.fontaine@heathgatecapital.example.com", "Conference", "London, UK",
      "Early-careers hiring from accelerator cohorts", "Hiring from cohorts / Demo & Hire", "Unknown",
      "Confirmed", "Decision-maker", "New", "", "", "Private-sector", "New",
      "Explicitly asked about Demo & Hire dates.", "OK to contact"),
    L("LEAD-017", "Dunmore Retail Analytics", "Private company", "Technology / Software", "10-49",
      "https://www.dunmoreretail.example.com", "Ben Okafor", "Founder & CEO",
      "ben.okafor@dunmoreretail.example.com", "Inbound web enquiry", "Bristol, UK",
      "Founder Path — exploring spinning out an internal tool", "Founder Path", "Unknown",
      "Unknown", "Decision-maker", "New", "", "", "Private-sector", "New",
      "More relevant to Founder Path than corporate offer — flag internally.", "OK to contact"),
    L("LEAD-018", "Colyer & Boothe Engineering", "Private company", "Engineering / Manufacturing", "1-9",
      "https://www.colyerboothe.example.com", "Marion Clegg", "Finance Director",
      "marion.clegg@colyerboothe.example.com", "Referral", "Derby, UK",
      "Unknown", "Unknown", "Unknown", "None identified", "Not a decision-maker", "New", "", "",
      "Private-sector", "New", "Finance contact, not involved in hiring or L&D decisions.", "OK to contact"),

    # --- Government-funded: strong matches (named funding routes, clear org type) ---
    L("LEAD-019", "Castlemere Combined Authority", "Combined authority", "Local Government", "250+",
      "https://www.castlemereca.example.gov.uk", "Fiona Okwuosa", "Head of Skills & Employment",
      "fiona.okwuosa@castlemereca.example.gov.uk", "Partner referral", "Birmingham, UK",
      "Regional AI adoption + digital skills programme", "Commissioned accelerator cohort",
      "Innovate UK", "Confirmed", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Explicitly referenced WMCA's award-winning programme as a model.", "OK to contact"),
    L("LEAD-020", "Thornbury Metropolitan Council", "Local authority", "Local Government", "250+",
      "https://www.thornburycouncil.example.gov.uk", "Patrick Nwosu", "Director of Employment & Skills",
      "patrick.nwosu@thornburycouncil.example.gov.uk", "Conference", "Sheffield, UK",
      "Youth employment / NEET re-engagement programme", "She Builds-style cohort", "DCMS",
      "Likely", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Council has prior Innovate UK-funded programmes.", "OK to contact"),
    L("LEAD-021", "Elmsworth District Council", "Local authority", "Local Government", "50-249",
      "https://www.elmsworthcouncil.example.gov.uk", "Diane Whitlock", "Economic Development Officer",
      "diane.whitlock@elmsworthcouncil.example.gov.uk", "Inbound web enquiry", "Elmsworth, UK",
      "Inclusive growth programme for small businesses", "SME sprint", "West Midlands Combined Authority (WMCA)",
      "Confirmed", "Decision-maker", "New", "", "", "Government-funded", "New", "", "OK to contact"),
    L("LEAD-022", "Northgate City Council", "Local authority", "Local Government", "250+",
      "https://www.northgatecouncil.example.gov.uk", "Imogen Falk", "Head of Digital Inclusion",
      "imogen.falk@northgatecouncil.example.gov.uk", "Networking event", "Newcastle, UK",
      "Digital/cyber skills for residents", "Commissioned accelerator cohort", "Innovate UK",
      "Likely", "Decision-maker", "Previously contacted", "2026-06-18",
      "Scoping call booked for next month", "Government-funded", "Qualifying",
      "Scoping call already booked — keep momentum.", "OK to contact"),

    # --- Government-funded: needing further eligibility checks (unverified funding route / missing) ---
    L("LEAD-023", "Ridgeway County Council", "Local authority", "Local Government", "250+",
      "https://www.ridgewaycouncil.example.gov.uk", "Harriet Soames", "Skills Commissioning Lead",
      "harriet.soames@ridgewaycouncil.example.gov.uk", "Referral", "Oxford, UK",
      "Possible digital skills programme", "Commissioned accelerator cohort",
      "Other public grant (unverified)", "Unclear", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Mentioned a 'regional growth fund' — route not yet confirmed as one Niyo works with.", "OK to contact"),
    L("LEAD-024", "Marshside Borough Council", "Local authority", "Local Government", "50-249",
      "https://www.marshsideborough.example.gov.uk", "Callum Reith", "Policy Officer",
      "callum.reith@marshsideborough.example.gov.uk", "Cold outreach list", "Hull, UK",
      "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "New", "", "",
      "Government-funded", "New", "Picked up from a council directory — needs qualifying from scratch.",
      "Needs review"),
    L("LEAD-025", "Vale of Elmsworth Enterprise Partnership", "Public sector body", "Employment & Skills", "50-249",
      "https://www.valeelmsworthlep.example.gov.uk", "", "Programme Manager",
      "contact@valeelmsworthlep.example.gov.uk", "Conference", "Elmsworth, UK",
      "Enterprise partnership funding route unclear", "SME sprint", "Unknown",
      "Unknown", "Unknown", "New", "", "", "Government-funded", "New",
      "No named contact captured yet — business card only had a role.", "Unknown"),

    # --- Government-funded: public sector adjacent (education, health) ---
    L("LEAD-026", "Oakridge Further Education College", "Public sector body", "Education", "250+",
      "https://www.oakridgefe.example.ac.uk", "Dr Susan Fairweather", "Vice Principal, Curriculum",
      "susan.fairweather@oakridgefe.example.ac.uk", "Referral", "Oakridge, UK",
      "AI curriculum partnership for students", "Niyo Kidz outreach", "DCMS",
      "Likely", "Decision-maker", "New", "", "", "Government-funded", "New", "", "OK to contact"),
    L("LEAD-027", "Bramcote Health Partnership", "Public sector body", "Health", "250+",
      "https://www.bramcotehealth.example.nhs.uk", "Nadia Qureshi", "Workforce Development Lead",
      "nadia.qureshi@bramcotehealth.example.nhs.uk", "Networking event", "Nottingham, UK",
      "Digital skills for admin staff", "Workforce upskilling academy (Niyo Learn)", "Unknown",
      "Unclear", "Influencer", "New", "", "", "Government-funded", "New",
      "Contact is keen but says procurement would sit with a separate team.", "OK to contact"),
    L("LEAD-028", "Greywell Youth Service", "Public sector body", "Youth Services", "10-49",
      "https://www.greywellyouth.example.gov.uk", "Tom Abara", "Service Manager",
      "tom.abara@greywellyouth.example.gov.uk", "Partner referral", "Preston, UK",
      "Youth employment pathway", "She Builds-style cohort", "Innovate UK",
      "Confirmed", "Decision-maker", "New", "", "", "Government-funded", "New", "", "OK to contact"),

    # --- Government-funded: not a decision-maker contact ---
    L("LEAD-029", "Hartwell Metropolitan Borough", "Local authority", "Local Government", "250+",
      "https://www.hartwellborough.example.gov.uk", "Lily Ferron", "Admin Assistant, Economic Development",
      "lily.ferron@hartwellborough.example.gov.uk", "Inbound web enquiry", "Wolverhampton, UK",
      "Picked up an enquiry form on behalf of her team", "Commissioned accelerator cohort", "Unknown",
      "Unknown", "Not a decision-maker", "New", "", "", "Government-funded", "New",
      "Filled in enquiry form on behalf of the actual commissioning lead — name not yet known.",
      "OK to contact"),

    # --- Charity / social enterprise / community organisation (ambiguous pipeline fit) ---
    L("LEAD-030", "Thornbury Youth Trust", "Charity / social enterprise", "Youth Services", "10-49",
      "https://www.thornburyyouthtrust.example.org", "Abena Osei", "Chief Executive",
      "abena.osei@thornburyyouthtrust.example.org", "Networking event", "Sheffield, UK",
      "Youth employment pathway for care leavers", "She Builds-style cohort", "DCMS",
      "Likely", "Decision-maker", "New", "", "", "Government-funded", "New", "", "OK to contact"),
    L("LEAD-031", "Bridgeview Community Foundation", "Charity / social enterprise", "Community / Voluntary", "1-9",
      "https://www.bridgeviewfoundation.example.org", "Grace Nwankwo", "Programmes Director",
      "grace.nwankwo@bridgeviewfoundation.example.org", "Referral", "Luton, UK",
      "Digital inclusion for the local community", "Workforce upskilling academy (Niyo Learn)", "Unknown",
      "Unclear", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Strong mission fit, funding route not yet identified.", "OK to contact"),
    L("LEAD-032", "Elmsworth Skills Charity", "Charity / social enterprise", "Employment & Skills", "10-49",
      "https://www.elmsworthskills.example.org", "Peter Langham", "Head of Partnerships",
      "peter.langham@elmsworthskills.example.org", "Conference", "Elmsworth, UK",
      "Co-delivery of a skills programme", "Commissioned accelerator cohort",
      "West Midlands Combined Authority (WMCA)", "Confirmed", "Decision-maker", "Warm", "2026-06-02",
      "Two calls held, drafting a joint proposal", "Government-funded", "Negotiation",
      "Far along — drafting joint proposal with WMCA funding.", "OK to contact"),
    L("LEAD-033", "Oak & Acorn Social Enterprise", "Charity / social enterprise", "Community / Voluntary", "1-9",
      "https://www.oakandacorn.example.org", "Jade Fitzgerald", "Founder",
      "jade.fitzgerald@oakandacorn.example.org", "Inbound web enquiry", "Bristol, UK",
      "Unclear — small enquiry, limited detail", "Unknown", "Unknown",
      "Unknown", "Unknown", "New", "", "", "Government-funded", "New",
      "Very early-stage enquiry — needs a proper qualifying call.", "Needs review"),
    L("LEAD-034", "Riverside Futures CIC", "Charity / social enterprise", "Community / Voluntary", "10-49",
      "https://www.riversidefutures.example.org", "Michael Osei", "Operations Lead",
      "michael.osei@riversidefutures.example.org", "Partner referral", "Cardiff, UK",
      "SME sprint for a community business idea", "SME sprint", "Unknown",
      "Unknown", "Influencer", "New", "", "", "Government-funded", "New",
      "Enthusiastic but says the board holds any funding decision.", "OK to contact"),

    # --- Ambiguous / missing organisation_type -> pipeline should come out 'Unclear' ---
    L("LEAD-035", "Northgate Youth Connect", "Unknown", "Youth Services", "Unknown",
      "https://www.northgateyouthconnect.example.org", "Sarah Vance", "Coordinator",
      "sarah.vance@northgateyouthconnect.example.org", "Cold outreach list", "Newcastle, UK",
      "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "New", "", "",
      "Unclassified", "New", "Org type never captured — could be charity or informal community group.",
      "Unknown"),
    L("LEAD-036", "Fernhill Collective", "Unknown", "Unknown", "Unknown",
      "https://www.fernhillcollective.example.org", "Rowan Blake", "Unknown",
      "rowan.blake@fernhillcollective.example.org", "Cold outreach list", "Unknown",
      "Unknown", "Unknown", "Unknown", "Unknown", "Unknown", "New", "", "",
      "Unclassified", "New", "Almost nothing known — scraped from an old contact list.", "Needs review"),

    # --- A few more private-sector to round the dataset out with realistic variety ---
    L("LEAD-037", "Abbotswood Data Systems", "Private company", "Technology / Software", "50-249",
      "https://www.abbotswooddata.example.com", "Yusuf Demir", "Head of Talent Acquisition",
      "yusuf.demir@abbotswooddata.example.com", "LinkedIn outreach", "Reading, UK",
      "Hiring pipeline from AI accelerator cohorts", "Hiring from cohorts / Demo & Hire", "Unknown",
      "Likely", "Decision-maker", "New", "", "", "Private-sector", "New", "", "OK to contact"),
    L("LEAD-038", "Carrow & Finch Insurance", "Private company", "Financial Services", "250-999",
      "https://www.carrowfinch.example.com", "Eleanor Vosper", "Group Learning Director",
      "eleanor.vosper@carrowfinch.example.com", "Conference", "Norwich, UK",
      "Workforce academy for underwriting teams", "Workforce upskilling academy (Niyo Learn)", "Unknown",
      "Confirmed", "Decision-maker", "New", "", "", "Private-sector", "New", "", "OK to contact"),
    L("LEAD-039", "Ironford Steel Group", "Private company", "Engineering / Manufacturing", "250-999",
      "https://www.ironfordsteel.example.com", "Craig Donaldson", "HR Business Partner",
      "craig.donaldson@ironfordsteel.example.com", "Referral", "Sheffield, UK",
      "Apprenticeship-adjacent upskilling", "Workforce upskilling academy (Niyo Learn)", "Unknown",
      "Unclear", "Influencer", "Previously contacted", "2026-03-11",
      "Had one call, said he'd check with the plant director", "Private-sector", "Contacted",
      "Waiting on internal sign-off from the plant director.", "OK to contact"),
    L("LEAD-040", "Quillon Media Group", "Private company", "Technology / Software", "10-49",
      "https://www.quillonmedia.example.com", "Harriet Okafor", "Founder",
      "harriet.okafor@quillonmedia.example.com", "Inbound web enquiry", "Brighton, UK",
      "Niyo Hack for a content-tooling challenge", "Niyo Hack", "Unknown",
      "Likely", "Decision-maker", "New", "", "", "Private-sector", "New", "", "OK to contact"),

    # --- Rounding charity/public sector out ---
    L("LEAD-041", "Dovecote NHS Trust", "Public sector body", "Health", "250+",
      "https://www.dovecotenhs.example.nhs.uk", "Farrah Siddiqui", "Head of OD & Workforce",
      "farrah.siddiqui@dovecotenhs.example.nhs.uk", "Networking event", "York, UK",
      "Digital upskilling for non-clinical staff", "Workforce upskilling academy (Niyo Learn)", "Unknown",
      "Unclear", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Keen but flagged NHS procurement processes will take time.", "OK to contact"),
    L("LEAD-042", "Priorswood Parish Council", "Local authority", "Local Government", "1-9",
      "https://www.priorswoodparish.example.gov.uk", "Edward Lyle", "Parish Clerk",
      "edward.lyle@priorswoodparish.example.gov.uk", "Cold outreach list", "Taunton, UK",
      "Unclear — very small parish council", "Unknown", "Unknown",
      "None identified", "Not a decision-maker", "New", "", "", "Government-funded", "New",
      "Parish-level body, likely too small for any funded programme — low priority.", "OK to contact"),
    L("LEAD-043", "Cliffmoor Enterprise Hub", "Charity / social enterprise", "Employment & Skills", "10-49",
      "https://www.cliffmoorhub.example.org", "Dominic Shaw", "Centre Manager",
      "dominic.shaw@cliffmoorhub.example.org", "Partner referral", "Plymouth, UK",
      "SME sprint referral pipeline for local founders", "SME sprint", "Innovate UK",
      "Likely", "Decision-maker", "New", "", "", "Government-funded", "New", "", "OK to contact"),
    L("LEAD-044", "Westgate Business Improvement District", "Private company", "Professional Services / Consulting",
      "10-49", "https://www.westgatebid.example.com", "Charlotte Reavey", "Director",
      "charlotte.reavey@westgatebid.example.com", "Conference", "Southampton, UK",
      "Social value reporting for member businesses", "Social value reporting (PPN 002)", "Unknown",
      "Unclear", "Decision-maker", "New", "", "", "Private-sector", "New",
      "Represents a group of small businesses rather than one employer — flag for discovery.",
      "OK to contact"),
]

# --- Duplicates (6 rows): same person/org re-entering via a different lead
# source, to exercise dedupe. Dedupe should match on email OR org+contact
# name, so these intentionally vary other fields (source, notes, CRM stage).
DUPLICATES = [
    L("LEAD-045", "Castlemere Logistics Ltd", "Private company", "Logistics", "250-999",
      "https://www.castlemerelogistics.example.com", "Priya Chandra", "Head of Learning & Development",
      "priya.chandra@castlemerelogistics.example.com", "LinkedIn outreach", "Birmingham, UK",
      "Upskilling the ops team on AI tools", "Workforce upskilling academy (Niyo Learn)", "Unknown",
      "Confirmed", "Decision-maker", "New", "", "", "Private-sector", "New",
      "Duplicate entry — also captured via a LinkedIn connect request.", "OK to contact"),
    L("LEAD-046", "Silverline Financial Services", "Private company", "Financial Services", "250-999",
      "https://www.silverlinefs.example.com", "Daniel Okafor", "Head of Talent",
      "daniel.okafor@silverlinefs.example.com", "Conference", "London, UK",
      "Graduate hiring pipeline", "Hiring from cohorts / Demo & Hire", "Unknown",
      "Likely", "Decision-maker", "New", "", "", "Private-sector", "New",
      "Duplicate entry — business card from a conference, same contact as LEAD-002.", "OK to contact"),
    L("LEAD-047", "Castlemere Combined Authority", "Combined authority", "Local Government", "250+",
      "https://www.castlemereca.example.gov.uk", "Fiona Okwuosa", "Head of Skills & Employment",
      "fiona.okwuosa@castlemereca.example.gov.uk", "Inbound web enquiry", "Birmingham, UK",
      "Regional AI adoption + digital skills programme", "Commissioned accelerator cohort",
      "Innovate UK", "Confirmed", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Duplicate entry — same contact submitted the web enquiry form too.", "OK to contact"),
    L("LEAD-048", "Thornbury Youth Trust", "Charity / social enterprise", "Youth Services", "10-49",
      "https://www.thornburyyouthtrust.example.org", "Abena Osei", "Chief Executive",
      "abena.osei@thornburyyouthtrust.example.org", "Partner referral", "Sheffield, UK",
      "Youth employment pathway for care leavers", "She Builds-style cohort", "DCMS",
      "Likely", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Duplicate entry — partner referral landed separately from the networking-event capture.",
      "OK to contact"),
    L("LEAD-049", "Pennington Engineering Ltd", "Private company", "Engineering / Manufacturing", "50-249",
      "https://www.penningtoneng.example.com", "Jonathan Vale", "Head of People",
      "jonathan.vale@penningtoneng.example.com", "Cold outreach list", "Coventry, UK",
      "Niyo Hack challenge for apprentices", "Niyo Hack", "Unknown",
      "Likely", "Decision-maker", "Previously contacted", "2026-05-14", "",
      "Private-sector", "New", "Duplicate entry — re-appeared on a purchased contact list.", "OK to contact"),
    L("LEAD-050", "Elmsworth District Council", "Local authority", "Local Government", "50-249",
      "https://www.elmsworthcouncil.example.gov.uk", "Diane Whitlock", "Economic Development Officer",
      "diane.whitlock@elmsworthcouncil.example.gov.uk", "Networking event", "Elmsworth, UK",
      "Inclusive growth programme for small businesses", "SME sprint", "West Midlands Combined Authority (WMCA)",
      "Confirmed", "Decision-maker", "New", "", "", "Government-funded", "New",
      "Duplicate entry — met again at a separate event, not recognised as existing.", "OK to contact"),
]

ALL_LEADS = LEADS + DUPLICATES


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=LEAD_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, rows: list[dict]) -> None:
    path.write_text(json.dumps(rows, indent=2))


EXPECTED_DUPLICATE_PAIRS = {
    "LEAD-045": "LEAD-001",
    "LEAD-046": "LEAD-002",
    "LEAD-047": "LEAD-019",
    "LEAD-048": "LEAD-030",
    "LEAD-049": "LEAD-011",
    "LEAD-050": "LEAD-021",
}

EXPECTED_DO_NOT_CONTACT = ["LEAD-014", "LEAD-015"]

EXPECTED_NEEDS_REVIEW = [
    "LEAD-008", "LEAD-024", "LEAD-025", "LEAD-033", "LEAD-035", "LEAD-036",
]

EXPECTED_NOT_DECISION_MAKER = ["LEAD-007", "LEAD-018", "LEAD-029", "LEAD-042"]

EXPECTED_UNCLEAR_PIPELINE = ["LEAD-035", "LEAD-036"]


def build_expected_results() -> dict:
    return {
        "total_leads": len(ALL_LEADS),
        "unique_leads": len(LEADS),
        "duplicate_pairs": EXPECTED_DUPLICATE_PAIRS,
        "expected_do_not_contact": EXPECTED_DO_NOT_CONTACT,
        "expected_needs_review_at_least": EXPECTED_NEEDS_REVIEW,
        "expected_not_decision_maker": EXPECTED_NOT_DECISION_MAKER,
        "expected_unclear_pipeline": EXPECTED_UNCLEAR_PIPELINE,
        "notes": (
            "This file lists known, hand-placed characteristics of the synthetic "
            "dataset for regression testing. It does not pin exact scores, since "
            "scoring weights in rules_config.py are provisional and expected to "
            "change once Niyo confirms real ICP/eligibility rules."
        ),
    }


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    write_csv(DATA_DIR / "leads.csv", ALL_LEADS)
    write_json(DATA_DIR / "leads.json", ALL_LEADS)
    write_json(DATA_DIR / "expected_results.json", build_expected_results())
    print(f"Wrote {len(ALL_LEADS)} leads to {DATA_DIR / 'leads.csv'} and leads.json")
    print(f"Wrote expected_results.json ({len(EXPECTED_DUPLICATE_PAIRS)} duplicate pairs)")


if __name__ == "__main__":
    main()
