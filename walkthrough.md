# SQL-mysteriet på Yrgo – genomgång

> ⚠️ **Spoilervarning!** Den här filen visar hela lösningen steg för steg. Försök gärna lösa mysteriet själv först och använd genomgången bara om du kör fast.

## Uppdraget

Ett brott har begåtts i Göteborg och polisen behöver din hjälp. Kommissarien gav dig brottsplatsrapporten, men du har lyckats tappa bort den. Du minns bara vagt att brottet var en **stöld** som skedde den **14 november 2025** i **Göteborg**.

Allt du behöver finns i databasen `yrgo_mystery`.

## Installation

Kör hela skriptet i MySQL 8.4, antingen från terminalen:

```bash
mysql -u root -p < yrgo_mystery.sql
```

eller genom att öppna `yrgo_mystery.sql` i MySQL Workbench och köra hela filen (blixtknappen).

Skriptet skapar databasen `yrgo_mystery` från början. Om databasen redan finns raderas den först, så du kan alltid köra skriptet igen för att börja om.

## Databasens tabeller

| Tabell | Innehåll |
|---|---|
| `crime_scene_report` | Polisens brottsplatsrapporter (datum, typ, beskrivning, stad) |
| `person` | Alla personer: namn, adress, personnummer och körkorts-id |
| `drivers_license` | Körkort: ålder, längd, ögonfärg, hårfärg och kön |
| `car` | Bilregistret: registreringsnummer, ägarens körkorts-id, märke och modell |
| `interview` | Utskrifter av polisförhör |
| `yrgo_card` | Yrgos passerkort: kortnummer, innehavare, korttyp och utbildning |
| `yrgo_access_log` | Logg över när passerkorten har använts i Yrgos dörrar |
| `event_checkin` | Incheckningar på evenemang i Göteborg |
| `income` | Årsinkomst per personnummer |
| `drone_operator` | Transportstyrelsens register över drönaroperatörer |
| `remote_id_signal` | Remote ID-signaler från drönare: tid, operatörs-id och positioner för drönare och pilot |
| `toll_passage` | Passager vid trängselskattekamerorna |
| `company` | Bolagsverkets företagsregister |
| `company_role` | Styrelseposter och andra roller i företagen |
| `lia_offer` | LIA-erbjudanden till Yrgos studenter |
| `solution` | Här kontrollerar du ditt svar |

Tabellerna hänger ihop så här:

- `person.license_id` → `drivers_license.id`
- `car.owner_id` → `drivers_license.id`
- `interview.person_id` → `person.id`
- `yrgo_card.person_id` → `person.id`
- `yrgo_access_log.card_id` → `yrgo_card.id`
- `event_checkin.person_id` → `person.id`
- `income.personal_number` → `person.personal_number`
- `drone_operator.person_id` → `person.id`
- `remote_id_signal.operator_id` → `drone_operator.operator_id` (när id:t går att läsa)
- `toll_passage.plate_number` → `car.plate_number` (utom för bilar som inte finns i registret)
- `company_role.org_number` → `company.org_number`
- `company_role.personal_number` → `person.personal_number`
- `lia_offer.card_id` → `yrgo_card.id`
- `lia_offer.org_number` → `company.org_number`

---

## Del 1: Hitta tjuven

### Steg 0 – Utforska databasen

Börja med att se vilka tabeller som finns och hur de ser ut:

```sql
USE yrgo_mystery;

SHOW TABLES;
DESCRIBE crime_scene_report;
```

### Steg 1 – Hitta brottsplatsrapporten

Vi vet datum, typ av brott och stad:

```sql
SELECT *
FROM crime_scene_report
WHERE date = '2025-11-14'
  AND type = 'stöld'
  AND city = 'Göteborg';
```

Resultat:

> Prototypen till examensprojektet ”Projekt Kråka” – en självflygande drönare – stals ur elektroniklabbet på Yrgo, Forskningsgången 3, natten innan examensmässan. Säkerhetskameran visar att det fanns två vittnen. **Det första vittnet bor i det sista huset på Hisingsgatan. Det andra vittnet, som heter Elin, bor någonstans på Lindholmsallén.**

Samma dag rapporterades också annan brottslighet i Göteborg och stölder i andra städer, så alla tre villkoren behövs.

### Steg 2 – Hitta vittnena

”Det sista huset” på gatan betyder det högsta husnumret. Sortera fallande och ta den första raden:

```sql
SELECT *
FROM person
WHERE address_street_name = 'Hisingsgatan'
ORDER BY address_number DESC
LIMIT 1;
```

| id | name | license_id | address_number | address_street_name |
|---|---|---|---|---|
| 16371 | Gustav Öberg | 318771 | 97 | Hisingsgatan |

Det andra vittnet heter Elin i förnamn. Använd `LIKE` med jokertecknet `%`:

```sql
SELECT *
FROM person
WHERE name LIKE 'Elin %'
  AND address_street_name = 'Lindholmsallén';
```

| id | name | license_id | address_number | address_street_name |
|---|---|---|---|---|
| 41529 | Elin Sjöberg | 490173 | 12 | Lindholmsallén |

### Steg 3 – Läs vittnesförhören

```sql
SELECT p.name, i.transcript
FROM interview i
JOIN person p ON p.id = i.person_id
WHERE i.person_id IN (16371, 41529);
```

