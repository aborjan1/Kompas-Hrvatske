# Kompas Hrvatske – karta

Kako je karta složena: podloga, slojevi, kamera, podaci, predmemorija i licence. Za
pokretanje vidi [pokretanje.md](pokretanje.md), za sučelje [sucelje.md](sucelje.md), za
format podataka [format-podataka.md](format-podataka.md). Kod je u `web/src/map/`.

## Pregled

Karta je [Mapbox GL JS](https://docs.mapbox.com/mapbox-gl-js/) sa stilom **Outdoors**
(`mapbox://styles/mapbox/outdoors-v12`): reljef, globus i atmosfera su već u stilu.
`createMap.js` stvara kartu, a `MapView.svelte` je tanki Svelte omotač koji na nju dodaje
naše slojeve i spaja ih sa stanjem.

Karta i paneli nikad ne zovu jedni druge. Oboje čitaju iste storeove:

| Store | Datoteka | Što karta iz njega uzima |
| --- | --- | --- |
| `view` | `src/state.js` | razina i područje → kamera; klik na kartu zove `selectArea()` |
| `indicator` | `src/data/indicator.js` | brojke po šifri, boje i naslov legende |
| `odabir` | `src/data/podaci.js` | županija odabranog grada (za sloj gradova i općina) |
| `euProjekti` | `src/data/euProjekti.js` | je li sloj EU projekata uključen i zbrojevi po gradu |
| `ukljuceniFiltri` | `src/data/gradskiPrikaz.js` | filtri gradskog prikaza Zagreba i Rijeke |

Prelazak mišem i oblačić su unutarnji posao karte (`hover.js`) i ne idu u stanje.

| Datoteka | Sadržaj |
| --- | --- |
| `config.js` | stil, token, uvodni let, granice Hrvatske, raspon zuma, adrese podataka |
| `createMap.js` | stvaranje karte, nazivi na hrvatskom, zaključavanje kamere, isključivanje unosa |
| `MapView.svelte` | slojevi, kamera (`focusOn`), klikovi, oblačići, legenda |
| `countyLayer.js` | županije: boje po razredima (`quantileClasses`, `colorExpression`) |
| `jlsLayer.js` | gradovi i općine otvorene županije, odabrani grad istaknut |
| `euLayer.js` | krugovi EU projekata, jedan po gradu ili općini |
| `cityLayers.js` | gradski prikaz Zagreba i Rijeke: satelit i 4 filtra |
| `spaceMask.js` | svemir oko Hrvatske i sjaj uz obalu i granicu |
| `labels.js` | skriva nazive mjesta i zanimljivosti izvan Hrvatske |
| `hover.js` | isticanje i oblačić za bilo koji sloj |
| `legend.js` | legenda kao Mapbox kontrola |
| `warmUp.js` | zagrijavanje za prezentaciju (`?zagrij`) |
| `geometry.js` | okviri područja, pojednostavljeni obris Hrvatske |

## Slojevi

Redom odozdo prema gore:

| Sloj | Izvor | Kada se vidi |
| --- | --- | --- |
| Podloga Outdoors (kopno, more, reljef, ceste) | Mapbox | uvijek |
| Županije (`zupanije-fill`, rub, isticanje) | `zupanije.geojson` | obojane na razini države; na razini županije samo ako tema nema pokazatelj za gradove |
| Gradovi i općine (`jls-fill`, rub, isticanje, odabrani) | `jls/<šifra>.geojson` | u otvorenoj županiji; odabrani grad ima tamni rub i bijeli halo, ostali su izblijeđeni |
| EU projekti (`eu-projekti-krugovi`) | `tocke/eu-projekti.geojson` | kad je uključen gumb „EU projekti”; površina kruga prema iznosu iz EU |
| Satelit (`grad-satelit`) i zone, četvrti | Mapbox satelit, `gradovi/` | u gradskom prikazu Zagreba i Rijeke |
| Nazivi iz podloge | Mapbox | izvan Hrvatske skriveni (`labels.js`, osim imena država) |
| Svemir (`svemir-maska`) i sjaj (`svemir-sjaj`) | `svemir.geojson` | nakon uvodnog leta; sve izvan hrvatskog kopna postaje zvjezdano nebo |
| Obrub grada (`grad-obrub-rub`, `grad-obrub`) | `jls/<šifra>.geojson` | u gradskom prikazu, iznad satelita i cesta |
| Točkice gradskog prikaza | `gradovi/` | iznad svega, da ih ceste i nazivi ne skrivaju |

Naši slojevi područja umeću se ispred prvog sloja natpisa iz stila (`beforeId`). U stilu
Outdoors taj je sloj rano, pa su ceste iznad naših boja. Točkice gradskog prikaza dodaju se
bez `beforeId`, na sam vrh.

**Gradski prikaz** otvara se sam kad se odabere Zagreb (`01333`) ili Rijeka (`03735`)
(`GRADOVI` u `gradskiPrikaz.js`). Satelit se postupno pojavi i nestane (0,8 s). Filtri:

| Filtar | Zagreb | Rijeka |
| --- | --- | --- |
| Ekonomska područja | 17 četvrti po udjelu gospodarske površine | – |
| Poslovne zone | zone iz planova (neizgrađene iscrtkane), napuštene površine | – |
| Javna ulaganja | kapitalna ulaganja 2023. i 2024. | – |
| Gradska imovina | prazni prostori i garaže, tržnice, gradska društva | prostori u zakupu |

Sve lokacije su iste točkice; iznos i adresa su u oblačiću. Datoteka filtra učitava se kad
se filtar prvi put uključi.

**Svemir.** Maska je unaprijed izračunat poligon: okolica Hrvatske (10° Z – 50° I,
25° – 65° S) bez hrvatskog kopna i otoka. Prikazuje se pri prvom slijetanju kamere i
blago se pojavi (1,5 s). Rubovi rupa u maski dobivaju plavi sjaj.

## Kamera

- **Uvod.** Karta se otvara na globusu (`INTRO_START`) i čim se nacrta leti 6 s na
  područje iz adrese, obično cijelu Hrvatsku. Gumb „Preskoči uvod” ili Esc odmah slijeće.
- **Smanjeno kretanje.** Letovi nisu `essential`, pa Mapbox pri `prefers-reduced-motion`
  skače umjesto da leti. Prijelazi satelita i svemira tada su odmah.
- **Let i zaključavanje** (`focusOn` u `MapView.svelte`). Prije leta zaustavi se prethodni
  let, skinu se ograničenja i isključi korisnički unos (scroll, povlačenje, tipkovnica,
  dodir), jer bi let prekinut usred puta ostavio kameru otključanu. Nakon slijetanja
  `lockToView()` postavi `maxBounds` na kadar, proširen za 5 % sa svake strane, i
  `minZoom` na trenutni zum. Proširenje je potrebno: s granicom točno veličine kadra zum
  oko kursora izvan sredine zapne prije minimuma.
- **Odzumiravanje na višu razinu.** Kad je kamera na najmanjem zumu, još malo scrollanja
  prema van (`PULL_TO_LEAVE`) odabire višu razinu: grad → županija → Hrvatska.
- **Raspon zuma.** Do `MAX_ZOOM` (10,25, cijeli grad); u gradskom prikazu do
  `CITY_MAX_ZOOM` (13, kvart). Najveći zum spušta se tek kad kamera izađe iz grada, inače
  bi kamera skočila.
- **Bez naginjanja i okretanja**: `maxPitch: 0`, isključeni `dragRotate`, `touchPitch` i
  okretanje dodirom i tipkovnicom. Gumb kompasa je skriven.
- **Početak.** Osvježavanje i vraćeni tab kreću od cijele Hrvatske; otvoreni link vodi na
  područje iz adrese (`src/url.js`).

## Podaci koje karta učitava

| Datoteka (`web/public/data/`) | Kada |
| --- | --- |
| `zupanije.geojson` | na startu |
| `svemir.geojson` | na startu |
| `jls/<šifra županije>.geojson` | kad se otvori županija |
| `tocke/eu-projekti.geojson` (~3,6 MB) | prvi put kad se uključi „EU projekti” |
| `gradovi/<grad>/…` | prvi put kad se uključi filtar u gradskom prikazu |

Brojke za boje karta ne čita sama: dolaze iz `meta.json`, `zupanije.json` i `jls.json`
preko storea `indicator`. Opis svih datoteka je u [format-podataka.md](format-podataka.md).

`svemir.geojson` je jednom napravljen iz unije 21 županije (`zupanije.geojson`), oduzete od
okolnog pravokutnika, i spremljen kao gotova datoteka. Ako se zadrži, treba ga premjestiti
u `pipeline/` i raditi iz službene državne granice DGU-a (razina `1stOrder` u
`pipeline/granice.py`).

## Predmemorija

- **U posjetu**: `maxTileCacheSize: 2000` drži sve viđene dijelove karte u memoriji.
- **Između posjeta**: service worker `web/public/sw.js` 30 dana čuva Mapbox dijelove karte,
  fontove, ikone i satelit. Iz ključa briše parametar `sku`, koji Mapbox mijenja pri svakom
  učitavanju. Radi samo u objavljenoj verziji (`npm run build` + `npm run preview` ili
  GitHub Pages), ne u `npm run dev`.
- **Zagrijavanje za prezentaciju**: `http://localhost:4173/?zagrij` (ili isti dodatak na
  objavljenoj stranici) skine sve dijelove karte nad Hrvatskom do zuma 10 (~500 dijelova,
  ~40 MB, 20–30 s) u predmemoriju. Napredak piše gore lijevo. Treba ga napraviti na
  računalu i u pregledniku s kojeg se prezentira.

## Podloge i licence

| Što | Izvor | Uvjeti |
| --- | --- | --- |
| Podloga i nazivi | Mapbox Outdoors, © Mapbox © OpenStreetMap | besplatno 50.000 učitavanja karte mjesečno; logo i navođenje obavezni |
| Satelit u gradskom prikazu | Mapbox Static Tiles (`styles/v1/mapbox/satellite-v9/tiles/512/…`), © Mapbox © Maxar | zasebna kvota Static Tiles API-ja |
| Granice županija, gradova i općina | Državna geodetska uprava | Otvorena dozvola; izvor, datum preuzimanja i dozvola u gumbu „i” na karti |
| EU projekti | vidi [format-podataka.md](format-podataka.md) | |

Satelit ide preko Static Tiles API-ja jer `mapbox://mapbox.satellite` (v4 raster) na našem
planu vraća 429.

**Token.** Javni Mapbox token (`pk.…`) završi u stranici, pa je ograničen po adresi:

- razvojni token u `web/.env.local`, dopušten na `http://localhost:5173` i
  `http://localhost:4173`;
- produkcijski token u GitHub tajni `VITE_MAPBOX_TOKEN`, dopušten samo na
  `https://aborjan1.github.io` (`.github/workflows/pages.yaml`).

## Poznata ograničenja

- **Prijelaz boje.** Mapbox pada („Cannot read properties of undefined (reading 'r')”) kad
  stapa običnu boju u boju po području (`feature-state`). Zato je `colorExpression()` uvijek
  izraz po području, a slojevi boja postavljaju `fill-color-transition` na
  `FILL_COLOR_NO_BLEND` (bez stapanja). Isto vrijedi za svaki novi sloj koji boji po
  vrijednosti.
- **Jedan razred.** `step` bez ijednog praga Mapbox odbija, pa jedan razred (Grad Zagreb ima
  samo jedan grad) postaje jedna boja.
- **Nazivi država** su na lokalnom jeziku i pismu (npr. Srbija ćirilicom).
- **Pomorska granica** se ne crta; stil ima samo kopnene granice, a svemir počinje na obali.
- **EU projekti** su smješteni u središte grada, ne na adresu, pa je jedan krug po gradu
  sve što podaci smiju pokazati. Sjedište korisnika (npr. ministarstva u Zagrebu) napuhuje
  iznos.
- **Nazivi na obali** (Zadar, Split) mogu biti djelomično prekriveni svemirom.

## Kako dodati novi sloj

1. Napravi modul u `web/src/map/` po uzoru na `euLayer.js`: `createXLayer(map)` dodaje izvor
   (`promoteId` ili `generateId` ako treba isticanje) i slojeve, vraća `show` i `hide`.
2. Ako sloj boji po vrijednosti, koristi `colorExpression()` i `FILL_COLOR_NO_BLEND`.
3. U `MapView.svelte` ga stvori u `map.on('load')` i spoji sa storeom koji kaže kad se vidi.
   Karta ne smije sama mijenjati panele: ako treba gumb, stanje ide u store u `src/data/`.
4. Oblačić: `addHoverTooltip(map, { layerId, source, describe, yieldTo })`. Slojevi koji su
   ispod ga prepuštaju novom sloju preko `yieldTo`.
5. Klik: ako sloj leži iznad županija ili gradova, njihovi klikovi moraju ga preskočiti
   (`claimedBy` u `MapView.svelte`).
6. Novu datoteku podataka opiši u [format-podataka.md](format-podataka.md).
