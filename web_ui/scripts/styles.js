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
            "black","MidnightBlue","Navy","DarkBlue",
            "MediumBlue","blue","RoyalBlue","DodgerBlue",
            "DeepSkyBlue","LightSkyBlue", "Cyan", "PaleTurquoise",
            "aquamarine","lightgreen","mediumaquamarine","GreenYellow",
            "Lime","chartreuse","yellow","Gold", "orange",
            "DarkOrange", "Coral", "Tomato","Crimson"
        ];  // FIXME Temporary.

        return {
            radius : 12,
            opacity: 0.5,
            duration: 200,

            colorScaleExtent: [ 0, 96 ],
            radiusScaleExtent: [ 1, undefined ],
            colorDomain: "linear",
            radiusDomain: null,
            colorRange:colorRange,
            radiusRange: [ 1, 12 ],
            pointerEvents: 'all'
        }

    }

}