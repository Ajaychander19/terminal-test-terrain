# Évolution du programme

## Semaine 1

### Objectif

Analyser le fonctionnement du programme, comprendre son architecture.
Introduction aux formats de fichier.

### Programme

Programme d'analyse du réseau 4G, prend en charge le format Zk-Samp.

4 étapes de fonctionnement :

1. **Configuration** : on choisit le répertoire de production des fichiers.


2. **Field-test \*.csv to \*.pcap and \*.json conversion** : lecture du fichier Zk-Samp, décodage. Production de
fichiers textes temporaires pour chaque dissecteur Wireshark (= *parsers* de paquet). Appel de `text2pcap` pour en 
faire des fichiers pcap. Fusion des fichiers temporaires `.pcap` avec `mergecap`. Ré-ordonnancement des paquets avec 
`reordercap` par horodatage ; obtention du fichier `.pcap` final. Production fichier JSON temporaire depuis `.pcap` 
final avec `tshark`. Ajout à ce fichier des données de géolocalisation ; production JSON `C_...`, contenant les données 
des paquets SIB et de chaque mesure.


3. **Cartoradio File Conversion** : production de fichiers "sites" et "zones" JSON pour chaque opérateur à partir de 
fichiers CSV de Cartoradio. Les fichiers "sites" donnent des informations sur les stations de bases (numéro, exploitant,
géoloc...), les fichier "zones" permettent la description des cellules associées. On se base sur 2 fichiers Cartoradio :
`Antennes_Emetteurs_Bandes_Cartoradio.csv`, contenant des informations sur les identifiants de stations de base, leur 
mise en service, les fréquences..., et `Sites_Cartoradio.csv` contenant les géolocalisations de ces stations de base, 
les adresses, les terrains utilisés...  On récupère les données de ces fichiers avec la bibliothèque `pandas`, permettant notamment d'organiser les données 
suivant  le modèle relationnel (`DataFrame`). On utilise alors une jointure naturelle pour lier les données, puis on les 
groupe par opérateur. On génère pour chaque opérateur 2 fichiers : un fichier `sites` (CSV) qui contient les 
informations de localisation et d'exploitant des stations de bases, et un fichier `Zone` (JSON) contenant les 
informations d'orientation des antennes, utiles pour calculer l'étendue de la cellule 4G.


4. **Cell Association Processing** : calcul du fichier JSON d'association utilisé par l'interface de visualisation. 
On lie les données du fichier `C_...` (RSRP, TAC, PCI...) avec celles du fichier `sites` (position, fréquences... 
des stations de base). On utilise à cette étape l'algorithme de Voronoi pour produire la délimitation des cellules 4G 
théoriques, en utilisant des groupements par PCI / EARFCN des données. Production d'un fichier `association` (JSON).

### Bugfixes
* Production NaN dans les géolocalisations dans les fichiers `Zone` : filtrage des NaN.

## Semaines 2 et 3

### Objectif
Analyse du format AOF d'Accuver Xcal. Pouvoir produire en fin de semaine une trace en format PCAP des messages LTE RRC 
(SIB, MeasurementReports...).

### Structure des fichiers AOF
Les fichiers AOF sont écrits en CSV, avec pour séparateur le caractère `|`. Ils suivent la structure suivante :

* Informations de fichier (délimiteur ouvrant `<AOF_Information_START>`, fermant `<AOF_Information_END>`). Informations 
de fichier, version par exemple. Pas intéressant ici.

* Description de fichier (`<Description Start>` -> `<Description End>`) : contient la description des message utilisés. 
Chaque description est divisée en deux lignes : une ligne de nommage des messages de la forme 
`NOM_MESSAGE|champ1|champ2|champ3|...|champN` et une ligne de typage `NOM_MESSAGE|type1|type2|type3|...|typeN`, 
décrivant les types de chaque champ. 

    Formellement, une définition de message suit la syntaxe suivante :

    ```bnf
    <msg_def> ::= (<print_char>+ ("|" <print_char>+)+ <newline>){2}
    ```

    avec `<print_char>` désignant tout caractère imprimable, et `<newline>` un retour à la ligne. Pour rappel, l'exposant 
