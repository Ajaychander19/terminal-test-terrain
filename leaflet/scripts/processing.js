const processing = {

    calcVoronoi: function (antennas) {

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

    },

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

    calcAntennas: function (antDirs) {

        return antDirs.map(
            (antDir) => turf.lineString([[antDir.lngA, antDir.latA], [antDir.lngB, antDir.latB]])
        );

    }

}