**Gustav Öberg:**
> Jag hörde ett brak från Yrgo och såg en man springa ut med en stor låda under armen. Han hade ett passerkort i ett orange nyckelband, och sådana har bara de med labbehörighet. Kortnumret började på "48Z". Han hoppade in i en bil vars registreringsnummer innehöll "H 42".

**Elin Sjöberg:**
> Jag såg när det hände, och jag kände igen tjuven från Yrgo. Han gick förbi mig i entrén när jag var där på min kvällskurs måndagen den 10 november.

Nu har vi fem ledtrådar:

1. Tjuven är en **man**.
2. Hans passerkort har **labbehörighet**.
3. Kortnumret börjar på **48Z**.
4. Registreringsnumret innehåller **H 42**.
5. Han var på Yrgo den **10 november 2025**.

### Steg 4 – Undersök passerkorten

Vilka korttyper finns det?

```sql
SELECT DISTINCT card_type FROM yrgo_card;
```

Resultatet är `Student`, `Gäst`, `Labb` och `Personal`. Labbehörighet motsvaras alltså av korttypen `Labb`.

```sql
SELECT *
FROM yrgo_card
WHERE id LIKE '48Z%'
  AND card_type = 'Labb';
```

| id | person_id | name | card_type | program |
|---|---|---|---|---|
| 48Z55 | 67318 | Jonas Berglund | Labb | Inbyggda system |
| 48Z7A | 28644 | Viktor Lindqvist | Labb | Elektronikingenjör |
| 48ZQP | 53902 | Oscar Nyström | Labb | Automationstekniker |

Tre misstänkta. Vilka av dem var på Yrgo den 10 november?

```sql
SELECT c.id, c.name, a.access_date, a.time_in, a.time_out, a.door
FROM yrgo_card c
JOIN yrgo_access_log a ON a.card_id = c.id
WHERE c.id LIKE '48Z%'
  AND c.card_type = 'Labb'
  AND a.access_date = '2025-11-10';
```

| id | name | access_date | time_in | time_out | door |
|---|---|---|---|---|---|
| 48Z55 | Jonas Berglund | 2025-11-10 | 17:41:00 | 19:36:00 | Huvudentré |
| 48Z7A | Viktor Lindqvist | 2025-11-10 | 08:05:00 | 15:22:00 | Elektroniklabb |

Två personer kvar. Notera att Elin var på kvällskurs, och bara Jonas var på Yrgo på kvällen. Men vi behöver mer bevis.

### Steg 5 – Kontrollera registreringsnumret

```sql
SELECT p.name, dl.gender, car.plate_number, car.make, car.model
FROM car
JOIN drivers_license dl ON dl.id = car.owner_id
JOIN person p           ON p.license_id = dl.id
WHERE car.plate_number LIKE '%H 42%';
```

| name | gender | plate_number | make | model |
|---|---|---|---|---|
| Karin Ekberg | kvinna | BHH 421 | Kia | Niro |
| Jonas Berglund | man | KHH 42W | Volkswagen | Golf |
| Rasmus Dahlberg | man | RXH 42C | BMW | X3 |

Bara **Jonas Berglund** förekommer i båda listorna.

### Allt i en fråga

Alla ledtrådar kan kombineras i en enda fråga:

```sql
SELECT p.name, c.id AS card_id, car.plate_number
FROM person p
JOIN drivers_license dl ON dl.id = p.license_id
JOIN car                ON car.owner_id = dl.id
JOIN yrgo_card c        ON c.person_id = p.id
JOIN yrgo_access_log a  ON a.card_id = c.id
WHERE c.id LIKE '48Z%'
  AND c.card_type = 'Labb'
  AND a.access_date = '2025-11-10'
  AND car.plate_number LIKE '%H 42%'
  AND dl.gender = 'man';
```

| name | card_id | plate_number |
|---|---|---|
| Jonas Berglund | 48Z55 | KHH 42W |

### Steg 6 – Kontrollera svaret

```sql
INSERT INTO solution VALUES (1, 'Jonas Berglund');
SELECT value FROM solution;
```

> Grattis, du hittade tjuven! Men vänta, det finns mer... Om du vill ha en riktig utmaning kan du försöka ta reda på vem som egentligen låg bakom stölden. Läs förhöret med tjuven. Vill du göra det ännu svårare? Försök klara det med högst två SQL-frågor. Använd samma INSERT-sats för att kontrollera ditt svar.

---

## Del 2: Hitta hjärnan bakom stölden

### Steg 7 – Läs tjuvens förhör

```sql
SELECT transcript
FROM interview
WHERE person_id = 67318;
```

> Okej, okej, jag erkänner. Jag blev anlitad av en kvinna med gott om pengar. Jag vet inte vad hon heter, men hon är mellan 165 och 170 cm lång, har rött hår och kör en Volvo XC90. Jag vet att hon var på "Lindholmen Tech Mingel" tre gånger i oktober 2025. Hon ville ha ritningarna och koden till drönaren, och jag behövde pengarna.

Fråga 1 av 2 är förbrukad om du siktar på utmaningen med högst två frågor.

### Steg 8 – Hitta kvinnan

Körkorts- och bilregistret ger tre kandidater:

```sql
SELECT p.id, p.name, dl.height, dl.hair_color, car.make, car.model
FROM drivers_license dl
JOIN car      ON car.owner_id = dl.id
JOIN person p ON p.license_id = dl.id
WHERE dl.gender = 'kvinna'
  AND dl.hair_color = 'röd'
  AND dl.height BETWEEN 165 AND 170
  AND car.make = 'Volvo'
  AND car.model = 'XC90';
```

