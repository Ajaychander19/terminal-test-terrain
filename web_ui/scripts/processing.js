/**
 * Contains data processing methods, used to calculate some geometrical elements from data.
 * 
 * @namespace
 */
const processing = {

    /**
     * Calculates Voronoi diagram from antennas data.
     * The calculation is done using turf.js Voronoi function, which produces
     * GeoJSON data of the Voronoi diagram.
     * 
     * @param {*} antennas Antennas object from the file reader object.
     * @returns GeoJSON Voronoi diagram obtained from antennas.
     * 
     * @function
     */
    calcVoronoi: function (antennas) {
    
        if (!Array.isArray(antennas)) {
            antennas = Object.values(antennas);
        }
        let bsPoints = antennas.map(ant => turf.point([ant.lng, ant.lat]));
        let bsFeats = turf.featureCollection(bsPoints);
        let mercatorPoints = turf.toMercator(bsFeats);
        let bbox = turf.bbox(mercatorPoints);
        let voronoiMerc = turf.voronoi(mercatorPoints, { bbox });
        return turf.toWgs84(voronoiMerc);
    },

    
    ///Old version
    /*calcVoronoi: function (antennas) {
        

        // Base station coordinates list.
        let bsPoints = [];

        // Listing coordinates...
        for (let i in antennas) {
            let ant = antennas[i];
            bsPoints.push(turf.point([ant.lng, ant.lat]));
        }

        // Calculating GeoJSON features.
        let bsFeats = turf.featureCollection(bsPoints);
        let bbox = turf.bbox(bsFeats);

        return turf.voronoi(bsFeats, {bbox: bbox});

    },*/


    /**
     * Calculates sectors delimitation lines from delimiters data.
     * Produced lines are GeoJSON objects made with turf.js library. These
     * line are truncated in order to not go outside corresponding Voronoi cell.
     * 
     * @param {*} voronoi Voronoi diagram GeoJSON object.
     * @param {*} antennas Antennas object from the file reader object.
     * @returns Array of truncated sector delimitation lines which match with Voronoi cells.
     * 
     * @function
     */
    calcDelimiters: function (voronoi, antennas) {

        // List of calculated delimiters.
        let result = [];

        let vorFeats = voronoi.features;    // Voronoi polygons.
        let antIndex = 0;                   // Position of the antenna Voronoi polygon.

        // For each antenna...
        for (let i in antennas) {

            let ant = antennas[i];              // Current antenna.
            let feature = vorFeats[antIndex];   // Antenna Voronoi polygon.

            // For each delimiter of the antenna...
            ant.dels.forEach((del) => {

                    // GeoJSON of the delimiter.
                    let line = turf.lineString([[ant.lng, ant.lat], [del.lngB, del.latB]]);

                    // Intersection between the delimiter and the hull of the Voronoi cell.
                    let inter = turf.lineIntersect(line, feature).features;

                    // Truncating the delimiter following the hull of the Voronoi cell.
                    if (inter.length !== 0) result.push(
                        turf.lineString([[ant.lng, ant.lat], inter[0].geometry.coordinates])
                    );
            });

            antIndex++;

        }
        

        return result;

    },

    /**
     * Calculates antennas directivity line from antennas directivity data.
     * Produced lines are GeoJSON objects made with turf.js library.
     * 
     * @param {Array} antDirs Antenna directivity data from the file reader object.
     * @returns Antenna directivity GeoJSON line.
     * 
     * @function
     */
    calcAntennas: function (antDirs) {
        return antDirs.map((antDir) =>
            turf.lineString(
                [[antDir.lngA, antDir.latA], [antDir.lngB, antDir.latB]],
                {
                    cartoNum: antDir.cartoNum 
                }
            )
        );
    },
    getTechnologies: function (techno) {
        return techno.map(techno => techno.technology);
    },

    getVersions: function (version) {
    return version.map(v => v.version);
}


}