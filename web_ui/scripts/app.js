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

                this.#drawingMap.drawCells(vor, ants, dels);
                this.#drawingMap.drawAssocs(this.#fileReader.assocs, antennas);

                this.#drawingMap.setAntLayer(true);

            }

        }

    }

};

(function () {
    new app.App();
})();