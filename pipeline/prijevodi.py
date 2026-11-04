"""Engleski tekstovi za kartu (web/public/data/en.json).

Hrvatski ostaje izvorni jezik: svi ostali izlazi su na hrvatskom, a ovdje su engleski
nazivi i objašnjenja pokazatelja, tema, tipologije, vremenskih nizova, funkcija proračuna,
županija i napomena. Sučelje ih učitava samo kad korisnik odabere engleski (EN).

Nazivi gradova i općina, dobavljača, EU projekata i službeni nazivi skupova podataka ostaju
izvorni. Nazivi planiranih EU poziva prevedeni su ovdje; poziv kojeg ovdje nema prikazuje se
pod hrvatskim nazivom (planovi se mijenjaju), a build to samo ispiše.

`izracunaj()` provjerava da prijevod postoji za svaki pokazatelj, temu, tip, niz i
funkciju koje izvoz sadrži, pa novi pokazatelj bez prijevoda zaustavi build.
"""

from __future__ import annotations

import re

TEME = {
    "ljudi": "People",
    "novac": "Money",
    "porezi": "Taxes",
    "imovina": "Property",
    "nabava": "Procurement",
}

# naziv: official name (shown as "Official name"); objasnjenje: plain-language meaning;
# napomena: how it is calculated (only where the Croatian original has one).
POKAZATELJI: dict[str, dict[str, str]] = {
    "stanovnistvo": {
        "naziv": "Population",
        "objasnjenje": "How many people live here according to the 2021 Census. All per-resident "
        "amounts are divided by this number.",
    },
    "stanovnistvo_procjena": {
        "naziv": "Population (Croatian Bureau of Statistics estimate)",
        "objasnjenje": "How many people live here in mid-2025 according to the estimate of the "
        "Croatian Bureau of Statistics, counting migration, births and deaths since the census.",
        "napomena": "Mid-year estimate. Per-resident amounts are still based on the 2021 Census, "
        "because there is no newer estimate for cities and municipalities.",
    },
    "promjena_stanovnistva": {
        "naziv": "Population change",
        "objasnjenje": "By what percentage the population changed from 2021 to 2025. A minus "
        "means more people died or moved away than were born or moved in.",
        "napomena": "Change of the mid-year estimate compared with mid-2021 (migration, births "
        "and deaths).",
    },
    "gustoca_naseljenosti": {
        "naziv": "Population density",
        "objasnjenje": "How many people live on one square kilometre on average. A high number "
        "means a densely populated area, a low one a sparsely populated area.",
    },
    "prosjecna_starost": {
        "naziv": "Average age",
        "objasnjenje": "Average age of all residents. A higher number means an older community, "
        "with more pensioners and fewer children.",
    },
    "prosjecna_neto_placa": {
        "naziv": "Average net salary",
        "objasnjenje": "How much employees of companies and institutions take home per month on "
        "average, after tax and contributions. Sole traders are not included.",
        "napomena": "Monthly average in legal entities, based on the JOPPD tax form.",
    },
    "zaposleni": {
        "naziv": "Employed persons",
        "objasnjenje": "How many people have a job. Per resident shows the number of employed "
        "per 1,000 residents.",
        "napomena": "As of 31 March, administrative sources.",
    },
    "stopa_nezaposlenosti": {
        "naziv": "Registered unemployment rate",
        "objasnjenje": "Out of 100 people who work or are looking for work, how many are "
        "registered as unemployed with the Croatian Employment Service.",
    },
    "neto_dohodak": {
        "naziv": "Net income of residents",
        "objasnjenje": "How much all residents together received in the year after tax and "
        "contributions: salaries, pensions and other income. Per resident it is the average per "
        "person, children included.",
        "napomena": "Salaries, pensions and other income after tax and contributions, for the "
        "whole year.",
    },
    "bdp": {
        "naziv": "Gross domestic product (GDP)",
        "objasnjenje": "The value of everything produced in Croatia in a year. The most common "
        "measure of the size of an economy.",
    },
    "bruto_dodana_vrijednost": {
        "naziv": "Gross value added",
        "objasnjenje": "How much value companies, sole traders and public services in the county "
        "create in a year. Similar to GDP, but without taxes on products such as VAT.",
        "napomena": "Value of production in the county; GDP without taxes on products. The "
        "Croatian Bureau of Statistics does not publish GDP by county.",
    },
    "eu_ugovoreno": {
        "naziv": "Contracted EU funds (OPCC 2014–2020)",
        "objasnjenje": "How much EU money was contracted for projects here in the 2014–2020 "
        "period. Contracted does not mean paid out.",
        "napomena": "ESIF share of contracted projects, by place of implementation.",
    },
    "eu_projekti": {
        "naziv": "Number of EU projects (OPCC 2014–2020)",
        "objasnjenje": "How many projects with EU funding were contracted here in the 2014–2020 "
        "period.",
    },
    "eu_2127_ugovoreno": {
        "naziv": "Contracted EU funds 2021–2027",
        "objasnjenje": "How much EU money has been contracted so far for projects here in the "
        "2021–2027 period. The period is still running, and contracted does not mean paid out.",
        "napomena": "EU share of contracted projects from the Competitiveness and Cohesion, "
        "Integrated Territorial and Efficient Human Resources programmes. Counties by project "
        "location (Efficient Human Resources by the beneficiary's seat); cities and "
        "municipalities by the beneficiary's seat. Projects of state bodies and projects without "
        "a location count only in the national total.",
    },
    "eu_2127_projekti": {
        "naziv": "Number of EU projects 2021–2027",
        "objasnjenje": "How many projects with EU funding have been contracted here so far in "
        "the 2021–2027 period.",
        "napomena": "A project carried out in several counties counts in each of them.",
    },
    "hbor_krediti": {
        "naziv": "HBOR loans from EU funds",
        "objasnjenje": "How much companies, farmers and the public sector received in favourable "
        "loans from HBOR (the Croatian development bank) financed from EU funds.",
        "napomena": "Five ESIF programmes of HBOR, by county of investment.",
    },
    "inflacija": {
        "naziv": "Inflation (annual, HICP)",
        "objasnjenje": "How much prices rose in a year. For example, 4% means that what cost "
        "€100 a year ago now costs €104.",
    },
    "saldo_proracuna": {
        "naziv": "General government balance",
        "objasnjenje": "The difference between revenue and expenditure of the whole state, "
        "including cities, municipalities and funds. A minus means the state spends more than it "
        "collects and borrows the difference.",
        "napomena": "Negative = deficit (net borrowing), ESA 2010.",
    },
    "javni_dug": {
        "naziv": "General government debt",
        "objasnjenje": "How much the state owes in total through loans and bonds, together with "
        "cities, municipalities and public funds.",
    },
    "lokalni_prihodi": {
        "naziv": "Local budget revenue",
        "objasnjenje": "All the money the city or municipality received in the year: taxes, "
        "fees, grants from the state and the EU, and sales of assets. For a county we add up all "
        "its cities and municipalities too.",
        "napomena": "Budget outturn (not plan), latest year. For a county: the county budget and "
        "the budgets of all its cities and municipalities; for the country: the sum of all local "
        "budgets.",
    },
    "lokalni_rashodi": {
        "naziv": "Local budget expenditure",
        "objasnjenje": "All the money the city or municipality spent in the year: salaries, "
        "materials, services, support to residents and investment.",
        "napomena": "Budget outturn (not plan), latest year. For a county: the county budget and "
        "the budgets of all its cities and municipalities; for the country: the sum of all local "
        "budgets.",
    },
    "lokalna_ulaganja": {
        "naziv": "Local budget investment (annual average)",
        "objasnjenje": "The part of expenditure that went into lasting assets: roads, buildings, "
        "kindergartens, equipment. It shows how much is being built, not just spent. We take the "
        "average of the last three years, because one large project can multiply a single year.",
        "napomena": "Expenditure on non-financial assets (roads, buildings, equipment), annual "
        "average of the last three years of budget outturn. For a county: the county and all its "
        "cities and municipalities.",
    },
    "saldo_lokalnog_proracuna": {
        "naziv": "Local budget surplus or deficit",
        "objasnjenje": "Revenue minus expenditure in the year. A plus is a surplus; a minus "
        "means more was spent than received, and the difference is covered by a loan or savings.",
        "napomena": "Revenue minus expenditure in the year (without borrowing and surplus "
        "carried over).",
    },
    "udio_pomoci_u_prihodima": {
        "naziv": "Share of grants in budget revenue",
        "objasnjenje": "Out of every €100 of revenue, how much the city or municipality received "
        "from the state, the EU or other budgets instead of collecting it itself. A high share "
        "means more dependence on others' money, but it also includes EU money for projects.",
        "napomena": "Grants from the state budget, the EU and other budgets (group 63) in total "
        "revenue (groups 6 and 7).",
    },
    "porez_na_dohodak": {
        "naziv": "Income tax paid",
        "objasnjenje": "How much tax residents paid on salaries, pensions and other income. This "
        "tax belongs to the city or municipality they live in and is its main own revenue.",
        "napomena": "Belongs to cities and municipalities; by the taxpayer's place of residence.",
    },
    "stopa_poreza_dohodak_niza": {
        "naziv": "Lower income tax rate",
        "objasnjenje": "The tax rate on income up to the threshold of the higher bracket, paid by "
        "most employees. It is set by the city or municipality, so a lower rate means more take-"
        "home pay.",
        "napomena": "The rate is set by the city or municipality. For a county and the country: "
        "average of cities and municipalities weighted by population.",
    },
    "stopa_poreza_dohodak_visa": {
        "naziv": "Higher income tax rate",
        "objasnjenje": "The tax rate on the part of income above the higher-bracket threshold, "
        "i.e. on higher salaries. It is also set by the city or municipality.",
        "napomena": "The rate is set by the city or municipality. For a county and the country: "
        "average of cities and municipalities weighted by population.",
    },
    "promjena_stope_niza": {
        "naziv": "Change of the lower income tax rate",
        "objasnjenje": "Whether the city or municipality changed its lower income tax rate this "
        "year, and by how many percentage points. A minus means the tax was cut.",
        "napomena": "Difference from last year, in percentage points.",
    },
    "porez_na_potrosnju": {
        "naziv": "Consumption tax",
        "objasnjenje": "A local tax on drinks sold in cafés and restaurants. The money goes to "
        "the city or municipality.",
        "napomena": "Local tax on drinks in hospitality; the highest rate where a range is set.",
    },
    "porez_na_nekretnine": {
        "naziv": "Property tax",
        "objasnjenje": "How much an owner pays per square metre a year for a flat or house where "
        "nobody lives permanently and which is not let long-term, e.g. a holiday home.",
        "napomena": "Annual amount per m²; the highest amount where a range is set.",
    },
    "kupoprodaje_nekretnina": {
        "naziv": "Property sales",
        "objasnjenje": "How many properties (flats, houses, land) were sold in the year. It shows "
        "how active the property market is.",
    },
    "porez_na_promet_nekretnina": {
        "naziv": "Real estate transfer tax (budget revenue)",
        "objasnjenje": "How much the city or municipality received from the tax the buyer of a "
        "property in its area pays. The more properties are sold and the dearer they are, the "
        "higher the amount.",
        "napomena": "Budget outturn, account 6134 (occasional property taxes), which for cities "
        "and municipalities is the real estate transfer tax. For a county: the county and all its "
        "cities and municipalities.",
    },
    "prihodi_od_imovine": {
        "naziv": "Revenue from non-financial assets",
        "objasnjenje": "How much the city or municipality earns from its property: renting out "
        "premises and land, concessions and fees for use.",
        "napomena": "Budget outturn, group 642: concession fees, lease and rent of property, fees "
        "for the use of property and other. For a county: the county and all its cities and "
        "municipalities.",
    },
    "pravne_osobe_aktivne": {
        "naziv": "Active legal entities",
        "objasnjenje": "How many active companies, associations, institutions and other legal "
        "entities there are. Sole traders are not included.",
    },
    "javna_nabava": {
        "naziv": "Public procurement contracts (5 years)",
        "objasnjenje": "How much the city or municipality contracted through public procurement "
        "in five years: works, goods and services such as roads, buildings, energy and "
        "maintenance.",
        "napomena": "Total value of contracts signed in five years by the administration of the "
        "city, municipality or county (EOJN RH contract register), without its institutions and "
        "companies; kuna converted at 7.5345. For a county: the county administration and all "
        "its cities and municipalities.",
    },
    "nabava_najveci_dobavljac": {
        "naziv": "Share of the largest supplier in public procurement",
        "objasnjenje": "What share of public procurement money went to one company, the one that "
        "received the most. A high share means reliance on one supplier; in small municipalities "
        "with few contracts this is more common and is not an irregularity in itself.",
        "napomena": "Value of contracts with the supplier with the most contracted money, divided "
        "by the total value of contracts in the same five years.",
    },
    "nabava_bez_objave": {
        "naziv": "Contracts awarded without prior publication",
        "objasnjenje": "What share of contracts was awarded without a public call to all "
        "bidders. The law allows this only in special cases, e.g. urgency or when only one "
        "bidder can do the job.",
        "napomena": "Share of the value of contracts from the negotiated procedure without prior "
        "publication in the total value of contracts in the same five years.",
    },
}