| id | name | height | hair_color | make | model |
|---|---|---|---|---|---|
| 19730 | Annika Holm | 166 | röd | Volvo | XC90 |
| 46058 | Lena Forsberg | 170 | röd | Volvo | XC90 |
| 88214 | Cecilia Wallin | 168 | röd | Volvo | XC90 |

Vem av dem var på Lindholmen Tech Mingel tre gånger i oktober? Använd `GROUP BY` och `HAVING`. Det här är fråga 2 av 2, där allt kombineras:

```sql
SELECT p.name, dl.height, i.annual_income, COUNT(*) AS antal_besok
FROM person p
JOIN drivers_license dl ON dl.id = p.license_id
JOIN car                ON car.owner_id = dl.id
JOIN event_checkin e    ON e.person_id = p.id
LEFT JOIN income i      ON i.personal_number = p.personal_number
WHERE dl.gender = 'kvinna'
  AND dl.hair_color = 'röd'
  AND dl.height BETWEEN 165 AND 170
  AND car.make = 'Volvo'
  AND car.model = 'XC90'
  AND e.event_name = 'Lindholmen Tech Mingel'
  AND e.date BETWEEN '2025-10-01' AND '2025-10-31'
GROUP BY p.id, p.name, dl.height, i.annual_income
HAVING COUNT(*) = 3;
```

| name | height | annual_income | antal_besok |
|---|---|---|---|
| Cecilia Wallin | 168 | 2450000 | 3 |

Fällor att se upp för:

- **Annika Holm** var bara på minglet en gång i oktober.
- **Lena Forsberg** har också varit där fyra gånger, men bara en av gångerna var i oktober. Utan datumfiltret kan hon se misstänkt ut.

Cecilia Wallins årsinkomst på 2 450 000 kr är dessutom den högsta i hela databasen. Det stämmer med ”en kvinna med gott om pengar”.

### Steg 9 – Kontrollera svaret

```sql
INSERT INTO solution VALUES (1, 'Cecilia Wallin');
SELECT value FROM solution;
```

> Grattis, du hittade hjärnan bakom stölden! Projekt Kråka är tillbaka på Yrgo i tid till examensmässan. Men vänta... Cecilia Wallins namn förekommer i en annan polisutredning, där hennes vittnesmål skickade polisen åt fel håll. Nu när vi vet att hon inte går att lita på kanske det fallet går att lösa. Sök efter henne i brottsplatsrapporterna!

### Extra: ett sista bevis

Cecilia Wallin hade ett gästkort på Yrgo. Se var det användes:

```sql
SELECT c.id, c.card_type, a.access_date, a.time_in, a.time_out, a.door
FROM yrgo_card c
JOIN yrgo_access_log a ON a.card_id = c.id
WHERE c.person_id = 88214;
```

| id | card_type | access_date | time_in | time_out | door |
|---|---|---|---|---|---|
| GX4T2 | Gäst | 2025-11-12 | 10:05:00 | 11:32:00 | Elektroniklabb |

Två dagar före stölden var hon alltså på ”studiebesök” i just elektroniklabbet.

---

## Del 3: Chalmersfallet

Cecilia Wallin har visat sig vara en lögnare. Men hon har också vittnat i en tidigare utredning. Om hon ljög även där kan vi kanske lösa det fallet också.

### Steg 10 – Hitta den gamla utredningen

Vi vet inte datum eller typ av brott, bara att Cecilia Wallins namn förekommer i rapporten:

```sql
SELECT *
FROM crime_scene_report
WHERE description LIKE '%Cecilia Wallin%';
```

| date | type | city |
|---|---|---|
| 2025-03-21 | stöld | Göteborg |

> En prototyp till ett nytt solid-state-batteri stals ur batterilabbet på Chalmers, Johanneberg, under kvällen. Huvudvittnet Cecilia Wallins signalement ledde ingenstans, och utredningen lades ned i brist på bevis.

Polisen letade alltså efter någon som stämde med Cecilias beskrivning, men hittade ingen. Om Cecilia ljög borde tjuven se ut precis tvärtom.

### Steg 11 – Hitta förhören

Rapporten nämner inte vilka som förhördes. Men alla som pratade om fallet borde ha nämnt Chalmers:

```sql
SELECT p.id, p.name, i.transcript
FROM interview i
JOIN person p ON p.id = i.person_id
WHERE i.transcript LIKE '%Chalmers%';
```

Fyra förhör dyker upp:

**Cecilia Wallin:**
> Ja, jag var på Chalmers den kvällen i mars, på Innovationsdagen. När jag gick mot parkeringen såg jag tjuven springa ut ur batterilabbet. Jag såg henne tydligt: det var en kvinna, kortare än jag, med blont hår. Och hon var definitivt inte en av besökarna på Innovationsdagen – hon kom utifrån.

**Sanna Lindgren** (väktare):
> Jag gick min kvällsrunda på Chalmers när larmet gick i batterilabbet. Jag sprang ut och såg tjuven hoppa in i en Tesla och köra iväg mot Gibraltargatan. Det var för mörkt för att se registreringsnumret eller hur personen såg ut.

**Mattias Hedlund** (doktorand):
> Jag jobbade sent i labbet bredvid på Chalmers den 21 mars. Hela byggnaden var låst för alla utom besökarna på Chalmers Innovationsdag – de hade fått tillfälliga besökskort som gick till labben. Så tjuven måste ha varit en av besökarna som checkade in den dagen.

