# Rozpoznání SPZ

## Úvod

Cílem této ročníkové práce bylo navrhnout a zrealizovat kamerový systém, který dokáže rozpoznat obličej a který snímaný obraz přenáší pomocí wifi sítě na zobrazovací zařízení. Mým cílem bylo vytvořit systém pro rozpoznávání SPZ s funkcí simulace závory pomocí LED diody. Aplikace, využívající webkameru (nebo soubor nahraný z počítače), vytvoří obrázek, který následně vyhodnotí, zda obsahuje SPZ. Pokud ano, porovná SPZ se seznamem povolených SPZ, a pokud je nalezena shoda, LED dioda se rozbliká. Pokud ne, nic se nezmění.

Systém také umožňuje zobrazení historie SPZ, její smazání, a také zobrazení, přidávání a mazání seznamu povolených SPZ.

Systém je napsaný v Pythonu a používá Arduino Uno.

## Rozbor

Celý systém je postaven na Arduinu Uno, kde je jednoduchý obvod skládající se ze dvou drátků, odporu a LED diody. Arduino je napájeno přes USB-B port a připojeno k napájení pomocí USB-C kabelu.

## Systém

Software je napsaný v Pythonu a zajišťuje logiku rozpoznání SPZ. Používá následující knihovny:

- `os`
- `sys`
- `time`
- `json`
- `tkinter`
- `cv2`
- `numpy`
- `easyocr`
- `imutils`
- `serial`
- `PIL`
- `serial.tools.list_ports`

Druhá část systému je napsaná v jazyce Arduino, kde je jednoduchý skript pro ovládání LED diody v pravidelných intervalech.
## Nešla mi nahrát aplikace na github jinak než přes git lfs, protože byla moc velká mám ji u sebe. Pokud byste si ji chtěli exporovat po svém tak tady je návod
1. Otevřete command prompt
2. Jdete do slozky kde máte stazeny projket (cd vase\cesta\ksouboru)
3. Zadejte tento prikaz python -m PyInstaller --onefile --windowed --add-data "spravne_spz.json;." --add-data "spz_history.json;." --add-data "obrazky;obrazky" spz_rec.py
4. Ve stejne slozce se vam vytvori slozka dist a v ni bude .exe soubor na, který kliknete.  
## Jan Lukeš C3C