TIPOLOGIJA = {
    "naziv": "Type of city or municipality",
    "metoda": "Machine learning (k-means, 5 groups) on five features of all cities and "
    "municipalities: population (log), net income per resident (log), share of grants in budget "
    "revenue, budget revenue per resident (log) and average age of residents. Features are "
    "standardised; the most similar by profile are the five nearest in the same space.",
    "obiljezja": {
        "velicina": "population (log)",
        "dohodak": "net income per resident (log)",
        "pomoci": "share of grants in budget revenue",
        "prihodi": "budget revenue per resident (log)",
        "dob": "average age of residents",
    },
    "tipovi": {
        "sredista": {
            "naziv": "Larger cities and regional centres",
            "opis": "The largest communities with higher income; the budget is mostly funded by "
            "own revenue.",
        },
        "mali-stariji": {
            "naziv": "Small municipalities with an older population",
            "opis": "Very small and the oldest communities; with few residents the budget per "
            "resident is high, but a large part comes from grants.",
        },
        "samostalni": {
            "naziv": "Financially self-reliant communities",
            "opis": "High income and high own budget revenue, with grants only a small part.",
        },
        "ovisni": {
            "naziv": "Lower-income communities dependent on grants",
            "opis": "The lowest income of residents; more than half of the budget comes from the "
            "state budget, the EU and other grants.",
        },
        "prosjecni": {
            "naziv": "Average smaller cities and municipalities",
            "opis": "Close to the Croatian average in income and dependence on grants, with the "
            "lowest budget revenue per resident.",
        },
    },
}