**Tobias Magnusson:**
> Jag läste om batteristölden på Chalmers i GP, men jag vet ingenting mer än det.

Tobias Magnusson vet ingenting och kan strykas. Lägg märke till att Cecilia och Mattias säger emot varandra om huruvida tjuven var besökare. Det är en första varningsklocka.

### Steg 12 – Sortera ledtrådarna

Från de trovärdiga vittnena:

1. Tjuven körde en **Tesla** (Sanna).
2. Tjuven **checkade in på Chalmers Innovationsdag den 21 mars 2025** (Mattias).

Från Cecilia, som vi vet ljuger:

3. ”En kvinna”
4. ”Kortare än jag”
5. ”Med blont hår”
6. ”Inte en av besökarna”

För att kunna använda ”kortare än jag” behöver vi veta hur lång Cecilia är:

```sql
SELECT dl.height
FROM person p
JOIN drivers_license dl ON dl.id = p.license_id
WHERE p.name = 'Cecilia Wallin';
```

Hon är **168 cm**.

Vilka datum har evenemanget haft? Det är bra att kontrollera innan man filtrerar:

```sql
SELECT DISTINCT event_name, date
FROM event_checkin
WHERE event_name LIKE '%Chalmers%';
```

| event_name | date |
|---|---|
| Chalmers Innovationsdag | 2025-03-21 |
| Chalmers Innovationsdag | 2024-03-22 |

Evenemanget har alltså hållits två gånger. Datumet måste vara med i filtret.

### Steg 13 – Försök lita på Cecilia

Om vi tar Cecilias beskrivning för sann och kombinerar den med Sannas Tesla:

```sql
SELECT p.name
FROM person p
JOIN drivers_license dl ON dl.id = p.license_id
JOIN car                ON car.owner_id = dl.id
WHERE car.make = 'Tesla'
  AND dl.gender = 'kvinna'
  AND dl.height < 168
  AND dl.hair_color = 'blond';
```

**Inga rader alls!** Det finns ingen person i hela registret som stämmer med hennes beskrivning. Det blir inte bättre om vi lägger till evenemanget. Hennes vittnesmål pekar inte på någon.

### Steg 14 – Strunta i Cecilia

Om vi bara använder de trovärdiga vittnena:

```sql
SELECT p.name, dl.gender, dl.height, dl.hair_color, car.model
FROM person p
JOIN drivers_license dl ON dl.id = p.license_id
JOIN car                ON car.owner_id = dl.id
JOIN event_checkin e    ON e.person_id = p.id
WHERE car.make = 'Tesla'
  AND e.event_name = 'Chalmers Innovationsdag'
  AND e.date = '2025-03-21'
ORDER BY p.name;
```

| name | gender | height | hair_color | model |
|---|---|---|---|---|
| Daniel Falk | man | 191 | svart | Model Y |
| Erik Hellström | man | 183 | blond | Model 3 |
| Frida Nordin | kvinna | 159 | röd | Model 3 |
| Johanna Bergman | kvinna | 172 | svart | Model 3 |
| Malin Ekström | kvinna | 162 | brun | Model Y |
| Tobias Wikström | man | 165 | brun | Model Y |

Sex misstänkta. Det räcker inte.

### Steg 15 – Vänd på Cecilias lögner

Om allt Cecilia sa var tvärtemot sanningen är tjuven:

| Cecilia sa | Sanningen |
|---|---|
| en kvinna | en **man** |
| kortare än jag (168 cm) | **längre än 168 cm** |
| blont hår | **inte blont** hår |
| inte en besökare | **en besökare** (bekräftas av Mattias) |

Lägg ihop allt:

```sql
SELECT p.id, p.name, dl.gender, dl.height, dl.hair_color, car.plate_number, car.model
FROM person p
JOIN drivers_license dl ON dl.id = p.license_id
JOIN car                ON car.owner_id = dl.id
JOIN event_checkin e    ON e.person_id = p.id
WHERE car.make = 'Tesla'
  AND e.event_name = 'Chalmers Innovationsdag'
  AND e.date = '2025-03-21'
  AND dl.gender = 'man'
  AND dl.height > 168
  AND dl.hair_color <> 'blond';
```

| id | name | gender | height | hair_color | plate_number | model |
|---|---|---|---|---|---|---|
| 98888 | Daniel Falk | man | 191 | svart | LPN 19R | Model Y |

Fällor att se upp för:

- **Erik Hellström** är en lång man, men han är blond.
- **Tobias Wikström** är man men bara 165 cm.
- **Johanna Bergman** är lång och mörkhårig, men en kvinna.
- **Andreas Sundberg** (man, 188 cm, brunt hår, Tesla) stämmer med allt, utom att han var på Innovationsdagen 2024 och inte 2025. Den som glömmer datumfiltret får två träffar.

### Steg 16 – Läs tjuvens förhör

```sql
SELECT transcript
FROM interview
WHERE person_id = 98888;
```

> Okej, jag erkänner. Det var jag som tog batteriprototypen ur labbet i Johanneberg. Men det var inte min idé! Det var hon med det röda håret som kör en Volvo XC90 som planerade allt. Hon betalade mig 200 000 kronor och lovade att ge polisen en falsk beskrivning så att jag skulle gå fri.

