/**
 * Main application namespace, contains the App class.
 * @namespace
 */
const app = {

    /**
     * Application class, wraps the application state and methods.
     * @class
     */
    App: class {

        _map                        // Leaflet map.
        _drawingMap                 // Map object to wrap the Leaflet map.
        _fileReader                 // CSVReader object.
        _technology                 // 4G/5G NR
        _version

        _earfcnOnServing = true;    // true if "Serving EARFCN" is selected.
        _pciOnServing = true;       // true if "Serving PCI" is selected.
        _onServing = true;          // true if serving measurement layers must be dispalyed.

        _selEarfcns = null;         // Selected EARFCNs (with drop down menu).
        _selPcis = null;            // Selected PCIs (with drop down menu).
        _selBeams = null;

        _checkEarfcns = [];         // Selected EARFCNs (with sites checkboxes).
        _checkPcis = [];            // Selected PCIs (with sites checkboxes).
        _checkBeams = [];           // Selected Beams for each PCI

        _allSites = true;           // true if "All Sites" is selected in Sites.
        _profil = false; 
        _altCol = 1;                // Alternate PCI color value.

        // Corresponds to layer checkboxes states, true if the checkbox is checked.
        _rsrpChecked = false;
        _rsrqChecked = false;
        _rssiChecked = false;
        _cinrChecked = false;
        _pciTooltiprChecked = false;
        _withCheckBox=false;
        _chartInstance = null; // chart instance 
        _inprocessing=false;
        _pointProfil = [];    // tableau final : [lng1, lat1, lng2, lat2]
        _antennaData = null;  // Données de l'antenne sélectionnée : {lng, lat, height, earfcn, pci, azimuth}

        /**
         * Application class constructor.
         * @constructor
         */
        constructor() {

            // Background layers of the map.

            let baseMaps = {
                
                'Base Layer': L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
                    className: 'map-tiles'}),
                'Satellite Layer': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
                })
            };

            // Creating the map.
            //document.getElementById('map').style.height = '80vh';
            let latMin = 41.3;   
            let latMax = 51.1;   
            let lngMin = -5.3;   
            let lngMax = 9.6;    

            let centerLat = (latMin + latMax) / 2;
            let centerLng = (lngMin + lngMax) / 2;
            this._map = L.map('map', styles.mapStyle(baseMaps['Base Layer'], 6, centerLat, centerLng));

            this.reset();   // Resetting UI.

            // Adding background layers. 
            L.control.layers(baseMaps, null, { collapsed: false }).addTo(this._map);

            // Wrapping the map in a map drawing object.
            this._drawingMap = new drawing.Map(this._map);
            
            this.marker1 = null;
            this.marker2 = null;
            this.profilLine = null;
            this.createPointMarker = (latlng, number) => {
                const color = number === 1 ? "#006CFF" : "#1ABC5C";

                return L.circleMarker(latlng, {
                    radius: 12,
                    weight: 0,           // Pas de contour
                    color: color,        // Couleur du contour (non visible)
                    fillColor: color,    // Couleur principale
                    fillOpacity: 1,      // Entièrement opaque
                    className: "modern-marker"
                }).addTo(this._map).bindTooltip(
                    `<b>${number}</b>`,
                    {
                        permanent: true,
                        direction: "center",
                        className: "profil-label-modern"
                    }
                );
            };

            // CSS pour le label (version corrigée et modernisée)
            const profilCSS = document.createElement("style");
            profilCSS.innerHTML = `
            .profil-label-modern {
                /* --- Correction du rectangle blanc --- */
                background-color: transparent; /* Fond transparent */
                border: none;                  /* Aucune bordure */
                box-shadow: none;              /* Aucune ombre sur le conteneur */

                /* --- Améliorations esthétiques --- */
                font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                font-size: 14px;
                font-weight: 600;
                color: white;
                
                /* Ombre portée sur le texte pour la lisibilité */
                text-shadow: 0px 1px 3px rgba(0, 0, 0, 0.5);

                /* Empêche la sélection ou l'interaction avec le texte */
                user-select: none;
                pointer-events: none;
            }

            .modern-marker {
                /* Vide pour ne pas avoir d'animation au survol */
                /* On peut ajouter un curseur pour indiquer l'interactivité */
                cursor: pointer;
            }
            `;
            document.head.appendChild(profilCSS);




            // --------- GESTION DES CLICS SUR LA CARTE --------- //
            this._map.on("click", (e) => {
                const profilBtn = document.getElementById("profil_milti");

                // 1) Premier point
                if (this._pointProfil.length === 0) {

                    // Reset si ancien profil existait
                    if (this.marker1) this._map.removeLayer(this.marker1);
                    if (this.marker2) this._map.removeLayer(this.marker2);
                    if (this.profilLine) this._map.removeLayer(this.profilLine);

                    this.marker2 = null;
                    this.profilLine = null;

                    this._pointProfil.push(e.latlng.lng); // lng1
                    this._pointProfil.push(e.latlng.lat); // lat1

                    this.marker1 = this.createPointMarker(e.latlng, 1);
                    this._profil = true;
                    this.updateAssocs()
                    console.log("profil:",this._profil);
                    console.log("Point 1 capté :", this._pointProfil);
                    return;
                }

                // 2) Deuxième point
                if (this._pointProfil.length === 2) {

                    this._pointProfil.push(e.latlng.lng); // lng2
                    this._pointProfil.push(e.latlng.lat); // lat2

                    this.marker2 = this.createPointMarker(e.latlng, 2);

                    this.profilLine = L.polyline(
                        [
                            [this._pointProfil[1], this._pointProfil[0]],
                            [e.latlng.lat, e.latlng.lng]
                        ],
                        {
                            color: "#FF5722",
                            weight: 4,
                            opacity: 0.9,
                            dashArray: "6,6"
                        }
                    ).addTo(this._map);
                    this._profil = false;
                    this.updateAssocs();

                    console.log("Point 2 capté :", this._pointProfil);
                    profilBtn.disabled = false;

                    return;
                }

                // 3) Si déjà 2 points → reset auto
                if (this._pointProfil.length === 4) {
                    
                    profilBtn.disabled = true;
                    this._pointProfil = [];
                    this._antennaData = null;
                    if (this.marker1) this._map.removeLayer(this.marker1);
                    if (this.marker2) this._map.removeLayer(this.marker2);
                    if (this.profilLine) this._map.removeLayer(this.profilLine);

                    this.marker1 = null;
                    this.marker2 = null;
                    this.profilLine = null;
                    this._profil = false;
                    this.updateAssocs();

                    console.log("Réinitialisation → Cliquez pour nouveau point 1");
                }

            });


            // Setting up UI Events.
            this.attributeEvents();

        }

        /**
         * Updates layers by redrawing them. This function is used to display changes in selected
         * EARFCNs and PCIs.
         * 
         * @function
         */
        update() {
            let points = this._fileReader.points;       // Serving points.
            
            let earfcns = this._fileReader.earfcns;     // EARFCNs
            let pcis = this._fileReader.pcis;           // PCIs
            let beams = this._fileReader.beams;         // beams
            let selEarfcns = this._selEarfcns;          // EARFCNs selected with drop down menu.
            let selPcis = this._selPcis;                // PCIs selected with drop down menu.
            let checkEarfcns = this._checkEarfcns;      // EARFCNs selected with checkboxes.
            let checkPcis = this._checkPcis;            // PCIs selected with sites checkboxes.
            let checkBeams = this._checkBeams;

            console.log("selEarfcns:", selEarfcns);
            console.log("selPcis:", selPcis);
            console.log("checkEarfcns:", checkEarfcns);
            console.log("checkPcis:", checkPcis);
            console.log("checkBeams:", checkBeams);


            // Extremums
            const RSRP_MIN = -120;
            const RSRP_MAX = -60;

            const RSRQ_MIN = -20;
            const RSRQ_MAX = -3;

            // TODO Deteminate range for RSSI.
            const RSSI_MIN = -120;
            const RSSI_MAX = -30;

            // TODO Determinate range for CINR.
            const CINR_MIN = -20;
            const CINR_MAX = 20;
            // TODO Determinate range for PCI.
            const PCI_MIN = 0;
            const PCI_MAX = 1008;

            // Filtering EARFCNs and PCIs following drop down menus selection.
            let filtEarpcis = utils.subEarpci(earfcns, pcis, beams, selEarfcns, selPcis);

            // Filtering EARFCNs and PCIs using sites checkboxes.
            let onlySitesEarpcis = utils.subEarpci(filtEarpcis.earfcns, filtEarpcis.pcis, filtEarpcis.beams, checkEarfcns, checkPcis);
            
            // Final EARFCNs and PCIs list.
            let finalEarfcns = (this._allSites) ? selEarfcns : onlySitesEarpcis.earfcns;
            let finalPcis = (this._allSites) ? selPcis : onlySitesEarpcis.pcis;
            console.log("finalpci: "+finalPcis + " , final earfcn: "+finalEarfcns);
            let finalBeams = checkBeams;

            // Updating TAC / PCI layers.
            this._drawingMap.updatePCILayer(points, finalEarfcns, finalPcis, finalBeams, this._altCol);
            this._drawingMap.updateTACLayer(points, finalEarfcns, finalPcis, finalBeams);

            // Updating serving measurement layers.
            this._drawingMap.drawServingRSRP(points, RSRP_MIN, RSRP_MAX, finalEarfcns, finalPcis, finalBeams);
            //this._drawingMap.drawServingPCI(points, PCI_MIN, PCI_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawServingRSRQ(points, RSRQ_MIN, RSRQ_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawServingRSSI(points, RSSI_MIN, RSSI_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawServingCINR(points, CINR_MIN, CINR_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawServingPCI_tooltip(points, PCI_MIN, PCI_MAX, finalEarfcns, finalPcis, finalBeams);
        
            // Updating global measurement layers.
            this._drawingMap.drawRSRP(this._fileReader.rsrps, earfcns, pcis, beams, RSRP_MIN, RSRP_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawRSRQ(this._fileReader.rsrqs, earfcns, pcis, beams, RSRQ_MIN, RSRQ_MAX, finalEarfcns, finalPcis, finalBeams);
            this._drawingMap.drawRSSI(this._fileReader.rssis, earfcns, pcis, beams, RSSI_MIN, RSSI_MAX, finalEarfcns, finalPcis, finalBeams);
            //this._drawingMap.drawPCI(this._fileReader.pcis, earfcns, pcis, beams, PCI_MIN, PCI_MAX, finalEarfcns, finalPcis, finalBeams);

        }

        /**
         * Displays or hides layers following checked checkboxes and selected EARFCNs / PCIs.
         * This function DOES NOT redraws layers.
         * 
         * @function
         */
        updateDisplay() {

            if (this._onServing) {

                // Displaying serving measurement layers.
                console.log("i am onserving");

                this._drawingMap.setServingRSRP(this._rsrpChecked);
                this._drawingMap.setServingRSRQ(this._rsrqChecked);
                this._drawingMap.setServingRSSI(this._rssiChecked);
                this._drawingMap.setServingCINR(this._cinrChecked);
                this._drawingMap.setServingPCITOOLTIP(this._pciTooltiprChecked);

                this._drawingMap.setRSRP(false);
                this._drawingMap.setRSRQ(false);
                this._drawingMap.setRSSI(false);
                //this._drawingMap.setpciTooltip(false);

            } else {
                console.log("i am all");


                // Displaying global measurement layers.

                this._drawingMap.setRSRP(this._rsrpChecked);
                this._drawingMap.setRSRQ(this._rsrqChecked);
                this._drawingMap.setRSSI(this._rssiChecked);
                //this._drawingMap.setpciTooltip(this._pciTooltiprChecked);

                this._drawingMap.setServingRSRP(false);
                this._drawingMap.setServingRSRQ(false);
                this._drawingMap.setServingRSSI(false);
                this._drawingMap.setServingCINR(false);
                //this._drawingMap.setServingPCITOOLTIP(false);

            }

        }

        /**
         * Définit les données de l'antenne sélectionnée depuis le popup.
         * 
         * @param {object} antennaData - Objet contenant {lng, lat, height, earfcn, pci, azimuth}
         * @function
         */
        setAntennaData(antennaData) {
            this._antennaData = antennaData;
            console.log("Données d'antenne reçues dans app.js:", this._antennaData);
            
            // Si on a déjà un premier point, on peut activer le bouton profil
            if (this._pointProfil.length === 2 && this._antennaData) {
                const profilBtn = document.getElementById("profil_milti");
                profilBtn.disabled = false;
                
                // Créer le marker 2 pour l'antenne
                if (this.marker2) this._map.removeLayer(this.marker2);
                this.marker2 = this.createPointMarker(
                    {lat: antennaData.lat, lng: antennaData.lng}, 
                    2
                );
                
                // Créer la ligne entre le point 1 et l'antenne
                if (this.profilLine) this._map.removeLayer(this.profilLine);
                this.profilLine = L.polyline(
                    [
                        [this._pointProfil[1], this._pointProfil[0]],
                        [antennaData.lat, antennaData.lng]
                    ],
                    {
                        color: "#FF5722",
                        weight: 4,
                        opacity: 0.9,
                        dashArray: "6,6"
                    }
                ).addTo(this._map);
                
                // Mettre à jour _pointProfil avec les coordonnées de l'antenne
                this._pointProfil[2] = antennaData.lng;
                this._pointProfil[3] = antennaData.lat;
                
                console.log("Profil prêt avec antenne:", this._pointProfil);
            }
        }

        /**
         * Update sites pins and their checkboxes, following selected EARFCNs and PCIs.
         * 
         * @function
         */
        updateAssocs() {
            // Getting selected EARFCNS / PCIS.
            let earpcis = utils.subEarpci(this._fileReader.earfcns,this._fileReader.pcis, this._fileReader._beams, this._selEarfcns, this._selPcis);
            let frequency=utils.earfcnToFreqLte(5225);
            // Redrawing associated stations pins.
            console.log("test: ",this._fileReader.antennaDirections);
            console.log("profil:",this._profil);
            this._drawingMap.drawAssocs(
                this._fileReader.antennaDirections, this._fileReader.assocs, this._fileReader.antennas, this._checkEarfcns, this._checkPcis, this._checkBeams,
                () => this.update(), earpcis.earfcns, earpcis.pcis, earpcis.beams,!this._allSites,this._profil, this._technology, this);
            this._withCheckBox=!this._withCheckBox;
            

        }

        /**
         * Resets the state of the app and the UI.
         * 
         * @function
         */
        reset() {

            // Resetting attributes.

            this._earfcnOnServing = true;
            this._pciOnServing = true;
            this._onServing = true;
            this._allSites = true;

            this._selEarfcns = null;
            this._selPcis = null;
            this._selBeams = null;

            this._checkEarfcns = [];
            this._checkPcis = [];
            this._checkBeams = [];

            this._rsrpChecked = false;
            this._rsrqChecked = false;
            this._rssiChecked = false;
            this._cinrChecked = false;
            this._pciTooltiprChecked = false;

            this._fileReader = null;
            
            this._altCol = 1;

            // Clearing drop down selectors.
            document.querySelectorAll('#EARFCN_select, #pci-select').forEach((elt) => elt.innerHTML = '');
            document.querySelector('#sites-select').value = 'all-sites';

            // Unchecking checkboxes.
            document.querySelectorAll('input[type="checkbox"]').forEach((elt) => elt.checked = false);

            // Locking the UI.
            document.querySelector('#fileSelect').disabled = false;
            this.enableInputs(false);

            // Hiding remaining layers.
            if (this._drawingMap) {
                this.updateDisplay();
                this._drawingMap.setAntLayer(false);
                this._drawingMap.setAssocLayer(false);
                this._drawingMap.setCellLayer(false);
                this._drawingMap.setTACLayer(false);
                this._drawingMap.setPCILayer(false);
            }

        }

        /**
         * Enables or disables inputs.
         * @param {boolean} b true to enable inputs, false otherwise.
         * 
         * @function
         */
        enableInputs(b) {

            //let visuInputs = document.querySelectorAll('.visu-params input, .visu-params select, #clear-all');
            let visuInputs = document.querySelectorAll('.visu-params input, .visu-params select, #Heatmap_Legend, #Measurement_info, #showStatsBtn');
            
            visuInputs.forEach((input) => input.disabled = !b);

        }
        
        /*showLoader() {
            document.getElementById('loader').style.display = 'block';
        }
        hideLoader() {
            document.getElementById('loader').style.display = 'none';
        }*/

        /**
         * Attributes event handlers to UI components.
         * 
         * @function
         */
        attributeEvents() {
            const profilButton = document.querySelector('#profil_milti');

            // Déclare une variable globale (ou au scope de attributeEvents)
            let profilChartInstance = null;
            // Références aux éléments du DOM
            const profilModal = document.getElementById('profilModal');
            const profilModalBackdrop = document.getElementById('profilModalBackdrop');
            const closeProfilButton = document.getElementById('closeProfil');
            const ctxProfil = document.getElementById('profilChart').getContext('2d');
            

            // Fonction pour afficher la modale avec animation
            function showProfilModal() {
                profilModal.style.display = 'flex';
                profilModalBackdrop.style.display = 'block';
                setTimeout(() => {
                    profilModal.style.opacity = 1;
                    profilModal.style.transform = 'translate(-50%, -50%)';
                    profilModalBackdrop.style.opacity = 1;
                }, 10);
            }

            // Fonction pour masquer la modale
            function hideProfilModal() {
                profilModal.style.opacity = 0;
                profilModal.style.transform = 'translate(-50%, -45%)';
                profilModalBackdrop.style.opacity = 0;
                setTimeout(() => {
                    profilModal.style.display = 'none';
                    profilModalBackdrop.style.display = 'none';
                }, 300);
            }

            closeProfilButton.onclick = hideProfilModal;
            profilModalBackdrop.onclick = hideProfilModal;

            profilButton.onclick = async () => {
                const point1 = [this._pointProfil[0], this._pointProfil[1]];
                const point2 = [this._pointProfil[2], this._pointProfil[3]];
                const dx = point2[0] - point1[0]; // différence de longitude
                const dy = point2[1] - point1[1]; // différence de latitude

                const distanceMeters = Math.sqrt(dx*dx + dy*dy) * 111000;
                let nbpoints = Math.ceil(distanceMeters / 0.5);
                console.log("nbpoints is: ",nbpoints);
                console.log("distance  is: ",distanceMeters);

                const points = utils.generatePoints(point1, point2, nbpoints);

                try {
                    const altitudes = await utils.getAltitudes(points);
                    console.log("Altitudes :", altitudes);

                    // Calcul des distances cumulées
                    const distances = [0];
                    for (let i = 1; i < points.length; i++) {
                        const dx = points[i][0] - points[i-1][0];
                        const dy = points[i][1] - points[i-1][1];
                        distances.push(distances[i-1] + Math.sqrt(dx*dx + dy*dy) * 111000);
                    }
                    
                    // Gestion de l'altitude de départ et d'arrivée (avec hauteur d'antenne si applicable)
                    const startAltitude = altitudes[0];
                    let endAltitude = altitudes[altitudes.length - 1];
                    
                    // Si une antenne est sélectionnée, ajouter sa hauteur à l'altitude finale
                    if (this._antennaData && this._antennaData.height && this._antennaData.height !== '-') {
                        const antennaHeight = parseFloat(this._antennaData.height);
                        if (!isNaN(antennaHeight)) {
                            endAltitude += antennaHeight;
                            console.log(`Hauteur d'antenne ajoutée: ${antennaHeight}m, altitude finale: ${endAltitude}m`);
                        }
                    }

                    // Afficher le modal
                    profilModal.style.display = 'block';

                    // Détruire l'ancien graphique si existant
                    if (profilChartInstance) {
                        profilChartInstance.destroy();
                    }

                    // Créer le nouveau graphique
                    showProfilModal();

                    if (profilChartInstance) {
                        profilChartInstance.destroy();
                    }

                    // Création du dégradé de couleur basé sur l'altitude
                    const minAlt = Math.min(...altitudes);
                    const maxAlt = Math.max(...altitudes);
                    const colorScale = d3.interpolateRgb("green", "red"); // Vert (bas) -> Rouge (haut)

                    profilChartInstance = new Chart(ctxProfil, {
                        type: 'line',
                        data: {
                            labels: distances.map(d => d.toFixed(0)),
                            datasets: [
                                {
                                label: 'Elevation Profile',
                                data: altitudes,
                                fill: {
                                    target: 'origin',
                                    above: 'rgba(255, 87, 34, 0.1)', // Couleur de remplissage sous la ligne
                                },
                                borderColor: 'rgba(255, 87, 34, 0.8)',
                                tension: 0.4,
                                pointRadius: 0, // On cache les points par défaut
                                pointBackgroundColor: 'white',
                                pointBorderColor: 'rgba(255, 87, 34, 1)',
                                pointHoverRadius: 6, // Points plus gros au survol
                                pointHoverBorderWidth: 3,
                                borderWidth: 1.5,
                                // Segmentation pour le dégradé de couleur
                                segment: {
                                    borderColor: ctx => {
                                        const y = ctx.p1.parsed.y;
                                        const normalizedAlt = (y - minAlt) / (maxAlt - minAlt);
                                        return colorScale(normalizedAlt);
                                    }
                                }
                                },
                                {
                                    label: 'Line of Sight',
                                    // On ne dessine qu'entre le premier et le dernier point
                                    data: [startAltitude, ...Array(altitudes.length - 2).fill(null), endAltitude],
                                    borderColor: '#00BFFF',    // Couleur bleue pour la visibilité
                                    borderWidth: 2,             // Épaisseur de la ligne
                                    borderDash: [10, 5],        // Style en pointillés
                                    fill: false,                // Pas de remplissage
                                    tension: 0,                 // Ligne parfaitement droite
                                    pointRadius: 5,             // Marquer le début et la fin
                                    pointBackgroundColor: '#00BFFF',
                                    spanGaps: true
                                }
                        ]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            animation: {
                                duration: 1000,
                                easing: 'easeInOutQuart'
                            },
                            plugins: {
                                legend: { display: false }, // Le titre est suffisant
                                title: { display: false }, // On utilise notre propre header
                                tooltip: {
                                    mode: 'index',
                                    intersect: false,
                                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                    titleFont: { size: 14, weight: 'bold' },
                                    bodyFont: { size: 12 },
                                    padding: 12,
                                    cornerRadius: 8,
                                    callbacks: {
                                        label: (context) => `Altitude: ${context.parsed.y.toFixed(1)} m`
                                    }
                                }
                            },
                            scales: {
                                x: {
                                    title: { display: true, text: 'Distance (m)', color: '#aaa' },
                                    ticks: { color: '#aaa' },
                                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                                },
                                y: {
                                    title: { display: true, text: 'Altitude (m)', color: '#aaa' },
                                    ticks: { color: '#aaa' },
                                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                                }
                            },
                            // Plugin pour dessiner une ligne verticale au survol
                            interaction: {
                                mode: 'index',
                                intersect: false,
                            },
                            plugins: [{
                                id: 'crosshair',
                                afterDraw: chart => {
                                    if (chart.tooltip?._active?.length) {
                                        let x = chart.tooltip._active[0].element.x;
                                        let yAxis = chart.scales.y;
                                        let ctx = chart.ctx;
                                        ctx.save();
                                        ctx.beginPath();
                                        ctx.moveTo(x, yAxis.top);
                                        ctx.lineTo(x, yAxis.bottom);
                                        ctx.lineWidth = 1;
                                        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
                                        ctx.stroke();
                                        ctx.restore();
                                    }
                                }
                            }]
                        }
                    });


                } catch (err) {
                    console.error(err);
                }
            };



            



            document.querySelector('#Heatmap_Legend').onclick = () => {
                document.getElementById('popup').style.display = 'block';
                renderLegends();
                
            };
            document.querySelector('#close').onclick = () => {
                document.getElementById('popup').style.display = 'none';
                
            };
            
            const popup = document.getElementById("popup");
            const header = document.getElementById("popupHeader");

            let isDragging = false;
            let offsetX = 0;
            let offsetY = 0;

            header.addEventListener("mousedown", (e) => {
            isDragging = true;
            offsetX = e.clientX - popup.offsetLeft;
            offsetY = e.clientY - popup.offsetTop;
            });

            document.addEventListener("mouseup", () => {
            isDragging = false;
            });

            document.addEventListener("mousemove", (e) => {
            if (isDragging) {
                const maxLeft = window.innerWidth - popup.offsetWidth;
                const maxTop = window.innerHeight - popup.offsetHeight;

                let newLeft = e.clientX - offsetX;
                let newTop = e.clientY - offsetY;

                // Empêcher de sortir de l'écran
                newLeft = Math.max(0, Math.min(newLeft, maxLeft));
                newTop = Math.max(0, Math.min(newTop, maxTop));

                popup.style.left = `${newLeft}px`;
                popup.style.top = `${newTop}px`;
            }
            });

            function closePopup() {
            popup.style.display = "none";
            }

            // tooltip background 
            document.querySelectorAll('.hexbin-tooltip').forEach(el => {
            el.style.background = 'white';
            el.style.color = 'black';
            el.style.padding = '6px 10px';
            el.style.borderRadius = '10px';
            el.style.border = '1px solid #ccc';
            el.style.fontSize = '13px';
            el.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)';
            el.style.pointerEvents = 'none';
            el.style.maxWidth = '250px';
            });



            // Select file button.
            document.querySelector('#fileSelect').onclick = (evt) => {

                let inputElt = document.querySelector('#fileElem');
                inputElt.click();

            };

            // File selector.
            // Asynchronous method due to the asynchronous file reading.
            document.querySelector('#fileElem').onchange = async (evt) => {
                // Show loader overlay
                document.getElementById('loader-overlay').classList.add('active');

                await new Promise(resolve => setTimeout(resolve, 50));

                let file = evt.target.files[0];
                this._fileReader = new csvreadv2.CSVReader(file);
                await this._fileReader.readFile();

                document.getElementById('loader-overlay').classList.remove('active');
                const alertBox = document.getElementById("alert-success");
                alertBox.textContent = "✅ The file has been read successfully!";
                alertBox.style.display = "block";

                await new Promise(resolve => setTimeout(resolve, 50));

                let antennas = this._fileReader.antennas;
                let vor = processing.calcVoronoi(antennas);
                let dels = processing.calcDelimiters(vor, antennas);
                let ants = processing.calcAntennas(this._fileReader.antennaDirections);
                this._technology = processing.getTechnologies(this._fileReader.measurementTechno);
                this._version = processing.getVersions(this._fileReader.measurementVersion);
                const heading = document.getElementById('earfcn-heading');
                const select = document.getElementById('EARFCN_select');
                

                let earfcns = this._fileReader.earfcns;
                let pcis = this._fileReader.pcis;
                let pciNb = this._fileReader.pciNb;

                this._drawingMap.drawCells(vor, ants, dels);
                this.updateAssocs();
                this._drawingMap.setAntLayer(true);
                this._drawingMap.setAssocLayer(true);
                this._drawingMap.drawSelectors(earfcns, pcis, pciNb, this._technology);
                this.enableInputs(true);
                this.update();

                const technoImg = document.getElementById("technoImg");
                const technoLabel = document.getElementById("technoLabel");
                const popup = document.getElementById("measurementPopup");
                const btn = document.getElementById("Measurement_info");
                const closeBtn = document.getElementById("popupClose");

                if (this._technology.at(-1) === "5G NR") {
                    heading.textContent = 'NRARFCN';
                    select.options[0].text = 'Serving NRARFCN';
                    select.options[1].text = 'All NRARFCNs';

                    technoImg.src = "img/5G.png";
                    technoImg.style.display = "inline-block";
                    technoLabel.style.display = "inline-block";
                    technoLabel.textContent = "Technology:";
                } else {
                    heading.textContent = 'EARFCN';
                    select.options[0].text = 'Serving EARFCN';
                    select.options[1].text = 'All EARFCNs';

                    technoImg.src = "img/4G.png";
                    technoImg.style.display = "inline-block";
                    technoLabel.style.display = "inline-block";
                    technoLabel.textContent = "Technology:";
                }
                
                btn.addEventListener("click", () => {
                document.getElementById("popup-techno").textContent = this._technology?.at(-1) || "N/A";
                document.getElementById("popup-version").textContent = "v"+this._version+".0"
                //document.getElementById("popup-date").textContent = this._fileReader?.measurementDate || new Date().toLocaleDateString();

                
                popup.style.display = "flex";
                });

                
                closeBtn.addEventListener("click", () => {
                popup.style.display = "none";
                });

                
                window.addEventListener("click", (event) => {
                if (event.target === popup) {
                    popup.style.display = "none";
                }
                });

                setTimeout(() => {
                    alertBox.style.display = "none";
                }, 1500);
            };

            // Theoritical cells checkbox.
            document.querySelector('#Theory_Cell').onclick = (evt) => {
                this._drawingMap.setCellLayer(evt.target.checked);
            };

            // TAC checkbox.
            document.querySelector('#Tracking_area').onclick = (evt) => {
                const processing = document.getElementById("processing");
                processing.textContent = "processing ...";
                processing.style.display = "block";

                requestAnimationFrame(() => {
                    setTimeout(() => {
                        this._drawingMap.setTACLayer(evt.target.checked);
                        processing.style.display = "none";
                    }, 0);
                });
            };


            // PCI checkbox.
            document.querySelector('#PCI').onclick = (evt) => {                              
                const processing = document.getElementById("processing");
                processing.textContent = "processing ...";
                processing.style.display = "block";

                requestAnimationFrame(() => {
                        setTimeout(() => {
                            this._pciTooltiprChecked = evt.target.checked;
                            this._drawingMap.setPCILayer(evt.target.checked);
                            this.updateDisplay();
                            
                            processing.style.display = "none";
                        }, 0);
                    });
            };


            // RSRP checkbox.
            document.querySelector('#RSRP').onclick = (evt) => {

                this._rsrpChecked = evt.target.checked;
                this.updateDisplay();

            };

            // RSRQ checkbox.
            document.querySelector('#rsrq').onclick = (evt) => {
                
                this._rsrqChecked = evt.target.checked;
                this.updateDisplay();

            };

            // RSSI checkbox.
            document.querySelector('#rssi').onclick = (evt) => {
                
                this._rssiChecked = evt.target.checked;
                this.updateDisplay();

            };

            // CINR checkbox.
            document.querySelector('#cinr').onclick = (evt) => { 
                
                this._cinrChecked = evt.target.checked;
                this.updateDisplay();

            };

            // Sites selector.
            document.querySelector('#sites-select').onchange = (evt) => {
                const processing = document.getElementById("processing");
                processing.textContent = "processing ...";
                processing.style.display = "block";

                requestAnimationFrame(() => {
                        setTimeout(() => {
                            this._allSites = (evt.target.value === 'all-sites');
                            this.update();
                            this.updateAssocs();
                            processing.style.display = "none";
                        }, 0);
                    });
            };


            // EARFCNs selector.
            document.querySelector('#EARFCN_select').onchange = (evt) => {
                const processing = document.getElementById("processing");
                processing.textContent = "processing ...";
                processing.style.display = "block";

                requestAnimationFrame(() => {
                    setTimeout(() => {
                        let val = evt.target.value;    

                        this._earfcnOnServing = (val === 'serving-earfcn');

                        this._selEarfcns = (!this._earfcnOnServing && val !== 'all-earfcns') ? 
                            [parseInt(val)] : null;

                        this._onServing = this._earfcnOnServing || this._pciOnServing;

                        this.update();
                        this.updateDisplay();
                        this.updateAssocs();

                        processing.style.display = "none";
                    }, 0);
                });
            };


            // PCIs selector.
            // Same than EARFCNs.
            document.querySelector('#pci-select').onchange = (evt) => {
                const processing = document.getElementById("processing");
                processing.textContent = "processing ...";
                processing.style.display = "block";

                requestAnimationFrame(() => {
                    setTimeout(() => {
                        let val = evt.target.value;

                        this._pciOnServing = (val === 'serving-pci');

                        this._selPcis = (!this._pciOnServing && val !== 'all-pcis') ? 
                            [parseInt(val)] : null;

                        this._onServing = this._earfcnOnServing || this._pciOnServing;

                        this.update();
                        this.updateDisplay();
                        this.updateAssocs();

                        processing.style.display = "none";
                    }, 0);
                });
            };


            // "Clear All" button.
            //document.querySelector('#clear-all').onclick = (evt) => this.reset();

            // Alternative color button.
            document.querySelector('#ColorAlt').onclick = (evt) => {
                const processing = document.getElementById("processing");
                processing.textContent = "processing ...";
                processing.style.display = "block";

                requestAnimationFrame(() => {
                    setTimeout(() => {
                        this._altCol = evt.target.checked ? 0 : 1;
                        this.update();

                        processing.style.display = "none";
                    }, 0);
                });
            };
            document.querySelector('#showStatsBtn').onclick = () => {
                document.getElementById('map').style.display = 'none';
                document.getElementById('statistiques').style.display = 'block';
            
                let points = this._fileReader.points;            
                const ctx = document.getElementById("Chart").getContext("2d");
            
                if (this._chartInstance) {
                    this._chartInstance.destroy();
                }
            
                const rsrpValues = [];
                const rssiValues = [];
                const rsrqValues = [];
                const pciValues = [];
                const indices = [];
            
                let index = 0;
                for (const tac in points) {
                    for (const pci in points[tac]) {
                        for (const cid in points[tac][pci]) {
                            const samples = points[tac][pci][cid];
                            for (const sample of samples) {
                                if (
                                    sample.rsrp !== undefined &&
                                    sample.rssi !== undefined &&
                                    sample.rsrq !== undefined
                                ) {
                                    rsrpValues.push(sample.rsrp);
                                    rssiValues.push(sample.rssi);
                                    rsrqValues.push(sample.rsrq);
                                    pciValues.push(pci); 
                                    indices.push(index++);
                                }
                            }
                        }
                    }
                }
            
                this._chartInstance = new Chart(ctx, {
                    type: "line",
                    data: {
                        labels: indices,
                        datasets: [
                            {
                                label: "RSRP (dBm)",
                                data: rsrpValues,
                                borderColor: "#4e79a7",
                                backgroundColor: "rgba(78, 121, 167, 0.1)",
                                yAxisID: "yLeft",
                                tension: 0.2,
                                pointRadius: 0,
                                fill: false
                            },
                            {
                                label: "RSSI (dBm)",
                                data: rssiValues,
                                borderColor: "#f28e2b",
                                backgroundColor: "rgba(242, 142, 43, 0.1)",
                                yAxisID: "yLeft",
                                tension: 0.2,
                                pointRadius: 0,
                                fill: false
                            },
                            {
                                label: "RSRQ (dB)",
                                data: rsrqValues,
                                borderColor: "#59a14f",
                                backgroundColor: "rgba(89, 161, 79, 0.1)",
                                yAxisID: "yRight",
                                tension: 0.2,
                                pointRadius: 0,
                                fill: false
                            }
                        ]
                    },
                    options: {
                        responsive: true,
                        interaction: {
                            mode: 'index',
                            intersect: false,
                        },
                        plugins: {
                            title: {
                                display: true,
                                text: "RSRP, RSSI, and RSRQ Variation"
                            },
                            legend: {
                                position: "top"
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.dataset.label || '';
                                        const value = context.parsed.y;
                                        const index = context.dataIndex;
                                        const pci = pciValues[index];
                                        return `${label}: ${value} dBm (PCI: ${pci})`;
                                    }
                                }
                            },
                            zoom: {
                                pan: {
                                    enabled: true,
                                    mode: 'xy'
                                },
                                zoom: {
                                    wheel: { enabled: true },
                                    pinch: { enabled: true },
                                    mode: 'x'
                                }
                            }
                        },
                        scales: {
                            x: {
                                title: {
                                    display: true,
                                    text: "Measurement Index"
                                }
                            },
                            yLeft: {
                                type: "linear",
                                position: "left",
                                title: {
                                    display: true,
                                    text: "Signal Strength (dBm)"
                                },
                                ticks: {
                                    beginAtZero: false
                                }
                            },
                            yRight: {
                                type: "linear",
                                position: "right",
                                title: {
                                    display: true,
                                    text: "RSRQ (dB)"
                                },
                                grid: {
                                    drawOnChartArea: false
                                }
                            }
                        }
                    }
                });
            };
            
        
            
            document.querySelector('#showMapBtn').onclick = () => {
                document.getElementById('map').style.display = 'block';
                document.getElementById('statistiques').style.display = 'none';
            };
            

        }

    }

};