DRZAVA = "Croatia"

ZUPANIJE = {
    "01": "Zagreb County",
    "02": "Krapina-Zagorje County",
    "03": "Sisak-Moslavina County",
    "04": "Karlovac County",
    "05": "Varaždin County",
    "06": "Koprivnica-Križevci County",
    "07": "Bjelovar-Bilogora County",
    "08": "Primorje-Gorski Kotar County",
    "09": "Lika-Senj County",
    "10": "Virovitica-Podravina County",
    "11": "Požega-Slavonia County",
    "12": "Brod-Posavina County",
    "13": "Zadar County",
    "14": "Osijek-Baranja County",
    "15": "Šibenik-Knin County",
    "16": "Vukovar-Srijem County",
    "17": "Split-Dalmatia County",
    "18": "Istria County",
    "19": "Dubrovnik-Neretva County",
    "20": "Međimurje County",
    "21": "City of Zagreb",
}

IZDAVATELJI = {
    "Državni zavod za statistiku": "Croatian Bureau of Statistics",
    "Državna geodetska uprava": "State Geodetic Administration",
    "HBOR": "HBOR (Croatian Bank for Reconstruction and Development)",
    "Hrvatska narodna banka": "Croatian National Bank",
    "Ministarstvo financija": "Ministry of Finance",
    "Ministarstvo regionalnoga razvoja i fondova Europske unije": "Ministry of Regional "
    "Development and EU Funds",
    "Narodne novine d.d. – Elektronički oglasnik javne nabave RH (objava: Open Contracting Data "
    "Registry)": "Narodne novine – Electronic Public Procurement Classifieds of Croatia "
    "(published by the Open Contracting Data Registry)",
    "Porezna uprava": "Tax Administration",
}

