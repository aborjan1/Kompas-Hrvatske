# Kompas Hrvatske – alati

Popis alata korištenih za izradu rješenja, s licencama, kako traže pravila Datathona.
Verzije su one iz `web/package.json` i `pipeline/requirements.txt`.

## Web aplikacija

| Alat | Verzija | Licenca | Za što |
| --- | --- | --- | --- |
| [Svelte](https://svelte.dev/) | 5 | MIT | sučelje |
| [Vite](https://vite.dev/) | 8 | MIT | razvojni server i build |
| [Mapbox GL JS](https://github.com/mapbox/mapbox-gl-js) | 3.33 | Mapbox Terms of Service (vlasnička, **nije otvoreni kod**) | karta, globus, kamera |
| [@maplibre/maplibre-gl-style-spec](https://github.com/maplibre/maplibre-style-spec) | 26 | ISC | filtri stila karte |
| [Chart.js](https://www.chartjs.org/) | 4 | MIT | grafovi usporedbe |
| [Fuse.js](https://www.fusejs.io/) | 7 | Apache-2.0 | pretraga bez kvačica |

Podloga karte: Mapbox Outdoors (podaci © Mapbox, © OpenStreetMap suradnici, ODbL).

## Obrada podataka

| Alat | Licenca | Za što |
| --- | --- | --- |
| [Python](https://www.python.org/) | PSF | obrada |
| [pandas](https://pandas.pydata.org/) | BSD-3-Clause | tablice |
| [python-calamine](https://github.com/dimastbk/python-calamine) | MIT | čitanje .xlsx i .xls |
| [openpyxl](https://openpyxl.readthedocs.io/) | MIT | pisanje .xlsx |
| [GeoPandas](https://geopandas.org/) (Shapely, pyproj, pyogrio) | BSD-3-Clause, MIT | granice i točke, pretvorba HTRS96/TM → WGS84, pojednostavljenje granica |
| [requests](https://requests.readthedocs.io/) | Apache-2.0 | preuzimanje s portala i API-ja |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | BSD-3-Clause | API ključevi iz `.env` |
| [pdfplumber](https://github.com/jsvine/pdfplumber) | MIT | tablice iz PDF priopćenja DZS-a |
| [Ruff](https://docs.astral.sh/ruff/) | MIT | provjera i formatiranje koda |
| [pytest](https://pytest.org/) | MIT | testovi |

## Razvoj i objava

| Alat | Licenca | Za što |
| --- | --- | --- |
| [Git](https://git-scm.com/) | GPL-2.0 | verzije koda |
| [GitHub](https://github.com/), GitHub Actions, GitHub Pages | usluga | javni repozitorij, automatski build i objava demo verzije |
| [Visual Studio Code](https://code.visualstudio.com/) | MIT (izvorni kod) | uređivanje koda |
| [Google Chrome](https://www.google.com/chrome/) (headless) | vlasnička | automatske provjere izgleda, tipkovnice i snimke zaslona |

## Alati umjetne inteligencije

| Alat | Tko | Za što |
| --- | --- | --- |
| [Claude](https://www.anthropic.com/claude) (Anthropic), kroz Claude Code | svi članovi tima | pomoć pri pisanju i pregledu koda (obrada podataka, karta, sučelje), testova i dokumentacije |

Funkcionalnosti, izbor podataka i dizajn odredio je tim. Svaku promjenu koju je predložio AI
alat član tima je pregledao, isprobao i tek onda objavio.
