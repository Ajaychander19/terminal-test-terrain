/**
 * Contains general-purpose function for program.
 * 
 * @namespace
 */
const lteBands = [
  { band: 1, earfcnMin: 0, earfcnMax: 599, nOffsDl: 0, dlFreqLow: 2110.0 },
  { band: 2, earfcnMin: 600, earfcnMax: 1199, nOffsDl: 600, dlFreqLow: 1930.0 },
  { band: 3, earfcnMin: 1200, earfcnMax: 1949, nOffsDl: 1200, dlFreqLow: 1805.0 },
  { band: 4, earfcnMin: 1950, earfcnMax: 2399, nOffsDl: 1950, dlFreqLow: 2110.0 },
  { band: 5, earfcnMin: 2400, earfcnMax: 2649, nOffsDl: 2400, dlFreqLow: 869.0 },
  { band: 6, earfcnMin: 2650, earfcnMax: 2749, nOffsDl: 2650, dlFreqLow: 875.0 },
  { band: 7, earfcnMin: 2750, earfcnMax: 3449, nOffsDl: 2750, dlFreqLow: 2620.0 },
  { band: 8, earfcnMin: 3450, earfcnMax: 3799, nOffsDl: 3450, dlFreqLow: 925.0 },
  { band: 9, earfcnMin: 3800, earfcnMax: 4149, nOffsDl: 3800, dlFreqLow: 1844.9 },
  { band: 10, earfcnMin: 4150, earfcnMax: 4749, nOffsDl: 4150, dlFreqLow: 2110.0 },
  { band: 11, earfcnMin: 4750, earfcnMax: 4949, nOffsDl: 4750, dlFreqLow: 1475.9 },
  { band: 12, earfcnMin: 5010, earfcnMax: 5179, nOffsDl: 5010, dlFreqLow: 729.0 },
  { band: 13, earfcnMin: 5180, earfcnMax: 5279, nOffsDl: 5180, dlFreqLow: 746.0 },
  { band: 14, earfcnMin: 5280, earfcnMax: 5379, nOffsDl: 5280, dlFreqLow: 758.0 },
  { band: 17, earfcnMin: 5730, earfcnMax: 5849, nOffsDl: 5730, dlFreqLow: 734.0 },
  { band: 18, earfcnMin: 5850, earfcnMax: 5999, nOffsDl: 5850, dlFreqLow: 860.0 },
  { band: 19, earfcnMin: 6000, earfcnMax: 6149, nOffsDl: 6000, dlFreqLow: 875.0 },
  { band: 20, earfcnMin: 6150, earfcnMax: 6449, nOffsDl: 6150, dlFreqLow: 791.0 },
  { band: 21, earfcnMin: 6450, earfcnMax: 6599, nOffsDl: 6450, dlFreqLow: 1495.9 },
  { band: 22, earfcnMin: 6600, earfcnMax: 7399, nOffsDl: 6600, dlFreqLow: 3510.0 },
  { band: 23, earfcnMin: 7500, earfcnMax: 7699, nOffsDl: 7500, dlFreqLow: 2180.0 },
  { band: 24, earfcnMin: 7700, earfcnMax: 8039, nOffsDl: 7700, dlFreqLow: 1525.0 },
  { band: 25, earfcnMin: 8040, earfcnMax: 8689, nOffsDl: 8040, dlFreqLow: 1930.0 },
  { band: 26, earfcnMin: 8690, earfcnMax: 9039, nOffsDl: 8690, dlFreqLow: 859.0 },
  { band: 27, earfcnMin: 9040, earfcnMax: 9209, nOffsDl: 9040, dlFreqLow: 852.0 },
  { band: 28, earfcnMin: 9210, earfcnMax: 9659, nOffsDl: 9210, dlFreqLow: 758.0 },
  { band: 29, earfcnMin: 9660, earfcnMax: 9769, nOffsDl: 9660, dlFreqLow: 717.0 },
  { band: 30, earfcnMin: 9770, earfcnMax: 9869, nOffsDl: 9770, dlFreqLow: 2350.0 },
  { band: 31, earfcnMin: 9870, earfcnMax: 9919, nOffsDl: 9870, dlFreqLow: 462.5 },
  { band: 32, earfcnMin: 9920, earfcnMax: 10359, nOffsDl: 9920, dlFreqLow: 1452.0 },
  { band: 33, earfcnMin: 36000, earfcnMax: 36199, nOffsDl: 36000, dlFreqLow: 1900.0 },
  { band: 34, earfcnMin: 36200, earfcnMax: 36349, nOffsDl: 36200, dlFreqLow: 2010.0 },
  { band: 35, earfcnMin: 36350, earfcnMax: 36949, nOffsDl: 36350, dlFreqLow: 1850.0 },
  { band: 36, earfcnMin: 36950, earfcnMax: 37549, nOffsDl: 36950, dlFreqLow: 1930.0 },
  { band: 37, earfcnMin: 37550, earfcnMax: 37749, nOffsDl: 37550, dlFreqLow: 1910.0 },
  { band: 38, earfcnMin: 37750, earfcnMax: 38249, nOffsDl: 37750, dlFreqLow: 2570.0 },
  { band: 39, earfcnMin: 38250, earfcnMax: 38649, nOffsDl: 38250, dlFreqLow: 1880.0 },
  { band: 40, earfcnMin: 38650, earfcnMax: 39649, nOffsDl: 38650, dlFreqLow: 2300.0 },
  { band: 41, earfcnMin: 39650, earfcnMax: 41589, nOffsDl: 39650, dlFreqLow: 2496.0 },
  { band: 42, earfcnMin: 41590, earfcnMax: 43589, nOffsDl: 41590, dlFreqLow: 3400.0 },
  { band: 43, earfcnMin: 43590, earfcnMax: 45589, nOffsDl: 43590, dlFreqLow: 3600.0 },
  { band: 44, earfcnMin: 45590, earfcnMax: 46589, nOffsDl: 45590, dlFreqLow: 703.0 },
  { band: 45, earfcnMin: 46590, earfcnMax: 46789, nOffsDl: 46590, dlFreqLow: 1447.0 },
  { band: 46, earfcnMin: 46790, earfcnMax: 54539, nOffsDl: 46790, dlFreqLow: 5150.0 },
  { band: 47, earfcnMin: 54540, earfcnMax: 55239, nOffsDl: 54540, dlFreqLow: 5855.0 },
  { band: 48, earfcnMin: 55240, earfcnMax: 56739, nOffsDl: 55240, dlFreqLow: 3550.0 },
  { band: 49, earfcnMin: 56740, earfcnMax: 58239, nOffsDl: 56740, dlFreqLow: 3550.0 },
  { band: 50, earfcnMin: 58240, earfcnMax: 59089, nOffsDl: 58240, dlFreqLow: 1432.0 },
  { band: 51, earfcnMin: 59090, earfcnMax: 59139, nOffsDl: 59090, dlFreqLow: 1427.0 },
  { band: 52, earfcnMin: 59140, earfcnMax: 60139, nOffsDl: 59140, dlFreqLow: 3300.0 },
  { band: 53, earfcnMin: 60140, earfcnMax: 60254, nOffsDl: 60140, dlFreqLow: 2483.5 },
  { band: 54, earfcnMin: 60255, earfcnMax: 60304, nOffsDl: 60255, dlFreqLow: 1670.0 },
  { band: 65, earfcnMin: 65536, earfcnMax: 66435, nOffsDl: 65536, dlFreqLow: 2110.0 },
  { band: 66, earfcnMin: 66436, earfcnMax: 67335, nOffsDl: 66436, dlFreqLow: 2110.0 },
  { band: 67, earfcnMin: 67336, earfcnMax: 67535, nOffsDl: 67336, dlFreqLow: 738.0 },
  { band: 68, earfcnMin: 67536, earfcnMax: 67835, nOffsDl: 67536, dlFreqLow: 753.0 },
  { band: 69, earfcnMin: 67836, earfcnMax: 68335, nOffsDl: 67836, dlFreqLow: 2570.0 },
  { band: 70, earfcnMin: 68336, earfcnMax: 68585, nOffsDl: 68336, dlFreqLow: 1995.0 },
  { band: 71, earfcnMin: 68586, earfcnMax: 68935, nOffsDl: 68586, dlFreqLow: 617.0 },
  { band: 72, earfcnMin: 68936, earfcnMax: 68985, nOffsDl: 68936, dlFreqLow: 461.0 },
  { band: 73, earfcnMin: 68986, earfcnMax: 69035, nOffsDl: 68986, dlFreqLow: 460.0 },
  { band: 74, earfcnMin: 69036, earfcnMax: 69465, nOffsDl: 69036, dlFreqLow: 1475.0 },
  { band: 75, earfcnMin: 69466, earfcnMax: 70315, nOffsDl: 69466, dlFreqLow: 1432.0 },
  { band: 76, earfcnMin: 70316, earfcnMax: 70365, nOffsDl: 70316, dlFreqLow: 1427.0 },
  { band: 85, earfcnMin: 70366, earfcnMax: 70545, nOffsDl: 70366, dlFreqLow: 728.0 },
  { band: 87, earfcnMin: 70546, earfcnMax: 70595, nOffsDl: 70546, dlFreqLow: 420.0 },
  { band: 88, earfcnMin: 70596, earfcnMax: 70645, nOffsDl: 70596, dlFreqLow: 422.0 },
  { band: 103, earfcnMin: 70646, earfcnMax: 70655, nOffsDl: 70646, dlFreqLow: 757.0 },
  { band: 106, earfcnMin: 70656, earfcnMax: 70705, nOffsDl: 70656, dlFreqLow: 935.0 },
  { band: 107, earfcnMin: 70706, earfcnMax: 71055, nOffsDl: 70706, dlFreqLow: 612.0 },
  { band: 108, earfcnMin: 71056, earfcnMax: 73335, nOffsDl: 71056, dlFreqLow: 470.0 },
  { band: 111, earfcnMin: 73386, earfcnMax: 73485, nOffsDl: 73386, dlFreqLow: 1820.0 }
];