SERIJE = {
    "stanovnistvo": {
        "naziv": "Population (Croatian Bureau of Statistics estimate)",
        "napomena": "Mid-year estimate; includes migration, births and deaths.",
    },
    "nezaposlenost": {
        "naziv": "Registered unemployment rate",
        "napomena": "Annual average of monthly rates.",
    },
    "neto_dohodak": {
        "naziv": "Total income of residents",
        "napomena": "Net income (salaries, pensions and other, after tax and contributions); 2022 "
        "converted from kuna at the fixed rate of 7.5345.",
    },
    "porez_na_dohodak": {
        "naziv": "Income tax paid",
        "napomena": "Income tax by the taxpayer's place of residence; it belongs to the city or "
        "municipality.",
    },
    "kupoprodaje_nekretnina": {
        "naziv": "Properties sold",
        "napomena": "Number of sales per year (full years).",
    },
    "porez_na_promet_nekretnina": {
        "naziv": "Tax on property sales",
        "napomena": "Real estate transfer tax in the budget (account 6134). For a county: the "
        "county and its cities and municipalities together.",
    },
    "prihodi_od_imovine": {
        "naziv": "Revenue from leases and concessions",
        "napomena": "Revenue from non-financial assets in the budget (group 642). For a county: "
        "the county and its cities and municipalities together.",
    },
    "javna_nabava": {
        "naziv": "Public procurement contracts",
        "napomena": "Value of contracts of the city, municipality or county administration by "
        "year of signing (EOJN RH contract register).",
    },
}

