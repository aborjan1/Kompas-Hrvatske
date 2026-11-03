# Kompas Hrvatske

Interaktivna karta Hrvatske koja na jednom mjestu prikazuje gospodarske i javne podatke po razinama Država → Županija → Grad. Rješenje za Datathon Portala otvorenih podataka, izazov C: Gospodarstvo i učinkovito upravljanje.

**Demo:** <https://aborjan1.github.io/Kompas-Hrvatske/>

## Kako odgovaramo na izazov C

Podaci o gospodarstvu i javnim financijama gradova, općina i županija postoje, ali su
razbacani po 45 skupova podataka 11 izdavatelja, u različitim formatima i s različitim
nazivima istih mjesta. Kompas ih povezuje po službenim šiframa i prikazuje na jednom mjestu,
uz izvor i objašnjenje svakog broja.

| Cilj izazova C | Kako ga Kompas ostvaruje |
| --- | --- |
| Smanjenje vremena i troška pronalaženja i obrade informacija | Proračun jedne općine po namjeni do sada je značio preuzimanje arhive Ministarstva financija, traženje datoteke županije i lista općine; usporedba sa sličnima i s dohotkom stanovnika još i spajanje s tablicama Porezne uprave i DZS-a. U Kompasu je to nekoliko klikova, za svih 556 gradova i općina. |
| Povezivanje lokalnih, prostornih, gospodarskih i administrativnih podataka | Proračuni (MFIN), porezi i dohodak (Porezna uprava), stanovništvo i gospodarstvo (DZS), EU projekti i planirani EU pozivi (MRRFEU), javna nabava (registar ugovora EOJN RH), krediti (HBOR), javne financije (HNB) i službene granice (DGU) spojeni po šiframa županija i gradova, prostorno i preko adresa. |
| Razvoj analitičkih alata i stvaranje nove vrijednosti | Rangovi, usporedbe sa sličnima, grafovi proračuna kroz godine i **tipologija gradova i općina strojnim učenjem** (k-means), **graf veza u javnoj nabavi** (koji dobavljači rade za koji grad i za koga još) i **EU pozivi za svaku općinu** uz usporedbu sa sličnima: informacije koje ne postoje ni u jednom izvornom skupu. |
| Poboljšanje postojećih dobara i usluga | Isti otvoreni podaci s Portala, ali povezani, objašnjeni jednostavnim riječima i s navedenim izvorom; izlazne datoteke su gotov izvedeni skup podataka za ponovnu uporabu. |
| Snižavanje operativnih troškova i administrativnog opterećenja | Gradovi, županije i ministarstva dobivaju usporedbu s drugima bez ručnog prikupljanja podataka. Statička arhitektura bez poslužitelja znači gotovo nulti trošak rada. |
| Povećanje produktivnosti u javnom sektoru i gospodarstvu | Analitičari, novinari, poduzetnici i investitori dobivaju profil bilo kojeg mjesta (dohodak, porezi, proračun, EU novac) za nekoliko sekundi, s poveznicom koja se može poslati. |

**Korisnici:** građani i lokalni vijećnici (kako stoji moj grad), službenici gradova i
općina (usporedba sa sličnima), ministarstva i agencije (regionalne razlike, učinak EU
fondova), novinari i istraživači, poduzetnici i investitori (gdje ulagati, porezi).

## Arhitektura

Statička aplikacija bez servera. Python unaprijed preuzme otvorene podatke (CKAN API
Portala i službene stranice izdavatelja), poveže ih i zapiše u JSON i GeoJSON datoteke, a
Vite + Svelte + Mapbox GL JS ih prikazuju u pregledniku. Standardi, integracija s javnim
sustavima i preduvjeti: [docs/arhitektura.md](docs/arhitektura.md).

## Dokumentacija

- [Arhitektura](docs/arhitektura.md) – slojevi, standardi, integracija s javnim sustavima, preduvjeti
- [Sučelje](docs/sucelje.md) – što aplikacija prikazuje i kako se koristi, sa snimkama zaslona
- [Pokretanje](docs/pokretanje.md) – PowerShell naredbe za web i obradu podataka, česti problemi
- [Podaci](docs/podaci-dokumentacija.md) – izvori, obrada i kontrola kvalitete
- [Alati](docs/alati.md) – korišteni alati s licencama i alati umjetne inteligencije
- [Tehnički opis web aplikacije](web/README.md) – stanje, URL, priče, rečenice

## Pokretanje (PowerShell)

Web aplikacija (potreban Node.js LTS):

```powershell
cd web
npm install
npm run dev      # http://localhost:5173
```

Obrada podataka (potreban Python 3.12):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r pipeline/requirements.txt

python pipeline/download.py   # preuzima sve potrebne izvore u data/raw/ (oko 1 GB)
python pipeline/build.py      # obrada → web/public/data/ (1–2 minute, s provjerama)
python -m pytest              # testovi i provjera datoteka za kartu
```

`download.py` preuzima skupove označene s `aktivno = da` u `data/sources.csv`, s portala
data.gov.hr (CKAN API) ili izravno sa službenih stranica izdavatelja. Već preuzete
datoteke preskače. Opis obrade je u [docs/provjera-skupova.md](docs/provjera-skupova.md),
a oblik izlaznih datoteka u [docs/format-podataka.md](docs/format-podataka.md).

## Struktura

```
pipeline/            Python: preuzimanje i obrada podataka
data/raw/            sirovi podaci (izvan Gita, skripta ih ponovno preuzima)
data/sources.csv     popis izvora podataka
web/                 Vite + Svelte aplikacija (vidi web/README.md)
docs/                dokumentacija i snimke zaslona
tests/               testovi obrade i provjera podataka za kartu
.github/workflows/   automatske provjere (podaci) i objava na GitHub Pages
```

## Izvori podataka

Rješenje koristi 45 skupova: 35 s [Portala otvorenih podataka](https://data.gov.hr) i 10
dopunskih izvora tijela javne vlasti (Ministarstvo financija, Ministarstvo regionalnoga
razvoja i fondova EU, DZS, registar ugovora EOJN RH). Cijela obrada podataka opisana je u
[docs/podaci-dokumentacija.md](docs/podaci-dokumentacija.md). Popis s izdavateljem, poveznicom, datumom preuzimanja i dozvolom
za svaki skup je u [docs/izvori-podataka.md](docs/izvori-podataka.md) (nastaje iz
[data/sources.csv](data/sources.csv)). Isti podaci su u `web/public/data/meta.json`, pa ih
aplikacija prikazuje uz svaki broj.

## Licenca

- **Kod** (Python, web aplikacija): [MIT](LICENSE).
- **Podaci** zadržavaju dozvolu svojih izdavatelja. Većina je pod
  [Otvorenom dozvolom](https://data.gov.hr/otvorena-dozvola) ili CC BY 4.0, uz obvezu
  navođenja izvora. Za skupove bez navedene dozvole navodi se izvor i napomena da su javno
  objavljeni. Pojedinačno: [docs/izvori-podataka.md](docs/izvori-podataka.md).