Röd hårfärg och en Volvo XC90 – han pekar alltså också ut Cecilia Wallin. Hans förhör innehåller varken ordet ”Chalmers” eller Cecilias namn. Därför gick det inte att hitta genom en textsökning i steg 11.

### Steg 17 – Kontrollera svaret

```sql
INSERT INTO solution VALUES (1, 'Daniel Falk');
SELECT value FROM solution;
```

> Grattis, du löste även Chalmersfallet! Cecilia Wallins vittnesmål var lögn från början till slut, och nu kan både hon och hennes medhjälpare ställas inför rätta. Batteriprototypen är tillbaka på Chalmers. Men lugnet varar inte länge. Den 10 december står Älvsnabben plötsligt still mitt på Göta älv, och över vattnet svävar en drönare som ser exakt ut som Projekt Kråka. Läs brottsplatsrapporterna från den dagen!

---

## Del 4: Drönaren över älven

Projekt Kråka står inlåst i labbet på Yrgo. Ändå flyger en exakt kopia över Göta älv mitt i Göteborg.

### Steg 18 – Hitta rapporten

```sql
SELECT date, type, description
FROM crime_scene_report
WHERE date = '2025-12-10'
  AND city = 'Göteborg';
```

Tre rapporter dyker upp: en stöld av en plånbok, ett inbrott och den här:

| date | type |
|---|---|
| 2025-12-10 | olovlig drönarflygning |

> En drönare som ser exakt ut som Yrgos Projekt Kråka flög över Göta älv mellan Lindholmspiren och Stenpiren kl. 14.20–14.55. Älvsnabben fick stå still i över en halvtimme. Drönarens Remote ID-signal fångades upp, men operatörs-id:t gick bara att läsa delvis. **Enligt signalen stod piloten på parkeringen vid Lindholmspiren (latitud 57.7072, longitud 11.9372) under hela flygningen.** En parkeringsvakt på Lindholmspiren har hörts av polisen.

*Remote ID* är EU:s krav på att drönare ska sända ut operatörens id och positioner, även var piloten står. Spelet använder en förenklad version.

### Steg 19 – Läs parkeringsvaktens förhör

```sql
SELECT p.id, p.name, i.transcript
FROM interview i
JOIN person p ON p.id = i.person_id
WHERE i.transcript LIKE '%Lindholmspiren%';
```

**Moa Isaksson:**
> Jag jobbar som parkeringsvakt på Lindholmspiren. Den 10 december kom en bil in på parkeringen strax innan drönaren lyfte. Föraren tog fram en stor fjärrkontroll och stod sedan vid bilen och tittade ut över älven hela tiden. När drönaren hade landat lade hen in den i bagageluckan och körde därifrån. Jag hann inte se registreringsnumret. Men alla bilar till och från Lindholmen måste passera trängselskattekameran vid Lindholmsmotet.

Piloten kom alltså **med bil**, körde in **före 14.20** och körde ut **efter 14.55**.

### Steg 20 – Signalerna under flygningen

`received_at` är en `DATETIME`, så tidsfönstret kan skrivas med datum och klockslag. Flera drönare flög samtidigt, så gruppera per operatörs-id:

```sql
SELECT operator_id,
       MIN(received_at)       AS first_signal,
       MAX(received_at)       AS last_signal,
       ROUND(AVG(pilot_lat), 4) AS pilot_lat,
       ROUND(AVG(pilot_lon), 4) AS pilot_lon
FROM remote_id_signal
WHERE received_at BETWEEN '2025-12-10 14:20:00' AND '2025-12-10 14:55:00'
GROUP BY operator_id
ORDER BY first_signal;
```

| operator_id | first_signal | last_signal | pilot_lat | pilot_lon |
|---|---|---|---|---|
| SWE-OP-7?3?K2 | 2025-12-10 14:20:00 | 2025-12-10 14:55:00 | 57.7072 | 11.9372 |
| SWE-OP-?4H?2M | 2025-12-10 14:20:00 | 2025-12-10 14:48:30 | 57.6900 | 11.9161 |
| SWE-OP-SGY2Y846B | 2025-12-10 14:31:10 | 2025-12-10 14:55:00 | 57.7032 | 11.9132 |

Två av id:na är delvis oläsliga (`?`). Bara den första piloten stod på platsen som rapporten anger. Den andra stod i Majorna och flög en takinspektion.

**Extra:** MySQL kan räkna avståndet i meter med `ST_Distance_Sphere`. Observera att `POINT` tar longituden först:

```sql
SELECT DISTINCT operator_id
FROM remote_id_signal
WHERE received_at BETWEEN '2025-12-10 14:20:00' AND '2025-12-10 14:55:00'
  AND ST_Distance_Sphere(POINT(pilot_lon, pilot_lat), POINT(11.9372, 57.7072)) < 300;
```

Resultatet är `SWE-OP-7?3?K2`. Piloten i Majorna stod ungefär 2,3 km bort.

### Steg 21 – Sök i operatörsregistret

Varje `?` står för exakt ett okänt tecken. I `LIKE` matchar `_` exakt ett tecken, medan `%` matchar hur många tecken som helst:

```sql
SELECT o.operator_id, p.name, o.registered_date
FROM drone_operator o
JOIN person p ON p.id = o.person_id
WHERE o.operator_id LIKE 'SWE-OP-7_3_K2';
```