# COFOG divisions, official English names.
FUNKCIJE = {
    "01": "General public services",
    "02": "Defence",
    "03": "Public order and safety",
    "04": "Economic affairs",
    "05": "Environmental protection",
    "06": "Housing and community amenities",
    "07": "Health",
    "08": "Recreation, culture and religion",
    "09": "Education",
    "10": "Social protection",
}

# meta.json `napomene`, by the Croatian text.
NAPOMENE = {
    "Granice su pojednostavljene za prikaz (županije ~400 m, općine ~80 m).": "Boundaries are "
    "simplified for display (counties ~400 m, municipalities ~80 m).",
    "EU projekti po gradovima i općinama raspoređeni su prema koordinatama projekta, a po "
    "županijama prema županiji navedenoj u izvoru.": "EU projects are assigned to cities and "
    "municipalities by project coordinates, and to counties by the county named in the source.",
    "Granice županija su probne (Natural Earth) dok ne obradimo DGU granice.": "County "
    "boundaries are provisional (Natural Earth) until the official boundaries are processed.",
    "Šifre gradova i općina su privremene (vidi data/areas.csv).": "City and municipality codes "
    "are provisional (see data/areas.csv).",
}

PRORACUNI_NAPOMENA = (
    "Outturn (not plan). County = the county budget and the budgets of all its cities and "
    "municipalities; country = the sum of all. Functions are for the latest year and exclude "
    "transfers to other budgets, so their sum is lower than total expenditure."
)

NABAVA_NAPOMENA = (
    "Contracts of the city, municipality or county administration from the EOJN RH contract "
    "register (without their institutions and companies). County: the county administration and "
    "all its cities and municipalities. Amounts in EUR, kuna converted at 7.5345."
)

EU_POZIVI_NAPOMENA = (
    "Indicative plans of calls for 2026 (Competitiveness and Cohesion, Integrated Territorial "
    "Programme: October 2026; Efficient Human Resources: 3rd amendment). Eligibility is inferred "
    "from the text of the plan; the exact conditions are in the call."
)

EU_PROGRAMI = {
    "PKK": "Competitiveness and Cohesion Programme 2021–2027",
    "ITP": "Integrated Territorial Programme 2021–2027",
    "ULJP": "Efficient Human Resources Programme 2021–2027",
}

EU_VRSTE = {
    "Otvoreni (privremeni)": "Open (time-limited)",
    "Otvoreni (trajni)": "Open (rolling)",
    "Ograničeni (trajni)": "Restricted (rolling)",
    "Ograničeni (privremeni)": "Restricted (time-limited)",
    "Ograničeni": "Restricted",
    "Otvoreni": "Open",
    "Izravna dodjela": "Direct award",
}

