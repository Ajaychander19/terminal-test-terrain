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

    calcDelimiters: function(voronoi, delimiters) {

        let result = [];

        let vorFeats = voronoi.features;

        let tempDels = [];

        for (let i in delimiters) {

            let del = delimiters[i];
            let feature = vorFeats[i];

            tempDels.push(del);

            if (feature !== undefined) {

                for (let j in tempDels) {

                    let tmpd = tempDels[j];
                    let line = turf.lineString([[tmpd.lngA, tmpd.latA], [tmpd.lngB, tmpd.latB]]);

                    let inter = turf.lineIntersect(line, feature).features;

                    if (inter.length !== 0) result.push(
                        turf.lineString([tmpd.lngA, tmpd.latA], inter[0].geometry.coordinates)
                    );

                }

                tempDels = [];

            }

        }

        return result;

    }

}