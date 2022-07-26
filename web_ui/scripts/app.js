const app = {
    
    // Model: class {

    //     constructor() {

    //     }

    // },

    // Controller: class {

    //     constructor() {

    //     }

    // },

    // View: class {

    //     constructor(map) {

    //     }

    // },

    App: class {

        #map
        #drawingMap
        #fileReader

        #earfcnOnServing = true;
        #pciOnServing = true;
        #onServing = true;

        #selEarfcn = null;
        #selPci = null;

        constructor() {

            // Background layers of the map.

            let baseMaps = {
                'Base Layer': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }),
                'Dark Layer': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
                    attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
                })
            };

            // Creating the map.
            this.#map = L.map('map', styles.mapStyle(baseMaps['Base Layer']));

            // Adding background layers. 
            L.control.layers(baseMaps, null, { collapsed: false }).addTo(this.#map);

            this.#drawingMap = new drawing.Map(this.#map);

            // Setting up UI Events.

            document.querySelector('#fileSelect').onclick = (_) => {

                let inputElt = document.querySelector('#fileElem');
                inputElt.click();

            };

            document.querySelector('#fileElem').onchange = async (evt) => {

                let file = evt.srcElement.files[0];
                this.#fileReader = new csvread.CSVReader(file);
                await this.#fileReader.readFile();

                let antennas = this.#fileReader.antennas;

                let vor = processing.calcVoronoi(antennas);
                let dels = processing.calcDelimiters(vor, antennas);
                let ants = processing.calcAntennas(this.#fileReader.antennaDirections);

                let earfcns = this.#fileReader.earfcns;
                let pcis = this.#fileReader.pcis;

                this.#drawingMap.drawCells(vor, ants, dels);
                this.#drawingMap.drawAssocs(this.#fileReader.assocs, antennas);

                this.#drawingMap.setAntLayer(true);

                this.#drawingMap.setAssocLayer(true);

                this.#drawingMap.drawSelectors(earfcns, pcis);

                this.update();

            };

            document.querySelector('#Theory_Cell').onclick = (evt) => {
                this.#drawingMap.setCellLayer(evt.srcElement.checked);
            };

            document.querySelector('#sites-select').onchange = (evt) => {

                let onlySitesSel = evt.srcElement.value === 'only-sites';

                // if (onlySitesSel) $('.check-div').show();
                // else $('.check-div').hide();

            };

            document.querySelector('#Tracking_area').onclick = (evt) => {
                this.#drawingMap.setTACLayer(evt.srcElement.checked);
            };

            document.querySelector('#PCI').onclick = (evt) => {
                this.#drawingMap.setPCILayer(evt.srcElement.checked);
            };

            document.querySelector('#RSRP').onclick = (evt) => {

                let checked = evt.srcElement.checked;
                
                if (this.#onServing) this.#drawingMap.setServingRSRP(checked);
                else this.#drawingMap.setRSRP(checked);

            };

            document.querySelector('#rsrq').onclick = (evt) => {
                
                let checked = evt.srcElement.checked;
                
                if (this.#onServing) this.#drawingMap.setServingRSRQ(checked);
                else this.#drawingMap.setRSRQ(checked);

            };

            document.querySelector('#rssi').onclick = (evt) => {
                
                let checked = evt.srcElement.checked;
                
                if (this.#onServing) this.#drawingMap.setServingRSSI(checked);
                else this.#drawingMap.setRSSI(checked);

            };

            document.querySelector('#cinr').onclick = (evt) => {
                
                let checked = evt.srcElement.checked;
                
                if (this.#onServing) this.#drawingMap.setServingCINR(checked);
                else this.#drawingMap.setCINR(checked);

            };

            document.querySelector('#EARFCN_select').onchange = (evt) => {

                let val = evt.srcElement.value;

                this.#earfcnOnServing = (val === 'serving-earfcn');

                this.#selEarfcn = (!this.#earfcnOnServing) ? [parseInt(val)] : null;

                this.#onServing = this.#earfcnOnServing || this.#pciOnServing;

                this.update();

            }

            document.querySelector('#pci-select').onchange = (evt) => {

                let val = evt.srcElement.value;

                this.#pciOnServing = (val === 'serving-pci');

                this.#selPci = (!this.#pciOnServing) ? [parseInt(val)] : null;
                
                this.#onServing = this.#earfcnOnServing || this.#pciOnServing;

                this.update();

            }

        }

        update() {

            let points = this.#fileReader.points;

            this.#drawingMap.updatePCILayer(points, this.#selEarfcn, this.#selPci);
            this.#drawingMap.updateTACLayer(points, this.#selEarfcn, this.#selPci);

            this.#drawingMap.drawServingRSRP(points, this.#selEarfcn, this.#selPci);
            this.#drawingMap.drawServingRSRQ(points, this.#selEarfcn, this.#selPci);
            this.#drawingMap.drawServingRSSI(points, this.#selEarfcn, this.#selPci);
            this.#drawingMap.drawServingCINR(points, this.#selEarfcn, this.#selPci);
        }

    }

};

(function () {
    new app.App();
})();