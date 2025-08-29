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

        /**
         * Application class constructor.
         * @constructor
         */
        constructor() {

            // Background layers of the map.

            let baseMaps = {
                'Base Layer': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }),
                'Dark Layer': L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
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
         * Update sites pins and their checkboxes, following selected EARFCNs and PCIs.
         * 
         * @function
         */
        updateAssocs() {
            // Getting selected EARFCNS / PCIS.
            let earpcis = utils.subEarpci(this._fileReader.earfcns,this._fileReader.pcis, this._fileReader._beams, this._selEarfcns, this._selPcis);
            let frequency=utils.earfcnToFreqLte(5225);
            // Redrawing associated stations pins.
            this._drawingMap.drawAssocs(
                this._fileReader.antennaDirections, this._fileReader.assocs, this._fileReader.antennas, this._checkEarfcns, this._checkPcis, this._checkBeams,
                () => this.update(), earpcis.earfcns, earpcis.pcis, earpcis.beams,!this._allSites, this._technology);
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


                console.log("technology is: " + this._technology);
                console.log("version is: " + this._version);

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
                // Remplir les infos dynamiquement
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
                console.log(points);
            
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