`+` signifie que le symbole doit être présent au moins fois, `{n}` que le symbole se répète `n` fois exactement.

    Sémantiquement, la seconde ligne doit contenir des types valides, et il doit y avoir autant de champs déclarés
sur la première ligne que de types sur la seconde.

    Cette partie présente un intérêt à la lecture manuelle du fichier, pour la compréhension de sa structure. 
Le programme étant construit a priori sur l'hypothèse que les messages sont bien formés, cette partie ne présente 
cependant pas d'intérêt au niveau de l'analyse par le programme.

* Contenu (`<Content Start>` -> `<Content End>`) : contient les messages enregistrés par Xcal. Chaque ligne débute par 
le nom du message, les valeurs sont ensuite spécifiées, on utilise le séparateur `|`.

    Syntaxiquement :

    ```bnf
    <msg_content> ::= (<print_char>* ("|" <print_char>*)+ <newline>)
    ```

    On rappelle que l'exposant `*` indique que le symbole associé peut paraître 0, 1, ou plusieurs fois.

    Sémantiquement, il doit y avoir pour un message le même nombre de champs que défini dans la partie description : le 
type de chaque champ doit correspondre au type donné pour ce champ dans la partie description.

### Structures des fichiers à produire.

#### Conversion vers PCAP

Pour chaque dissecteur Wireshark (associé à un canal), on doit générer un fichier texte,
contenant une notation textuelle pour chaque paquet. Format :
   
  ```
  YYYY-MM-DD HH:MM:SS.UUUUUU
  0000 XX XX XX XX
  ```

  où `XX XX XX XX` est le message en notation hexadécimale et `YYYY-MM-DD HH:MM:SS.UUUUUU` l'horodatage.

