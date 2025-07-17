/**
 * Contains class and methods used to draw data on the Leaflet map.
 *
 * @namespace
 */
const drawing = {
    /**
     * Wraps the map and the layer state to perform drawing and updating operations on them.
     *
     * @class
     */
    Map: class {
        _map            // Leaflet Map
        _cellLayer      // Voronoi cell layer.
        _antLayer       // Antennas layer.
        _assocLayer     // Association pin layer.
        _tacLayer       // TAC points layer.
        _pciLayer       // PCI Points layer.
        _servingRSRP    // Serving RSRP layer
        _servingRSRQ    // Serving RSRQ layer
        _servingRSSI    // Serving RSSI layer
        _servingCINR    // Serving RSRP layer
        _servingPciTooltipLayer // serving PCI tooltip 
        _rsrpLayer      // Global RSRP layer
        _rsrqLayer      // Global RSRQ layer
        _rssiLayer      // Global RSSI layer
        _cinrLayer      // Global RSRP layer
        _pciTooltipLayer      // Global PCI Tooltip layer
        _nonFilteredTAC
        _nonFilteredPCI
        /**
         * Class constructor.
         *
         * @param {L.Map} map Leaflet map to wrap.
         *
         * @constructor
         */
        constructor(map) {
            this._map = map;
            this._cellLayer = L.layerGroup();
            this._tacLayer = L.layerGroup();
            this._pciLayer = L.layerGroup();
            this._servingPCI = L.layerGroup(); 
            this._servingPciTooltipLayer = drawing.hexBin('PCI', styles.hexColor_pci());
            this._servingRSRP = drawing.hexBin('RSRP', styles.hexColor(0, 1));
            this._servingRSRQ = drawing.hexBin('RSRQ', styles.hexColor(0, 1));
            this._servingRSSI = drawing.hexBin('RSSI', styles.hexColor(0, 1));
            this._servingCINR = drawing.hexBin('CINR', styles.hexColor(0, 1));
            this._rsrpLayer = drawing.hexBin('RSRP', styles.hexColor(0, 1));
            this._rsrqLayer = drawing.hexBin('RSRQ', styles.hexColor(0, 1));
            this._rssiLayer = drawing.hexBin('RSSI', styles.hexColor(0, 1));
            this._cinrLayer = drawing.hexBin('CINR', styles.hexColor(0, 1));
            this._pciTooltiprLayer = drawing.hexBin('PCI', styles.hexColor_pci());
            this._assocLayer = L.layerGroup();
            this._nonFilteredTAC = null;
            this._nonFilteredPCI = null;
        }
        /**
         * Draws Voronoi cells, delimiters and antennas layers.
         *
         * @param {*} voronoi Voronoi diagram GeoJSON
         * @param {*} antFeats Antennas directivity lines GeoJSON.
         * @param {*} delFeats Sectors delimiters GeoJSON.
         *
         * @function
         */
        drawCells(voronoi, antFeats, delFeats) {
            console.log(antFeats); // Debug: show antenna features in the console

            // Clear the previous cell layer
            this._cellLayer.clearLayers();

            // Get the features of the Voronoi cells
            let vorFeats = voronoi.features;

            // Create GeoJSON layer for Voronoi cells with style
            let vorLayer = L.geoJson(turf.featureCollection(vorFeats), styles.polyStyle(0.1, '000000'));

            // Create GeoJSON layer for delimiters (borders between cells)
            let delLayer = L.geoJson(turf.featureCollection(delFeats), styles.styleDelimiter());

            delLayer.bringToBack(); // Ensure delimiters are behind other layers

            
            delFeats.forEach((feature, featureIndex) => {
                if (feature.geometry && feature.geometry.type === 'LineString') {
                    const coords = feature.geometry.coordinates; // tableau [ [lon, lat], ... ]
                    //console.log(coords);
                    for (let i = 0; i < coords.length - 1; i++) {
                        const [lon1, lat1] = coords[i];
                        const [lon2, lat2] = coords[i + 1];
                        // Utilisation de la fonction calculateAzimuth de ton fichier util
                        const azimuth = utils.calculateAzimuth(lat1, lon1, lat2, lon2);
                        //console.log(`Delimiter Feature ${featureIndex}, segment ${i}: azimuth = ${azimuth.toFixed(2)}°`);
                    }
                }
            });
            

            // Add Voronoi cells and delimiters to the cell layer group
            vorLayer.addTo(this._cellLayer);
            delLayer.addTo(this._cellLayer);

            // Create the antenna layer with custom styling and popup behavior
            this._antLayer = L.geoJson(turf.featureCollection(antFeats), {
                // Convert point features to styled circle markers
                pointToLayer: function(feature, latlng) {
                    return L.circleMarker(latlng, styles.styleAntenna());
                },

                // Define what happens for each antenna feature
                onEachFeature: function(feature, layer) {
                    // Extract longitude and latitude from the GeoJSON coordinates
                    const [longitude, latitude] = feature.geometry.coordinates[0];
                    // Extract antenna ID or site name (adjust according to your data)
                    const cartoNum = 'Unknown';

                    // Build popup HTML content with links to Cartoradio and Google Street View
                    let popupContent = `
                        <div class="tooltip-header" style="margin-bottom:8px;">
                            
                            <a href="https://www.cartoradio.fr/#/cartographie/all/lonlat/${longitude}/${latitude}" 
                            target="_blank" rel="noopener"><strong>
                            <span style="color:blue;">Carto</span><span style="color:hotpink;">radio</span>
                            </strong> 
                                
                            </a>
                            <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${latitude},${longitude}" 
                            target="_blank" rel="noopener" style="margin-left:8px;">
                                <img src="./img/pngegg.png" alt="Street View" width="32" height="32">
                            </a>
                        </div>
                    `;

                    // Bind the popup to the antenna marker
                    layer.bindPopup(popupContent, {
                        closeOnClick: true,
                        autoClose: true
                    });

                    // Optional: Change cursor on hover to indicate interactivity
                    layer.on('mouseover', function() {
                        this._path.style.cursor = 'pointer';
                    });
                }
            });

            // Optionally add the antenna layer to the map automatically
            this.setAntLayer(true); // <- You can control this dynamically if needed
        }

        /**
         * Draw serving points layer.
         * @param {*} points Points data
         * @param {function} valChooser Function that (earfcn, pci, point) => value which
         * extracts the value from the point.
         * @param {function} colorChooser Function (value) => color which calculate the point color.
         *
         * @returns Return an object containing multiple layers associated to EARFCNs / PCIs.
         *
         * @function
         */
        /*drawPoints(pointsData, valChooser, colorChooser) {
            let newPointLayers = {}; // Dictionnaire pour stocker les groupes de couches de marqueurs
            for (let earfcn in pointsData) {
                newPointLayers[earfcn] = {};
                let earfcnGr = pointsData[earfcn];
                for (let pciKey in earfcnGr) { // pciKey est la valeur PCI pour ce groupe
                    newPointLayers[earfcn][pciKey] = {};
                    let pciGr = earfcnGr[pciKey];
                    for (let beam in pciGr) {
                        let beamLayerGroup = L.layerGroup(); // Un groupe de couches pour les points de ce faisceau
                        let pointsArr = pciGr[beam]; // Tableau des points de mesure individuels

                        pointsArr.forEach((point) => { 
                            if (typeof point.lat !== 'undefined' && typeof point.lng !== 'undefined') {
                                let latLng = [point.lat, point.lng];
                                let valueForColor = valChooser(earfcn, pciKey, point); 
                                let color = colorChooser(valueForColor); // Couleur du point

                                let circleMarker = L.circleMarker(latLng, {
                                    radius: 4, 
                                    color: color, 
                                    weight: 1,
                                    opacity: 1,
                                    fillOpacity: 0.7 
                                });
                                let tooltipContent = "PCI: " + pciKey;                                                                            
                                circleMarker.bindTooltip(tooltipContent);
                                beamLayerGroup.addLayer(circleMarker); // Ajoute le marqueur au groupe du faisceau
                            }
                        });
                        newPointLayers[earfcn][pciKey][beam] = beamLayerGroup; // Stocke le groupe de couches
                    }
                }
            }
            return newPointLayers; // Retourne la structure attendue par setPointLayer
        }*/
       drawPoints(points, valChooser, colorChooser) {
            let pointDict = {};
            for (let earfcn in points) {
                pointDict[earfcn] = {};
                let earfcnGr = points[earfcn];
                for (let pci in earfcnGr) {
                    pointDict[earfcn][pci] = {};
                    let pciGr = earfcnGr[pci];
                    for (let beam in pciGr) {
                        let pointsDict = {};
                        let pointsArr = pciGr[beam];
                        pointsArr.forEach((point) => {
                            let latLng = [point.lat, point.lng];
                            let val = valChooser(earfcn, pci, point);
                            pointsDict[val] = pointsDict[val] || [];
                            pointsDict[val].push(latLng);
                        });
                        for (let val in pointsDict) {
                            let layer = new L.GridLayer.MaskCanvas(styles.pointStyle(colorChooser(val)));
                            layer.setData(pointsDict[val]);
                            pointDict[earfcn][pci][beam] = layer;
                        }
                    }
                }
            }
            return pointDict;
        }

        /**
         * Draws serving measurement heatmap layer.
         *
         * @param {*} layer Layer to draw on.
         * @param {function} points Serving measurement points.
         * @param {function} valChooser Function that (earfcn, pci, point) => value which
         * extracts the value from the point.
         * @param {number} min Minimum value (used for the color range).
         * @param {number} max Maximum value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         *
         * @function
         */
        drawServingHex(layer, points, valChooser, min, max, earfcns = null, pcis = null, beams = null) {
            // Layer data points;
            let hexData = [];
            // EARFCNs and PCIs amongs input points.
            let baseEarfncs = [];
            let basePcis = [];
            let baseBeams = [];
            // Iterating over points EARFCNs...
            for (let earfcn in points) {
                let pciGroup = points[earfcn];
                // Over PCIs...
                for (let pci in pciGroup) {
                    let beamGroup = points[earfcn][pci];
                    for (let beam in beamGroup) {
                        baseEarfncs.push(parseInt(earfcn));
                        basePcis.push(parseInt(pci));
                        baseBeams.push(parseInt(beam));
                    }
                }
            }
            // Filtering EARFCNs and PCIs...
            let earpcis = utils.subEarpci(baseEarfncs, basePcis, baseBeams, earfcns, pcis);
            let filtEarfcns = earpcis.earfcns;
            let filtPcis = earpcis.pcis;
            let filtBeams = earpcis.beams;
            // For each reamining EARFCNs and PCIs...
            for (let i in filtEarfcns) {
                let earfcn = filtEarfcns[i];
                let pci = filtPcis[i];

                // beams list of the pci
                let beamList = filtBeams[pci];

                //if beam selected in drop-down menu
                if (beams[pci]) {
                    // Pushing asscoiated measurements in hexData...
                    for (let b in beamList) {
                        let currentBeam = beamList[b];

                        // if all beams are selected then add all points for each beam in the list
                        if (beams[pci].includes("all")) {
                            points[earfcn][pci][currentBeam].forEach(
                                (pt) => {
                                    let val = valChooser(earfcn, pci, pt);
                                    hexData.push([pt.lng, pt.lat, val]);
                                }
                            );
                        }
                        // if 'currentBeam' is selected then add all points of this beam
                        else if (beams[pci].includes(currentBeam.toString())) {
                            points[earfcn][pci][currentBeam].forEach(
                                (pt) => {
                                    let val = valChooser(earfcn, pci, pt);
                                    hexData.push([pt.lng, pt.lat, val]);
                                }
                            );
                        }
                    }
                } else {
                    // if no beams are selected then add all the existing measurements for an EARFCN/PCI couple
                    for (var e = 0; e < beamList.length; e++) {
                        var be = beamList[e];
                        if (!isNaN(be)) {
                            if (points[earfcn][pci][be]) {
                                points[earfcn][pci][be].forEach(
                                    (pt) => {
                                        let val = valChooser(earfcn, pci, pt);
                                        hexData.push([pt.lng, pt.lat, val]);
                                    }
                                );
                            }
                        }
                    }
                }
            }
            // Drawing the layer.
            layer.options.colorScaleExtent = [min, max];
            layer.redraw();
            // Adding data...
            layer.data(hexData);
        }
        /**
         * Draws the pins of the associated stations.
         *
         * @param {*} assocs Association data.
         * @param {*} antennas Antennas data.
         * @param {*} checkEarfcns Checked EARFCNs array.
         * @param {*} checkPcis Checked PCIs array.
         * @param {*} checkBeams Beams map.
         * @param {*} updateMethod Function to call when updates occur.
         * @param {Array} earfcns Selected EARFCNs (optional).
         * @param {Array} pcis Selected PCIs (optional).
         * @param {*} beams Beam data (optional).
         * @param {boolean} check_box Whether to show checkboxes (true/false).
         */
        drawAssocs(antdirs, assocs, antennas, checkEarfcns, checkPcis, checkBeams, updateMethod, earfcns = null, pcis = null, beams = null, check_box = true) {
            this._assocLayer.clearLayers();

            for (let cartoNum in assocs) {
                let assocList = assocs[cartoNum];  // Tableau d’associations
                let ant = antennas[cartoNum];      // Antenne de référence
                let antdirList = antdirs.filter(dir => dir.cartoNum === +cartoNum);  // Directions associées

                let azimuthData = [];

                assocList.forEach((assocItem) => {
                    let matchedDir = antdirList.find(dir => dir.antNum === assocItem.antNum);
                    if (matchedDir) {
                        azimuthData.push([
                            assocItem.antNum,      // ← Ajout de antNum
                            assocItem.pci,
                            matchedDir.latA,
                            matchedDir.lngA,
                            matchedDir.latB,
                            matchedDir.lngB
                        ]);
                    }
                });

                console.log(`Azimuth data for cartoNum ${cartoNum}:`);
                console.log(azimuthData);

                // Marqueur station
                let marker = L.marker([ant.lat, ant.lng], {
                    icon: styles.stationIcon()
                });

                // Popup selon le mode
                let popupContent = check_box
                    ? this.drawAssocPopup(azimuthData, ant, cartoNum, assocList, checkEarfcns, checkPcis, checkBeams, updateMethod, earfcns, pcis, beams)
                    : this.drawAssocPopupWithoutCheckbox(azimuthData, ant, cartoNum, assocList, checkEarfcns, checkPcis, checkBeams, updateMethod, earfcns, pcis, beams);

                marker.bindPopup(popupContent, {
                    closeOnClick: true,
                    autoClose: true
                });

                marker.addTo(this._assocLayer);
            }
        }



        /**
         * Draw the popup of an associated site.
         *
         * @param {number} cartoNum Cartoradio number of the site.
         * @param {*} assoc Association data.
         * @param {Array} checkEarfcns List of EARFCNs selected using checkboxes.
         * @param {function} checkPcis List of PCIs selected using checkboxes.
         * @param {function} updateMethod Layer update method.
         * @param {Array} earfcns Selected EARFCNs.
         * @param {Array} pcis  Selected PCIs.
         * @returns The div element of the popup.
         *
         * @function
         */
        drawAssocPopup(
            azimuthData,
            ant,
            cartoNum,
            assocList,
            checkEarfcns,
            checkPcis,
            checkBeams,
            updateMethod,
            earfcns = null,
            pcis = null,
            beams = null
        ) {
            let popDiv = document.createElement('div');

            popDiv.innerHTML = `
                <div class="tooltip-header" style="margin-bottom:8px;">
                <strong>Site Number:</strong> 
                <a href="https://www.cartoradio.fr/#/cartographie/all/lonlat/${ant.lng}/${ant.lat}" target="_blank" rel="noopener">
                    ${cartoNum}
                </a>
                <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${ant.lat},${ant.lng}" target="_blank" rel="noopener">
                    <img src="./img/pngegg.png" alt="Street View" width="32" height="32">
                </a>
                </div>`;

            let checkDiv = document.createElement('table');
            checkDiv.classList.add('check-table');
            checkDiv.style.width = '110%';
            checkDiv.style.borderCollapse = 'collapse';

            let thead = document.createElement('thead');
            let headerRow = document.createElement('tr');
            ['EARFCN', 'PCI', 'Azimuth (°)', 'Beams'].forEach(text => {
                let th = document.createElement('th');
                th.textContent = text;
                th.style.textAlign = 'left';
                th.style.padding = '4px 8px';
                th.style.borderBottom = '1px solid #ccc';
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            checkDiv.appendChild(thead);

            let tbody = document.createElement('tbody');

            let ascEarfcns = assocList.map(asc => asc.earfcn);
            let ascPcis = assocList.map(asc => asc.pci);

            let earpcis = utils.subEarpci(ascEarfcns, ascPcis, beams, earfcns, pcis);

            let groupedByPci = {};
            for (let i = 0; i < earpcis.earfcns.length; i++) {
                let pci = earpcis.pcis[i];
                let earfcn = earpcis.earfcns[i];
                let freq = utils.earfcnToFreqLte(earfcn);

                if (!groupedByPci[pci]) groupedByPci[pci] = [];
                groupedByPci[pci].push({ earfcn, freq });
            }

            let sortedPcis = Object.keys(groupedByPci).map(Number).sort((a, b) => a - b);

            for (let idx = 0; idx < sortedPcis.length; idx++) {
                let pci = sortedPcis[idx];
                checkBeams[pci] = ["all"];
                let entries = groupedByPci[pci];
                entries.sort((a, b) => b.freq - a.freq);

                let azimuth = '-';
                if (Array.isArray(azimuthData)) {
                    let match = azimuthData.find(row => row[1] === pci);
                    if (match) {
                        let latA = match[2];
                        let lngA = match[3];
                        let latB = match[4];
                        let lngB = match[5];
                        let azimuthAngle = utils.calculateAzimuth(latA, lngA, latB, lngB);
                        azimuth = `${azimuthAngle.toFixed(1)}° (${utils.getCardinalDirection(azimuthAngle)})`;
                    }
                }

                for (let { earfcn, freq } of entries) {
                    let row = document.createElement('tr');

                    let earfcnCell = document.createElement('td');
                    earfcnCell.style.padding = '4px 8px';
                    earfcnCell.style.verticalAlign = 'middle';

                    let wrapperLabel = document.createElement('label');
                    wrapperLabel.style.display = 'flex';
                    wrapperLabel.style.alignItems = 'center';
                    wrapperLabel.style.gap = '6px';

                    let checkBox = document.createElement('input');
                    checkBox.setAttribute('type', 'checkbox');
                    let checkId = 'check' + '-' + cartoNum + '-' + earfcn + '-' + pci;
                    checkBox.id = checkId;
                    checkBox.setAttribute('aria-label', `EARFCN ${earfcn}, PCI ${pci}`);

                    if (utils.indexOfEarpci(checkEarfcns, checkPcis, earfcn, pci) !== -1) {
                        checkBox.checked = true;
                    }

                    checkBox.onclick = (evt) => {
                        if (evt.target.checked) {
                            checkEarfcns.push(earfcn);
                            checkPcis.push(pci);
                        } else {
                            utils.removeEarpci(checkEarfcns, checkPcis, earfcn, pci);
                        }
                        updateMethod();
                    };

                    let labelText = document.createElement('span');
                    labelText.textContent = `${earfcn} (${freq?.toFixed(1)} MHz)`;

                    wrapperLabel.appendChild(checkBox);
                    wrapperLabel.appendChild(labelText);
                    earfcnCell.appendChild(wrapperLabel);

                    let pciCell = document.createElement('td');
                    pciCell.style.padding = '4px 8px';
                    pciCell.style.verticalAlign = 'middle';
                    pciCell.textContent = pci;

                    let azimuthCell = document.createElement('td');
                    azimuthCell.style.padding = '4px 8px';
                    azimuthCell.style.verticalAlign = 'middle';
                    azimuthCell.textContent = azimuth;

                    let beamCell = document.createElement('td');
                    beamCell.style.padding = '4px 8px';
                    beamCell.style.verticalAlign = 'middle';

                    if (pcis != null && earfcns != null && beams?.[pci]) {
                        let current_beams = beams[pci].sort();
                        current_beams = current_beams.filter((item, index) => current_beams.indexOf(item) === index);

                        let select_beams = document.createElement('select');
                        select_beams.style.minWidth = '120px';

                        let optionAll = document.createElement('option');
                        optionAll.text = "Best beam";
                        optionAll.value = "all";
                        select_beams.add(optionAll);

                        for (let beam of current_beams) {
                            let option = document.createElement('option');
                            option.text = beam;
                            option.value = beam;
                            select_beams.add(option);
                        }

                        select_beams.addEventListener('change', function () {
                            checkBeams[pci] = [select_beams.value];
                            updateMethod();
                        });

                        beamCell.appendChild(select_beams);
                    } else {
                        beamCell.textContent = '-';
                    }

                    row.append(earfcnCell, pciCell, azimuthCell, beamCell);
                    tbody.appendChild(row);
                }
            }

            checkDiv.appendChild(tbody);
            popDiv.appendChild(checkDiv);
            return popDiv;
        }

        drawAssocPopupWithoutCheckbox(
            azimuthData,
            ant,
            cartoNum,
            assoc,
            checkEarfcns,
            checkPcis,
            checkBeams,
            updateMethod,
            earfcns = null,
            pcis = null,
            beams = null
            ) {
            // Create the main container
            let popDiv = document.createElement('div');

            // Header with site number and links
            popDiv.innerHTML = `
                <div class="tooltip-header" style="margin-bottom:8px;">
                <strong>Site Number:</strong> 
                <a href="https://www.cartoradio.fr/#/cartographie/all/lonlat/${ant.lng}/${ant.lat}" target="_blank" rel="noopener">
                    ${cartoNum}
                </a>
                <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${ant.lat},${ant.lng}" target="_blank" rel="noopener">
                    <img src="./img/pngegg.png" alt="Street View" width="32" height="32">
                </a>
                </div>
            `;

            // Table element setup
            let checkDiv = document.createElement('table');
            checkDiv.classList.add('check-table');
            checkDiv.style.width = '100%';
            checkDiv.style.borderCollapse = 'collapse';

            // Table header with Azimuth added before Beams
            let thead = document.createElement('thead');
            let headerRow = document.createElement('tr');
            ['EARFCN', 'PCI', 'Azimuth (°)', 'Beams'].forEach(text => {
                let th = document.createElement('th');
                th.textContent = text;
                th.style.textAlign = 'left';
                th.style.padding = '4px 8px';
                th.style.borderBottom = '1px solid #ccc';
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);
            checkDiv.appendChild(thead);

            // Table body
            let tbody = document.createElement('tbody');

            // Extract EARFCNs and PCIs from assoc array
            let ascEarfcns = assoc.map((asc) => asc.earfcn);
            let ascPcis = assoc.map((asc) => asc.pci);
            // Filter EARFCN/PCI pairs using utils.subEarpci with optional beams, earfcns, and pcis
            let earpcis = utils.subEarpci(ascEarfcns, ascPcis, beams, earfcns, pcis);

            // Group EARFCNs by PCI
            let groupedByPci = {};
            for (let i = 0; i < earpcis.earfcns.length; i++) {
                let pci = earpcis.pcis[i];
                let earfcn = earpcis.earfcns[i];
                let freq = utils.earfcnToFreqLte(earfcn);

                if (!groupedByPci[pci]) groupedByPci[pci] = [];
                groupedByPci[pci].push({ earfcn, freq });
            }

            // Sort PCIs ascending
            let sortedPcis = Object.keys(groupedByPci).map(Number).sort((a, b) => a - b);

            // Build table rows
            for (let pci of sortedPcis) {
                checkBeams[pci] = ["all"];
                let entries = groupedByPci[pci];

                // Sort entries by descending frequency
                entries.sort((a, b) => b.freq - a.freq);

                for (let { earfcn, freq } of entries) {
                let select_beams = null;

                if (pcis != null && earfcns != null && beams?.[pci]) {
                    let current_beams = beams[pci].sort();
                    current_beams = current_beams.filter((item, index) => current_beams.indexOf(item) === index);

                    select_beams = document.createElement('select');
                    select_beams.style.minWidth = '120px';

                    let optionAll = document.createElement('option');
                    optionAll.text = "Best beam";
                    optionAll.value = "all";
                    select_beams.add(optionAll);

                    for (let beam of current_beams) {
                    let option = document.createElement('option');
                    option.text = beam;
                    option.value = beam;
                    select_beams.add(option);
                    }

                    select_beams.addEventListener('change', function () {
                    checkBeams[pci].pop();
                    let selectedValue = select_beams.value;
                    checkBeams[pci].push(selectedValue);
                    updateMethod();
                    });
                }

                // Calculate azimuth from site to antenna (approximate)
                let azimuth = '-';
                if (Array.isArray(azimuthData)) {
                    let match = azimuthData.find(row => row[1] === pci);
                    if (match) {
                        let latA = match[2];
                        let lngA = match[3];
                        let latB = match[4];
                        let lngB = match[5];
                        let azimuthAngle = utils.calculateAzimuth(latA, lngA, latB, lngB);
                        azimuth = `${azimuthAngle.toFixed(1)}° (${utils.getCardinalDirection(azimuthAngle)})`;
                    }
                }

                // Create table row
                let row = document.createElement('tr');

                // EARFCN cell
                let earfcnCell = document.createElement('td');
                earfcnCell.style.padding = '4px 8px';
                earfcnCell.style.verticalAlign = 'middle';
                earfcnCell.textContent = `${earfcn} (${freq?.toFixed(1)} MHz)`;

                // PCI cell
                let pciCell = document.createElement('td');
                pciCell.style.padding = '4px 8px';
                pciCell.style.verticalAlign = 'middle';
                pciCell.textContent = pci;

                // Azimuth cell
                let azimuthCell = document.createElement('td');
                azimuthCell.style.padding = '4px 8px';
                azimuthCell.style.verticalAlign = 'middle';
                azimuthCell.textContent = azimuth;

                // Beams cell
                let beamCell = document.createElement('td');
                beamCell.style.padding = '4px 8px';
                beamCell.style.verticalAlign = 'middle';
                if (select_beams) {
                    beamCell.appendChild(select_beams);
                } else {
                    beamCell.textContent = '-';
                }

                row.append(earfcnCell, pciCell, azimuthCell, beamCell);
                tbody.appendChild(row);
                }
            }

            checkDiv.appendChild(tbody);
            popDiv.appendChild(checkDiv);

            return popDiv;
            }




        /**
         * Write serving points on a group layer.
         * @param {*} layer Leaflet group layer.
         * @param {*} pointLayers Dictionary of points layers, classed by EARFCN / PCI.
         * @param {*} earfcns Selected EARFCNs.
         * @param {*} pcis  Selected PCIs.
         *
         * @function
         */
        setPointLayer(layer, pointLayers, earfcns = null, pcis = null, beams = null) {
            if (earfcns && pcis && earfcns.length !== pcis.length)
                throw new Error('earfncs and pcis should have the same length');
            layer.clearLayers();
            const earfcnLayers = earfcns ? earfcns.reduce((obj, earfcn) => {
                obj[earfcn] = pointLayers[earfcn];
                return obj;
            }, {}) : {...pointLayers};
            const layers = [];
            for (const earfcn in earfcnLayers) {
                const earfcnInt = parseInt(earfcn);
                const pciLayers = earfcnLayers[earfcn];
                for (const pci in pciLayers) {
                    const pciInt = parseInt(pci);
                    const beamsLayers = pciLayers[pci];
                    if (pcis) {
                        const pciIndexes = utils.indexesOf(pcis, pciInt);
                        pciIndexes.forEach((pciIndex) => {
                            if (
                                pciIndex !== -1 &&
                                ((earfcns && earfcnInt === earfcns[pciIndex]) || !earfcns)
                            ) {
                                for (const beam in beamsLayers) {
                                    const beamLayer = beamsLayers[beam];
                                    if (beams[pciInt]) {
                                        if (beams[pciInt].includes("all")) {
                                            layers.push(beamLayer);
                                        } else {
                                            const beamIndexes = utils.indexesOf(beams[pciInt], beam);
                                            beamIndexes.forEach((beamIndex) => {
                                                if (beamIndex !== -1) {
                                                    layers.push(beamLayer);
                                                }
                                            });
                                        }
                                    } else {
                                        layers.push(beamLayer);
                                    }
                                }
                            }
                        });
                    } else {
                        for (const beam in beamsLayers) {
                            const beamLayer = beamsLayers[beam];
                            layers.push(beamLayer);
                        }
                    }
                }
            }
            layers.forEach((l) => l.addTo(layer));
        }
        /**
         * Draws a global measurements heatmap layer.
         * @param {*} layer Layer to draw on.
         * @param {*} measurements Global measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum value.
         * @param {number} max Maximum value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         *
         * @function
         */
        drawHex(layer, measurements, earfcns, pcis, beams, min, max, reqEarfcns = null, reqPcis = null, reqBeams = null) {
            let hexData = [];

            // all measurements requested by EARFCNs/PCIs/BEAMs
            let earpcis = utils.subEarpci(earfcns, pcis, beams, reqEarfcns, reqPcis, reqBeams);

            // For each measurement object in the list (corresponds to a line 'MEASUREMENT')
            measurements.forEach(
                (measObj) => {
                    let meas = measObj.meas;
                    // indexes of selected measurements at the same timestamp
                    earpcis.indices.forEach(
                        (i) => {
                            let m = meas[i];
                            if (m) {
                                hexData.push([measObj.lng, measObj.lat, m]);
                            }
                        }
                    );
                }
            );
            layer.options.colorScaleExtent = [min, max];
            layer.redraw();
            layer.data(hexData);
        }
        /**
         * Draw the TAC layer from serving points data.
         * @param {*} points Serving points data.
         * @returns Return an object containing multiple TAC points layers associated to EARFCNs / PCIs.
         *
         * @function
         */
        drawTAC(points) {
            return this.drawPoints(points, (_e, _pc, p) => p.tac, styles.tacColor);
        }
        /**
         * Draw the PCI layer from serving points data.
         * @param {*} points Serving points data.
         * @returns Return an object containing multiple PCI points layers associated to EARFCNs / PCIs.
         *
         * @function
         */
        drawPCI(points, col = 1) {
            return this.drawPoints(points, (_e, pc, _p) => pc, (p) => styles.pciColor(p, col));
        }
        
        /**
         * Draws the serving PCI layer.
         * @param {*} points Serving measurement points.
         * @param {number} min Minimum PCI value (used for the color range).
         * @param {number} max Maximum PCI value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         * @param {Array} beams Selected beams.
         *
         * @function
         */
        /*drawServingPCI(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingPCI, points, (_e, _p, pt) => pt.pci, // Utilisation de pt.pci pour PCI
                min, max, earfcns, pcis, beams, // Passage des paramètres pour filtrer les EARFCN, PCI et beams
            );
        }*/

        /**
         * Draws the serving RSRP layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum RSRP value (used for the color range).
         * @param {number} max Maximum RSRP value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         *
         * @function
         */
        drawServingRSRP(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingRSRP, points, (_e, _p, pt) => Math.round(pt.rsrp),
                min, max, earfcns, pcis, beams,
            );
        }
        /**
         * Draws the serving RSRQ layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum RSRQ value (used for the color range).
         * @param {number} max Maximum RSRQ value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         *
         * @function
         */
        drawServingRSRQ(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingRSRQ, points, (_e, _p, pt) => Math.round(pt.rsrq),
                min, max, earfcns, pcis, beams
            );
        }
        /**
         * Draws the serving RSSI layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum RSSI value (used for the color range).
         * @param {number} max Maximum RSSI value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         *
         * @function
         */
        drawServingRSSI(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingRSSI, points, (_e, _p, pt) => Math.round(pt.rssi),
                min, max, earfcns, pcis, beams
            );
        }
        /**
         * Draws the serving CINR layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum CINR value (used for the color range).
         * @param {number} max Maximum CINR value (used for the color range).
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         *
         * @function
         */
        drawServingCINR(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingCINR, points, (_e, _p, pt) => Math.round(pt.cinr),
                min, max, earfcns, pcis, beams
            );
        }

        /**
         * Draws the serving CINR layer.
         * @param {function} points Serving measurement points.
         * @param {number} min Minimum PCI value (used for the color range)// not used.
         * @param {number} max Maximum PCI value (used for the color range)//not used.
         * @param {Array} earfcns Selected EARFCNs
         * @param {Array} pcis Selected PCIs.
         *
         * @function
         */
        drawServingPCI_tooltip(points, min, max, earfcns = null, pcis = null, beams = null) {
            this.drawServingHex(
                this._servingPciTooltipLayer, points, (_e, _p, pt) => _p,
                min, max, earfcns, pcis, beams
            );
        }

        /**
         * Draws the global RSRP layer.
         *
         * @param {*} measurements Global RSRP measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum RSRP value.
         * @param {number} max Maximum RSRP value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         *
         * @function
         */
        drawRSRP(measurements, earfcns, pcis, beams, min, max, subEarfcns = null, subPcis = null, subBeams = null) {
            this.drawHex(this._rsrpLayer, measurements, earfcns, pcis, beams, min, max, subEarfcns, subPcis, subBeams);
        }
        /**
         * Draws the global RSRQ layer.
         *
         * @param {*} measurements Global RSRQ measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum RSRQ value.
         * @param {number} max Maximum RSRQ value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         *
         * @function
         */
        drawRSRQ(measurements, earfcns, pcis, beams, min, max, subEarfcns = null, subPcis = null, subBeams = null) {
            this.drawHex(this._rsrqLayer, measurements, earfcns, pcis, beams, min, max, subEarfcns, subPcis, subBeams);
        }
        /**
         * Draws the global RSSI layer.
         *
         * @param {*} measurements Global RSSI measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum RSSI value.
         * @param {number} max Maximum RSSI value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         *
         * @function
         */
        drawRSSI(measurements, earfcns, pcis, beams, min, max, subEarfcns = null, subPcis = null, subBeams = null) {
            this.drawHex(this._rssiLayer, measurements, earfcns, pcis, beams, min, max, subEarfcns, subPcis, subBeams);
        }
        /**
         * Draws the global PCI-tooltip layer.
         *
         * @param {*} measurements Global RSSI measurement data.
         * @param {Array} earfcns EARFCNs for list of (EARFCN, PCI) pairs.
         * @param {Array} pcis PCIs for list of (EARFCN, PCI) pairs.
         * @param {number} min Minimum RSSI value.
         * @param {number} max Maximum RSSI value.
         * @param {Array} reqEarfcns Selected EARFCNs
         * @param {Array} reqPcis Selected PCIs.
         *
         * @function
         */
        /*drawPCI(measurements, earfcns, pcis, beams, min, max, subEarfcns = null, subPcis = null, subBeams = null) {
            this.drawHex(this._pciLayer, measurements, earfcns, pcis, beams, min, max, subEarfcns, subPcis, subBeams);
        }*/

        /**
         * Updates the TAC layer.
         *
         * @param {*} points Serving points data.
         * @param {Array} earfcn Selected EARFCNs.
         * @param {Array} pci  Selected PCIs.
         *
         * @function
         */
        updateTACLayer(points, earfcn = null, pci = null, beam = null) {
            this._nonFilteredTAC = this.drawTAC(points);
            this.setPointLayer(this._tacLayer, this._nonFilteredTAC, earfcn, pci, beam);
        }
        /**
         * Updates the PCI layer.
         *
         * @param {*} points Serving points data.
         * @param {Array} earfcn Selected EARFCNs.
         * @param {Array} pci  Selected PCIs.
         *
         * @function
         */
        updatePCILayer(points, earfcn = null, pci = null, beam = null, col = 1) {
            this._nonFilteredPCI = this.drawPCI(points, col);
            
            this.setPointLayer(this._pciLayer, this._nonFilteredPCI, earfcn, pci, beam);
            
        }
        /**
         * Sets Voronoi cells layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setCellLayer(b) {
            this._setLayerVisibility(this._cellLayer, b);
        }
        /**
         * Sets antennas layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setAntLayer(b) {
            this._setLayerVisibility(this._antLayer, b);
        }
        /**
         * Sets TAC layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setTACLayer(b) {
            this._setLayerVisibility(this._tacLayer, b);
        }
        /**
         * Sets PCI layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setPCILayer(b) {
            this._setLayerVisibility(this._pciLayer, b);
        }
        /**
         * Sets association layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setAssocLayer(b) {
            this._setLayerVisibility(this._assocLayer, b);
        }
        /**
         * Sets serving RSRP layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingRSRP(b) {
            this._setLayerVisibility(this._servingRSRP, b);
        }
        /**
         * Sets serving RSRQ layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingRSRQ(b) {
            this._setLayerVisibility(this._servingRSRQ, b);
        }
        /**
         * Sets serving RSSI layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingRSSI(b) {
            this._setLayerVisibility(this._servingRSSI, b);
        }
        /**
         * Sets serving CINR layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingCINR(b) {
            this._setLayerVisibility(this._servingCINR, b);
        }
        /**
         * Sets serving pci_tooltip layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setServingPCITOOLTIP(b) {
            this._setLayerVisibility(this._servingPciTooltipLayer, b);
        }
        /**
         * Sets global RSRP layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setRSRP(b) {
            this._setLayerVisibility(this._rsrpLayer, b);
        }
         /**
         * Sets global pci_tooltip layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setpciTooltip(b) {
            this._setLayerVisibility(this._pciTooltipLayer, b);
        }
        /**
         * Sets global RSRQ layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setRSRQ(b) {
            this._setLayerVisibility(this._rsrqLayer, b);
        }
        /**
         * Sets global RSSI layer visibility.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         */
        setRSSI(b) {
            this._setLayerVisibility(this._rssiLayer, b);
        }
        // setCINR(b) { this._setLayerVisibility(this._cinrLayer, b); }
        /**
         * Sets the visibility of a layer.
         * @param {*} layer Layer.
         * @param {boolean} b true to set the layer visible.
         *
         * @function
         * @private
         */
        _setLayerVisibility(layer, b) {
            if (b && !this._map.hasLayer(layer)) layer.addTo(this._map);
            else if (!b && this._map.hasLayer(layer)) layer.removeFrom(this._map);
        }
        /**
         * Draws EARFCNs / PCIs selectors.
         * @param {Array} earfcns EARFCNs from (EARFCN, PCI) layer list.
         * @param {Array} pcis PCIs from (EARFCN, PCI) layer list.
         *
         * @function
         */
        drawSelectors(earfcns, pcis, pciNb) {
            // Getting selector elements.
            let pciSelector = document.querySelector('#pci-select');
            let earSelector = document.querySelector('#EARFCN_select');
            // Adding "Serving" and "All" options.
            earSelector.innerHTML = '<option value="serving-earfcn">Serving EARFCN</option>'
                + '<option value="all-earfcns">All EARFCNs</option>';
            pciSelector.innerHTML = '<option value="serving-pci">Serving PCI</option>'
                + '<option value="all-pcis">All PCIs</option>';
            // Order relation used to sort EARFCNs and PCIs numbers.
            let order = (a, b) => {
                let numA = parseInt(a);
                let numB = parseInt(b);
                if (numA === numB) return 0;
                else if (numA < numB) return -1;
                else return 1;
            }
            // Adding EARFCNs options.
            earfcns.sort(order).forEach(
                (earfcn) => {
                    // Selector used to ensure we add only once time the same option.
                    if (!document.querySelector('#EARFCN_select option[value="' + earfcn + '"]')) {
                        // Creating option element.
                        let option = document.createElement('option');
                        option.setAttribute('value', earfcn);
                        option.innerHTML = earfcn;
                        // Adding it.
                        earSelector.append(option);
                    }
                }
            );
            // Adding PCIs options.
            pcis.sort(order).forEach(
                (pci) => {
                    if (!document.querySelector('#pci-select option[value="' + pci + '"]')) {
                        let option = document.createElement('option');
                        option.setAttribute('value', pci);
                        option.innerHTML = pci + " (" + pciNb[pci] +")";
                        pciSelector.append(option);
                    }
                }
            );
        }
    },
    /**
     * Creates an heatmap layer, with a custom tooltip displayable while hovering the layer.
     * Hexagons on the heatmap represents the minimum data point over this hexagon.
     *
     * @param {String} tooltip Hover tooltip text.
     * @param {*} options Style of the layer.
     *
     * @returns The new hex layer.
     *
     * @function
     */
    hexBin: function (tooltip, options) {
        // Creating the layer with style.
        let hex = L.hexbinLayer(options);
        // Minimum point selection function.
        let minFunct = function (d) {
            let tempArray = d.map((i) => i.o[2]);
            return Math.min.apply(null, tempArray);
        }
        hex._fn.colorValue = minFunct;
        // Handler used to show the tooltip.
        hex.hoverHandler(
            L.HexbinHoverHandler.tooltip({
                tooltipContent: (d) => tooltip + ': ' + minFunct(d)
            })
        );
        return hex;
    }
}
