/**
 * Contains Leaflet style (options) definition functions.
 * 
 * @namespace
 */
const styles = {

    /**
     * @returns Sector delimiter style.
     * 
     * @function
     */
    styleDelimiter: function () {
        return {
            color: 'green',
            weight: 2,
            opacity: 1,
            smoothFactor: 1
        };
    },

    /**
     * @returns Antenna directivity "branches" style.
     * 
     * @function
     */
    styleAntenna: function () {
        return {
            color: 'green',
            weight: 4,
            opacity: 1,
            smoothFactor: 1
        };
    },

    /**
     * Heatmap gradient constant.
     * 
     * @constant
     */
    HEATMAP: [],

    /**
     * yelo
     * @param {number} opac Opacity (0.0-1.0)
     * @param {String} hexColor Hexadecimal color (RRGGBB).
     * @returns Voronoi cells style of opacity opac and color hexColor.
     * 
     * @function
     */
    polyStyle: function (opac, hexColor) {

        return {
            weight: 2,
            opacity: 1,
            color: '#'+ hexColor,
            dashArray: '5',
            fillOpacity: opac,
            fillColor: '#'+ hexColor,
        };

    },

    /**
     * 
     * @param {String} color Hexadecimal color (RRGGBB).
     * @returns Style of points of color color.
     * 
     * @function
     */
    pointStyle: function (color)  {
        return {
            radius: 3,
            opacity: 1,
            color: '#'+color,
            noMask: true,
            lineColor: '#'+ color,
            useAbsoluteRadius: false
        }
    },

    /**
     * 
     * @param {number} pci PCI value.
     * @param {number} colorChoice Alternate color for PCI (0 or 1). 
     * @returns Style of PCI points of pci PCI value and colorChoice alt. color value.
     * 
     * @function
     */
    pciColor: function (pci, colorChoice) {
        // originated from the old program.

        let testedVal = (
            (colorChoice !== 0) ? 
            (pci % 9) * 57 + Math.trunc(pci / 9)
            : (pci % 3) * 170 + Math.trunc(pci / 3)
        ) + colorChoice;

        let colorVal = 10 + testedVal * 32895;
        
        return colorVal.toString(16);

    },

    /**
     * 
     * @param {number} tac TAC value. 
     * @returns Color of a TAC point of value tac.
     * 
     * @function
     */
    tacColor: function (tac) {
        // originated and readapted from the old program.

        let lcolor = (tac & 0xFF00) >> 8;
        let rcolor = tac & 0x00FF;

        let rolocr = parseInt(rcolor.toString(2).split("").reverse().join(""), 2);

        let color = lcolor << 16 | (rcolor & 0x3) << 14 | rolocr;

        return color.toString(16);

    },

    /**
     * 
     * @param {number} min Minimum measurement value.
     * @param {number} max Maximum measurement value.
     * @returns Style for heatmap hexagons, with a color range over [min, max].
     * 
     * @function
     */
    hexColor: function (min, max) {

        // copied from the old program.
        return {
			radius : 12,
			opacity: 0.6,
			duration: 200,

			colorScaleExtent: [ min, max ],
			radiusScaleExtent: [ 1, undefined ],
			colorDomain: null,
			radiusDomain: null,
			colorRange: styles.HEATMAP,
			radiusRange: [ 1, 12 ],

			pointserEvents: 'all'
        }

    },
    hexColor_pci: function () {

        // copied from the old program.
        return {
			radius : 12,
			opacity: 0,
			duration: 200,
			pointserEvents: 'all'
        }

    },

    /**
     * 
     * @returns The icon of an associated base station.
     * 
     * @function
     */
    stationIcon: function () {

        // copied from the old program.
        return L.icon({

            iconUrl: 'wifi-zone-marker.png',
            shadowUrl: 'site-shadow.png',
            iconSize:     [32, 32], // size of the icon
            shadowSize:   [39, 40], // size of the shadow
            iconAnchor:   [15,28], // point of the icon which will correspond to marker's location
            shadowAnchor: [12, 36]
        });

    },

    loaderStyle: function(state){
        return {
            border: "6px solid #f3f3f3",
            borderTop: "6px solid #3498db",
            borderRadius: "50%",
            width: "40px",
            height: "40px",
            animation: "spin 1s linear infinite",
            margin: "auto",
            display: state 
        };

    },

    /**
     * 
     * @param {*} baseMap Lealfet map default background.
     * @returns Style of a Leaflet map with default backround baseMap.
     * 
     * @function
     */
    mapStyle: function (baseMap) {

        // copied from the old program.
        return {
            center: [47.148, 4.474],
            maxZoom: 100, 
            zoom: 6,
            layers: baseMap
        };
    },
    

    /**
     * Produces a gradient made of a given number of color for HexBin layers.
     * 
     * The gradiant is created using RGB-hex from HSL (Hue-Saturation-Luminosity) conversion, 
     * by iterating over HSL values with H in [240, 0], over the given number of steps, 
     * and with S: 1.0, L: 0.5.
     * 
     * @param {number} stepNum Number of colors.
     * @returns An Array of stepNum hexadecimal RGB color code, forming an heatmap gradient.
     * 
     * @function
     */
    generateGradient: function (stepNum) {

        let result = [];

        let floatStep = 240.0 / stepNum;    // Step size.

        // Iterating step by step...
        for (let i = stepNum; i > 0; i--) {

            let hue = i * floatStep;    // Current hue.
            hue = hue < 0 ? 0 : hue;    // Avoiding hue being less than 0 due to floating-point errors.

            // Adding new hexadecimal code to results.
            result.push(d3.hsl(hue, 1.0, 0.5).formatHex())

        }

        return result;

    }

};

(function () { styles.HEATMAP = styles.generateGradient(255); })();