Les messages sur lesquels on travaille sont les messages RRC (Radio Resource Control) 
[[wiki](https://en.wikipedia.org/wiki/Radio_Resource_Control)]. Il s'agit d'un protocole de signalisation entre la
station de base et l'*User Equipment* (voir [ici](https://blogs.univ-poitiers.fr/f-launay/2015/05/08/protocole-rrc/))

Les canaux correspondant aux fichiers sont :
* `MAC-LTE-FRAMED` :
* `BCCH.BCH` : sur Broadcast Control Channel, infos sur la cellule.
* `BCCH.DL.SCH` : sur BCCH, Downlink Shared Channel, données de contrôle usager
* `DL.CCCH` : Downlink Common Control Channel, transmission de données de signalisation si DCCH non dispo (établissement
* de connexion RRC par exemple).
* `UL.CCCH` : Uplink Common Control Channel, transmission de données de signalisation si DCCH non dispo.
* `DL.DCCH` : Downlink Dedicated Control Channel, transmission de données de signalisation associée à l'utilisateur.
* `UL.DCCH` : Uplink Dedicated Control Channel, transmission de données de signalisation associée à l'utilisateur.

Ici, UL désigne une connexion *uplink*, c'est-à-dire de l'UE vers le réseau, et DL désigne une connexion *downlink*,
c'est-à-dire du réseau vers l'UE.

Source : Y. BOUGUEN, E. HARDOUIN, F. WOLFF, *LTE et les réseaux 4G*. Paris: Eyrolles, 2012, p. 87-88

#### Conversion vers JSON

Durant la phase d'analyse, deux types de données sont produites : les données `SIB`, liées aux paquets 
`SystemInformationBlock1`, contenant les données d'identification de la cellule (*Tracking Area Code*, *CellID*, 
*PLMN*), et les données `Mesurement`, liées aux données des messages `MeasurementReport`, contenant notamment le RSRP,
quantifiant la puissance du signal reçu.

Dans la première version, on utilise `pycrate` pour générer un dictionnaire au format ASN1 
(voir [wiki asn1](https://fr.wikipedia.org/wiki/ASN.1) et [ici](https://www.sstic.org/2018/presentation/pycrate/)), puis
on exploitait les données ASN1 pour produire le JSON final. Dans la seconde version, utilise les messages `QCLTE_PSCELL`
du fichier AOF pour récupérer les données nécessaires au `SIB`, `QCLTE_CELLINFO` pour les `Mesurement`.

Les entrées `SIB` suivent la structure suivante :
```json
{
    "Mesurement": {
        "PCI": "82",
        "EARFCN": "6300",
        "Geolocation": {
            "lat": "48.12014",
            "lng": "-1.62954"
        },
        "RSRP": 45,
        "neighbourMax_RSRP": -1000
    }
}
```

* Le `PCI` désigne le Physical Cell Identifier, identifiant physique de la cellule.
* L'`EARFCN` (Extended Absolute Radio Frequency Channel Number), code associé à la fréquence.
* `Geolocation` : géolocalisation, latitude `lat` et longitude `lng`.
* `RSRP` : Reference signal received power, mesure logarithmique de la puissance reçue d'une fréquence d'une station de
base, exprimée en dBm (décibels milliwatts).
* `neighbourMax_RSRP`, différence entre le RSRP reçu et le RSRP de station de base voisine le plus fort. (non implémenté)

```json
{
    "SIB": {
        "TAC": "c0:fa",
        "CellID": "09:77:19:07",
        "PCI": "82",
        "EARFCN": "6300",
        "geolocation": {
            "lat": "48.12010",
            "lng": "-1.62953"
        },
        "mcc": "208",
        "mnc": "10"
    }
}
```

* Le `TAC` (Tracking Area Code)
* Le `CellID`, identifiant distinguant la cellule des autres cellules voisines.
* Le `MCC` (Mobile Country Code) et le `MNC` (Mobile Network Code) sont deux identifiants caractérisant le `PLMN`
(Public Land Mobile Network), le `MCC` donnant le pays de la cellule (208 pour la France par ex.), et le `MNC` donnant
l'opérateur (10 pour SFR par ex.).

On produira un `Mesurement` pour chaque point GPS trouvé dans le fichier AOF ; on utilisera alors les données obtenues
par les derniers messages `QCLTE_CELLINFO` et `QCLTE_PSCELL`. On produira un `SIB` à chaque message `QCLTE_CELLINFO`
trouvé.

### Analyse sur la structure du fichier

Dans le cadre du programme de visualisation, il n'est pas nécessaire de vérifier toutes les contraintes syntaxiques et 
sémantiques définies précédemment ; il suffira en fait d'analyser certains points précis de la structure du fichier, 
servant de repère au programme.

Ces points seront les suivants :

* On a vu qu'il y avait 3 parties : informations fichier, description et contenu. Les messages se trouvent dans la 
partie contenu ; on utilisera donc les délimiteurs vus dans la partie précédente pour identifier les parties pertinentes
à analyser. On choisira, même si cela n'est pas forcément nécessaire à l'analyse, de s'assurer du bon ordre des 
parties : information, puis description, puis contenu.
* On reconnaîtra les messages à analyser à leur nom, précisé en première colonne (exemple : `GPS` pour les données GPS, 
`QCLTE_RRCMSG_V2` pour les messages RRC).
* Pour exploiter le contenu des messages, on utilisera simplement le séparateur `|` pour découper le message sous forme de 
liste.

Les repères utilisés pour identifier les messages et les sections ont pour avantage de se trouver en première colonne du
CSV : on utilisera donc les contenus des premières colonnes comme symboles d'analyse.

La structure du langage du fichier n'impliquant pas d'imbrication, et pouvant se lire sans retenir d'autre information
que la section courante, on peut intuitivement dire que ce dernier et rationnel, donc analysable par un automate fini.

On proposera l'automate suivant : 

![Automate analyse AOF](img/automate.svg)

Celui-ci exécutera des actions sémantiques au fur et à mesure de la reconnaissance du fichier, numérotées en rouge :

1. Écriture `[` ouvrant fichier JSON de sortie (voir partie suivante).
2. Reconnaissance ID téléphone.
3. Lecture des messages :
   1. `QCLTE_RRCMSG_V2` : production du message dans le fichier texte associé au canal correspondant.
      Dans la 1ère version, décodage du message vers l'ASN1 avec `pycrate`, dans la seconde version décodage du RSRP 
   avec les messages `QCLTE_PSCELL`, du PLMN et du CellID avec `QCLTE_CELLINFO`.
   
      Dans la seconde version, de données dans le JSON final s'il s'agit d'un message `SIB`.
   
   2. `QCLTE_PSCELL` : dans la seconde version, lecture des messages `PSCELL`. Enregistrement du RSRP courant à partir 
   des données CSV.
   3. `QCLTE_CELLINFO` : dans la seconde version, enregistrement MCC / MNC, CellID.
   4. `GPS` : production d'une mesure `Mesurement` associée à la géolocalisation courante.
4. Fermeture du fichier.

*Note : étant donné que le message d'identification du terminal n'est pas connu, on utilise pour l'instant une 
ɛ-transition entre les états 5 et 6.*

### Fonctionnalités ajoutées
* Lecture du format AOF par le programme.
* Processus de production plus concis, moins de fichiers intermédiaires, de meilleures performances de la fonctionnalité
`Field-testing` en terme de vitesse et en termes de consommation mémoire.

### Bugfixes
* "Bug du métro" : les cellules en tunnel profond, tranchée couverte ou station enterrée des 2 lignes de métro étaient 
prises en compte dans la modélisation originale des cellules théoriques, alors qu'elles émettent peu ou pas du tout vers
l'extérieur. Elles ne sont donc plus pris en compte lors de la conversion Cartoradio, et sont donc stockées dans des
fichiers séparés par opérateurs.
* L'interface web ne visualisait pas correctement le RSRP.
* Erreur d'affichage dans la sélection des PCI par EARFCN.

## Semaine 4

### Objectif
* Trouver un format de fichier plus concis que le JSON.
* Rechercher une solution de légende de heatmap.
* Commencer à regarder les fonctionnalités à ajouter (si le temps).

### Pourquoi un nouveau format de fichier ?

Le format utilisé actuellement pour la production de fichiers est le JSON. Si le langage JSON est conçu comme étant
facile à lire pour l'utilisateur, ce dernier a pour défaut principal de "s'étendre" beaucoup lorsqu'il s'agit de stocker
de grandes quantités de données : la structuration imbriquée des données, et l'identification de chaque champ ajoute de
la verbosité au fichier.

Pour ces raisons, on souhaite mettre en place un format de fichier remplissant les qualités suivantes :

* **Lisibilité** : l'utilisateur doit pouvoir lire et visualiser facilement le contenu du fichier.
* **Extensibilité** : le format doit être facilement extensible, et notamment assurer en cas d'ajout la rétrocompatibilité avec
les anciennes versions du logiciel.
* **Décodabilité** : le fichier doit être facile à décoder. Il doit d'ailleurs être également simple à écrire.

### Base du format : le format AOF.

Le format AOF, vu précédemment, possède quelques atouts intéressants, rejoignant les qualités énumérées précédemment :

* Il a une structure simple et est dérivé du format CSV : c'est donc un format de fichier relativement facile à
analyser (**décodabilité**).
* Le CSV permet d'afficher les résultats sur un tableur : le format AOF a pour avantage de spécifier sous cette forme
les noms des champs et les types des champs de chaque message. Il est également relativement lisible sous forme de texte
(**lisibilité**).
* Il est facile d'étendre un tel format de fichier : en identifiant chaque entrée CSV avec un nom définissant le rôle de
cette entrée, on peut choisir d'analyser les entrées intéressantes et d'ignorer les autres : on peut donc ajouter de
nouveaux types d'entrées sans poser de problèmes de compatibilité. De même, il est possible d'ajouter les champs que
l'on désire en fin de liste des champs sans problème, les anciennes versions du programme ne devraient pas dépasser
l'ancienne taille de la liste des champs (**extensibilité**).

### Proposition de syntaxe

On propose formellement la syntaxe suivante, sous forme d'expression rationnelle 
(on utilisera les 
[expressions rationnelles Python](https://docs.python.org/3/library/re.html)):

```regexp
DEFINE\n
(\w+\|\w+(\|\w+)*\n)*
CONTENT\n
(\w+\|([^\s|]| )*(\|([^\s|]| )*)*\n)*
END\n*
```

Informellement, le contenu du fichier ressemble à ceci :

```
DEFINE
nomEntree1|nomChamp1|nomChamp2|nomChamp3
nomEntree2|nomChamp4|nomChamp5|nomChamp6|nomChamp7|nomChamp8
nomEntree3|nomChamp9|nomChamp10
CONTENT
nomEntree1|10|test|50
nomEntree2|never|gonna|give|you|up
nomEntree1|10|test|50
nomEntree3|3.14|42
nomEntree3|56|8
nomEntree2|never|gonna|let|you|down
END
```

On a tout d'abord une partie de définition des données : de la même manière que pour le format AOF, on définit des
types d'entrées par leur nom, puis par le nom de leur champ. Les noms doivent utiliser des caractères alphanumériques, 
et peuvent également contenir le caractère `_`. On exige que les noms doivent contenir au moins un caractère, et que
chaque définition doit contenir, en plus du nom d'entrée, au moins un champ. Chaque définition de champ est séparée par
le caractère `|`. Il est possible d'avoir plusieurs définitions, séparées par un saut de ligne.

À partir de `CONTENT` se trouve la partie contenu. Pour chaque entrée, on indique le nom de l'entrée, puis les valeurs.
Les règles d'écriture des lignes sont les mêmes, si ce n'est qu'il est possible de ne pas spécifier de valeur pour les
champs (en dehors du nom).

Le fichier se termine par `END`. Il est possible d'avoir plusieurs sauts de ligne après le `END`.

### Sémantique

Le fichier suivant la notation CSV, celui-ci peut être visuellement représenté comme un tableau.

*Informellement*, il est demandé de déclarer chaque type d'entrée dans la partie `DEFINE` et que chaque entrée de la
partie `CONTENT` ait le même nombre de champs que dans sa déclaration de la partie `DEFINE`. On ne devra également pas
retrouver deux fois la même déclaration dans la partie `DEFINE`.
Cette partie est en réalité surtout utile pour la visualisation des données. Dans les faits, on ne fera pas de 
vérification lors de la lecture et l'analyse des fichiers sur la partie `DEFINE`.

*Note : possibilité dans certains cas d'entrées de tailles non définies. Les contraintes ne s'appliquent donc pas
forcément.*

Des règles sémantiques supplémentaires peuvent être utilisées suivant l'utilité du fichier.

### Format et suggestions d'amélioration

#### Organisation des données à afficher

Actuellement, le programme affiche les données suivantes :

* `Tracking Areas` : affiche la `Tracking Area` de chaque position, en utilisant
pour chaque position un code couleur.
* `PCI` : affiche le `PCI` associé a chaque position, en utilisant
pour chaque position un code couleur.
* `RSRP` : affiche une carte thermique des niveaux de signal RSRP, sous forme d'un pavage hexagonal, autour des mesures
GPS.
* `RSRP Offset` : affiche la différence entre le RSRP voisin le plus fort et le RSRP courant.
***Régression possible sur cette fonctionnalité***.
* Classement par EARFCN possible, affichage des cellules suivant les mesures.

On souhaite ajouter les fonctionnalités suivantes : 

* Sur les calques à pavage hexagonal : ajouter une légende (pas trouvé comment pour l'instant)
* Visualisation du :
  * `RSRQ` : rapport RSRP / RSRI, puis logarithme
  * `RSSI` : puissance signal avec prise en compte du bruit et des interférences.
  * `CINR` : rapport signal / (bruit, interférences).
* Sélection selon `EARFCN` **ET** `PCI`.

Les données d'entrées seront organisées probablement comme suit :

| TIMESTAMP | EARFCN1 | PCI1 | RSRP1 | EARFCN2 | PCI2 | RSRP2 | EARFCN3 | PCI3 | RSRP3 | ... |
|-----------|---------|------|-------|---------|------|-------|---------|------|-------|-----|
| t0        | 3000    | 21   | -94   | 151     | 21   | -104  | 3000    | 37   | -155  | ... |
| t1        | 151     | 21   | -87   | 3000    | 21   | -97   | 151     | 14   | -118  | ... |
| t2        | 151     | 21   | -82   | 3000    | 21   | -92   | 151     | 14   | -108  | ... |
| t3        | 3000    | 21   | -89   | 151     | 14   | -96   |         |      |       |     |

Pour chaque entrée du tableau, on recevra un timestamp, ainsi qu'un nombre indéfini de champs décrivant les données
mesurées en t1.

À des fins de performances, et sachant que l'on souhaite sélectionner les informations à visualiser suivant
le PCI et l'EARFCN, on trie les données par EARFCN / PCI :

| TIMESTAMP | EARFCN | 151  | 151  | 3000 | 3000 |
|-----------|--------|------|------|------|------|
|           | PCI    | 14   | 21   | 21   | 37   |
| t0        | RSRP   |      | -104 | -94  | -115 |
| t1        | RSRP   | -118 | -87  | -97  |      |
| t2        | RSRP   | -108 | -82  | -92  |      |
| t3        | RSRP   | -96  | -89  |      |      |

L'avantage de cette configuration est que la sélection EARFCN / PCI se fait en choisissant l'indice
correspondant à la bonne paire : il est avec cet indice possible de récupérer uniquement les valeurs concernées.
On notera le "renversement" effectué, les champs de mesures (ici RSRP) devenant des lignes.

Si ici seules les mesures RSRP sont présentées, on peut appliquer ce principe aux autres mesures mentionnées plus tôt
(RSRQ, RSSI, CINR...)

## Semaine 5 et 6

### Objectif
Commencer à produire le nouveau format de fichier

### Informations à visualiser

On souhaite visualiser, en fonction du **PCI** et de l'**EARFCN** :
* Le **RSRP**.
* Le **RSRQ**.
* Le **RSSI**.
* Le **CINR**.
* La position  **GPS**.
* Les **TAC**.
* Les **enveloppes convexes** (régression possible)

Concernant les antennes :   
* Les **numéros d'antenne**.
* Les **positions d'antennes**
* Les **cellules de Voronoï**
* L'**orientation** des antennes.
* Visualisation détaillée (pycrate ?)

Initialement, on a dans le fichier AOF, on a par message:
* Des mesures **GPS**.
* Le **PCI**
* Les **EARFCN** courants et voisins
* Le **RSRP**.
* Le **RSRQ**.
* Le **RSSI**.

Les fichiers Cartoradio contiennent :
* `sites` : **position des antennes**, **lieu dit**, **adresse** (utiles comme "commentaire").
* `antennes` : **azimuth**, **type système**, **hauteur**, **fréquences...**

### Traitements sur les données

#### AOF vers CSV

À partir du fichier AOF, on réorganise les données de mesures par EARFCN/PCI. On analyse une première fois le fichier
AOF pour récupérer les couples EARFCN/PCI, puis on re-parcourt une deuxième fois le fichier pour compléter le jeu de
données de sortie suivant la structure par couples EARFCN / PCI donnée plus haut.

Si deux mesures m1 et m2 sont prises au même moment (même timestamp), alors :
* Les mesures de m1 par EARFCN / PCI présents sont conservées.
* Les mesures de m2 par EARFCN / PCI non présents dans m1 sont ajoutées à m1.
* Les mesures de m2 par EARFCN / PCI présents aussi dans m1 ne sont pas gardées.

On définit dans le fichier les entrées suivants :
* `MEAS_EARFCNS|NA|NA|NA|NA|EARFCN1|EARFCN2|EARFCN3|etc` : EARFCNs trouvés.
* `MEAS_PCIS|NA|NA|NA|NA|PCI1|PCI2|PCI3|etc` : PCIs trouvés.
* `CELLINFO|Timestamp|Lat|Lng|EARFCN|PCI|TAC|CID|MCC|MNC` : informations sur une cellule (TAC, CID, PLMN).
* `MEASURE_SERVING|Timestamp|Lat|Lng|Serving_EARFCN|Serving_PCI` : EARFCN / PCI de la cellule courante.
* `MEASUREMENT|Timestamp|Lat|Lng|Measurement_Name|Values`  : mesures radio, par couples EARFCNs/PCIs. Actuellement,
RSRP, RSRQ, RSSI et CINR possibles.


