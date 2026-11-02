# Kompas Hrvatske – pokretanje

Upute za Windows i PowerShell. Projekt ima dva dijela: **web aplikaciju** (`web/`) i
**obradu podataka** (`pipeline/`). Za pregled i razvoj aplikacije dovoljna je web
aplikacija: gotovi podaci su već u repozitoriju (`web/public/data/`).

## Preduvjeti

| Alat | Verzija | Za što |
| --- | --- | --- |
| [Git](https://git-scm.com/) | bilo koja novija | preuzimanje koda |
| [Node.js](https://nodejs.org/) | LTS, 22 ili noviji | web aplikacija |
| [Python](https://www.python.org/) | 3.12 ili noviji | samo za obradu podataka |

```powershell
git clone https://github.com/aborjan1/Kompas-Hrvatske.git
cd Kompas-Hrvatske
```

## Web aplikacija

Sve naredbe za web pokreću se **u mapi `web`**.

```powershell
cd web
npm install
```

Karta koristi podlogu Mapbox, za koju treba pristupni token. Napravi besplatni račun na
<https://account.mapbox.com/>, kopiraj javni token (počinje s `pk.`) i upiši ga u
`web/.env.local`. Ta datoteka ne ide u Git.

```powershell
Copy-Item .env.example .env.local
notepad .env.local      # upiši VITE_MAPBOX_TOKEN=pk....
```

Razvoj (promjene u kodu odmah se vide u pregledniku):

```powershell
npm run dev             # http://localhost:5173
```

Produkcijska verzija, ista kao na GitHub Pages:

```powershell
npm run build           # izlaz u web/dist/
npm run preview         # http://localhost:4173
```

U produkcijskoj verziji radi i zagrijavanje za prezentaciju:
`http://localhost:4173/?zagrij` (vidi [sucelje.md](sucelje.md#prezentacija)).

## Obrada podataka

Potrebna samo kad se podaci preuzimaju ili osvježavaju. Pokreće se **iz korijena
repozitorija**.

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r pipeline/requirements.txt

python pipeline/download.py   # preuzima izvore u data/raw/ (oko 1 GB)
python pipeline/build.py      # obrada → web/public/data/ (1–2 minute, s provjerama)
python -m pytest              # testovi i provjera datoteka za kartu
```

Za Sudski registar i SRDI potrebni su ključevi u datoteci `.env` u korijenu (predložak:
`.env.example`). Detalji obrade su u
[podaci-dokumentacija.md](podaci-dokumentacija.md#10-pokretanje).

## Objava

Svaki push na granu `main` automatski builda aplikaciju i objavljuje je na
<https://aborjan1.github.io/Kompas-Hrvatske/> (`.github/workflows/pages.yaml`). Token za kartu
na objavljenoj stranici čita se iz GitHub tajne `VITE_MAPBOX_TOKEN` i ograničen je na tu
adresu. Uz to se pri svakom pushu pokreću provjere podataka (`.github/workflows/podaci.yaml`).

## Česti problemi

| Poruka ili simptom | Uzrok i rješenje |
| --- | --- |
| `npm error enoent … package.json` | Naredba je pokrenuta u korijenu repozitorija. Prvo `cd web`. |
| `Port 5173 is already in use` | Već radi jedan dev server (npr. u drugom terminalu). Zatvori ga ili otvori adresu koju Vite ispiše. |
| Karta je prazna, u konzoli `VITE_MAPBOX_TOKEN is missing` | Nema tokena u `web/.env.local`. Upiši ga i ponovno pokreni `npm run dev`. |
| `Activate.ps1 cannot be loaded … running scripts is disabled` | PowerShell blokira skripte. Jednom pokreni `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| `py` nije prepoznat | Python nije instaliran ili nije u PATH-u. Instaliraj ga s python.org i označi „Add python.exe to PATH”. |
