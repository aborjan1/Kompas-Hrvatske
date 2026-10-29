# Kompas Hrvatske

Interaktivna karta Hrvatske koja na jednom mjestu prikazuje gospodarske i javne podatke po razinama Država → Županija → Grad. Rješenje za Datathon Portala otvorenih podataka, izazov C: Gospodarstvo i učinkovito upravljanje.

**Demo:** _(link na GitHub Pages, u izradi)_

## Arhitektura

Statička aplikacija bez servera. Python unaprijed obradi otvorene podatke u GeoJSON i JSON datoteke, a Vite + Svelte + MapLibre ih prikazuju u pregledniku.

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

Rješenje koristi 40 skupova: 35 s [Portala otvorenih podataka](https://data.gov.hr) i 5
dopunskih izvora tijela javne vlasti (Ministarstvo financija, Ministarstvo regionalnoga
razvoja i fondova EU, DZS). Popis s izdavateljem, poveznicom, datumom preuzimanja i dozvolom
za svaki skup je u [docs/izvori-podataka.md](docs/izvori-podataka.md) (nastaje iz
[data/sources.csv](data/sources.csv)). Isti podaci su u `web/public/data/meta.json`, pa ih
aplikacija prikazuje uz svaki broj.

## Licenca

- **Kod** (Python, web aplikacija): [MIT](LICENSE).
- **Podaci** zadržavaju dozvolu svojih izdavatelja. Većina je pod
  [Otvorenom dozvolom](https://data.gov.hr/otvorena-dozvola) ili CC BY 4.0, uz obvezu
  navođenja izvora. Za skupove bez navedene dozvole navodi se izvor i napomena da su javno
  objavljeni. Pojedinačno: [docs/izvori-podataka.md](docs/izvori-podataka.md).