| operator_id | name | registered_date |
|---|---|---|
| SWE-OP-7A3XK2 | Sixten Mårtensson | 2023-04-02 |
| SWE-OP-7E3PK2 | Melvin Ekström | 2024-09-16 |
| SWE-OP-7R3MK2 | Andreas Sundberg | 2025-05-14 |
| SWE-OP-7T3BK2 | Tove Lundin | 2025-12-08 |

Fyra operatörer. Tove Lundin registrerade sig bara två dagar före flygningen, vilket ser misstänkt ut. Men det räcker inte som bevis.

Den som skriver `LIKE 'SWE-OP-7%3%K2'` får också med Patrik Söderberg, vars id `SWE-OP-7W31N0XK2` har det äldre, längre formatet.

### Steg 22 – Trängselskattekameran

Piloten måste ha passerat kameran vid Lindholmsmotet två gånger: in före 14.20 och ut efter 14.55. Det är två rader för samma bil, så tabellen behöver joinas med sig själv:

```sql
SELECT t_in.plate_number, t_in.passed_at AS drove_in, t_out.passed_at AS drove_out
FROM toll_passage t_in
JOIN toll_passage t_out ON t_out.plate_number = t_in.plate_number
WHERE t_in.station = 'Lindholmsmotet'  AND t_in.direction = 'in'
  AND t_in.passed_at  BETWEEN '2025-12-10 12:00:00' AND '2025-12-10 14:20:00'
  AND t_out.station = 'Lindholmsmotet' AND t_out.direction = 'ut'
  AND t_out.passed_at BETWEEN '2025-12-10 14:55:00' AND '2025-12-10 18:29:59'
ORDER BY drove_in;
```

Tolv bilar. Trängselskatt tas bara ut vardagar 06.00–18.29, och då registrerar kamerorna passagerna.

### Steg 23 – Lägg ihop allt

Från operatörs-id via person och bil till kameran:

```sql
SELECT p.name, o.operator_id, car.plate_number, car.make, car.model,
       t_in.passed_at AS drove_in, t_out.passed_at AS drove_out
FROM drone_operator o
JOIN person p            ON p.id = o.person_id
JOIN car                 ON car.owner_id = p.license_id
JOIN toll_passage t_in   ON t_in.plate_number = car.plate_number
JOIN toll_passage t_out  ON t_out.plate_number = car.plate_number
WHERE o.operator_id LIKE 'SWE-OP-7_3_K2'
  AND t_in.station = 'Lindholmsmotet'  AND t_in.direction = 'in'
  AND t_in.passed_at  BETWEEN '2025-12-10 12:00:00' AND '2025-12-10 14:20:00'
  AND t_out.station = 'Lindholmsmotet' AND t_out.direction = 'ut'
  AND t_out.passed_at BETWEEN '2025-12-10 14:55:00' AND '2025-12-10 18:29:59';
```

| name | operator_id | plate_number | make | model | drove_in | drove_out |
|---|---|---|---|---|---|---|
| Andreas Sundberg | SWE-OP-7R3MK2 | AHB 37T | Tesla | Model 3 | 2025-12-10 13:47:12 | 2025-12-10 15:08:40 |

Andreas Sundberg är mannen som stämde in på allt i Chalmersfallet utom årtalet.

Fällor att se upp för:

- **Sixten Mårtensson** körde in vid Lindholmsmotet 13.52 men ut igen redan 14.31, mitt under flygningen.
- **Melvin Ekström** körde in först 14.38, när drönaren redan var i luften.
- **Tove Lundin** var i stan, men passerade Tingstadstunneln och aldrig Lindholmsmotet.
- **Patrik Söderberg** passerar kameran precis som Andreas. Han försvinner bara om du använder `_` i stället för `%`.
- **Drönaren i Majorna** har också ett skadat id, men piloten stod 2,3 km bort.

### Steg 24 – Kontrollera svaret

```sql
INSERT INTO solution VALUES (1, 'Andreas Sundberg');
SELECT value FROM solution;
```

> Rätt! Andreas Sundberg – mannen som stämde in på allt i Chalmersfallet utom årtalet – är testpilot på Nordvind Drönarteknik AB, Cecilia Wallins bolag. ”Ritningarna kom från chefen. Hon sa att de var våra egna.” Projekt Kråka var borta en hel natt innan polisen hittade den. Det räckte för att kopiera allt. Cecilia sitter nu häktad, men någon fortsätter att sköta hennes affärer. Den 19 januari 2026 anmäler tolv studenter från Yrgo ett företag för bedrägeri. Läs brottsplatsrapporterna från den dagen!

Svaret godkänns bara om du redan har löst Chalmersfallet. Andreas var ju fel svar där.

---

## Del 5: Den falska LIA-platsen

Cecilia sitter häktad, men någon annan sköter hennes affärer.

### Steg 25 – Hitta rapporten

```sql
SELECT type, description
FROM crime_scene_report
WHERE date = '2026-01-19'
  AND city = 'Göteborg';
```

> Tolv studenter från Yrgo anmäler Kråkvind Innovation AB, Lindholmspiren 9. De erbjöds betald LIA men fick först skriva på ett sekretessavtal, ladda upp källkoden till sina examensprojekt för ”teknisk granskning” och betala 1 500 kronor för ”säkerhetsprövning”. På första LIA-dagen fanns bara ett tomt skrivbord i ett kontorshotell. Ingen svarar i telefon.

### Steg 26 – Företaget och offren