# Planned EU calls, by their Croatian name in the plan.
# fmt: off
EU_POZIVI = {
    "Nastavak podrške integracije sustava zdravstva i socijalne skrbi kroz unaprjeđenje "
    "dostupnosti usluga dugotrajne skrbi u zajednici": "Continued support for integrating health "
    "and social care by improving access to long-term care services in the community",
    "Podrška osnovnim školama za provedbu eksperimentalnog programa cjelodnevne škole, II.":
    "Support for primary schools running the experimental full-day school programme, II",
    "Podrška radu s darovitom djecom i učenicima": "Support for work with gifted children and "
    "pupils",
    "Razvoj održivog turizma kroz ulaganja u javnu turističku infrastrukturu": "Sustainable "
    "tourism through investment in public tourism infrastructure",
    "ITU - CIFood": "ITI – CIFood",
    "Tematske mreže za društveno-ekonomski razvoj": "Thematic networks for socio-economic "
    "development",
    "Modernizacija ustanova za provedbu cjelodnevne škole (CDŠ) u osnovnoškolskom obrazovanju":
    "Modernising primary schools for the full-day school programme",
    "Jačanje ciljanih intervencija u zajednici s ciljem prevencije iznenadne smrti":
    "Strengthening targeted community interventions to prevent sudden death",
    "Jednakost, uključivanje, participacija i integracija Roma - Pilot projekt pružanja usluga u "
    "zajednici - JUPI PILOT": "Equality, inclusion, participation and integration of Roma – "
    "pilot project of community services (JUPI PILOT)",
    "ITU - BIKE UP! - Širenje sustava javnih bicikala s popratnom biciklističkom "
    "infrastrukturom": "ITI – BIKE UP! Expanding the public bike system with cycling "
    "infrastructure",
    'ITU - Projekt "Preloška"': "ITI – “Preloška” project",
    "ITU - Rekonstrukcije zone kupališta Mornar": "ITI – Reconstruction of the Mornar bathing "
    "area",
    "ITU - Ulaganje u sportsko-rekreacijsku i zelenu infrastrukturu UP Vukovar": "ITI – "
    "Investment in sports, recreation and green infrastructure of the Vukovar urban area",
    "ITU-GREEN UPLOAD! - Razvoj zelene infrastrukture UP Zadar": "ITI – GREEN UPLOAD! Green "
    "infrastructure of the Zadar urban area",
    "ITU-Kulturna baština UA Osijek": "ITI – Cultural heritage of the Osijek urban agglomeration",
}
# fmt: on

_MJESECI_EN = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
_RIMSKI = "I II III IV V VI VII VIII IX X XI XII".split()
_MJESECI_GENITIV = [
    "siječnja", "veljače", "ožujka", "travnja", "svibnja", "lipnja",
    "srpnja", "kolovoza", "rujna", "listopada", "studenoga", "prosinca",
]  # fmt: skip


def godina_en(tekst: str | None) -> str | None:
    """Razdoblje podatka (meta.json `godina`) na engleskom: "2019.–2023." → "2019–2023",
    "stanje 30.9.2026" → "as of 30 Sep 2026", "IX. 2026." → "Sep 2026", "sredina 2025." →
    "mid-2025", "31. siječnja 2022" → "31 Jan 2022"."""
    if tekst is None:
        return None
    t = tekst.strip()
    t = re.sub(
        r"\b(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\.?",
        lambda m: f"{int(m[1])} {_MJESECI_EN[int(m[2]) - 1]} {m[3]}",
        t,
    )
    t = re.sub(
        r"\b(\d{1,2})\.\s*(" + "|".join(_MJESECI_GENITIV) + r")\s+(\d{4})\.?",
        lambda m: f"{int(m[1])} {_MJESECI_EN[_MJESECI_GENITIV.index(m[2])]} {m[3]}",
        t,
    )
    t = re.sub(
        r"\b(" + "|".join(sorted(_RIMSKI, key=len, reverse=True)) + r")\.\s*(\d{4})\.?",
        lambda m: f"{_MJESECI_EN[_RIMSKI.index(m[1])]} {m[2]}",
        t,
    )
    t = re.sub(r"\b(\d{4})\.", r"\1", t)
    t = re.sub(r"^stanje\s+", "as of ", t)
    t = re.sub(r"^sredina\s+", "mid-", t)
    return t


def napomena_poziva_en(tekst: str | None) -> str | None:
    """Napomena poziva iz eu_pozivi.py na engleskom."""
    if tekst is None:
        return None
    m = re.fullmatch(
        r"Samo za gradove i općine iz obuhvata (urbane aglomeracije|urbanog područja) (.+)\.",
        tekst,
    )
    if m:
        vrsta = "urban agglomeration" if m[1] == "urbane aglomeracije" else "urban area"
        return f"Only for cities and municipalities within the {m[2]} {vrsta}."
    raise SystemExit(f"Prijevodi: napomena poziva bez prijevoda: {tekst!r}")


