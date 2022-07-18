const processing = {

    calcVoronoi: function(antennas) {

        let bsPoints = [];

        for (let i in antennas) {
            let ant = antennas[i];
            bsPoints.push(turf.point([ant.lng, ant.lat]));
        }

        let bsFeats = turf.featureCollection(bsPoints);
        let bbox = turf.bbox(bsFeats);

        return turf.voronoi(bsFeats, {bbox: bbox});

    },

    calcDelimiters: function(voronoi, antennas) {

        let result = [];

        let vorFeats = voronoi.features;
        let antIndex = 0;

        for (let i in antennas) {

            let ant = antennas[i];
            let feature = vorFeats[antIndex];

            for (let j in ant.dels) {

                let del = ant.dels[j];

                let line = turf.lineString([[ant.lng, ant.lat], [del.lngB, del.latB]]);

                let inter = turf.lineIntersect(line, feature).features;

                if (inter.length !== 0) result.push(
                    turf.lineString([[ant.lng, ant.lat], inter[0].geometry.coordinates])
                );
            }

            antIndex++;

        }

        return result;

    }

}