```sql
SELECT co.org_number, co.registered_date, COUNT(*) AS students, SUM(l.fee_paid) AS total
FROM company co
JOIN lia_offer l  ON l.org_number = co.org_number
JOIN yrgo_card c  ON c.id = l.card_id
WHERE co.name = 'Kråkvind Innovation AB'
GROUP BY co.org_number, co.registered_date;
```

| org_number | registered_date | students | total |
|---|---|---|---|
| 559742-6740 | 2025-12-02 | 12 | 18000 |

Företaget registrerades i december och tog 18 000 kronor av tolv studenter från Inbyggda system och Elektronikingenjör. Inget annat företag har tagit betalt för en LIA-plats.

### Steg 27 – Styrelsen

```sql
SELECT cr.role, cr.personal_number, p.name
FROM company_role cr
LEFT JOIN person p ON p.personal_number = cr.personal_number
WHERE cr.org_number = (SELECT org_number FROM company WHERE name = 'Kråkvind Innovation AB');
```

| role | personal_number | name |
|---|---|---|
| Styrelseledamot | 19470804-3734 | Åke Blomqvist |
| Suppleant | 19780326-2862 | NULL |

Suppleanten har ett personnummer som **inte finns** i personregistret. Med en vanlig `JOIN` hade den raden försvunnit helt.

### Steg 28 – Målvakten

Åke Blomqvist är 78 år. Hur många styrelser sitter han i?

```sql
SELECT p.name, COUNT(*) AS companies,
       MIN(co.registered_date) AS first, MAX(co.registered_date) AS last,
       MAX(i.annual_income) AS income
FROM company_role cr
JOIN company co    ON co.org_number = cr.org_number
JOIN person p      ON p.personal_number = cr.personal_number
LEFT JOIN income i ON i.personal_number = p.personal_number
GROUP BY p.id, p.name
HAVING COUNT(*) >= 5;
```

| name | companies | first | last | income |
|---|---|---|---|---|
| Åke Blomqvist | 7 | 2025-12-02 | 2025-12-18 | 142000 |
| Bengt Claesson | 6 | 1991-04-15 | 2019-02-11 | 365000 |

**Bengt Claesson** är en pensionerad revisor med familjeföretag som har startats under nästan 30 år på olika adresser. Åke Blomqvists sju företag registrerades däremot alla under två veckor i december, på samma adress på Lindholmspiren, och han har en låg inkomst. Han är en **målvakt**, en person som lånar ut sitt namn till bolag som någon annan driver.

### Steg 29 – Läs målvaktens förhör

```sql
SELECT i.transcript
FROM interview i
JOIN person p ON p.id = i.person_id
WHERE p.name = 'Åke Blomqvist';
```

> Jag fick 5 000 kronor för att skriva under några papper. Det var en trevlig dam i min trappuppgång som ordnade allt. Hon sa att det bara var en formalitet.

Om du svarar `Åke Blomqvist` får du veta att du är på rätt spår, men att någon annan ligger bakom.

### Steg 30 – Grannarna

Samma trappuppgång betyder samma gata **och** samma husnummer. Joina personregistret med sig själv på två kolumner:

```sql
SELECT n.name, n.personal_number
FROM person m
JOIN person n
  ON n.address_street_name = m.address_street_name
 AND n.address_number = m.address_number
 AND n.id <> m.id
WHERE m.name = 'Åke Blomqvist';
```

| name | personal_number |
|---|---|
| Edvin Nordström | 20061012-4273 |
| Annika Holm | 19780326-1481 |
| Camilla Sundqvist | 19591220-5605 |
| Selma Fransson | 19940707-2462 |

### Steg 31 – Vem gömmer sig bakom suppleanten?

Det falska personnumret `19780326-2862` har ett riktigt födelsedatum. Bara de sista fyra siffrorna är påhittade. Vilka är födda den dagen?

```sql
SELECT name, personal_number, address_street_name, address_number
FROM person
WHERE personal_number LIKE '19780326-%';
```

| name | personal_number | address_street_name | address_number |
|---|---|---|---|
| Annika Holm | 19780326-1481 | Delsjövägen | 22 |
| Astrid Nyberg | 19780326-9005 | Plantagegatan | 14 |

Bara den ena bor i Åkes trappuppgång. Allt i en fråga, där födelsedatumet jämförs med `LEFT()`:

```sql
SELECT n.name
FROM company co
JOIN company_role cr ON cr.org_number = co.org_number AND cr.role = 'Suppleant'
JOIN person n        ON LEFT(n.personal_number, 8) = LEFT(cr.personal_number, 8)
WHERE co.name = 'Kråkvind Innovation AB'
  AND n.address_street_name = 'Delsjövägen'
  AND n.address_number = 22;
```

| name |
|---|
| Annika Holm |

**Annika Holm** är den andra rödhåriga XC90-föraren från del 2.

### Steg 32 – Bekräfta: känner hon Cecilia?

Två incheckningar på samma evenemang samma dag:

```sql
SELECT e1.event_name, e1.date
FROM event_checkin e1
JOIN event_checkin e2 ON e2.event_id = e1.event_id AND e2.date = e1.date
WHERE e1.person_id = (SELECT id FROM person WHERE name = 'Annika Holm')
  AND e2.person_id = (SELECT id FROM person WHERE name = 'Cecilia Wallin');
```

| event_name | date |
|---|---|
| Lindholmen Tech Mingel | 2025-10-16 |

### Extra för experter: bevisa att personnumret är falskt