def izracunaj(meta: dict, nizovi: dict, proracuni: dict, pozivi: dict, nabava: dict) -> dict:
    """Sadržaj en.json za izvoz koji build upravo piše. Zaustavlja build ako nešto što
    sučelje prikazuje nema prijevod."""
    nedostaje = []

    pokazatelji = {}
    for k, p in meta["pokazatelji"].items():
        en = POKAZATELJI.get(k)
        if not en or "naziv" not in en or "objasnjenje" not in en:
            nedostaje.append(f"pokazatelj {k}")
            continue
        if p.get("napomena") and "napomena" not in en:
            nedostaje.append(f"napomena pokazatelja {k}")
        pokazatelji[k] = {**en, "godina": godina_en(p.get("godina"))}

    for k in meta["teme"]:
        if k not in TEME:
            nedostaje.append(f"tema {k}")
    tip = meta.get("tipologija") or {}
    for k in tip.get("tipovi", {}):
        if k not in TIPOLOGIJA["tipovi"]:
            nedostaje.append(f"tip {k}")
    for k in tip.get("obiljezja", {}):
        if k not in TIPOLOGIJA["obiljezja"]:
            nedostaje.append(f"obilježje {k}")
    for n in meta["napomene"]:
        if n not in NAPOMENE:
            nedostaje.append(f"napomena: {n}")
    izdavatelji = {i["izdavatelj"].strip() for i in meta["izvori"].values()}
    for i in sorted(izdavatelji - set(IZDAVATELJI)):
        nedostaje.append(f"izdavatelj {i}")
    for k in nizovi["serije"]:
        if k not in SERIJE:
            nedostaje.append(f"niz {k}")
    for k in proracuni["funkcije"]:
        if k not in FUNKCIJE:
            nedostaje.append(f"funkcija {k}")
    for p in pozivi["pozivi"]:
        if p["vrsta"] not in EU_VRSTE:
            nedostaje.append(f"vrsta poziva {p['vrsta']}")
        if p["program"] not in EU_PROGRAMI:
            nedostaje.append(f"program {p['program']}")
    if nedostaje:
        raise SystemExit("Prijevodi: nedostaje engleski tekst za:\n  " + "\n  ".join(nedostaje))

    # Calls are added and renamed when the plans change; a missing name is shown in Croatian.
    bez_naziva = [p["naziv"] for p in pozivi["pozivi"] if p["naziv"] not in EU_POZIVI]
    for naziv in bez_naziva:
        print(f"  Poziv bez engleskog naziva (prikazuje se na hrvatskom): {naziv}")

    return {
        "verzija_formata": 1,
        "teme": {k: TEME[k] for k in meta["teme"]},
        "pokazatelji": pokazatelji,
        "napomene": [NAPOMENE[n] for n in meta["napomene"]],
        "tipologija": {
            "naziv": TIPOLOGIJA["naziv"],
            "metoda": TIPOLOGIJA["metoda"],
            "obiljezja": TIPOLOGIJA["obiljezja"],
            "tipovi": {k: TIPOLOGIJA["tipovi"][k] for k in tip.get("tipovi", {})},
        },
        "drzava": DRZAVA,
        "zupanije": ZUPANIJE,
        "izdavatelji": {i: IZDAVATELJI[i] for i in sorted(izdavatelji)},
        "serije": {k: SERIJE[k] for k in nizovi["serije"]},
        "funkcije": {k: FUNKCIJE[k] for k in proracuni["funkcije"]},
        "proracuni_napomena": PRORACUNI_NAPOMENA,
        "nabava": {"napomena": NABAVA_NAPOMENA, "razdoblje": godina_en(nabava["razdoblje"])},
        "eu_pozivi": {
            "napomena": EU_POZIVI_NAPOMENA,
            "programi": EU_PROGRAMI,
            "vrste": EU_VRSTE,
            "pozivi": {
                p["id"]: {
                    "naziv": EU_POZIVI.get(p["naziv"]),
                    "napomena": napomena_poziva_en(p["napomena"]),
                }
                for p in pozivi["pozivi"]
            },
        },
    }


def provjeri(en: dict, meta: dict) -> None:
    if set(en["pokazatelji"]) != set(meta["pokazatelji"]):
        raise SystemExit("Prijevodi: en.json i meta.json nemaju iste pokazatelje.")
    if len(en["zupanije"]) != 21:
        raise SystemExit("Prijevodi: nedostaju engleski nazivi županija.")