(function () {
    new app.App();
})();

function getRGBComponents(color) {
  const canvas = document.createElement("canvas");
  const ctx = canvas.getContext("2d");
  ctx.fillStyle = color;
  ctx.fillRect(0, 0, 1, 1);
  const data = ctx.getImageData(0, 0, 1, 1).data;
  return { r: data[0], g: data[1], b: data[2] };
}

function createLegend(label, minValue, maxValue) {
  const container = document.createElement("div");
  container.className = "legend-container";

  const row = document.createElement("div");
  row.className = "legend-row";

  const canvas = document.createElement("canvas");
  canvas.width = 20;
  canvas.height = 200;
  const ctx = canvas.getContext("2d");


  const imageData = ctx.createImageData(canvas.width, canvas.height);
  for (let y = 0; y < canvas.height; y++) {
    const val = maxValue - ((maxValue - minValue) * y / canvas.height);
    const color = utils.getColorFromPalette(val, minValue, maxValue, styles.HEATMAP);
    const rgb = getRGBComponents(color);

    for (let x = 0; x < canvas.width; x++) {
      const index = (y * canvas.width + x) * 4;
      imageData.data[index] = rgb.r;
      imageData.data[index + 1] = rgb.g;
      imageData.data[index + 2] = rgb.b;
      imageData.data[index + 3] = 255;
    }
  }
  ctx.putImageData(imageData, 0, 0);

  
  const steps = 10;
  const scale = document.createElement("div");
  scale.className = "scale";

  for (let i = 0; i <= steps; i++) {
    const val = maxValue - ((maxValue - minValue) / steps) * i;
    const span = document.createElement("span");
    span.textContent = Math.round(val);

    const stepDiv = document.createElement("div");
    stepDiv.style.height = `${canvas.height / steps}px`;
    stepDiv.appendChild(span);

    scale.appendChild(stepDiv);
  }

  row.appendChild(canvas);
  row.appendChild(scale);

  const labelDiv = document.createElement("div");
  labelDiv.className = "legend-label";
  labelDiv.textContent = label;

  container.appendChild(row);
  container.appendChild(labelDiv);

  
  const tooltip = document.createElement("div");
  tooltip.className = "legend-tooltip";
  document.body.appendChild(tooltip);

  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const y = e.clientY - rect.top;
    const val = maxValue - ((maxValue - minValue) * y / canvas.height);

    tooltip.textContent = `${label}: ${Math.round(val)}`;
    tooltip.style.left = `${e.pageX + 10}px`;
    tooltip.style.top = `${e.pageY + 10}px`;
    tooltip.style.display = "block";
  });

  canvas.addEventListener("mouseleave", () => {
    tooltip.style.display = "none";
  });

  return container;
}

function renderLegends() {
  const legendsWrapper = document.getElementById("legends-wrapper");
  legendsWrapper.innerHTML = "";

  const legends = [
    { label: "RSRP (dBm)", min: -120, max: -60 },
    { label: "RSRQ (dB)", min: -20, max: -3 },
    { label: "RSSI (dBm)", min: -120, max: -30 },
    { label: "CINR (dB)", min: -20, max: 20 }
  ];

  legends.forEach(({ label, min, max }) => {
    const legend = createLegend(label, min, max);
    legendsWrapper.appendChild(legend);
  });
}

renderLegends();