Svenska personnummer har en kontrollsiffra enligt Luhn-algoritmen. Siffrorna i `ÅÅMMDD-NNN` multipliceras omväxlande med 2 och 1, och siffersumman av produkterna avgör den sista siffran. En rekursiv CTE kan ta fram varje siffra:

```sql
WITH RECURSIVE pos AS (
    SELECT 1 AS n UNION ALL SELECT n + 1 FROM pos WHERE n < 9
),
digits AS (
    SELECT pn.personal_number,
           CAST(SUBSTRING(CONCAT(SUBSTRING(pn.personal_number, 3, 6),
                                 SUBSTRING(pn.personal_number, 10, 3)), pos.n, 1) AS UNSIGNED)
             * IF(pos.n % 2 = 1, 2, 1) AS product
    FROM (SELECT DISTINCT personal_number FROM company_role) pn
    CROSS JOIN pos
)
SELECT personal_number,
       (10 - SUM(product DIV 10 + product MOD 10) MOD 10) MOD 10 AS correct_check_digit,
       RIGHT(personal_number, 1) AS given_check_digit
FROM digits
GROUP BY personal_number
HAVING correct_check_digit <> given_check_digit;
```

| personal_number | correct_check_digit | given_check_digit |
|---|---|---|
| 19780326-2862 | 9 | 2 |

Av alla personnummer i `company_role` har bara suppleantens fel kontrollsiffra.

### Steg 33 – Kontrollera svaret

```sql
INSERT INTO solution VALUES (1, 'Annika Holm');
SELECT value FROM solution;
```

> Rätt! Annika Holm drev bluffbolagen åt Nordvind medan Cecilia satt häktad. Studenternas källkod skulle bli nästa version av Kråka 2. Studenterna får tillbaka sina avgifter, och Yrgo granskar numera alla LIA-företag i Bolagsverkets register. Hela nätverket kring Cecilia Wallin är avslöjat. Nu är det verkligen dags för en välförtjänt fika!

Svaret godkänns bara om du redan har löst drönarfallet. Annika var ju fel svar i del 2.

---

## Sammanfattning

**Yrgofallet**

| Roll | Namn |
|---|---|
| Vittne 1 | Gustav Öberg, Hisingsgatan 97 |
| Vittne 2 | Elin Sjöberg, Lindholmsallén 12 |
| Tjuv | **Jonas Berglund** (kort 48Z55, bil KHH 42W) |
| Hjärnan bakom stölden | **Cecilia Wallin** |

**Chalmersfallet**

| Roll | Namn |
|---|---|
| Vittne (väktare) | Sanna Lindgren |
| Vittne (doktorand) | Mattias Hedlund |
| Falskt vittne | Cecilia Wallin |
| Tjuv | **Daniel Falk** (Tesla Model Y, LPN 19R) |
| Hjärnan bakom stölden | **Cecilia Wallin** |

**Drönaren över älven**

| Roll | Namn |
|---|---|
| Vittne (parkeringsvakt) | Moa Isaksson |
| Pilot | **Andreas Sundberg** (operatörs-id SWE-OP-7R3MK2, bil AHB 37T) |
| Uppdragsgivare | Nordvind Drönarteknik AB, Cecilia Wallins bolag |

**Den falska LIA-platsen**

| Roll | Namn |
|---|---|
| Bluffbolag | Kråkvind Innovation AB, Lindholmspiren 9 |
| Målvakt | Åke Blomqvist, Delsjövägen 22 |
| Falsk suppleant | 19780326-2862 |
| Hjärnan bakom bedrägeriet | **Annika Holm**, Delsjövägen 22 |

## SQL-begrepp som används

- `SELECT`, `WHERE`, `AND`
- `ORDER BY ... DESC` och `LIMIT`
- `LIKE` med jokertecknet `%`, även för att söka i fritext
- `DISTINCT`
- `IN (...)` och `BETWEEN ... AND ...`
- `<>` (inte lika med) och `<`, `>`
- `JOIN` och `LEFT JOIN` över flera tabeller
- `GROUP BY`, `COUNT(*)` och `HAVING`
- `INSERT INTO`
- Att logiskt vända på villkor (negation)
- `LIKE` med jokertecknet `_` (exakt ett tecken)
- Tidsfönster på `DATETIME`-kolumner
- Att joina en tabell med sig själv (self-join), även på två kolumner
- `SUM`, `MIN` och `MAX`
- `LEFT JOIN` för att hitta rader som saknar motsvarighet
- Underfrågor i `WHERE`
- Strängfunktioner som `LEFT()`, `RIGHT()` och `SUBSTRING()`
- `ST_Distance_Sphere` (extra)
- `WITH RECURSIVE` (extra)

## Bra att veta

- Databasen använder den svenska sorteringsordningen `utf8mb4_sv_0900_ai_ci`. Därför behandlas å, ä och ö som egna bokstäver: `'stöld'` matchar inte `'stold'`. Jämförelser skiljer inte på stora och små bokstäver.
- Svaren i `solution` lagras som SHA-256-hashar, så de kan inte läsas direkt ur skriptet. Svarskontrollen bryr sig inte om stora/små bokstäver eller blanksteg i början och slutet.
- Svaren i del 4 och 5 godkänns bara när fallet före är löst. Om du laddar om databasen behöver du skriva in dina tidigare svar igen.
- Alla personer, händelser och företeelser i mysteriet är påhittade.
