"""Šifre i nazivi 21 županije (uključujući Grad Zagreb).

Šifre 01–21 su službene šifre županija (DZS), iste kao u oznakama ISO 3166-2:HR
(HR-01 … HR-21). Šifra se uvijek zapisuje kao tekst od dva znaka ("05", ne 5).
"""

ZUPANIJE: dict[str, tuple[str, str]] = {
    # šifra: (puni naziv, kratki naziv)
    "01": ("Zagrebačka županija", "Zagrebačka"),
    "02": ("Krapinsko-zagorska županija", "Krapinsko-zagorska"),
    "03": ("Sisačko-moslavačka županija", "Sisačko-moslavačka"),
    "04": ("Karlovačka županija", "Karlovačka"),
    "05": ("Varaždinska županija", "Varaždinska"),
    "06": ("Koprivničko-križevačka županija", "Koprivničko-križevačka"),
    "07": ("Bjelovarsko-bilogorska županija", "Bjelovarsko-bilogorska"),
    "08": ("Primorsko-goranska županija", "Primorsko-goranska"),
    "09": ("Ličko-senjska županija", "Ličko-senjska"),
    "10": ("Virovitičko-podravska županija", "Virovitičko-podravska"),
    "11": ("Požeško-slavonska županija", "Požeško-slavonska"),
    "12": ("Brodsko-posavska županija", "Brodsko-posavska"),
    "13": ("Zadarska županija", "Zadarska"),
    "14": ("Osječko-baranjska županija", "Osječko-baranjska"),
    "15": ("Šibensko-kninska županija", "Šibensko-kninska"),
    "16": ("Vukovarsko-srijemska županija", "Vukovarsko-srijemska"),
    "17": ("Splitsko-dalmatinska županija", "Splitsko-dalmatinska"),
    "18": ("Istarska županija", "Istarska"),
    "19": ("Dubrovačko-neretvanska županija", "Dubrovačko-neretvanska"),
    "20": ("Međimurska županija", "Međimurska"),
    "21": ("Grad Zagreb", "Grad Zagreb"),
}

assert len(ZUPANIJE) == 21