const utils = {
    normalize: function(val, min, max) {
        // Clamp et normalisation
        return Math.min(Math.max((val - min) / (max - min), 0), 1);
    },

    getColorFromPalette: function(val, min, max, palette) {
        const normalized = utils.normalize(val, min, max);
        // Calcul de l'index dans la palette
        const idx = Math.floor(normalized * (palette.length - 1));
        return palette[idx];
    },

    /**
     * Calculates the direction 
     * @param {number} angle the azimuth value
     * @returns {number} Azimuth in direction (N, W, S, ...)
     */
    getCardinalDirection :function (angle) {
        const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        const index = Math.round(angle / 45) % 8;
        return directions[index];
    },

    
    /**
     * Calculates the azimuth (initial bearing) between two GPS points in degrees.
     * @param {number} lat1 Latitude of the starting point
     * @param {number} lon1 Longitude of the starting point
     * @param {number} lat2 Latitude of the destination point
     * @param {number} lon2 Longitude of the destination point
     * @returns {number} Azimuth in degrees (0° = North, 90° = East)
     */
    /*calculateAzimuth: function(lat1, lon1, lat2, lon2) {
        return getGreatCircleBearing(
            { latitude: lat1, longitude: lon1 },
            { latitude: lat2, longitude: lon2 }
        );
    },*/
    // Fonction pour convertir les degrés en radians
    toRadians: function (degrees) {
        return degrees * (Math.PI / 180);
    },

    // Fonction pour convertir les radians en degrés
    toDegrees: function (radians) {
        return radians * (180 / Math.PI);
    },

    // Fonction de calcul de l'azimut
    calculateAzimuth: function (lat1, lon1, lat2, lon2) {
        const start = { latitude: lat1, longitude: lon1 };
        const end = { latitude: lat2, longitude: lon2 };
        return this.getGreatCircleBearing(start, end);
    },

    // Fonction de calcul du cap (bearing) du grand cercle
    getGreatCircleBearing: function (start, end) {
        const φ1 = this.toRadians(start.latitude);
        const φ2 = this.toRadians(end.latitude);
        const Δλ = this.toRadians(end.longitude - start.longitude);

        const y = Math.sin(Δλ) * Math.cos(φ2);
        const x =
        Math.cos(φ1) * Math.sin(φ2) -
        Math.sin(φ1) * Math.cos(φ2) * Math.cos(Δλ);
        const θ = Math.atan2(y, x);

        return (this.toDegrees(θ) + 360) % 360;
    },

    beamToDirection: function(beamNumber, totalBeams = 8) {
    const directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
        if (isNaN(beamNumber) || totalBeams <= 0) return '-';

        let angle = (360 / totalBeams) * beamNumber;

        return directions[Math.round(angle / 45) % 8];
    },

    /**
     * search for the band corresponding to a given earfcn
     * @param earfcn earfcn
     * @returns the corresponding frequency (Mhz)
    */
    earfcnToFreqLte: function(earfcn) {
        for (let band of lteBands) {
            if (earfcn >= band.earfcnMin && earfcn <= band.earfcnMax) {
            return band.dlFreqLow + 0.1 * (earfcn - band.nOffsDl);
            }
        }
        return null; // EARFCN not found
    },



    
    /**
     * Deep-copies an object (copy of the object and its childs), 
     * by serializing it in JSON then decoding this JSON.
     * 
     * @param {*} obj Object to deep-copy.
     * @returns A deep-copy of obj.
     * 
     * @function
     */
    deepCopy: function (obj) { return JSON.parse(JSON.stringify(obj)); },

    /**
     * Finds the indexes of occurences of a given value in an array.
     * 
     * @param {Array} arr Array to search in. 
     * @param {*} obj Object to search. 
     * @returns An Array of indexes of obj occurences.
     * 
     * @function
     */
    indexesOf: function (arr, obj) {

        let result = [];
        for (let i in arr) if (obj === arr[i]) result.push(parseInt(i));
        return result;

    },

    /**
     * Searches an EARFCN and PCI pair amongs EARFCN / PCI lists.
     * 
     * @param {Array} earfcns EARFCN list to search in.
     * @param {Array} pcis PCI list to search in.
     * @param {number} earfcn EARFCN to search.
     * @param {number} pci PCI to search.
     * @returns The index of the pair in earfcns and pcis if found, -1 otherwise.
     * 
     * @function
     */
    indexOfEarpci: function (earfcns, pcis, earfcn, pci) {

        let earfcnIdx = utils.indexesOf(earfcns, earfcn);
        let pcisIdx = utils.indexesOf(pcis, pci);

        let inter = earfcnIdx.filter((e) => pcisIdx.includes(e))

        return inter.length !== 0 ? inter[0] : -1;

    },

    /**
     * Remove an EARFCN / PCI pair from lists of EARFCN / PCI.
     * 
     * @param {Array} earfcns EARFCN list.
     * @param {Array} pcis PCI list.
     * @param {number} earfcn EARFCN to remove from list.
     * @param {number} pci PCI to remove from list.
     * 
     * @function
     */
    removeEarpci: function (earfcns, pcis, earfcn, pci) {
        
        let i = utils.indexOfEarpci(earfcns, pcis, earfcn, pci);

        if (i !== -1) {
            earfcns.splice(i, 1);
            pcis.splice(i, 1);
        }

    },

    /**
     * Filters EARFCN / PCIS from a superset list, using a subset list.
     * 
     * @param {Array} earfcns Superset of EARFCNs 
     * @param {Array} pcis Superset of PCIs
     * @param {Array} beams Superset of Beams
     * @param {Array} reqEarfcns Subset of EARFCNs (if null, represents all EARFCNs from the superset).
     * @param {Array} reqPcis Subset of PCIs (if null, represents all PCIs from the superset).
     * @param {Array} reqBeams Subset of Beams
     * @returns Object which contains lists of filtered EARFCNs / PCIs, and list of indexes of EARFCNs / PCIs
     * pairs in the superset.
     * 
     * @function 
     */
    subEarpci: function (earfcns, pcis, beams=null, reqEarfcns=null, reqPcis=null, reqBeams=null) {
        // Result object.
        let result = {earfcns: [], pcis: [], beams: {}, indices: []};

        // Indexes of EARFCNs / PCIs of the subset.
        let subEarfcnsIdx = [];
        let subPcisIdx = [];

        // Filling subEarfcnsIdx.
        if (!reqEarfcns) subEarfcnsIdx = earfcns.map((_, i) => parseInt(i));    // If null : all elements.
        else reqEarfcns.forEach(
            (e) => utils.interPush(subEarfcnsIdx, utils.indexesOf(earfcns, e))
        );

        // Filling subPcisIdx.
        if (!reqPcis) subPcisIdx = pcis.map((_, i) => parseInt(i));             // If null : all elements.
        else reqPcis.forEach(
            (e) => utils.interPush(subPcisIdx, utils.indexesOf(pcis, e))
        );

        subEarfcnsIdx.filter((i) => {    // Filtering over indexes.

            let e = earfcns[i];     // EARFCN associated to the current index.
            let p = pcis[i];        // PCI associated to the current index.

            // Searching (e, p) pair in reqEarfcn and reqPcis if possible, evaluating in null otherwise.
            let inter = (reqEarfcns && reqPcis) ?
                utils.indexesOf(reqEarfcns, e).filter(
                    (ear) => utils.indexesOf(reqPcis, p).includes(ear))
                : null;

            // Pair found or not possible to find the pair.
            let sameIndex = (inter) ? inter.length !== 0  : true

            // If pair found (if possible), and PCi found.
            return subPcisIdx.includes(i) && sameIndex;
        }).forEach( // Filling result.
           (i) =>
           {
                result.earfcns.push(earfcns[i]);
                result.pcis.push(pcis[i]);
                let p = pcis[i];

                if (!beams || reqBeams && (!Array.isArray(reqBeams[p]) || !reqBeams[p] || reqBeams[p].includes("all") || reqBeams[p].includes(beams[i].toString()))) {
                    result.indices.push(i);
                }

                if (beams) {
                    if (result.beams[p] === undefined) result.beams[p] = [];
                    result.beams[p].push(beams[i]);
                }
            }

        );
        return result;
    },

    /**
     * Pushes elements of arrayB in arrayA if not already in arrayA.
     * 
     * @param {Array} arrayA Array where arrayB elements will be inserted.
     * @param {Array} arrayB Array of elements to be inserted into arrayA.
     */
    interPush: function (arrayA, arrayB) {
        arrayB.forEach(
            (elt) => { if (!arrayA.includes(elt)) arrayA.push(elt); }
        )
    }

}