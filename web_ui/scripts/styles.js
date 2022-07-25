const styles = {

    STYLE_DELIMITER: {
        color: 'green',
        weight: 2,
        opacity: 1,
        smoothFactor: 1
    },

    STYLE_ANTENNA: {
        color: 'green',
        weight: 4,
        opacity: 1,
        smoothFactor: 1
    },

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

    pciColor: function (pci, colorChoice) {

        let testedVal = (
            (colorChoice != 0) ? 
            (pci % 9) * 57 + Math.trunc(pci / 9)
            : (pci % 3) * 170 + Math.trunc(pci / 3)
        ) + colorChoice;

        let colorVal = 10 + testedVal * 32895;
        
        return colorVal.toString(16);

    },

    tacColor: function (tac) {

        let lcolor = (tac & 0xFF00) >> 8;
        let rcolor = tac & 0x00FF;

        let rolocr = parseInt(rcolor.toString(2).split("").reverse().join(""), 2);

        let color = lcolor << 16 | (rcolor & 0x3) << 14 | rolocr;

        return color.toString(16);

    },

    hexColor: function (min, max) {

        let colorRange = [
            "blue","#52a4ff","#00f9ff","#50ff7f",     
            "#00FF00","#7CFF00","#B0FF00","#C2FF00","#D4FF00",
            "#E5FF00","#FFF600","#FFE400","#FFD300","#FFAF00",
            "#FF9E00","#FF8C00","#FF6900","#FF5700","red"
        ];  // FIXME Temporary.

        // copied from the old program.
        return {
			radius : 12,
			opacity: 0.6,
			duration: 200,

			colorScaleExtent: [ min, max ],
			radiusScaleExtent: [ 1, undefined ],
			colorDomain: null,
			radiusDomain: null,
			colorRange:["black","MidnightBlue","Navy","DarkBlue",
            "MediumBlue","blue","RoyalBlue","DodgerBlue",
            "DeepSkyBlue","LightSkyBlue", "Cyan", "PaleTurquoise",
            "aquamarine","lightgreen","mediumaquamarine","GreenYellow",
            "Lime","chartreuse","yellow","Gold", "orange",
            "DarkOrange", "Coral", "Tomato","Crimson"],
			radiusRange: [ 1, 12 ],

			pointerEvents: 'all'
        }

    },

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

    mapStyle: function (baseMap) {

        // copied from the old program.
        return {
            center: [47.148, 4.474],
            maxZoom: 17, 
            zoom: 6,
            layers: baseMap
        };
    }

}